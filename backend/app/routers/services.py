from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.database import get_db
from app.models import User, Transaction
from app.routers.auth import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])

def generate_reference():
    return f"SVC-{uuid.uuid4().hex[:8].upper()}"

class RechargeRequest:
    def __init__(self, phone: str, amount: float, operator: str, pin: Optional[str] = None):
        self.phone = phone
        self.amount = amount
        self.operator = operator
        self.pin = pin

@router.post("/recharge")
def create_recharge(
    phone: str,
    amount: float,
    operator: str,
    pin: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fee = round(amount * 0.01)
    total = amount + fee
    
    if current_user.balance < total:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    valid_operators = ["orange", "mtn", "moov", "telecel"]
    if operator not in valid_operators:
        raise HTTPException(status_code=400, detail="Opérateur non supporté")
    
    reference = generate_reference()
    transaction = Transaction(
        type="recharge",
        amount=amount,
        fee=fee,
        sender_id=current_user.id,
        sender_phone=current_user.phone,
        sender_name=current_user.full_name,
        recipient_phone=phone,
        reference=reference,
        extra_data={"operator": operator},
        status="completed"
    )
    
    db.add(transaction)
    current_user.balance -= total
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "success": True,
        "message": f"Recharge {operator} de {amount} XOF effectuée",
        "data": {
            "reference": reference,
            "amount": amount,
            "fee": fee,
            "phone": phone,
            "operator": operator
        }
    }