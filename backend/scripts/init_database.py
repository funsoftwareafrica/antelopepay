"""
Script d'initialisation complète de la base de données

Utilisation:
    cd backend
    python -m scripts.init_database
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole, OperatorBalance
from passlib.context import CryptContext
from datetime import datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === DÉFINITION DES IDENTIFIANTS PAR DÉFAUT ===
ADMIN_PHONE = "+22791599100"
ADMIN_PASSWORD = "bufulon123"
ADMIN_EMAIL = "admin@antelopepay.com"
ADMIN_INITIAL_BALANCE = 10_000_000.0  # Solde initial pour l'admin

TEST_PHONE = "+22799168983"
TEST_PASSWORD = "bufulon123"
TEST_EMAIL = "test@antelopepay.com"

def init_database():
    """Initialisation complète de la base de données"""
    
    print("\n" + "=" * 60)
    print("🏦 ANTELOPEPAY - Initialisation de la Base de Données")
    print("=" * 60 + "\n")
    
    # 1. Créer les tables
    print("📦 Création des tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("   ✅ Tables créées avec succès\n")
    except Exception as e:
        print(f"   ❌ Erreur création tables: {e}")
        return
    
    db = SessionLocal()
    
    try:
        # 2. Créer l'administrateur par défaut
        print("👤 Création de l'administrateur par défaut...")
        
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if existing_admin:
            # MISE À JOUR DU SOLDE SI L'ADMIN EXISTE DEJA
            existing_admin.balance = ADMIN_INITIAL_BALANCE
            existing_admin.is_active = True
            existing_admin.is_verified = True
            print("    ✅ Admin existant mis à jour")
            print(f"      Nouveau solde forcé: {ADMIN_INITIAL_BALANCE:,.0f} XOF")
        else:
            admin = User(
                id=str(uuid.uuid4()),
                phone=ADMIN_PHONE,
                email=ADMIN_EMAIL,
                full_name="Administrateur Principal",
                password_hash=pwd_context.hash(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_verified=True,
                is_active=True,
                balance=ADMIN_INITIAL_BALANCE
            )
            db.add(admin)
            print("    ✅ Admin créé")
            print(f"      Téléphone: {ADMIN_PHONE}")
            print(f"      Mot de passe: {ADMIN_PASSWORD}")
            print(f"      Solde initial: {ADMIN_INITIAL_BALANCE:,.0f} XOF")
        
        # 3. Créer un utilisateur de test
        print("👤 Création d'un utilisateur de test...")
        
        existing_test = db.query(User).filter(User.phone == TEST_PHONE).first()
        
        if not existing_test:
            test_user = User(
                id=str(uuid.uuid4()),
                phone=TEST_PHONE,
                email=TEST_EMAIL,
                full_name="Utilisateur Test",
                password_hash=pwd_context.hash(TEST_PASSWORD),
                role=UserRole.USER,
                is_verified=True,
                is_active=True,
                balance=50000.0  # 50,000 XOF pour tester
            )
            db.add(test_user)
            print("    ✅ Utilisateur test créé")
            print(f"      Téléphone: {TEST_PHONE}")
            print(f"      Mot de passe: {TEST_PASSWORD}")
            print("      Solde: 50,000 XOF")
        else:
            print("     ⚠️ Utilisateur test existe déjà")
            print(f"      Téléphone existant: {existing_test.phone}")
        
        print()
        
        # 4. Créer les opérateurs
        print("📱 Création des opérateurs Mobile Money...")
        
        operators = [
            {"operator": "orange_money", "balance": 5000000.0, "account": "OM-ANT-001"},
            {"operator": "mtn_money", "balance": 5000000.0, "account": "MTN-ANT-001"},
            {"operator": "moov_money", "balance": 3000000.0, "account": "MOOV-ANT-001"},
            {"operator": "telecel_cash", "balance": 3000000.0, "account": "TC-ANT-001"},
        ]
        
        for op_data in operators:
            existing = db.query(OperatorBalance).filter(
                OperatorBalance.operator == op_data["operator"]
            ).first()
            
            if not existing:
                operator = OperatorBalance(
                    id=str(uuid.uuid4()),
                    operator=op_data["operator"],
                    balance=op_data["balance"],
                    account_number=op_data["account"],
                    is_active=True
                )
                db.add(operator)
                print(f"    ✅ {op_data['operator']}: {op_data['balance']:,.0f} XOF")
            else:
                print(f"    ⚠️ {op_data['operator']}: existe déjà")
        
        db.commit()
        
        print()
        print("=" * 60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 60)
        print("\n🔑 Comptes créés (ou existants):")
        print("-" * 60)
        print("   ADMIN:")
        print(f"      Téléphone: {ADMIN_PHONE}")
        print(f"      Mot de passe: {ADMIN_PASSWORD}")
        print(f"      Solde: {ADMIN_INITIAL_BALANCE:,.0f} XOF")
        print()
        print("   UTILISATEUR TEST:")
        print(f"      Téléphone: {TEST_PHONE}")
        print(f"      Mot de passe: {TEST_PASSWORD}")
        print("      Solde initial: 50,000 XOF")
        print("-" * 60)
        print("\n⚠️  IMPORTANT: Changez les mots de passe en production!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()