from .base import BasePayrollComponent
from payroll_engine.domain.payroll_models import AttendanceMetrics
from typing import Dict, Any

class ProfessionalTaxComponent(BasePayrollComponent):
    def __init__(self, work_state: str):
        self._work_state = work_state

    def calculate(self, base_earnings: Dict[str, float], attendance: AttendanceMetrics, config_rules: Dict[str, Any]) -> float:
        gross_earnings = sum(base_earnings.values())
        state_slabs = config_rules.get("professional_tax", {}).get(self._work_state, [])
        
        for slab in state_slabs:
            if slab["min_gross"] <= gross_earnings <= slab["max_gross"]:
                return float(slab["deduction_amount"])
        return 0.0