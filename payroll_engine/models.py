from django.db import models
import uuid
from django.core.serializers.json import DjangoJSONEncoder

class EmployeeORM(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=255)
    state_tax_region = models.CharField(max_length=100)  # e.g., "Maharashtra"
    pan = models.CharField(max_length=10)
    tax_regime = models.CharField(max_length=20, default="NEW_REGIME")
    base_salary_structure_dict = models.JSONField()  # Store basic_salary, hra, allowances

    def __str__(self):
        return self.full_name

class SystemRuleConfigurationORM(models.Model):
    is_active = models.BooleanField(default=True)
    json_rules_matrix = models.JSONField()  # Holds statutory limits dynamically

class PayrollLedgerORM(models.Model):
    employee = models.ForeignKey(EmployeeORM, on_delete=models.CASCADE)
    pay_period = models.CharField(max_length=7)  # MM-YYYY
    gross_total = models.FloatField()
    net_payout = models.FloatField()
    breakdown_log = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    # 🛡️ THIS IS THE LINE OF CODE FOR THE DATABASE CONSTRAINT:
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'pay_period'], 
                name='unique_employee_payroll_per_period'
            )
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.pay_period}"

class SalaryStructure(models.Model):
    """Container grouping dynamic rules for localized states/grades."""
    name = models.CharField(max_length=150, help_text="e.g., Maharashtra Corporate Template")
    state_code = models.CharField(max_length=10) # e.g., MH, KA, DL
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DynamicSalaryComponentRule(models.Model):
    """
    Extensible execution rule block. 
    If your manager asks to add any new property, it simply flows straight 
    into the configuration_schema matrix without changing the SQL layout.
    """
    structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name="rules")
    component_code = models.CharField(max_length=50, help_text="e.g., PF, PT, HRA, BASIC")
    name = models.CharField(max_length=150, help_text="e.g., Provident Fund Deduction Rule")
    sequence = models.PositiveIntegerField(help_text="Processing priority order index.")
    
    # 🛡️ THE EXTENSIBLE CORE: Holds all properties, ceilings, brackets, or custom rates dynamically
    configuration_schema = models.JSONField(
        encoder=DjangoJSONEncoder,
        default=dict,
        help_text="Houses nested computational schema specifications variables."
    )
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence']
        unique_together = ('structure', 'component_code')

    def __str__(self):
        return f"{self.structure.name} -> {self.component_code}"