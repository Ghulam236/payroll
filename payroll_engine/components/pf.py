from .base import BasePayrollComponent
from payroll_engine.domain.payroll_models import AttendanceMetrics
from typing import Dict, Any

class ProvidentFundComponent(BasePayrollComponent):
    def calculate(self, base_earnings: Dict[str, float], attendance: AttendanceMetrics, config_rules: Dict[str, Any]) -> float:
        raw_basic = base_earnings.get("basic_salary", 0.0)
        attendance_ratio = (attendance.days_in_month - attendance.unapproved_lop_days) / attendance.days_in_month
        adjusted_basic = raw_basic * attendance_ratio
        
        pf_config = config_rules.get("provident_fund", {})
        ceiling = pf_config.get("statutory_wage_ceiling", 15000.00)
        contribution_rate = pf_config.get("employee_contribution_rate", 0.12)
        
        calculation_base = min(adjusted_basic, ceiling) if pf_config.get("enforce_ceiling", True) else adjusted_basic
        return round(calculation_base * contribution_rate, 2)