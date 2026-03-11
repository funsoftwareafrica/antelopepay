"""
Moteur de détection de fraude et validation automatique
Score de risque: 0.0 = très sûr, 1.0 = très risqué
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import User, Transaction, TransactionType, TransactionStatus
from app.config import settings


class RiskLevel:
    """Niveaux de risque"""
    LOW = "low"           # Auto-approuvé
    MEDIUM = "medium"     # Vérification OTP requise
    HIGH = "high"         # Validation admin requise
    CRITICAL = "critical" # Transaction bloquée


class FraudDetectionEngine:
    """
    Moteur de détection de fraude
    
    Fonctionnalités:
    - Score de risque calculé dynamiquement
    - Analyse comportementale de l'utilisateur
    - Détection d'anomalies
    - Apprentissage des habitudes
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==========================================
    # CALCUL DU SCORE DE RISQUE
    # ==========================================
    
    def calculate_risk_score(
        self, 
        user: User, 
        amount: float, 
        transaction_type: TransactionType,
        phone: Optional[str] = None
    ) -> Tuple[float, List[str], Dict]:
        """
        Calcule le score de risque d'une transaction
        
        Returns:
            (score, raisons, détails)
            - score: float entre 0.0 et 1.0
            - raisons: liste des facteurs de risque
            - détails: dict avec le détail de chaque facteur
        """
        score = 0.0
        reasons = []
        details = {}
        
        # 1. Ancienneté du compte
        account_score = self._check_account_age(user)
        if account_score > 0:
            score += account_score
            reasons.append(f"Compte récent ({self._get_account_age_days(user)} jours)")
            details["account_age"] = account_score
        
        # 2. Statut de vérification
        if not user.is_verified:
            score += 0.15
            reasons.append("Compte non vérifié")
            details["unverified"] = 0.15
        
        # 3. Première transaction
        is_first = self._is_first_transaction(user.id, transaction_type)
        if is_first:
            score += 0.20
            reasons.append("Première transaction de ce type")
            details["first_transaction"] = 0.20
            
            # Première transaction + gros montant = très suspect
            if amount >= settings.LARGE_AMOUNT_THRESHOLD:
                score += 0.15
                reasons.append(f"Premier {transaction_type.value} avec montant élevé")
                details["large_first"] = 0.15
        
        # 4. Analyse du montant
        amount_score = self._analyze_amount(user, amount, transaction_type)
        if amount_score > 0:
            score += amount_score
            details["amount_analysis"] = amount_score
        
        # 5. Fréquence des transactions
        frequency_score, freq_reasons = self._check_frequency(user.id)
        if frequency_score > 0:
            score += frequency_score
            reasons.extend(freq_reasons)
            details["frequency"] = frequency_score
        
        # 6. Heure de la transaction
        time_score = self._check_transaction_time()
        if time_score > 0:
            score += time_score
            reasons.append("Transaction à heure inhabituelle")
            details["unusual_time"] = time_score
        
        # 7. Échecs récents
        failure_score = self._check_recent_failures(user.id)
        if failure_score > 0:
            score += failure_score
            reasons.append("Échecs de transaction récents")
            details["recent_failures"] = failure_score
        
        # 8. Numéro de téléphone (pour retraits)
        if phone and transaction_type == TransactionType.WITHDRAW:
            phone_score = self._analyze_phone(phone, user)
            if phone_score > 0:
                score += phone_score
                reasons.append("Numéro de téléphone inhabituel")
                details["phone_analysis"] = phone_score
        
        # 9. Comportement inhabituel
        behavior_score = self._analyze_behavior(user, amount, transaction_type)
        if behavior_score > 0:
            score += behavior_score
            reasons.append("Comportement inhabituel détecté")
            details["behavior"] = behavior_score
        
        # Normaliser le score
        final_score = min(score, 1.0)
        
        return final_score, reasons, details
    
    # ==========================================
    # MÉTHODES DE VÉRIFICATION
    # ==========================================
    
    def _get_account_age_days(self, user: User) -> int:
        """Retourne l'âge du compte en jours"""
        return (datetime.utcnow() - user.created_at).days
    
    def _check_account_age(self, user: User) -> float:
        """
        Score basé sur l'ancienneté du compte
        - < 24h: 0.30
        - < 7 jours: 0.20
        - < 30 jours: 0.10
        - > 30 jours: 0.00
        """
        days = self._get_account_age_days(user)
        
        if days < 1:
            return 0.30
        elif days < 7:
            return 0.20
        elif days < 30:
            return 0.10
        return 0.0
    
    def _is_first_transaction(self, user_id: str, trans_type: TransactionType) -> bool:
        """Vérifie si c'est la première transaction de ce type"""
        count = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.type == trans_type,
            Transaction.status == TransactionStatus.COMPLETED
        ).count()
        
        return count == 0
    
    def _analyze_amount(self, user: User, amount: float, trans_type: TransactionType) -> float:
        """
        Analyse le montant par rapport aux habitudes
        """
        score = 0.0
        
        # Très gros montant
        if amount >= settings.VERY_LARGE_AMOUNT_THRESHOLD:
            score += 0.20
        elif amount >= settings.LARGE_AMOUNT_THRESHOLD:
            score += 0.10
        
        # Comparer avec la moyenne historique
        avg_amount = self._get_historical_average(user.id, trans_type)
        
        if avg_amount > 0:
            # Montant > 3x la moyenne
            if amount > avg_amount * 3:
                score += 0.15
            # Montant > 5x la moyenne
            elif amount > avg_amount * 5:
                score += 0.25
        
        # Montant rond suspect (ex: exactement 100,000)
        if amount >= 50000 and amount % 10000 == 0:
            score += 0.05
        
        return score
    
    def _get_historical_average(self, user_id: str, trans_type: TransactionType) -> float:
        """Calcule le montant moyen des transactions passées"""
        result = self.db.query(func.avg(Transaction.amount)).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.type == trans_type,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar()
        
        return float(result or 0)
    
    def _check_frequency(self, user_id: str) -> Tuple[float, List[str]]:
        """
        Vérifie la fréquence des transactions
        """
        score = 0.0
        reasons = []
        now = datetime.utcnow()
        
        # Transactions dans la dernière heure
        hour_ago = now - timedelta(hours=1)
        count_hour = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= hour_ago
        ).count()
        
        if count_hour >= settings.MAX_TRANSACTIONS_PER_HOUR:
            score += 0.25
            reasons.append(f"Fréquence élevée: {count_hour} transactions/heure")
        
        # Transactions aujourd'hui
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count_today = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= today_start
        ).count()
        
        if count_today >= settings.MAX_TRANSACTIONS_PER_DAY:
            score += 0.15
            reasons.append(f"Quota journalier atteint: {count_today} transactions")
        
        return score, reasons
    
    def _check_transaction_time(self) -> float:
        """
        Vérifie si l'heure est inhabituelle
        Transactions nocturnes (00h-06h) sont plus suspectes
        """
        hour = datetime.utcnow().hour
        
        if 0 <= hour < 6:
            return 0.10  # Nuit
        elif 6 <= hour < 8:
            return 0.05  # Tôt le matin
        return 0.0
    
    def _check_recent_failures(self, user_id: str) -> float:
        """Vérifie les échecs récents"""
        since = datetime.utcnow() - timedelta(hours=24)
        
        count = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.status == TransactionStatus.FAILED,
            Transaction.created_at >= since
        ).count()
        
        if count >= settings.MAX_FAILED_ATTEMPTS:
            return 0.20
        elif count >= 2:
            return 0.10
        return 0.0
    
    def _analyze_phone(self, phone: str, user: User) -> float:
        """Analyse le numéro de téléphone"""
        score = 0.0
        
        # Numéro différent de celui du compte?
        if phone != user.phone:
            # Vérifier si ce numéro a été utilisé récemment
            recent_use = self.db.query(Transaction).filter(
                Transaction.sender_id == user.id,
                Transaction.phone_number == phone,
                Transaction.status == TransactionStatus.COMPLETED
            ).count()
            
            if recent_use == 0:
                score += 0.10  # Nouveau numéro
        
        return score
    
    def _analyze_behavior(self, user: User, amount: float, trans_type: TransactionType) -> float:
        """
        Analyse comportementale avancée
        Détecte les changements brusques d'habitudes
        """
        score = 0.0
        
        # Récupérer les 10 dernières transactions
        recent = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user.id,
                Transaction.recipient_id == user.id
            ),
            Transaction.status == TransactionStatus.COMPLETED
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        if len(recent) >= 5:
            # Vérifier la variété des types de transaction
            types_used = set(t.type for t in recent)
            
            # Nouveau type de transaction non utilisé récemment
            if trans_type not in types_used:
                score += 0.10
        
        return score
    
    # ==========================================
    # DÉCISION FINALE
    # ==========================================
    
    def get_decision(
        self, 
        user: User, 
        amount: float, 
        transaction_type: TransactionType,
        phone: Optional[str] = None
    ) -> Dict:
        """
        Prend une décision automatique basée sur le score de risque
        
        Returns:
            {
                "action": "auto"|"verify"|"manual"|"block",
                "risk_level": "low"|"medium"|"high"|"critical",
                "score": float,
                "reasons": [],
                "details": {}
            }
        """
        score, reasons, details = self.calculate_risk_score(
            user, amount, transaction_type, phone
        )
        
        # Déterminer le niveau de risque
        if score < settings.RISK_LOW_THRESHOLD:
            risk_level = RiskLevel.LOW
            action = "auto"
            message = "✅ Transaction automatique - Risque faible"
        
        elif score < settings.RISK_MEDIUM_THRESHOLD:
            risk_level = RiskLevel.MEDIUM
            action = "verify"
            message = "🔐 Vérification OTP requise"
        
        elif score < settings.RISK_HIGH_THRESHOLD:
            risk_level = RiskLevel.HIGH
            action = "manual"
            message = "👤 Validation administrateur requise"
        
        else:
            risk_level = RiskLevel.CRITICAL
            action = "block"
            message = "🚫 Transaction bloquée - Risque critique"
        
        # Vérifications supplémentaires indépendantes du score
        
        # Vérifier les limites de montant
        if transaction_type == TransactionType.DEPOSIT:
            if amount > settings.DAILY_DEPOSIT_LIMIT:
                action = "manual"
                risk_level = RiskLevel.HIGH
                reasons.append("Dépasse la limite journalière de dépôt")
        
        elif transaction_type == TransactionType.WITHDRAW:
            if amount > settings.DAILY_WITHDRAW_LIMIT:
                action = "manual"
                risk_level = RiskLevel.HIGH
                reasons.append("Dépasse la limite journalière de retrait")
        
        return {
            "action": action,
            "risk_level": risk_level,
            "score": round(score, 3),
            "reasons": reasons,
            "details": details,
            "message": message
        }
    
    # ==========================================
    # VÉRIFICATIONS DE LIMITES
    # ==========================================
    
    def check_daily_limits(self, user_id: str, amount: float, trans_type: TransactionType) -> Dict:
        """Vérifie les limites journalières"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Volume du jour
        result = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.sender_id == user_id if trans_type == TransactionType.WITHDRAW 
            else Transaction.recipient_id == user_id,
            Transaction.type == trans_type,
            Transaction.status.in_([TransactionStatus.COMPLETED, TransactionStatus.PENDING]),
            Transaction.created_at >= today
        ).scalar()
        
        daily_used = float(result or 0)
        
        if trans_type == TransactionType.DEPOSIT:
            limit = settings.DAILY_DEPOSIT_LIMIT
        else:
            limit = settings.DAILY_WITHDRAW_LIMIT
        
        remaining = limit - daily_used
        
        return {
            "limit": limit,
            "used": daily_used,
            "remaining": remaining,
            "can_proceed": daily_used + amount <= limit,
            "exceeds": max(0, daily_used + amount - limit)
        }
    
    def check_monthly_limits(self, user_id: str, amount: float, trans_type: TransactionType) -> Dict:
        """Vérifie les limites mensuelles"""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.sender_id == user_id if trans_type == TransactionType.WITHDRAW 
            else Transaction.recipient_id == user_id,
            Transaction.type == trans_type,
            Transaction.status.in_([TransactionStatus.COMPLETED, TransactionStatus.PENDING]),
            Transaction.created_at >= month_start
        ).scalar()
        
        monthly_used = float(result or 0)
        
        if trans_type == TransactionType.DEPOSIT:
            limit = settings.MONTHLY_DEPOSIT_LIMIT
        else:
            limit = settings.MONTHLY_WITHDRAW_LIMIT
        
        return {
            "limit": limit,
            "used": monthly_used,
            "remaining": limit - monthly_used,
            "can_proceed": monthly_used + amount <= limit
        }
    
    def count_today_transactions(self, user_id: str) -> int:
        """Compte les transactions du jour"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= today
        ).count()