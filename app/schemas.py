from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentBase(BaseModel):
    """Base schema defining common student attributes."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the student",
        examples=["Aarav Sharma"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth in YYYY-MM-DD format",
        examples=["2002-05-14"],
    )
    email: Optional[EmailStr] = Field(
        default=None,
        max_length=150,
        description="Valid email address of the student",
        examples=["aarav.sharma@example.com"],
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Contact phone number",
        examples=["9876543210"],
    )
    course: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Course or degree enrolled in",
        examples=["Computer Science"],
    )
    address: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Residential address",
        examples=["123 MG Road, Bengaluru"],
    )
    enrollment_date: Optional[date] = Field(
        default=None,
        description="Enrollment date in YYYY-MM-DD format",
        examples=["2024-08-01"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty or composed only of whitespace."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Student name cannot be empty or whitespace only")
        return trimmed

    @field_validator("phone", "course", "address", mode="before")
    @classmethod
    def trim_optional_strings(cls, v):
        """Trim optional strings and convert empty strings to None."""
        if isinstance(v, str):
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class StudentCreate(StudentBase):
    """Schema for student creation request (POST /students)."""

    pass


class StudentUpdatePut(StudentBase):
    """Schema for full student replacement request (PUT /students/{student_id})."""

    pass


class StudentUpdatePatch(BaseModel):
    """Schema for partial student update request (PATCH /students/{student_id})."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Full name of the student",
    )
    date_of_birth: Optional[date] = Field(
        default=None,
        description="Date of birth in YYYY-MM-DD format",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        max_length=150,
        description="Valid email address of the student",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Contact phone number",
    )
    course: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Course or degree enrolled in",
    )
    address: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Residential address",
    )
    enrollment_date: Optional[date] = Field(
        default=None,
        description="Enrollment date in YYYY-MM-DD format",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Ensure name is not empty or composed only of whitespace if provided."""
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Student name cannot be empty or whitespace only")
            return trimmed
        return v

    @field_validator("phone", "course", "address", mode="before")
    @classmethod
    def trim_optional_strings(cls, v):
        """Trim optional strings and convert empty strings to None."""
        if isinstance(v, str):
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class StudentResponse(BaseModel):
    """Schema for student response including auto-generated student_id."""

    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    date_of_birth: str
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[str] = None
