import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import EmployeeORM, PayrollLedgerORM
from .tasks import process_monthly_payroll_task

from django.shortcuts import get_object_or_404
from .models import EmployeeORM, PayrollLedgerORM, SystemRuleConfigurationORM
from .models import SalaryStructure

@method_decorator(csrf_exempt, name='dispatch')
class EmployeeCreateView(View):
    """Handles Postman HTTP requests to seed dynamic employee entries into the DB."""
    
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
            
            # Extract payroll breakdown data structures securely
            new_worker = EmployeeORM.objects.create(
                full_name=payload.get("full_name"),
                state_tax_region=payload.get("state_tax_region", "Maharashtra"),
                pan=payload.get("pan"),
                tax_regime=payload.get("tax_regime", "NEW_REGIME"),
                base_salary_structure_dict=payload.get("salary_structure")
            )
            
            return JsonResponse({
                "status": "EMPLOYEE_RECORD_CREATED",
                "employee_uuid": str(new_worker.uuid),
                "message": f"Successfully onboarded {new_worker.full_name} into the database system."
            }, status=201)
            
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class TriggerPayrollCalculationView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
            emp_uuid = payload.get("employee_uuid")
            try:
                emp_record = EmployeeORM.objects.get(uuid=emp_uuid)
            except EmployeeORM.DoesNotExist:
                print(f"❌ Cancelled: Employee {employee_uuid_str} no longer exists in the system database.")
                return {"status": "ABORTED_NOT_FOUND"}
            period = payload.get("period")
            lop_days = int(payload.get("lop_days", 0))
            if lop_days < 0 or lop_days > 31:
                return JsonResponse({
                    "error": "INVALID_ATTENDANCE_METRICS",
                    "message": "Loss-of-Pay (LOP) days must be between 0 and 31 days."
                }, status=400)
            if PayrollLedgerORM.objects.filter(employee__uuid=emp_uuid, pay_period=period).exists():
                return JsonResponse({
                    "status": "REJECTED",
                    "error": "DUPLICATE_PROCESSING_REJECTED",
                    "message": f"Payroll for employee {emp_uuid} has already been completed for {period}."
                }, status=409) # Clean 409 Conflict Response
            task_receipt = process_monthly_payroll_task.delay(
                payload.get("employee_uuid"),
                payload.get("period"),
                payload.get("lop_days", 0)
            )
            return JsonResponse({
                "status": "QUEUED",
                "message": "Asynchronous pipeline processing initialized.",
                "celery_task_id": task_receipt.id
            }, status=202)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)



class FetchSavedPayrollReportView(View):
    """Dedicated fast GET API endpoint for managers to review saved payroll data from DB."""
    
    def get(self, request, employee_uuid, period, *args, **kwargs):
        try:
            # 1. Locate the employee using their UUID string
            employee = get_object_or_404(EmployeeORM, uuid=employee_uuid)
            
            # 2. Grab the specific saved payroll ledger entry matching the period
            ledger_record = get_object_or_404(
                PayrollLedgerORM, 
                employee=employee, 
                pay_period=period
            )
            
            # 3. Pull the active rules matrix configuration to append to the report context
            config_record = SystemRuleConfigurationORM.objects.filter(is_active=True).first()
            rules_matrix = config_record.json_rules_matrix if config_record else {}
            
            # 4. Return the exact saved data structure directly to Postman
            return JsonResponse({
                "status": "FETCH_SUCCESSFUL",
                "review_salary_detail": {
                    "salary_information": ledger_record.breakdown_log,
                    "statutory_rules_applied": rules_matrix
                }
            }, status=200)
            
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)

from .models import SalaryStructure, DynamicSalaryComponentRule
from .utils import recursive_schema_merge


