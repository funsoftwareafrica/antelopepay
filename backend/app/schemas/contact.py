"""
Contact Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContactCreate(BaseModel):
    """Schema for creating a contact"""
    name: str
    phone: str
    is_favorite: Optional[bool] = False


class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    name: Optional[str] = None
    phone: Optional[str] = None
    is_favorite: Optional[bool] = None


class ContactResponse(BaseModel):
    """Schema for contact response"""
    id: str
    name: str
    phone: str
    is_favorite: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for list of contacts"""
    contacts: list[ContactResponse]
    total: int