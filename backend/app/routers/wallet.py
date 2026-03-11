"""
Wallet Router - Dépôt et Retrait
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
import uuid
import random

from app.database import get_db
from app.config import settings
from app.models import (
    User, Transaction, OperatorBalance,
    TransactionType, TransactionStatus
)
from app.schemas.transaction import (
    DepositRequest, WithdrawRequest, 
    WalletBalanceResponse
)
from app.dependencies import get_current_user

# INITIALISATION DU ROUTER (Ceci manquait)
router = APIRouter(prefix="/wallet", tags=["Wallet"])

# DÉFINITION DES VALEURS PAR DÉFAUT
AUTO_APPROVE_DEPOSIT_LIMIT = getattr(settings, 'AUTO_APPROVE_DEPOSIT_LIMIT', 100000.0)
AUTO_APPROVE_WITHDRAW_LIMIT = getattr(settings, 'AUTO_APPROVE_WITHDRAW_LIMIT', 50000.0)
DAILY_DEPOSIT_LIMIT = getattr(settings, 'DAILY_DEPOSIT_LIMIT', 5000000.0)
DAILY_WITHDRAW_LIMIT = getattr(settings, 'DAILY_WITHDRAW_LIMIT', 2000000.0)
WITHDRAW_FEE_PERCENT = getattr(settings, 'WITHDRAW_FEE_PERCENT', 0.01)
WITHDRAW_FEE_MIN = getattr(settings, 'WITHDRAW_FEE_MIN', 50.0)
WITHDRAW_FEE_MAX = getattr(settings, 'WITHDRAW_FEE_MAX', 2500.0)


def generate_reference(prefix: str = "TRX") -> str:
    """Génère une référence unique"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    return f"{prefix}{timestamp}{random_num}"


def calculate_withdraw_fee(amount: float) -> float:
    """Calcule les frais de retrait"""
    fee = amount * WITHDRAW_FEE_PERCENT
    return max(WITHDRAW_FEE_MIN, min(fee, WITHDRAW_FEE_MAX))


def get_or_create_operator_balance(db: Session, operator: str) -> OperatorBalance:
    """Récupère ou crée le solde d'un opérateur"""
    op = db.query(OperatorBalance).filter(OperatorBalance.operator == operator).first()
    if not op:
        op = OperatorBalance(
            operator=operator,
            balance=5000000.0,
            is_active=True
        )
        db.add(op)
        db.commit()
        db.refresh(op)
    return op


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère le solde du portefeuille"""
    return WalletBalanceResponse(
        balance=float(current_user.balance or 0),
        savings=float(current_user.savings or 0),
        currency="XOF"
    )


@router.get("/limits")
async def get_transaction_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les limites de transaction"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Dépôts du jour
    deposit_today = db.query(Transaction).filter(
        Transaction.recipient_id == current_user.id,
        Transaction.type == TransactionType.DEPOSIT,
        Transaction.created_at >= today,
        Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.COMPLETED])
    ).all()
    
    deposit_used = sum(float(t.amount) for t in deposit_today)
    
    # Retraits du jour
    withdraw_today = db.query(Transaction).filter(
        Transaction.sender_id == current_user.id,
        Transaction.type == TransactionType.WITHDRAW,
        Transaction.created_at >= today,
        Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.COMPLETED])
    ).all()
    
    withdraw_used = sum(float(t.amount) for t in withdraw_today)
    
    return {
        "success": True,
        "data": {
            "deposit": {
                "daily_limit": DAILY_DEPOSIT_LIMIT,
                "daily_used": deposit_used,
                "daily_remaining": max(0, DAILY_DEPOSIT_LIMIT - deposit_used),
                "auto_limit": AUTO_APPROVE_DEPOSIT_LIMIT
            },
            "withdraw": {
                "daily_limit": DAILY_WITHDRAW_LIMIT,
                "daily_used": withdraw_used,
                "daily_remaining": max(0, DAILY_WITHDRAW_LIMIT - withdraw_used),
                "auto_limit": AUTO_APPROVE_WITHDRAW_LIMIT
            },
            "user_verified": current_user.is_verified
        }
    }


@router.post("/deposit")
async def create_deposit(
    deposit: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dépôt via Mobile Money"""
    
    # --- DEBUG AFFICHAGE ---
    print(f"\n--- DÉBUT DÉPÔT ---")
    print(f"Montant demandé: {deposit.amount}")
    print(f"Limite auto: {AUTO_APPROVE_DEPOSIT_LIMIT}")
    print(f"Solde actuel user (avant): {current_user.balance}")
    # -----------------------

    if deposit.amount < 100:
        raise HTTPException(400, "Montant minimum: 100 XOF")
    
    if deposit.amount > DAILY_DEPOSIT_LIMIT:
        raise HTTPException(400, f"Montant maximum: {DAILY_DEPOSIT_LIMIT:,.0f} XOF")
    
    valid_methods = ["orange_money", "mtn_money", "moov_money", "telecel_cash", "bank"]
    if deposit.method not in valid_methods:
        raise HTTPException(400, f"Méthodes acceptées: {', '.join(valid_methods)}")
    
    reference = generate_reference("DEP")
    
    # LOGIQUE
    if deposit.amount <= AUTO_APPROVE_DEPOSIT_LIMIT:
        print(">>> MODE: AUTO-APPROBATION (Créditation immédiate)")
        status = TransactionStatus.COMPLETED
        current_user.balance = float(current_user.balance or 0) + deposit.amount
        message = f"Dépôt de {deposit.amount:,.0f} XOF effectué avec succès!"
        final_status = "completed"
    else:
        print(">>> MODE: EN ATTENTE (Pas de crédit)")
        status = TransactionStatus.PENDING
        message = f"Dépôt de {deposit.amount:,.0f} XOF enregistré. Validation en cours."
        final_status = "pending"

    transaction = Transaction(
        id=str(uuid.uuid4()),
        recipient_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=deposit.amount,
        fee=0.0,
        currency="XOF",
        method=deposit.method,
        phone_number=deposit.phone_number,
        status=status,
        reference=reference,
        description=f"Dépôt via {deposit.method.replace('_', ' ').title()}",
        completed_at=datetime.utcnow() if status == TransactionStatus.COMPLETED else None
    )
    
    db.add(transaction)
    
    print(f"Solde user (après calcul): {current_user.balance}")
    print(">>> TENTATIVE DE COMMIT (Sauvegarde DB)...")

    db.commit()
    db.refresh(transaction)
    
    print(">>> COMMIT RÉUSSI !")
    print(f"Nouveau solde en mémoire: {current_user.balance}")
    print("--- FIN DÉPÔT ---\n")
    
    return {
        "success": True,
        "message": message,
        "transaction_id": transaction.id,
        "reference": reference,
        "amount": deposit.amount,
        "status": final_status,
        "new_balance": float(current_user.balance)
    }


