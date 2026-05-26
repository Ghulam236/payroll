from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ClientPayrollRule

class PayrollRuleDashboardService:
    
    @staticmethod
    @transaction.atomic
    def create_or_update_rule(client_id: int, component_code: str, validated_data: dict) -> ClientPayrollRule:
        """
        Implements safe rule update logic. Instead of overwriting history, 
        it caps the active rule and spawns a new version cleanly.
        """
        effective_from = validated_data.get('effective_from')
        
        # 1. Look for a currently active configuration rule
        current_active_rule = ClientPayrollRule.objects.filter(
            client_id=client_id,
            component_id=component_code,
            effective_to__isnull=True
        ).first()
        
        if current_active_rule:
            # Prevent retrofitting rules to a date that broke past historical order bounds
            if current_active_rule.effective_from >= effective_from:
                raise ValueError("New effective date must be later than the current rule's starting date.")
                
            # Close out out-of-date row safely
            current_active_rule.effective_to = effective_from - timedelta(days=1)
            current_active_rule.save()

        # 2. Build the brand-new active rule row structure
        new_rule = ClientPayrollRule.objects.create(**validated_data)
        return new_rule

    @staticmethod
    @transaction.atomic
    def soft_delete_rule(rule_id: int) -> None:
        """
        Soft deletes a rule by stamping its effective window closed today,
        preserving historical calculation safety.
        """
        rule = ClientPayrollRule.objects.get(id=rule_id)
        today = timezone.now().date()
        
        if rule.effective_from > today:
            # If the rule was scheduled for the future and never ran, hard delete it
            rule.delete()
        else:
            # If it's running/has run, close it off to preserve history
            rule.effective_to = today
            rule.save()