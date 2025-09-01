from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from bot.enums import PreferredGenders
from bot.validators import validate_preference_age, validate_preference_ages


class PreferencesInSchema(BaseModel):
    min_age: int | None = None
    max_age: int | None = None
    preferred_gender: PreferredGenders

    @field_validator("min_age", "max_age")
    @classmethod
    def validate_ages(cls, v):
        """Validate individual age values."""
        return validate_preference_age(v)

    @model_validator(mode="after")
    def validate_age_range(self):
        """Validate that min_age is less than max_age."""
        if self.min_age is not None and self.max_age is not None:
            validate_preference_ages(self.min_age, self.max_age)
        return self


class PreferencesUpdateSchema(BaseModel):
    min_age: int | None = None
    max_age: int | None = None
    preferred_gender: PreferredGenders | None = None

    @field_validator("min_age", "max_age")
    @classmethod
    def validate_ages(cls, v):
        """Validate individual age values."""
        return validate_preference_age(v)

    @model_validator(mode="after")
    def validate_age_range(self):
        """Validate that min_age is less than max_age if both are provided."""
        if self.min_age is not None and self.max_age is not None:
            validate_preference_ages(self.min_age, self.max_age)
        return self


class PreferencesSchema(PreferencesInSchema):
    id: int
    user_id: UUID
