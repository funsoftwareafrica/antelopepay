"""
Router Administration - Gestion des transactions et utilisateurs
Accès réservé aux administrateurs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from datetime import datetime, timedelta
from typing import Optional, List
import uuid

from app.database import get_db
from app.config import settings
from app.models import (
    User, Transaction, OperatorBalance, 
    TransactionType, TransactionStatus, UserRole
)
from app.routers.auth import get_current_user
from app.services.mobile_money import mm_service
from app.services.notifications import notification_service
from app.services.fraud_detection import FraudDetectionEngine
from passlib.context import CryptContext

router = APIRouter(prefix="/admin", tags=["Administration"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# DÉPENDANCES
# ==========================================

def require_admin(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur est admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Privilèges administrateur requis."
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte administrateur désactivé."
        )
    return current_user


# ==========================================
# TABLEAU DE BORD
# ==========================================

@router.get("/dashboard")
async def admin_dashboard(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Tableau de bord administrateur
    Vue d'ensemble de l'activité
    """
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # === UTILISATEURS ===
    total_users = db.query(User).filter(User.role == UserRole.USER).count()
    active_users = db.query(User).filter(
        User.role == UserRole.USER,
        User.is_active == True
    ).count()
    verified_users = db.query(User).filter(
        User.role == UserRole.USER,
        User.is_verified == True
    ).count()
    new_users_today = db.query(User).filter(
        User.role == UserRole.USER,
        User.created_at >= today
    ).count()
    
    # === TRANSACTIONS ===
    # En attente (CRITIQUE)
    pending_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PENDING
    ).count()
    
    # Urgentes (en attente depuis + de 1 heure)
    urgent_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PENDING,
        Transaction.created_at < now - timedelta(hours=1)
    ).count()
    
    # Aujourd'hui
    transactions_today = db.query(Transaction).filter(
        Transaction.created_at >= today
    ).count()
    
    completed_today = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.completed_at >= today
    ).count()
    
    failed_today = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.FAILED,
        Transaction.created_at >= today
    ).count()
    
    # === VOLUMES FINANCIERS ===
    # Dépôts aujourd'hui
    deposit_volume_today = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.DEPOSIT,
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.completed_at >= today
    ).scalar() or 0
    
    # Retraits aujourd'hui
    withdraw_volume_today = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.WITHDRAW,
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.completed_at >= today
    ).scalar() or 0
    
    # Frais collectés aujourd'hui
    fees_today = db.query(func.sum(Transaction.fee)).filter(
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.completed_at >= today
    ).scalar() or 0
    
    # Volume mensuel
    monthly_volume = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.completed_at >= month_start
    ).scalar() or 0
    
    # === LIQUIDITÉ OPÉRATEURS ===
    operators = db.query(OperatorBalance).filter(
        OperatorBalance.is_active == True
    ).all()
    
    total_liquidity = sum(op.balance for op in operators)
    low_liquidity_operators = [
        {"name": op.operator, "balance": op.balance}
        for op in operators
        if op.balance < 500000  # Alerte si < 500k
    ]
    
    # === ALERTES ===
    alerts = []
    
    # Alerte transactions en attente
    if pending_transactions > 20:
        alerts.append({
            "level": "warning",
            "message": f"{pending_transactions} transactions en attente de validation",
            "action": "Veuillez traiter les transactions en attente"
        })
    
    # Alerte transactions urgentes
    if urgent_transactions > 5:
        alerts.append({
            "level": "critical",
            "message": f"{urgent_transactions} transactions en attente depuis +1h",
            "action": "Traitement urgent requis"
        })
    
    # Alerte liquidité
    for op in low_liquidity_operators:
        alerts.append({
            "level": "warning",
            "message": f"Liquidité faible: {op['name']} ({op['balance']:,.0f} XOF)",
            "action": "Rechargez le compte opérateur"
        })
    
    return {
        "success": True,
        "data": {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "new_today": new_users_today
            },
            "transactions": {
                "pending": pending_transactions,
                "urgent": urgent_transactions,
                "today": transactions_today,
                "completed_today": completed_today,
                "failed_today": failed_today
            },
            "volumes": {
                "deposit_today": float(deposit_volume_today),
                "withdraw_today": float(withdraw_volume_today),
                "fees_today": float(fees_today),
                "monthly_total": float(monthly_volume)
            },
            "liquidity": {
                "total": total_liquidity,
                "operators": [
                    {
                        "name": op.operator,
                        "balance": op.balance,
                        "status": "ok" if op.balance >= 500000 else "low"
                    }
                    for op in operators
                ]
            },
            "alerts": alerts,
            "pending_count": pending_transactions
        }
    }


