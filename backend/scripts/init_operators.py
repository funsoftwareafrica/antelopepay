
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import OperatorBalance
from datetime import datetime
import uuid


def init_operators():
    """Initialise les opérateurs Mobile Money avec leurs soldes initiaux"""
    
    db = SessionLocal()
    
    operators_data = [
        {
            "operator": "orange_money",
            "balance": 5000000.0,  # 5 millions XOF
            "account_number": "OM-ANT-001",
            "display_name": "Orange Money",
            "color": "#FF7900"
        },
        {
            "operator": "mtn_money",
            "balance": 5000000.0,
            "account_number": "MTN-ANT-001",
            "display_name": "MTN Mobile Money",
            "color": "#FFCC00"
        },
        {
            "operator": "moov_money",
            "balance": 3000000.0,
            "account_number": "MOOV-ANT-001",
            "display_name": "Moov Money",
            "color": "#0089CF"
        },
        {
            "operator": "telecel_cash",
            "balance": 3000000.0,
            "account_number": "TC-ANT-001",
            "display_name": "Telecel Cash",
            "color": "#E3001B"
        }
    ]
    
    try:
        print("\n" + "=" * 50)
        print(" ANTELOPEPAY - Initialisation Opérateurs")
        print("=" * 50 + "\n")
        
        created_count = 0
        updated_count = 0
        
        for op_data in operators_data:
            existing = db.query(OperatorBalance).filter(
                OperatorBalance.operator == op_data["operator"]
            ).first()
            
            if existing:
                print(f"  {op_data['display_name']}: existe déjà")
                print(f"   Solde actuel: {existing.balance:,.0f} XOF")
                
                # Mettre à jour le solde si demandé
                response = input(f"   Mettre à jour le solde à {op_data['balance']:,.0f} XOF? (o/n): ")
                if response.lower() in ["o", "oui", "y", "yes"]:
                    existing.balance = op_data["balance"]
                    existing.last_sync_at = datetime.utcnow()
                    updated_count += 1
                    print(f"    Solde mis à jour")
            else:
                operator = OperatorBalance(
                    id=str(uuid.uuid4()),
                    operator=op_data["operator"],
                    balance=op_data["balance"],
                    account_number=op_data["account_number"],
                    is_active=True
                )
                db.add(operator)
                created_count += 1
                print(f" {op_data['display_name']}: créé")
                print(f"   Solde initial: {op_data['balance']:,.0f} XOF")
                print(f"   Compte: {op_data['account_number']}")
            
            print()
        
        db.commit()
        
        # Afficher le récapitulatif
        total_liquidity = sum(op["balance"] for op in operators_data)
        
        print("=" * 50)
        print(" RÉCAPITULATIF")
        print("=" * 50)
        print(f"   Opérateurs créés:   {created_count}")
        print(f"   Opérateurs mis à jour: {updated_count}")
        print(f"   Liquidité totale:   {total_liquidity:,.0f} XOF")
        print("=" * 50 + "\n")
        
        # Lister tous les opérateurs
        print(" Liste des opérateurs:")
        print("-" * 50)
        
        all_operators = db.query(OperatorBalance).all()
        for op in all_operators:
            status = " Actif" if op.is_active else " Inactif"
            balance_status = "🟢" if op.balance >= 500000 else ("🟡" if op.balance > 0 else "🔴")
            print(f"   {balance_status} {op.operator}: {op.balance:,.0f} XOF - {status}")
        
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f" Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_operators()