@router.post("/withdraw")
async def create_withdraw(
    withdraw: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrait vers Mobile Money"""
    if withdraw.amount < 100:
        raise HTTPException(400, "Montant minimum: 100 XOF")
    
    if withdraw.amount > DAILY_WITHDRAW_LIMIT:
        raise HTTPException(400, f"Montant maximum: {DAILY_WITHDRAW_LIMIT:,.0f} XOF")
    
    valid_methods = ["orange_money", "mtn_money", "moov_money", "telecel_cash"]
    if withdraw.method not in valid_methods:
        raise HTTPException(400, f"Méthodes acceptées: {', '.join(valid_methods)}")
    
    fee = calculate_withdraw_fee(withdraw.amount)
    total_debit = withdraw.amount + fee
    
    if float(current_user.balance or 0) < total_debit:
        raise HTTPException(
            400, 
            f"Solde insuffisant. Solde: {float(current_user.balance or 0):,.0f} XOF"
        )
    
    reference = generate_reference("WDR")
    
    if withdraw.amount <= AUTO_APPROVE_WITHDRAW_LIMIT:
        status = TransactionStatus.COMPLETED
        completed_at = datetime.utcnow()
        
        op = get_or_create_operator_balance(db, withdraw.method)
        if op.balance >= withdraw.amount:
            op.balance -= withdraw.amount
            
        message = f"Retrait de {withdraw.amount:,.0f} XOF effectué! Frais: {fee:,.0f} XOF"
        final_status = "completed"
    else:
        status = TransactionStatus.PENDING
        completed_at = None
        message = f"Retrait de {withdraw.amount:,.0f} XOF enregistré. Validation en cours."
        final_status = "pending"
    
    transaction = Transaction(
        id=str(uuid.uuid4()),
        sender_id=current_user.id,
        type=TransactionType.WITHDRAW,
        amount=withdraw.amount,
        fee=fee,
        currency="XOF",
        method=withdraw.method,
        phone_number=withdraw.phone_number,
        status=status,
        reference=reference,
        description=f"Retrait via {withdraw.method.replace('_', ' ').title()}",
        completed_at=completed_at
    )
    
    db.add(transaction)
    current_user.balance = float(current_user.balance or 0) - total_debit
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "success": True,
        "message": message,
        "transaction_id": transaction.id,
        "reference": reference,
        "amount": withdraw.amount,
        "fee": fee,
        "status": final_status,
        "new_balance": float(current_user.balance)
    }


@router.get("/transactions")
async def get_wallet_transactions(
    page: int = 1,
    page_size: int = 20,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Historique des transactions wallet"""
    
    query = db.query(Transaction).filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.recipient_id == current_user.id)
    ).filter(
        Transaction.type.in_([TransactionType.DEPOSIT, TransactionType.WITHDRAW])
    )
    
    if transaction_type:
        try:
            trans_type = TransactionType(transaction_type)
            query = query.filter(Transaction.type == trans_type)
        except ValueError:
            pass
    
    total = query.count()
    
    transactions = query.order_by(desc(Transaction.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "type": t.type.value,
                "amount": float(t.amount),
                "fee": float(t.fee),
                "status": t.status.value,
                "reference": t.reference,
                "method": t.method,
                "phone_number": t.phone_number,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in transactions
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }