import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User


def add_balance(phone: str, amount: float):
    """Ajoute du solde à un utilisateur"""
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            print(f" Utilisateur non trouvé: {phone}")
            return
        
        old_balance = user.balance
        user.balance += amount
        
        db.commit()
        
        print("\n" + "=" * 50)
        print(" SOLDE MIS À JOUR")
        print("=" * 50)
        print(f"   Utilisateur: {user.full_name or user.phone}")
        print(f"   Téléphone:   {user.phone}")
        print(f"   Ancien solde: {old_balance:,.0f} XOF")
        print(f"   Ajouté:      +{amount:,.0f} XOF")
        print(f"   Nouveau solde: {user.balance:,.0f} XOF")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f" Erreur: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Ajouter du solde à un utilisateur"
    )
    
    parser.add_argument(
        "--phone", "-p",
        required=True,
        help="Numéro de téléphone de l'utilisateur"
    )
    
    parser.add_argument(
        "--amount", "-a",
        type=float,
        required=True,
        help="Montant à ajouter (XOF)"
    )
    
    args = parser.parse_args()
    
    add_balance(args.phone, args.amount)


if __name__ == "__main__":
    main()