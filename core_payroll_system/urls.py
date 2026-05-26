# from django.contrib import admin
# from django.urls import path
# from payroll_engine.views import (
#     TriggerPayrollCalculationView, 
#     EmployeeCreateView, 
#     FetchSavedPayrollReportView , # ◄── Add import
#     DynamicRuleEngineAPIView,
#     SalaryStructureAPIView
# )
# ########
# from rest_framework.routers import DefaultRouter
# from .views import SalaryComponentViewSet, ClientPayrollRuleViewSet

# # Instantiate the DRF router system
# router = DefaultRouter()
# router.register(r'salary-components', SalaryComponentViewSet, basename='salary-component')
# router.register(r'client-rules', ClientPayrollRuleViewSet, basename='client-rule')

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/employee/create/', EmployeeCreateView.as_view(), name='create_employee'),
#     path('api/payroll/calculate/', TriggerPayrollCalculationView.as_view(), name='calculate_payroll'),
    
#     # 💡 Fresh GET Endpoint: Pass the employee UUID and period inside the URL path parameter
#     path('api/payroll/report/<uuid:employee_uuid>/<str:period>/', FetchSavedPayrollReportView.as_view(), name='fetch_payroll_report'),
#     path('api/v2/compliance/rules/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_base'),
#     path('api/v2/compliance/rules/<int:structure_id>/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_detail'),
    

#     #
#     # 🏢 Salary Structure Template CRUD
#     path('api/v2/compliance/structures/', SalaryStructureAPIView.as_view(), name='structures_base'),
#     path('api/v2/compliance/structures/<int:structure_id>/', SalaryStructureAPIView.as_view(), name='structures_detail'),
#     path('api/v1/', include(router.urls)),
# ]



from django.contrib import admin
from django.urls import path, include  # ◄── Crucial Fix
from rest_framework.routers import DefaultRouter

from payroll_engine.views import (
    TriggerPayrollCalculationView, 
    EmployeeCreateView, 
    FetchSavedPayrollReportView,
    DynamicRuleEngineAPIView,
    SalaryStructureAPIView,
    SalaryComponentViewSet,    # Import your ViewSets
    ClientPayrollRuleViewSet
)

# Instantiate the DRF router system
router = DefaultRouter()
router.register(r'salary-components', SalaryComponentViewSet, basename='salary-component')
router.register(r'client-rules', ClientPayrollRuleViewSet, basename='client-rule')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/employee/create/', EmployeeCreateView.as_view(), name='create_employee'),
    path('api/payroll/calculate/', TriggerPayrollCalculationView.as_view(), name='calculate_payroll'),
    
    # Fresh GET Endpoint for reports
    path('api/payroll/report/<uuid:employee_uuid>/<str:period>/', FetchSavedPayrollReportView.as_view(), name='fetch_payroll_report'),
    
    # Dynamic Compliance Rules V2 Endpoints
    path('api/v2/compliance/rules/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_base'),
    path('api/v2/compliance/rules/<int:structure_id>/', DynamicRuleEngineAPIView.as_view(), name='dynamic_rules_detail'),
    
    # Salary Structure Template CRUD
    path('api/v2/compliance/structures/', SalaryStructureAPIView.as_view(), name='structures_base'),
    path('api/v2/compliance/structures/<int:structure_id>/', SalaryStructureAPIView.as_view(), name='structures_detail'),
    
    # Dashboard Rules CRUD V1 (Router-driven)
    path('api/v1/', include(router.urls)),
]