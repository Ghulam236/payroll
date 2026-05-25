from celery import shared_task
from .models import EmployeeORM, PayrollLedgerORM, SystemRuleConfigurationORM
from payroll_engine.domain.payroll_models import EmployeeProfile, AttendanceMetrics
from payroll_engine.components.pf import ProvidentFundComponent
from payroll_engine.components.pt import ProfessionalTaxComponent
from payroll_engine.components.base import IndianPayrollEngine
from django.db import IntegrityError

@shared_task(bind=True, max_retries=3)
def process_monthly_payroll_task(self, employee_uuid_str: str, month_year_str: str, lop_days: int):
    try:
        
        
        emp_record = EmployeeORM.objects.get(uuid=employee_uuid_str)
        config_record = SystemRuleConfigurationORM.objects.filter(is_active=True).first()
        
        profile = EmployeeProfile(
            employee_id=str(emp_record.uuid),
            name=emp_record.full_name,
            work_state=emp_record.state_tax_region,
            pan_number=emp_record.pan,
            selected_regime=emp_record.tax_regime
        )
        attendance = AttendanceMetrics(days_in_month=30, unapproved_lop_days=lop_days)
        
        engine = IndianPayrollEngine()
        engine.register_component(ProvidentFundComponent())
        engine.register_component(ProfessionalTaxComponent(work_state=profile.work_state))
        
        results = engine.calculate_monthly_payroll(
            employee=profile,
            earnings=emp_record.base_salary_structure_dict,
            attendance=attendance,
            configuration_rules=config_record.json_rules_matrix
        )
        
        PayrollLedgerORM.objects.create(
            employee=emp_record,
            pay_period=month_year_str,
            gross_total=results["earnings_summary"]["gross_salary"],
            net_payout=results["net_take_home_payout"],
            breakdown_log=results
        )

        return f"Success processing payroll calculation ledger entry for: {profile.name}"
    except IntegrityError as exc:
        # 💡 DO NOT RETRY IF IT'S A DUPLICATE. Log a clean message instead.
        print(f"⚠️ Constraint triggered: Payroll already exists for employee {employee_uuid_str} for period {month_year_str}.")
        return {"status": "SKIPPED_DUPLICATE"}
        
    except Exception as exc:
        # Retry only for unexpected system/network drops
        raise self.retry(exc=exc, countdown=5)
