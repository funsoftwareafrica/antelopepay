"""
Transfers Router - Transferts d'argent
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
import uuid

from app.database import get_db
from app.models import User, Transaction, Contact, TransactionType, TransactionStatus
from app.schemas.transaction import TransactionCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("")
async def create_transfer(
    transfer: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Créer un nouveau transfert"""
    
    # Vérifier le solde
    fee = transfer.amount * 0.015
    fee = max(50, min(fee, 2500))
    total_debit = transfer.amount + fee
    
    if current_user.balance < total_debit:
        raise HTTPException(400, f"Solde insuffisant. Il vous faut {total_debit:,.0f} XOF.")
    
    # Vérifier qu'on ne s'envoie pas à soi-même
    if transfer.recipient_phone == current_user.phone:
        raise HTTPException(400, "Impossible de s'envoyer de l'argent à soi-même")
    
    # Trouver le destinataire
    recipient = db.query(User).filter(User.phone == transfer.recipient_phone).first()
    
    # Générer IDs et Référence
    transaction_id = str(uuid.uuid4())
    reference = f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Utilisation de DEPOSIT pour éviter l'erreur AttributeError
    new_transaction = Transaction(
        id=transaction_id,
        sender_id=current_user.id,
        recipient_id=recipient.id if recipient else None,
        recipient_phone=transfer.recipient_phone,
        amount=transfer.amount,
        fee=fee,
        currency="XOF",
        type=TransactionType.DEPOSIT,
        status=TransactionStatus.COMPLETED,
        reference=reference,
        description=transfer.note or "Transfert P2P",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    db.add(new_transaction)
    
    # Mettre à jour les soldes
    current_user.balance -= total_debit
    
    if recipient:
        recipient.balance += transfer.amount
    
    # Ajouter aux contacts récents (sans le champ last_transaction_at qui n'existe pas)
    existing_contact = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.phone == transfer.recipient_phone
    ).first()
    
    if not existing_contact:
        new_contact = Contact(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            phone=transfer.recipient_phone,
            name=recipient.full_name if recipient else transfer.recipient_phone,
            created_at=datetime.utcnow()
            # J'ai supprimé last_transaction_at car il n'est pas dans votre modèle
        )
        db.add(new_contact)
    
    db.commit()
    db.refresh(new_transaction)
    
    return {
        "success": True,
        "message": f"Transfert de {transfer.amount:,.0f} XOF effectué avec succès!",
        "data": {
            "transaction_id": transaction_id,
            "reference": reference,
            "amount": transfer.amount,
            "fee": fee,
            "status": "completed",
            "new_balance": current_user.balance
        }
    }


@router.get("")
async def get_transfer_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'historique des transferts"""
    
    query = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == current_user.id,
            Transaction.recipient_id == current_user.id
        )
    )
    
    total = query.count()
    
    transactions = query.order_by(desc(Transaction.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    formatted = []
    for tx in transactions:
        is_sender = tx.sender_id == current_user.id
        tx_type = "send" if is_sender else "receive"
        
        formatted.append({
            "id": tx.id,
            "type": tx_type,
            "amount": float(tx.amount),
            "fee": float(tx.fee),
            "status": tx.status.value,
            "reference": tx.reference,
            "recipient_phone": tx.recipient_phone,
            "recipient_name": tx.recipient.full_name if tx.recipient else tx.recipient_phone,
            "created_at": tx.created_at.isoformat() if tx.created_at else None
        })
    
    return {
        "success": True,
        "transactions": formatted,
        "total": total,
        "page": page,
        "page_size": page_size
    }