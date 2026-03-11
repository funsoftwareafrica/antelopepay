"""
Analytics Router
Financial statistics and trends
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models import User, Transaction, TransactionType, TransactionStatus
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=ApiResponse[dict])
async def get_analytics(
    period: str = "month",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial summary for a period (week, month, year)"""
    now = datetime.utcnow()
    
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # Get transactions for period - utilise sender_id et recipient_id
    transactions = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == current_user.id,
            Transaction.recipient_id == current_user.id
        ),
        Transaction.created_at >= start_date,
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    # Calculer revenus
    income = sum(
        float(t.amount) for t in transactions 
        if t.recipient_id == current_user.id and t.type in [TransactionType.RECEIVE, TransactionType.DEPOSIT]
    )
    
    # Calculer dépenses
    expenses = sum(
        float(t.amount) for t in transactions 
        if t.sender_id == current_user.id and t.type in [TransactionType.SEND, TransactionType.WITHDRAW, TransactionType.RECHARGE, TransactionType.BILL]
    )
    
    return ApiResponse(
        success=True,
        message="Résumé récupéré",
        data={
            "period": period,
            "income": income,
            "expenses": expenses,
            "balance": float(current_user.balance) if current_user.balance else 0,
            "savings": float(current_user.savings) if current_user.savings else 0,
            "transaction_count": len(transactions),
            "currency": "XOF"
        }
    )


@router.get("/expenses-by-category", response_model=ApiResponse[dict])
async def get_expenses_by_category(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expenses breakdown by category"""
    start_date = datetime.utcnow() - timedelta(days=30)
    
    transactions = db.query(Transaction).filter(
        Transaction.sender_id == current_user.id,
        Transaction.created_at >= start_date,
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    categories = {}
    total = 0
    
    for t in transactions:
        cat = t.type.value
        amount = float(t.amount)
        categories[cat] = categories.get(cat, 0) + amount
        total += amount
    
    breakdown = [
        {
            "category": cat,
            "amount": amt,
            "percentage": round((amt / total * 100) if total > 0 else 0, 1)
        }
        for cat, amt in categories.items()
    ]
    
    return ApiResponse(
        success=True,
        message="Répartition récupérée",
        data={
            "breakdown": breakdown,
            "total": total,
            "currency": "XOF"
        }
    )