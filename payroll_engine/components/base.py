from abc import ABC, abstractmethod
from typing import Dict, Any, List
from payroll_engine.domain.payroll_models import AttendanceMetrics, EmployeeProfile

class BasePayrollComponent(ABC):
    @abstractmethod
    def calculate(self, base_earnings: Dict[str, float], attendance: AttendanceMetrics, config_rules: Dict[str, Any]) -> float:
        pass

class IndianPayrollEngine:
    def __init__(self) -> None:
        self._pipeline: List[BasePayrollComponent] = []

    def register_component(self, component: BasePayrollComponent) -> None:
        self._pipeline.append(component)

    def calculate_monthly_payroll(self, employee: EmployeeProfile, earnings: Dict[str, float], attendance: AttendanceMetrics, configuration_rules: Dict[str, Any]) -> Dict[str, Any]:
        gross_earnings = sum(earnings.values())
        breakdown_deductions = {}
        
        for component in self._pipeline:
            component_identifier = component.__class__.__name__
            deduction_amount = component.calculate(earnings, attendance, configuration_rules)
            breakdown_deductions[component_identifier] = deduction_amount
            
        total_deductions = sum(breakdown_deductions.values())
        return {
            "employee_id": employee.employee_id,
            "earnings_summary": {"gross_salary": round(gross_earnings, 2), "breakdown": earnings},
            "statutory_deductions": {"total": round(total_deductions, 2), "breakdown": breakdown_deductions},
            "net_take_home_payout": round(gross_earnings - total_deductions, 2)
        }