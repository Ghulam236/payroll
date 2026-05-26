from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Union

# --- 1. Flat Schema ---
class FlatConfigSchema(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "INR"

# --- 2. Percentage Schema ---
class PercentageConfigSchema(BaseModel):
    percentage_value: float = Field(gt=0, le=100)
    calculated_on_component: str
    max_cap_limit: Optional[float] = None

# --- 3. Slab Range Schema ---
class SlabItem(BaseModel):
    min_range: float
    max_range: Optional[float] = None
    type: Literal["FLAT", "PERCENTAGE"]
    value: float

class SlabRangeConfigSchema(BaseModel):
    calculated_on_value: str
    slabs: List[SlabItem]

    @field_validator('slabs')
    def validate_slabs(cls, v):
        # Ensure the ranges follow an ascending, non-overlapping sequence
        sorted_slabs = sorted(v, key=lambda x: x.min_range)
        for i in range(len(sorted_slabs) - 1):
            if sorted_slabs[i].max_range is None:
                raise ValueError("Only the last slab range can have an open max_range (null).")
            if sorted_slabs[i].max_range > sorted_slabs[i+1].min_range:
                raise ValueError(f"Slab overlap detected between {sorted_slabs[i]} and {sorted_slabs[i+1]}")
        return v

# --- Factory to resolve the right validator (Open/Closed Principle) ---
class RuleConfigValidatorFactory:
    _MAP = {
        'FLAT': FlatConfigSchema,
        'PERCENTAGE': PercentageConfigSchema,
        'SLAB_RANGE': SlabRangeConfigSchema
    }

    @classmethod
    def validate(cls, calc_type: str, data: dict):
        schema = cls._MAP.get(calc_type)
        if not schema:
            # If CONDITION_BASED is handled later, it's open for extension here
            return True 
        
        # Pydantic raises ValidationError if formatting is wrong
        schema(**data)