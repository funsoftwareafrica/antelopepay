import sys
import os
import argparse

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin(phone: str, password: str, email: str = None, full_name: str = None):
    """Crée un compte administrateur"""
    
    db = SessionLocal()
    
    try:
        # Vérifier si un admin existe déjà
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if existing_admin:
            print("\n" + "=" * 50)
            print("  Un administrateur existe déjà!")
            print(f"   Téléphone: {existing_admin.phone}")
            print(f"   Email: {existing_admin.email}")
            print("=" * 50)
            
            # Note: input() bloquera le script si exécuté de manière non-interactive
            # On continue automatiquement pour les tests, ou on demande en interactif
            import sys
            if sys.stdin.isatty():
                response = input("\nVoulez-vous créer un autre admin? (oui/non): ")
                if response.lower() not in ["oui", "o", "yes", "y"]:
                    print(" Opération annulée.")
                    return
            else:
                print(" Mode non-interactif: création annulée pour éviter les doublons.")
                return
        
        # Vérifier si le téléphone existe
        existing_phone = db.query(User).filter(User.phone == phone).first()
        if existing_phone:
            print(f" Erreur: Le numéro {phone} existe déjà!")
            return
        
        # Vérifier si l'email existe
        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                print(f" Erreur: L'email {email} existe déjà!")
                return
        
        # Créer l'admin
        admin = User(
            phone=phone,
            email=email,
            full_name=full_name or "Administrateur",
            password_hash=pwd_context.hash(password),
            role=UserRole.ADMIN,
            is_verified=True,
            is_active=True,
            balance=0.0
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "=" * 50)
        print(" ADMINISTRATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 50)
        print(f"   ID:        {admin.id}")
        print(f"   Téléphone: {admin.phone}")
        print(f"   Email:     {admin.email or 'Non défini'}")
        print(f"   Nom:       {admin.full_name}")
        print(f"   Mot de passe: {password}")
        print("=" * 50)
        print("\n  IMPORTANT: Changez le mot de passe après la première connexion!")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f" Erreur lors de la création: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Créer un compte administrateur AntelopePay"
    )
    
    # MODIFICATION: Utilisation des mêmes identifiants par défaut que init_database.py
    parser.add_argument(
        "--phone", "-p",
        default="+22791599100",
        help="Numéro de téléphone de l'admin"
    )
    
    parser.add_argument(
        "--password", "-pwd",
        default="bufulon123",
        help="Mot de passe de l'admin"
    )
    
    parser.add_argument(
        "--email", "-e",
        default="admin@antelopepay.com",
        help="Email de l'admin"
    )
    
    parser.add_argument(
        "--name", "-n",
        default="Administrateur Principal",
        help="Nom complet de l'admin"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 50)
    print("🏦 ANTELOPEPAY - Création Admin")
    print("=" * 50 + "\n")
    
    create_admin(
        phone=args.phone,
        password=args.password,
        email=args.email,
        full_name=args.name
    )


if __name__ == "__main__":
    main()