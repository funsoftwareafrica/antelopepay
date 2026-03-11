from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, Contact
from app.schemas import ContactCreate, ContactUpdate, ContactResponse, ContactListResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("")
def get_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id)\
        .order_by(Contact.is_favorite.desc(), Contact.name).all()
    
    return {
        "success": True,
        "data": [ContactResponse.model_validate(c) for c in contacts],
        "total": len(contacts)
    }

@router.post("")
def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = Contact(
        user_id=current_user.id,
        name=contact_data.name,
        phone=contact_data.phone,
        is_favorite=contact_data.is_favorite
    )
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return ContactResponse.model_validate(contact)

@router.delete("/{contact_id}")
def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    
    db.delete(contact)
    db.commit()
    
    return {"success": True, "message": "Contact supprimé"}