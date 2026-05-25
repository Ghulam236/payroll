from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class EmployeeProfile:
    employee_id: str
    name: str
    work_state: str
    pan_number: str
    selected_regime: str

@dataclass(frozen=True)
class AttendanceMetrics:
    days_in_month: int
    unapproved_lop_days: int