@method_decorator(csrf_exempt, name='dispatch')
class DynamicRuleEngineAPIView(View):
    """
    Centralized API Engine driving Create, Read, Update, and Delete functions 
    over the infinitely extensible Indian compliance matrix fields.
    """

    def get(self, request, structure_id=None, *args, **kwargs):
        """
        1. READ / RETRIEVE ACTIONS
        Fetch all active runtime components mapped to an execution structure profile.
        """
        if structure_id:
            structure = get_object_or_404(SalaryStructure, pk=structure_id)
            rules = DynamicSalaryComponentRule.objects.filter(structure=structure)
            rules_payload = [{
                "component_code": r.component_code,
                "name": r.name,
                "sequence": r.sequence,
                "configuration_schema": r.configuration_schema,
                "is_active": r.is_active
            } for r in rules]
            
            return JsonResponse({
                "status": "SUCCESS",
                "structure": {"id": structure.id, "name": structure.name, "state": structure.state_code},
                "rules": rules_payload
            }, status=200)
            
        # List all structure blueprints globally if no ID is targeted
        structures = SalaryStructure.objects.all()
        output = [{"id": s.id, "name": s.name, "state": s.state_code} for s in structures]
        return JsonResponse({"status": "SUCCESS", "salary_structures": output}, status=200)

    def post(self, request, *args, **kwargs):
        """
        2. CREATE ACTION
        Seeds a completely fresh calculation block rule mapping to a structure container.
        """
        try:
            payload = json.loads(request.body)
            structure_id = payload.get("structure_id")
            structure = get_object_or_404(SalaryStructure, pk=structure_id)
            
            new_rule = DynamicSalaryComponentRule.objects.create(
                structure=structure,
                component_code=payload.get("component_code").upper().strip(),
                name=payload.get("name"),
                sequence=payload.get("sequence"),
                configuration_schema=payload.get("configuration_schema", {})
            )
            return JsonResponse({
                "status": "COMPLIANCE_RULE_CREATED",
                "id": new_rule.id,
                "message": f"Successfully loaded framework parameters for {new_rule.component_code}."
            }, status=201)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)

    def patch(self, request, structure_id, *args, **kwargs):
        """
        3. DYNAMIC DEEP UPDATE ACTION
        HR admins can pass any new properties directly here. The patch engine merges 
        nested arrays safely without losing surrounding configuration fields.
        """
        try:
            payload = json.loads(request.body)
            component_code = payload.get("component_code", "").upper().strip()
            
            # Target the specific dynamic rule record inside the structural registry
            rule_target = get_object_or_404(
                DynamicSalaryComponentRule, 
                structure_id=structure_id, 
                component_code=component_code
            )
            
            # Extract incoming schema parameters patch fragment
            incoming_patch = payload.get("configuration_schema", {})
            
            # Execute our deep merge safety traversal algorithm
            current_compiled_schema = rule_target.configuration_schema
            updated_schema = recursive_schema_merge(current_compiled_schema, incoming_patch)
            
            # Bind back properties, save records
            rule_target.configuration_schema = updated_schema
            if "sequence" in payload:
                rule_target.sequence = payload.get("sequence")
            if "name" in payload:
                rule_target.name = payload.get("name")
            rule_target.save()
            
            return JsonResponse({
                "status": "SCHEMA_MUTATION_SUCCESSFUL",
                "message": f"Successfully updated nested fields for rule component {component_code}.",
                "current_schema_state": rule_target.configuration_schema
            }, status=200)
            
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)

    def delete(self, request, structure_id, *args, **kwargs):
        """
        4. DELETE ACTION
        Drops a rule component directly from a selected salary configuration template.
        """
        payload = json.loads(request.body)
        component_code = payload.get("component_code", "").upper().strip()
        
        deleted_rows, _ = DynamicSalaryComponentRule.objects.filter(
            structure_id=structure_id, 
            component_code=component_code
        ).delete()
        
        return JsonResponse({
            "status": "PURGE_COMPLETE",
            "message": f"Dropped component {component_code}. Cleared {deleted_rows} rule vectors."
        }, status=200)
@method_decorator(csrf_exempt, name='dispatch')
class SalaryStructureAPIView(View):
    """
    Provides full HR CRUD controls over Salary Structure templates.
    """

    def get(self, request, structure_id=None, *args, **kwargs):
        """
        1. READ (List All or Retrieve One)
        """
        if structure_id:
            structure = get_object_or_404(SalaryStructure, pk=structure_id)
            return JsonResponse({
                "status": "SUCCESS",
                "structure": {
                    "id": structure.id,
                    "name": structure.name,
                    "state_code": structure.state_code,
                    "is_active": structure.is_active
                }
            }, status=200)

        structures = SalaryStructure.objects.all()
        output = [{
            "id": s.id,
            "name": s.name,
            "state_code": s.state_code,
            "is_active": s.is_active
        } for s in structures]
        return JsonResponse({"status": "SUCCESS", "salary_structures": output}, status=200)

    def post(self, request, *args, **kwargs):
        """
        2. CREATE A STRUCTURE
        """
        try:
            payload = json.loads(request.body)
            if not payload.get("name") or not payload.get("state_code"):
                return JsonResponse({"error": "Missing required fields: 'name' or 'state_code'"}, status=400)

            structure = SalaryStructure.objects.create(
                name=payload.get("name"),
                state_code=payload.get("state_code").upper().strip(),
                is_active=payload.get("is_active", True)
            )
            return JsonResponse({
                "status": "STRUCTURE_CREATED",
                "structure_id": structure.id,
                "message": f"Structure template '{structure.name}' created successfully."
            }, status=201)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)

    def put(self, request, structure_id, *args, **kwargs):
        """
        3. UPDATE A STRUCTURE (Full/Partial Update)
        """
        try:
            structure = get_object_or_404(SalaryStructure, pk=structure_id)
            payload = json.loads(request.body)

            structure.name = payload.get("name", structure.name)
            structure.state_code = payload.get("state_code", structure.state_code).upper().strip()
            structure.is_active = payload.get("is_active", structure.is_active)
            structure.save()

            return JsonResponse({
                "status": "STRUCTURE_UPDATED",
                "message": f"Successfully updated structure ID {structure_id}.",
                "structure": {
                    "id": structure.id,
                    "name": structure.name,
                    "state_code": structure.state_code,
                    "is_active": structure.is_active
                }
            }, status=200)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=400)

    def delete(self, request, structure_id, *args, **kwargs):
        """
        4. DELETE A STRUCTURE
        """
        structure = get_object_or_404(SalaryStructure, pk=structure_id)
        structure_name = structure.name
        structure.delete()  # 💡 This will cascade delete all linked rules automatically!
        
        return JsonResponse({
            "status": "STRUCTURE_DELETED",
            "message": f"Permanently removed structure template '{structure_name}' and its associated rules."
        }, status=200)