# ==========================================
# GESTION DES TRANSACTIONS
# ==========================================

@router.get("/transactions/pending")
async def get_pending_transactions(
    urgent_only: bool = False,
    transaction_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Liste des transactions en attente de validation
    
    - urgent_only: seulement celles en attente depuis +1h
    - transaction_type: filtrer par type (deposit, withdraw, send)
    """
    query = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PENDING
    )
    
    # Filtre urgent
    if urgent_only:
        query = query.filter(
            Transaction.created_at < datetime.utcnow() - timedelta(hours=1)
        )
    
    # Filtre type
    if transaction_type:
        try:
            trans_type = TransactionType(transaction_type)
            query = query.filter(Transaction.type == trans_type)
        except ValueError:
            pass
    
    total = query.count()
    
    # Trier par ancienneté (plus ancien d'abord)
    transactions = query.order_by(Transaction.created_at)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    result = []
    for t in transactions:
        # Récupérer les infos utilisateur
        user = None
        if t.sender_id:
            user = db.query(User).filter(User.id == t.sender_id).first()
        elif t.recipient_id:
            user = db.query(User).filter(User.id == t.recipient_id).first()
        
        waiting_hours = (datetime.utcnow() - t.created_at).total_seconds() / 3600
        
        result.append({
            "id": t.id,
            "reference": t.reference,
            "type": t.type.value,
            "amount": t.amount,
            "fee": t.fee,
            "currency": t.currency,
            "method": t.method,
            "phone_number": t.phone_number,
            "description": t.description,
            "created_at": t.created_at.isoformat(),
            "waiting_hours": round(waiting_hours, 2),
            "is_urgent": waiting_hours > 1,
            "risk_score": t.extra_data.get("risk_score", 0) if t.extra_data else 0,
            "risk_level": t.extra_data.get("risk_level", "unknown") if t.extra_data else "unknown",
            "risk_reasons": t.extra_data.get("risk_reasons", []) if t.extra_data else [],
            "user": {
                "id": user.id if user else None,
                "phone": user.phone if user else None,
                "full_name": user.full_name if user else None,
                "is_verified": user.is_verified if user else False,
                "balance": user.balance if user else 0
            } if user else None
        })
    
    return {
        "success": True,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "urgent_count": sum(1 for t in result if t["is_urgent"])
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Détails complets d'une transaction"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(404, "Transaction non trouvée")
    
    # Utilisateur source
    sender = None
    if transaction.sender_id:
        sender = db.query(User).filter(User.id == transaction.sender_id).first()
    
    # Utilisateur destinataire
    recipient = None
    if transaction.recipient_id:
        recipient = db.query(User).filter(User.id == transaction.recipient_id).first()
    
    # Validateur (si déjà traité)
    validator = None
    if transaction.validated_by:
        validator = db.query(User).filter(User.id == transaction.validated_by).first()
    
    # Historique des transactions de l'utilisateur
    user_id = transaction.sender_id or transaction.recipient_id
    user_transactions = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == user_id,
            Transaction.recipient_id == user_id
        ),
        Transaction.id != transaction.id
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    return {
        "success": True,
        "data": {
            "transaction": {
                "id": transaction.id,
                "reference": transaction.reference,
                "type": transaction.type.value,
                "amount": transaction.amount,
                "fee": transaction.fee,
                "currency": transaction.currency,
                "status": transaction.status.value,
                "method": transaction.method,
                "phone_number": transaction.phone_number,
                "external_reference": transaction.external_reference,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
                "extra_data": transaction.extra_data
            },
            "sender": {
                "id": sender.id,
                "phone": sender.phone,
                "full_name": sender.full_name,
                "email": sender.email,
                "balance": sender.balance,
                "is_verified": sender.is_verified,
                "created_at": sender.created_at.isoformat()
            } if sender else None,
            "recipient": {
                "id": recipient.id,
                "phone": recipient.phone,
                "full_name": recipient.full_name,
                "email": recipient.email,
                "balance": recipient.balance,
                "is_verified": recipient.is_verified,
                "created_at": recipient.created_at.isoformat()
            } if recipient else None,
            "validator": {
                "id": validator.id,
                "phone": validator.phone,
                "full_name": validator.full_name
            } if validator else None,
            "validation_notes": transaction.validation_notes,
            "user_history": [
                {
                    "id": t.id,
                    "reference": t.reference,
                    "type": t.type.value,
                    "amount": t.amount,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in user_transactions
            ]
        }
    }


@router.post("/transactions/{transaction_id}/validate")
async def validate_transaction(
    transaction_id: str,
    action: str,  # "approve" ou "reject"
    notes: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Valide ou rejette une transaction en attente
    
    - action: "approve" pour approuver, "reject" pour rejeter
    - notes: notes de validation (obligatoire si rejet)
    """
    
    if action not in ["approve", "reject"]:
        raise HTTPException(400, "Action invalide. Utilisez 'approve' ou 'reject'")
    
    if action == "reject" and not notes:
        raise HTTPException(400, "Notes obligatoires pour un rejet")
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(404, "Transaction non trouvée")
    
    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(
            400, 
            f"Transaction déjà {transaction.status.value}"
        )
    
    # ==========================================
    # APPROBATION
    # ==========================================
    if action == "approve":
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()
        transaction.validated_by = admin.id
        transaction.validation_notes = notes
        
        # === DÉPÔT ===
        if transaction.type == TransactionType.DEPOSIT:
            user = db.query(User).filter(
                User.id == transaction.recipient_id
            ).first()
            
            if user:
                user.balance += transaction.amount
                
                # Notification
                await notification_service.send_deposit_success(
                    phone=user.phone,
                    amount=transaction.amount,
                    reference=transaction.reference,
                    new_balance=user.balance
                )
        
        # === RETRAIT ===
        elif transaction.type == TransactionType.WITHDRAW:
            # Le compte a déjà été débité lors de la création
            # Maintenant effectuer le transfert réel
            
            # Vérifier la liquidité
            if not check_operator_balance(db, transaction.method, transaction.amount):
                raise HTTPException(
                    400, 
                    f"Liquidité insuffisante chez {transaction.method}"
                )
            
            # Effectuer le transfert via API (si disponible)
            if transaction.method in ["orange_money", "mtn_money"]:
                try:
                    result = await mm_service.process_withdrawal(
                        operator=transaction.method,
                        amount=transaction.amount,
                        phone=transaction.phone_number,
                        reference=transaction.reference
                    )
                    
                    if result.get("success"):
                        # Débiter l'opérateur
                        debit_operator_balance(db, transaction.method, transaction.amount)
                        
                        # Notifier
                        user = db.query(User).filter(
                            User.id == transaction.sender_id
                        ).first()
                        
                        if user:
                            await notification_service.send_withdraw_success(
                                phone=user.phone,
                                amount=transaction.amount,
                                fee=transaction.fee,
                                reference=transaction.reference
                            )
                    else:
                        # Échec API - mais transaction approuvée manuellement
                        # L'admin devra faire le transfert manuellement
                        transaction.validation_notes = f"{notes or ''} [TRANSFERT MANUEL REQUIS]"
                        
                except Exception as e:
                    transaction.validation_notes = f"{notes or ''} [ERREUR API: {str(e)}]"
            else:
                # Opérateur sans API - transfert manuel requis
                transaction.validation_notes = f"{notes or ''} [TRANSFERT MANUEL REQUIS - {transaction.method}]"
        
        # === TRANSFERT ===
        elif transaction.type == TransactionType.SEND:
            # Créditer le destinataire
            recipient = db.query(User).filter(
                User.phone == transaction.recipient_phone
            ).first()
            
            if recipient:
                recipient.balance += transaction.amount
                
                await notification_service.send_transfer_received(
                    phone=recipient.phone,
                    amount=transaction.amount,
                    sender=transaction.sender.phone if transaction.sender else "Anonyme"
                )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Transaction approuvée avec succès",
            "data": {
                "transaction_id": transaction.id,
                "reference": transaction.reference,
                "status": "completed",
                "validated_by": admin.full_name or admin.phone,
                "validated_at": datetime.utcnow().isoformat()
            }
        }
    
    # ==========================================
    # REJET
    # ==========================================
    else:
        transaction.status = TransactionStatus.CANCELLED
        transaction.validated_by = admin.id
        transaction.validation_notes = notes
        
        # Rembourser si nécessaire
        if transaction.type == TransactionType.WITHDRAW:
            # Rembourser l'utilisateur
            user = db.query(User).filter(
                User.id == transaction.sender_id
            ).first()
            
            if user:
                user.balance += transaction.amount + transaction.fee
                
                # Notification
                await notification_service.send_transaction_blocked(
                    phone=user.phone,
                    amount=transaction.amount,
                    reason=notes
                )
        
        elif transaction.type == TransactionType.SEND:
            # Rembourser l'expéditeur
            user = db.query(User).filter(
                User.id == transaction.sender_id
            ).first()
            
            if user:
                user.balance += transaction.amount + transaction.fee
        
        db.commit()
        
        return {
            "success": True,
            "message": "Transaction rejetée",
            "data": {
                "transaction_id": transaction.id,
                "reference": transaction.reference,
                "status": "cancelled",
                "reason": notes
            }
        }


