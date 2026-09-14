"""
Schemas specific to the /auth endpoints.

`RegisterRequest.role` is typed as `Literal[UserRole.STUDENT, UserRole.RECRUITER]`
rather than the full `UserRole` enum - this is a deliberate, schema-level
guarantee that public registration can never create an admin account. A
request with `"role": "admin"` fails Pydantic validation (422) before it
ever reaches the service layer.
"""
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal[UserRole.STUDENT, UserRole.RECRUITER]
    full_name: str = Field(min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)

    # --- student-only fields (ignored if role == recruiter) ---
    department_id: Optional[int] = None
    batch_year: Optional[int] = Field(default=None, ge=1990, le=2100)
    cgpa: Optional[Decimal] = Field(default=None, ge=0, le=10)

    # --- recruiter-only fields (ignored if role == student) ---
    designation: Optional[str] = Field(default=None, max_length=100)
