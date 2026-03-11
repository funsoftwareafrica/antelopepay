"""
Transaction Schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""
    recipient_phone: str
    amount: float
    pin: Optional[str] = None
    note: Optional[str] = None


class TransferCreate(BaseModel):
    """Schema for creating a transfer"""
    recipient_phone: str
    amount: float
    pin: str
    source: str = "balance"
    note: Optional[str] = None


class DepositRequest(BaseModel):
    """Schema for deposit request"""
    amount: float
    method: str
    phone_number: str


class WithdrawRequest(BaseModel):
    """Schema for withdraw request"""
    amount: float
    method: str
    phone_number: str
    pin: Optional[str] = None


class WalletBalanceResponse(BaseModel):
    """Schema for wallet balance response"""
    balance: float
    savings: float
    currency: str = "XOF"


class TransactionResponse(BaseModel):
    """Schema for single transaction response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    type: str
    amount: float
    fee: float
    currency: str
    status: str
    reference: str
    method: Optional[str] = None
    phone_number: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TransactionListResponse(BaseModel):
    """Schema for list of transactions"""
    transactions: List[TransactionResponse]
    total: int


class MobileMoneyTransactionResponse(BaseModel):
    """Schema for mobile money transaction response"""
    success: bool
    message: str
    transaction_id: Optional[str] = None
    reference: Optional[str] = None
    amount: Optional[float] = None
    fee: Optional[float] = None
    status: str