@router.post("/transactions/batch-validate")
async def batch_validate_transactions(
    transaction_ids: List[str],
    action: str,
    notes: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Validation en lot de plusieurs transactions
    Maximum 50 transactions à la fois
    """
    
    if len(transaction_ids) > 50:
        raise HTTPException(400, "Maximum 50 transactions par lot")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(400, "Action invalide")
    
    results = {
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for trans_id in transaction_ids:
        try:
            # Réutiliser la logique de validation simple
            transaction = db.query(Transaction).filter(
                Transaction.id == trans_id,
                Transaction.status == TransactionStatus.PENDING
            ).first()
            
            if not transaction:
                results["failed"] += 1
                results["errors"].append({
                    "id": trans_id,
                    "error": "Transaction non trouvée ou déjà traitée"
                })
                continue
            
            if action == "approve":
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                transaction.validated_by = admin.id
                transaction.validation_notes = notes
                
                # Créditer pour dépôt
                if transaction.type == TransactionType.DEPOSIT:
                    user = db.query(User).filter(
                        User.id == transaction.recipient_id
                    ).first()
                    if user:
                        user.balance += transaction.amount
                
            else:
                transaction.status = TransactionStatus.CANCELLED
                transaction.validated_by = admin.id
                transaction.validation_notes = notes
                
                # Rembourser pour retrait
                if transaction.type == TransactionType.WITHDRAW:
                    user = db.query(User).filter(
                        User.id == transaction.sender_id
                    ).first()
                    if user:
                        user.balance += transaction.amount + transaction.fee
            
            results["success"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "id": trans_id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Lot traité: {results['success']} succès, {results['failed']} échecs",
        "data": results
    }


@router.get("/transactions")
async def list_all_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Liste toutes les transactions avec filtres avancés
    """
    query = db.query(Transaction)
    
    # Filtres
    if status:
        try:
            status_enum = TransactionStatus(status)
            query = query.filter(Transaction.status == status_enum)
        except ValueError:
            pass
    
    if transaction_type:
        try:
            type_enum = TransactionType(transaction_type)
            query = query.filter(Transaction.type == type_enum)
        except ValueError:
            pass
    
    if user_id:
        query = query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            )
        )
    
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Transaction.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(Transaction.created_at <= to_date)
        except ValueError:
            pass
    
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    
    if search:
        query = query.filter(
            or_(
                Transaction.reference.ilike(f"%{search}%"),
                Transaction.phone_number.ilike(f"%{search}%"),
                Transaction.description.ilike(f"%{search}%")
            )
        )
    
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
                "reference": t.reference,
                "type": t.type.value,
                "amount": t.amount,
                "fee": t.fee,
                "status": t.status.value,
                "method": t.method,
                "phone_number": t.phone_number,
                "sender_id": t.sender_id,
                "recipient_id": t.recipient_id,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in transactions
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==========================================
# GESTION DES UTILISATEURS
# ==========================================

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    min_balance: Optional[float] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Liste des utilisateurs avec filtres"""
    
    query = db.query(User).filter(User.role != UserRole.ADMIN)
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            pass
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    if min_balance is not None:
        query = query.filter(User.balance >= min_balance)
    
    total = query.count()
    
    users = query.order_by(desc(User.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "success": True,
        "data": [
            {
                "id": u.id,
                "phone": u.phone,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "balance": u.balance,
                "savings": u.savings,
                "is_verified": u.is_verified,
                "is_active": u.is_active,
                "country": u.country,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Détails d'un utilisateur"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    
    # Statistiques transactions
    sent_count = db.query(Transaction).filter(
        Transaction.sender_id == user_id
    ).count()
    
    received_count = db.query(Transaction).filter(
        Transaction.recipient_id == user_id
    ).count()
    
    pending_count = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == user_id,
            Transaction.recipient_id == user_id
        ),
        Transaction.status == TransactionStatus.PENDING
    ).count()
    
    # Volume total
    from sqlalchemy import func as sql_func
    
    total_sent = db.query(sql_func.sum(Transaction.amount)).filter(
        Transaction.sender_id == user_id,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0
    
    total_received = db.query(sql_func.sum(Transaction.amount)).filter(
        Transaction.recipient_id == user_id,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0
    
    # Dernières transactions
    recent_transactions = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == user_id,
            Transaction.recipient_id == user_id
        )
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    return {
        "success": True,
        "data": {
            "user": {
                "id": user.id,
                "phone": user.phone,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "balance": user.balance,
                "savings": user.savings,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "country": user.country,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
            },
            "stats": {
                "sent_transactions": sent_count,
                "received_transactions": received_count,
                "pending_transactions": pending_count,
                "total_sent_volume": float(total_sent),
                "total_received_volume": float(total_received)
            },
            "recent_transactions": [
                {
                    "id": t.id,
                    "reference": t.reference,
                    "type": t.type.value,
                    "amount": t.amount,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in recent_transactions
            ]
        }
    }


@router.post("/users")
async def create_user(
    phone: str,
    password: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role: str = "user",
    initial_balance: float = 0.0,
    is_verified: bool = True,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Crée un nouvel utilisateur"""
    
    # Vérifier unicité téléphone
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        raise HTTPException(400, "Ce numéro de téléphone existe déjà")
    
    if email:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(400, "Cet email existe déjà")
    
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(400, "Rôle invalide. Utilisez 'admin' ou 'user'")
    
    user = User(
        id=str(uuid.uuid4()),
        phone=phone,
        email=email,
        full_name=full_name,
        password_hash=pwd_context.hash(password),
        role=user_role,
        balance=initial_balance,
        is_verified=is_verified,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "Utilisateur créé avec succès",
        "data": {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "balance": user.balance
        }
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    balance: Optional[float] = None,
    savings: Optional[float] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Modifie un utilisateur"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    
    # Empêcher la modification de son propre compte
    if user_id == admin.id:
        raise HTTPException(400, "Impossible de modifier votre propre compte")
    
    # Vérifications d'unicité
    if phone and phone != user.phone:
        existing = db.query(User).filter(User.phone == phone).first()
        if existing:
            raise HTTPException(400, "Ce numéro existe déjà")
        user.phone = phone
    
    if email and email != user.email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(400, "Cet email existe déjà")
        user.email = email
    
    # Mises à jour
    if full_name is not None:
        user.full_name = full_name
    
    if password:
        user.password_hash = pwd_context.hash(password)
    
    if role:
        try:
            user.role = UserRole(role)
        except ValueError:
            raise HTTPException(400, "Rôle invalide")
    
    if balance is not None:
        user.balance = balance
    
    if savings is not None:
        user.savings = savings
    
    if is_active is not None:
        user.is_active = is_active
    
    if is_verified is not None:
        user.is_verified = is_verified
    
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "Utilisateur modifié avec succès",
        "data": {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "balance": user.balance,
            "savings": user.savings,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Supprime un utilisateur"""
    
    if user_id == admin.id:
        raise HTTPException(400, "Impossible de supprimer votre propre compte")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    
    if user.balance > 0 or user.savings > 0:
        raise HTTPException(
            400,
            f"Impossible de supprimer. Solde: {user.balance:,.0f} XOF, Épargne: {user.savings:,.0f} XOF"
        )
    
    # Vérifier transactions en attente
    pending = db.query(Transaction).filter(
        or_(
            Transaction.sender_id == user_id,
            Transaction.recipient_id == user_id
        ),
        Transaction.status == TransactionStatus.PENDING
    ).count()
    
    if pending > 0:
        raise HTTPException(400, f"{pending} transactions en attente pour cet utilisateur")
    
    db.delete(user)
    db.commit()
    
    return {
        "success": True,
        "message": "Utilisateur supprimé avec succès"
    }


# ==========================================
# GESTION DES OPÉRATEURS
# ==========================================

@router.get("/operators")
async def list_operators(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Liste des opérateurs Mobile Money et leurs soldes"""
    
    operators = db.query(OperatorBalance).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": op.id,
                "operator": op.operator,
                "balance": op.balance,
                "account_number": op.account_number,
                "is_active": op.is_active,
                "has_api": op.api_key is not None and op.api_key != "",
                "last_sync_at": op.last_sync_at.isoformat() if op.last_sync_at else None,
                "status": "ok" if op.balance >= 500000 else ("low" if op.balance > 0 else "empty")
            }
            for op in operators
        ]
    }


