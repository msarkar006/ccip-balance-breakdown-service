"""
Auth domain schemas for request/response models.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request payload."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    """Login response payload."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: "CurrentUserResponse" = Field(..., description="Current user information")


class StepUpRequest(BaseModel):
    """Step-up authentication request."""

    password: str = Field(..., min_length=8, description="User password for verification")


class StepUpResponse(BaseModel):
    """Step-up authentication response."""

    success: bool = Field(..., description="Whether step-up was successful")
    message: str = Field(..., description="Response message")
    valid_until: datetime = Field(..., description="Step-up validity timestamp")


class CurrentUserResponse(BaseModel):
    """Current user information."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    session_id: int = Field(..., description="Current session ID")
    session_expires_at: datetime = Field(..., description="Session expiry timestamp")
    step_up_verified_at: Optional[datetime] = Field(None, description="Step-up verification timestamp")
    selected_account_id: Optional[int] = Field(None, description="Selected account ID")

    model_config = ConfigDict(from_attributes=True)


class LogoutResponse(BaseModel):
    """Logout response."""

    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(..., description="Response message")


class SessionRevokeResponse(BaseModel):
    """Session revocation response."""

    success: bool = Field(..., description="Whether session was revoked")
    message: str = Field(..., description="Response message")
