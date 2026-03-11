from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt

from app.database import get_db
from app.models import User, RefreshToken, UserRole
from app.schemas import UserCreate, UserLogin
from app.auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, verify_token
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user

@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.phone == user_data.phone).first()
    if existing:
        return {"success": False, "message": "Ce numéro est déjà utilisé"}
    
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            return {"success": False, "message": "Cet email est déjà utilisé"}
    
    new_user = User(
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        email=user_data.email or None,
        country=user_data.country or None,
        pin_hash=get_password_hash(user_data.pin) if user_data.pin else None,
        role=UserRole.USER,
        balance=0.0,
        savings=0.0,
        is_verified=False,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    token_record = RefreshToken(
        user_id=new_user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(token_record)
    db.commit()
    
    # CORRECTION: Structure de réponse alignée sur le frontend (data.data.user)
    return {
        "success": True,
        "message": "Compte créé avec succès",
        "data": {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "user": {
                "id": str(new_user.id),
                "phone": new_user.phone,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "country": new_user.country,
                "role": new_user.role.value,
                "balance": 0,
                "savings": 0,
                "is_verified": new_user.is_verified,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            }
        }
    }

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == credentials.phone).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        return {"success": False, "message": "Identifiants incorrects"}
    
    if not user.is_active:
        return {"success": False, "message": "Compte désactivé"}
    
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(token_record)
    db.commit()
    
    # CORRECTION: Structure de réponse alignée sur le frontend
    return {
        "success": True,
        "message": "Connexion réussie",
        "data": {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "email": user.email,
                "full_name": user.full_name,
                "country": user.country,
                "role": user.role.value,
                "balance": float(user.balance or 0),
                "savings": float(user.savings or 0),
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    }

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user_id = verify_token(credentials.credentials, "access")
    if user_id:
        tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        for t in tokens:
            t.is_revoked = True
        db.commit()
    
    return {"success": True, "message": "Déconnexion réussie"}

@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        return {"success": False, "message": "Token manquant"}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if payload.get("type") != "access":
            return {"success": False, "message": "Token invalide"}
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # CORRECTION: Structure de réponse alignée sur le frontend
        return {
            "success": True,
            "data": {
                "user": {
                    "id": str(user.id),
                    "phone": user.phone,
                    "email": user.email,
                    "full_name": user.full_name,
                    "country": user.country,
                    "role": user.role.value,
                    "balance": float(user.balance or 0),
                    "savings": float(user.savings or 0),
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
        }
    except jwt.JWTError:
        return {"success": False, "message": "Token invalide"}