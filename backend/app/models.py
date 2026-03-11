from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"
    RECHARGE = "recharge"
    BILL_PAYMENT = "bill_payment"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    balance = Column(Float, default=0.0)
    savings = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_id", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.recipient_id", back_populates="recipient")
    contacts = relationship("Contact", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = Column(String(50), unique=True, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=True)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=True)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    currency = Column(String(10), default="XOF")
    method = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_transactions")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="contacts")

class OperatorBalance(Base):
    __tablename__ = "operator_balances"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operator = Column(String(50), unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
