"""
Response Schemas
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Generic API Response"""
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None