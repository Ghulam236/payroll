from django.contrib import admin
from django.urls import path
from payroll_engine.views import (
    TriggerPayrollCalculationView, 
    EmployeeCreateView, 
    FetchSavedPayrollReportView , # ◄── Add import
    DynamicRuleEngineAPIView,
    SalaryStructureAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/employee/create/', EmployeeCreateView.as_view(), name='create_employee'),
    path('api/payroll/calculate/', TriggerPayrollCalculationView.as_view(), name='calculate_payroll'),
    
    # 💡 Fresh GET Endpoint: Pass the employee UUID and period inside the URL path parameter
    path('api/payroll/report/<uuid:employee_uuid>/<str:period>/', FetchSavedPayrollReportView.as_view(), name='fetch_payroll_report'),
    path('api/v2/compliance/rules/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_base'),
    path('api/v2/compliance/rules/<int:structure_id>/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_detail'),
    

    #
    # 🏢 Salary Structure Template CRUD
    path('api/v2/compliance/structures/', SalaryStructureAPIView.as_view(), name='structures_base'),
    path('api/v2/compliance/structures/<int:structure_id>/', SalaryStructureAPIView.as_view(), name='structures_detail'),
    
]