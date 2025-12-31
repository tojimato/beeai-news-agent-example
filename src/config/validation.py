"""
Data validation models using Pydantic for strict schema enforcement.

Provides validation for configuration objects to ensure data integrity
and provide clear error messages at load time rather than runtime.
"""

from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class RecipientModel(BaseModel):
    """Strict validation model for recipient configuration.
    
    Ensures all required fields are present, correctly typed, and valid.
    """
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    email: EmailStr
    profession: str
    name: str
    hour: int
    minute: int
    language: Literal["tr", "en"] = "tr"
    
    @field_validator('hour')
    @classmethod
    def validate_hour(cls, v: int) -> int:
        """Validate hour is 0-23."""
        if not 0 <= v <= 23:
            raise ValueError(f"hour must be 0-23, got {v}")
        return v
    
    @field_validator('minute')
    @classmethod
    def validate_minute(cls, v: int) -> int:
        """Validate minute is 0-59."""
        if not 0 <= v <= 59:
            raise ValueError(f"minute must be 0-59, got {v}")
        return v
    
    @field_validator('profession')
    @classmethod
    def validate_profession(cls, v: str) -> str:
        """Profession must be non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError(f"profession must be non-empty string, got {v}")
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Name must be non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError(f"name must be non-empty string, got {v}")
        return v.strip()


class RecipientsListModel(BaseModel):
    """Wrapper model for list of recipients with validation."""
    recipients: list[RecipientModel]
    
    @classmethod
    def from_list(cls, data: list[dict]) -> "RecipientsListModel":
        """Create from raw list of dicts with validation.
        
        Args:
            data: List of recipient dictionaries.
        
        Returns:
            Validated RecipientsListModel.
        
        Raises:
            ValueError: If validation fails.
        """
        return cls(recipients=[RecipientModel(**item) for item in data])


class PipelineInputModel(BaseModel):
    """Validation model for pipeline execution inputs."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    profession: str
    language: Literal["tr", "en"] = "tr"
    
    @field_validator('profession')
    @classmethod
    def validate_profession(cls, v: str) -> str:
        """Profession must be non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError(f"profession must be non-empty string")
        return v.strip()