@router.post("/operators/{operator_id}/recharge")
async def recharge_operator(
    operator_id: str,
    amount: float,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Recharge le solde d'un opérateur
    (après virement bancaire ou dépôt physique)
    """
    
    if amount <= 0:
        raise HTTPException(400, "Montant invalide")
    
    operator = db.query(OperatorBalance).filter(
        OperatorBalance.id == operator_id
    ).first()
    
    if not operator:
        raise HTTPException(404, "Opérateur non trouvé")
    
    old_balance = operator.balance
    operator.balance += amount
    operator.last_sync_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Solde {operator.operator} rechargé de {amount:,.0f} XOF",
        "data": {
            "operator": operator.operator,
            "old_balance": old_balance,
            "added_amount": amount,
            "new_balance": operator.balance,
            "reference": reference,
            "notes": notes,
            "recharged_by": admin.id
        }
    }


@router.put("/operators/{operator_id}")
async def update_operator(
    operator_id: str,
    account_number: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Met à jour les informations d'un opérateur"""
    
    operator = db.query(OperatorBalance).filter(
        OperatorBalance.id == operator_id
    ).first()
    
    if not operator:
        raise HTTPException(404, "Opérateur non trouvé")
    
    if account_number is not None:
        operator.account_number = account_number
    
    if api_key is not None:
        operator.api_key = api_key
    
    if api_secret is not None:
        operator.api_secret = api_secret
    
    if is_active is not None:
        operator.is_active = is_active
    
    db.commit()
    
    return {
        "success": True,
        "message": "Opérateur mis à jour",
        "data": {
            "operator": operator.operator,
            "is_active": operator.is_active,
            "has_api": operator.api_key is not None
        }
    }


# ==========================================
# STATISTIQUES ET RAPPORTS
# ==========================================

@router.get("/reports/transactions")
async def transaction_report(
    date_from: str,
    date_to: str,
    group_by: str = "day",  # day, week, month
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Rapport des transactions par période
    """
    
    try:
        start = datetime.fromisoformat(date_from)
        end = datetime.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(400, "Format de date invalide")
    
    # Statistiques globales
    transactions = db.query(Transaction).filter(
        Transaction.created_at >= start,
        Transaction.created_at <= end
    ).all()
    
    total_count = len(transactions)
    total_volume = sum(t.amount for t in transactions if t.status == TransactionStatus.COMPLETED)
    total_fees = sum(t.fee for t in transactions if t.status == TransactionStatus.COMPLETED)
    
    # Par type
    by_type = {}
    for t_type in TransactionType:
        type_trans = [t for t in transactions if t.type == t_type]
        by_type[t_type.value] = {
            "count": len(type_trans),
            "volume": sum(t.amount for t in type_trans if t.status == TransactionStatus.COMPLETED),
            "fees": sum(t.fee for t in type_trans if t.status == TransactionStatus.COMPLETED)
        }
    
    # Par statut
    by_status = {}
    for t_status in TransactionStatus:
        by_status[t_status.value] = len([t for t in transactions if t.status == t_status])
    
    # Par méthode
    by_method = {}
    for t in transactions:
        if t.method:
            if t.method not in by_method:
                by_method[t.method] = {"count": 0, "volume": 0}
            by_method[t.method]["count"] += 1
            if t.status == TransactionStatus.COMPLETED:
                by_method[t.method]["volume"] += t.amount
    
    return {
        "success": True,
        "data": {
            "period": {
                "from": date_from,
                "to": date_to
            },
            "summary": {
                "total_transactions": total_count,
                "total_volume": total_volume,
                "total_fees": total_fees
            },
            "by_type": by_type,
            "by_status": by_status,
            "by_method": by_method
        }
    }


@router.get("/reports/users")
async def user_report(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Rapport sur les utilisateurs"""
    
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    total = db.query(User).filter(User.role == UserRole.USER).count()
    active = db.query(User).filter(
        User.role == UserRole.USER,
        User.is_active == True
    ).count()
    verified = db.query(User).filter(
        User.role == UserRole.USER,
        User.is_verified == True
    ).count()
    
    new_today = db.query(User).filter(
        User.role == UserRole.USER,
        User.created_at >= today
    ).count()
    
    new_week = db.query(User).filter(
        User.role == UserRole.USER,
        User.created_at >= week_ago
    ).count()
    
    new_month = db.query(User).filter(
        User.role == UserRole.USER,
        User.created_at >= month_ago
    ).count()
    
    # Utilisateurs avec solde
    with_balance = db.query(User).filter(
        User.role == UserRole.USER,
        User.balance > 0
    ).count()
    
    total_balance = db.query(func.sum(User.balance)).filter(
        User.role == UserRole.USER
    ).scalar() or 0
    
    return {
        "success": True,
        "data": {
            "total_users": total,
            "active_users": active,
            "verified_users": verified,
            "new_users": {
                "today": new_today,
                "this_week": new_week,
                "this_month": new_month
            },
            "balances": {
                "users_with_balance": with_balance,
                "total_balance_held": float(total_balance)
            }
        }
    }


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def check_operator_balance(db: Session, operator: str, amount: float) -> bool:
    """Vérifie la liquidité d'un opérateur"""
    op = db.query(OperatorBalance).filter(
        OperatorBalance.operator == operator,
        OperatorBalance.is_active == True
    ).first()
    return op and op.balance >= amount


def debit_operator_balance(db: Session, operator: str, amount: float):
    """Débite le solde d'un opérateur"""
    op = db.query(OperatorBalance).filter(
        OperatorBalance.operator == operator
    ).first()
    if op:
        op.balance -= amount
        op.last_sync_at = datetime.utcnow()