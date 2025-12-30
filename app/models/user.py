"""User models for authentication and authorization."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles with different permission levels."""

    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[str] = Field(default=None, description="User email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: bool = Field(default=True, description="Whether user is active")


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, description="Password")


class UserUpdate(BaseModel):
    """Schema for user updates."""

    email: Optional[str] = Field(default=None, description="User email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: Optional[bool] = Field(default=None, description="Whether user is active")
    password: Optional[str] = Field(default=None, min_length=8, description="Password")


class UserResponse(UserBase):
    """Schema for user response."""

    user_id: str = Field(..., description="Unique user ID")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    bypass_guardrails: bool = Field(default=False, description="Can bypass guardrails")

    class Config:
        """Pydantic config."""
        from_attributes = True


class UserDB(BaseModel):
    """Database model for Neo4j storage - all properties flattened."""

    user_id: str = Field(..., description="Unique user ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(default=None, description="Email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    password_hash: str = Field(..., description="Password hash")
    role: str = Field(default="user", description="User role")
    is_active: bool = Field(default=True, description="Is user active")
    created_at: float = Field(..., description="Creation timestamp")
    updated_at: float = Field(..., description="Last update timestamp")
    last_login: Optional[float] = Field(default=None, description="Last login timestamp")
    bypass_guardrails: bool = Field(default=False, description="Can bypass guardrails")

    class Config:
        """Pydantic config."""
        from_attributes = True


class TokenData(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="Username (subject)")
    user_id: str = Field(..., description="User ID")
    role: str = Field(..., description="User role")
    exp: Optional[float] = Field(default=None, description="Expiration time")


class AuthUser(BaseModel):
    """Authenticated user context for requests."""

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Is user active")
    bypass_guardrails: bool = Field(..., description="Can bypass guardrails")
