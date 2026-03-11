"""
Webhooks pour les callbacks Mobile Money
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import User, Transaction, OperatorBalance, TransactionStatus
from app.services.notifications import notification_service

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


@router.post("/orange/deposit")
async def orange_deposit_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook appelé par Orange Money quand un dépôt est confirmé
    """
    try:
        payload = await request.json()
        
        reference = payload.get("order_id")
        status = payload.get("status", "").upper()
        
        transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if not transaction:
            return {"error": "Transaction not found"}
        
        if status == "SUCCESS":
            user = db.query(User).filter(
                User.id == transaction.recipient_id
            ).first()
            
            if user and transaction.status == TransactionStatus.PENDING:
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                transaction.external_reference = payload.get("transaction_id")
                user.balance += transaction.amount
                
                db.commit()
                
                # Notifier l'utilisateur
                await notification_service.send_deposit_success(
                    phone=user.phone,
                    amount=transaction.amount,
                    reference=transaction.reference,
                    new_balance=user.balance
                )
        
        elif status in ["FAILED", "CANCELLED"]:
            transaction.status = TransactionStatus.FAILED
            db.commit()
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/orange/withdraw")
async def orange_withdraw_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook pour retraits Orange Money"""
    try:
        payload = await request.json()
        
        reference = payload.get("order_id")
        status = payload.get("status", "").upper()
        
        transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if not transaction:
            return {"error": "Transaction not found"}
        
        if status == "SUCCESS":
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            transaction.external_reference = payload.get("transaction_id")
            
            # Débiter le solde opérateur
            operator = db.query(OperatorBalance).filter(
                OperatorBalance.operator == "orange_money"
            ).first()
            if operator:
                operator.balance -= transaction.amount
            
            db.commit()
            
            user = db.query(User).filter(User.id == transaction.sender_id).first()
            if user:
                await notification_service.send_withdraw_success(
                    phone=user.phone,
                    amount=transaction.amount,
                    fee=transaction.fee,
                    reference=transaction.reference
                )
        
        elif status in ["FAILED", "CANCELLED"]:
            # Rembourser l'utilisateur
            user = db.query(User).filter(User.id == transaction.sender_id).first()
            if user:
                user.balance += transaction.amount + transaction.fee
            
            transaction.status = TransactionStatus.FAILED
            db.commit()
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/mtn/deposit")
async def mtn_deposit_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook pour dépôts MTN"""
    try:
        payload = await request.json()
        
        reference = payload.get("externalId")
        status = payload.get("status", "").upper()
        
        transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if not transaction:
            return {"error": "Transaction not found"}
        
        if status == "SUCCESSFUL":
            user = db.query(User).filter(
                User.id == transaction.recipient_id
            ).first()
            
            if user and transaction.status == TransactionStatus.PENDING:
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                transaction.external_reference = payload.get("financialTransactionId")
                user.balance += transaction.amount
                
                db.commit()
                
                await notification_service.send_deposit_success(
                    phone=user.phone,
                    amount=transaction.amount,
                    reference=transaction.reference,
                    new_balance=user.balance
                )
        
        elif status in ["FAILED", "CANCELLED", "REJECTED"]:
            transaction.status = TransactionStatus.FAILED
            db.commit()
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/mtn/withdraw")
async def mtn_withdraw_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook pour retraits MTN"""
    try:
        payload = await request.json()
        
        reference = payload.get("externalId")
        status = payload.get("status", "").upper()
        
        transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if not transaction:
            return {"error": "Transaction not found"}
        
        if status == "SUCCESSFUL":
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            transaction.external_reference = payload.get("financialTransactionId")
            
            operator = db.query(OperatorBalance).filter(
                OperatorBalance.operator == "mtn_money"
            ).first()
            if operator:
                operator.balance -= transaction.amount
            
            db.commit()
            
            user = db.query(User).filter(User.id == transaction.sender_id).first()
            if user:
                await notification_service.send_withdraw_success(
                    phone=user.phone,
                    amount=transaction.amount,
                    fee=transaction.fee,
                    reference=transaction.reference
                )
        
        elif status in ["FAILED", "CANCELLED", "REJECTED"]:
            user = db.query(User).filter(User.id == transaction.sender_id).first()
            if user:
                user.balance += transaction.amount + transaction.fee
            
            transaction.status = TransactionStatus.FAILED
            db.commit()
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"error": str(e)}