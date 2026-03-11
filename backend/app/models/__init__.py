"""
SQLAlchemy Models for AntelopePay
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
from datetime import datetime


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    """Rôles des utilisateurs"""
    ADMIN = "admin"
    USER = "user"


class TransactionType(str, enum.Enum):
    """Types de transactions"""
    SEND = "send"
    RECEIVE = "receive"
    RECHARGE = "recharge"
    BILL = "bill"
    QR_PAYMENT = "qr_payment"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class TransactionStatus(str, enum.Enum):
    """Statuts des transactions"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    pin_hash = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    country = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    savings = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    sent_transactions = relationship("Transaction", back_populates="sender", foreign_keys="Transaction.sender_id")
    received_transactions = relationship("Transaction", back_populates="recipient", foreign_keys="Transaction.recipient_id")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    """Transaction model - toutes les opérations financières"""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="XOF", nullable=False)
    
    recipient_phone = Column(String(20), nullable=True)
    recipient_name = Column(String(255), nullable=True)
    
    # Pour les dépôts/retraits Mobile Money
    method = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    external_reference = Column(String(100), nullable=True)
    
    # Admin validation
    validated_by = Column(String, ForeignKey("users.id"), nullable=True)
    validation_notes = Column(Text, nullable=True)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    reference = Column(String(50), unique=True, nullable=False, index=True)
    
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    sender = relationship("User", back_populates="sent_transactions", foreign_keys=[sender_id])
    recipient = relationship("User", back_populates="received_transactions", foreign_keys=[recipient_id])
    validator = relationship("User", foreign_keys=[validated_by])
    
    def __repr__(self):
        return f"<Transaction {self.reference} - {self.type}>"


class OperatorBalance(Base):
    """Soldes des comptes opérateurs Mobile Money"""
    __tablename__ = "operator_balances"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    operator = Column(String(50), unique=True, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    account_number = Column(String(100), nullable=True)
    api_key = Column(String(255), nullable=True)
    api_secret = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="contacts")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="refresh_tokens")


class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())