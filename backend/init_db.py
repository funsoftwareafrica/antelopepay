import os
import sys
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    db_filename = "app.db"
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_filename)
    
    if os.path.exists(db_path):
        print(f"Suppression de l'ancienne base de donnees : {db_path}")
        os.remove(db_path)
    
    print("Creation des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables creees.")

    db = SessionLocal()
    try:
        admin_phone = "+22791599100"
        # Hash du mot de passe
        hashed_pwd = pwd_context.hash("bufulon123@")
        
        # IMPORTANT : On utilise hashed_password car c'est le nom du champ dans le modele
        admin_user = User(
            phone=admin_phone,
            hashed_password=hashed_pwd, 
            full_name="Administrateur",
            email="admin@antelopepay.com",
            country="Niger",
            balance=10000000.00, 
            savings=0.00,
            is_verified=True,
            is_active=True,
            pin="1234" 
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Utilisateur administrateur cree : {admin_phone}")
        
    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initialisation...")
    init_database()
    print("Termine !")
