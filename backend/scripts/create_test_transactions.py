import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, Transaction, TransactionType, TransactionStatus
from datetime import datetime, timedelta
import uuid


def create_test_transactions():
    """Crée des transactions de test en attente"""
    
    db = SessionLocal()
    
    try:
        # Récupérer l'utilisateur test
        user = db.query(User).filter(User.phone == "+2250700000002").first()
        
        if not user:
            print(" Utilisateur test non trouvé. Créez-le d'abord.")
            return
        
        print(f"\n Utilisateur: {user.full_name or user.phone}")
        print(f"   Solde actuel: {user.balance:,.0f} XOF\n")
        
        created_count = 0
        methods = ["orange_money", "mtn_money", "moov_money", "telecel_cash"]
        
        # 1. Dépôts en attente
        print(" Création des dépôts...")
        deposit_amounts = [15000, 25000, 75000, 120000]
        
        for i, amount in enumerate(deposit_amounts):
            ref = f"DEP{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
            risk_score = random.uniform(0.1, 0.9)
            risk_level = "low" if risk_score < 0.3 else ("medium" if risk_score < 0.6 else "high")
            risk_reasons = []
            if risk_level == "medium":
                risk_reasons = ["Montant inhabituel"]
            elif risk_level == "high":
                risk_reasons = ["Première transaction", "Montant élevé"]
            
            transaction = Transaction(
                id=str(uuid.uuid4()),
                recipient_id=user.id,
                type=TransactionType.DEPOSIT,
                amount=amount,
                fee=0.0,
                currency="XOF",
                method=methods[i % len(methods)],
                phone_number=user.phone,
                status=TransactionStatus.PENDING,
                reference=ref,
                description=f"Dépôt via {methods[i % len(methods)].replace('_', ' ').title()}",
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 180)),
                extra_data={
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "risk_reasons": risk_reasons
                }
            )
            
            db.add(transaction)
            created_count += 1
            print(f"    Dépôt: {amount:,.0f} XOF via {methods[i % len(methods)]} - Risque: {risk_level}")
        
        # 2. Retraits en attente
        print("\n Création des retraits...")
        withdraw_amounts = [10000, 35000, 80000]
        
        for i, amount in enumerate(withdraw_amounts):
            fee = amount * 0.01
            total = amount + fee
            
            if user.balance < total:
                print(f"    Solde insuffisant pour retrait {amount:,.0f} XOF - ignoré")
                continue
            
            ref = f"WDR{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
            risk_score = random.uniform(0.1, 0.9)
            risk_level = "low" if risk_score < 0.3 else ("medium" if risk_score < 0.6 else "high")
            risk_reasons = []
            if risk_level == "medium":
                risk_reasons = ["Fréquence élevée"]
            elif risk_level == "high":
                risk_reasons = ["Premier retrait", "Compte récent"]
            
            transaction = Transaction(
                id=str(uuid.uuid4()),
                sender_id=user.id,
                type=TransactionType.WITHDRAW,
                amount=amount,
                fee=fee,
                currency="XOF",
                method=methods[i % len(methods)],
                phone_number=user.phone,
                status=TransactionStatus.PENDING,
                reference=ref,
                description=f"Retrait via {methods[i % len(methods)].replace('_', ' ').title()}",
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 120)),
                extra_data={
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "risk_reasons": risk_reasons
                }
            )
            
            # Débiter le compte
            user.balance -= total
            
            db.add(transaction)
            created_count += 1
            print(f"    Retrait: {amount:,.0f} XOF via {methods[i % len(methods)]} - Risque: {risk_level}")
        
        db.commit()
        
        print(f"\n" + "=" * 50)
        print(f" {created_count} TRANSACTIONS CRÉÉES!")
        print("=" * 50)
        print(f"   Solde utilisateur: {user.balance:,.0f} XOF")
        print("\n Allez sur le panel admin pour les valider:")
        print("   1. Ouvrir: http://localhost:3000")
        print("   2. Se connecter: +2250700000001 / Admin@123456")
        print("   3. Cliquer sur 'Panel Admin'")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f" Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_transactions()