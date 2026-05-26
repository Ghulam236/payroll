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



########## new implwwmntio from here ###########
from django.core.exceptions import ValidationError

class SalaryComponentCategory(models.TextChoices):
    BASE = 'BASE', 'Base Salary'
    ALLOWANCE = 'ALLOWANCE', 'Allowance'
    DEDUCTION = 'DEDUCTION', 'Deduction'

class CalculationType(models.TextChoices):
    FLAT = 'FLAT', 'Fixed Amount'
    PERCENTAGE = 'PERCENTAGE', 'Percentage Based'
    SLAB_RANGE = 'SLAB_RANGE', 'Slab/Range Based'
    CONDITION_BASED = 'CONDITION_BASED', 'Conditional Threshold'

class SalaryComponent(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="e.g., BASIC, HRA, PF, PT")
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SalaryComponentCategory.choices)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class ClientPayrollRule(models.Model):
    client_id = models.IntegerField(help_text="ID of the client company/tenant")
    component = models.ForeignKey(SalaryComponent, on_delete=models.PROTECT, to_field='code')
    calculation_type = models.CharField(max_length=20, choices=CalculationType.choices)
    
    # Stores the raw JSON format for the specific type
    rule_config = models.JSONField(help_text="Dynamic configuration object tailored to calculation_type")
    
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_payroll_rules'
        ordering = ['-effective_from']

    def __str__(self):
        return f"Client {self.client_id} - {self.component_id} ({self.calculation_type})"