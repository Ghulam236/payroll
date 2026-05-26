from rest_framework import serializers
from pydantic import ValidationError as PydanticValidationError
from .models import ClientPayrollRule, SalaryComponent
from .validators import RuleConfigValidatorFactory

# serlzers for validation 

class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'

class ClientPayrollRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayrollRule
        fields = '__all__'

    def validate(self, data):
        calc_type = data.get('calculation_type')
        rule_config = data.get('rule_config')

        # Run dynamic payload structure validation using our Factory
        try:
            RuleConfigValidatorFactory.validate(calc_type, rule_config)
        except PydanticValidationError as e:
            raise serializers.ValidationError({"rule_config": e.errors()})

        return data