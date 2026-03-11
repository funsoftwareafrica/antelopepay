"""
Service de notifications (SMS, Email, Push)
"""
import httpx
from typing import Optional
from datetime import datetime

from app.config import settings


class NotificationService:
    """Service de notifications multi-canal"""
    
    # ==========================================
    # SMS via Africa's Talking
    # ==========================================
    
    @staticmethod
    async def send_sms(phone: str, message: str) -> bool:
        """
        Envoie un SMS via Africa's Talking
        
        Args:
            phone: Numéro au format international (ex: +22507000000)
            message: Message (max 160 caractères pour SMS standard)
        """
        if not settings.AFRICASTALKING_API_KEY:
            print(f"[SMS MOCK] To: {phone}, Message: {message}")
            return True
        
        url = "https://api.africastalking.com/version1/messaging"
        
        # Formater le numéro
        phone = phone.replace("+", "")
        
        payload = {
            "username": settings.AFRICASTALKING_USERNAME,
            "to": phone,
            "message": message,
            "from": settings.AFRICASTALKING_SENDER_ID
        }
        
        headers = {
            "apiKey": settings.AFRICASTALKING_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, data=payload, headers=headers)
                return response.status_code == 201
        except Exception as e:
            print(f"Erreur SMS: {e}")
            return False
    
    # ==========================================
    # NOTIFICATIONS PRÉDÉFINIES
    # ==========================================
    
    @staticmethod
    async def send_deposit_success(phone: str, amount: float, reference: str, new_balance: float):
        """Notification de dépôt réussi"""
        message = f"""
AntelopePay
✅ Dépôt réussi!
Montant: {amount:,.0f} XOF
Réf: {reference}
Nouveau solde: {new_balance:,.0f} XOF
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_withdraw_success(phone: str, amount: float, fee: float, reference: str):
        """Notification de retrait réussi"""
        message = f"""
AntelopePay
✅ Retrait réussi!
Montant: {amount:,.0f} XOF
Frais: {fee:,.0f} XOF
Réf: {reference}
Argent envoyé sur votre Mobile Money.
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_transaction_pending(phone: str, trans_type: str, amount: float, reference: str):
        """Notification de transaction en attente"""
        message = f"""
AntelopePay
⏳ {trans_type.title()} en attente
Montant: {amount:,.0f} XOF
Réf: {reference}
Validation en cours (24h max).
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_withdraw_otp(phone: str, otp: str, amount: float):
        """Envoie le code OTP pour retrait"""
        message = f"""
AntelopePay
🔐 Votre code de confirmation:
{otp}
Montant: {amount:,.0f} XOF
Valable 5 minutes.
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_transaction_blocked(phone: str, amount: float, reason: str):
        """Notification de transaction bloquée"""
        message = f"""
AntelopePay
🚫 Transaction bloquée
Montant: {amount:,.0f} XOF
Raison: {reason}
Contactez le support si nécessaire.
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_transfer_received(phone: str, amount: float, sender: str):
        """Notification de transfert reçu"""
        message = f"""
AntelopePay
💰 Vous avez reçu {amount:,.0f} XOF
De: {sender}
        """.strip()
        
        return await NotificationService.send_sms(phone, message)
    
    @staticmethod
    async def send_verification_code(phone: str, code: str):
        """Envoie le code de vérification"""
        message = f"""
AntelopePay
Votre code de vérification: {code}
Valable 5 minutes.
        """.strip()
        
        return await NotificationService.send_sms(phone, message)


# Instance globale
notification_service = NotificationService()