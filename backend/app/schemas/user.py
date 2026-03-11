"""
User Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    phone: str
    password: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    pin: Optional[str] = None
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    """Schema for user login"""
    phone: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    phone: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    balance: float = 0.0
    savings: float = 0.0
    is_verified: bool = False
    is_active: bool = True
    role: str = "user"
    country: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True