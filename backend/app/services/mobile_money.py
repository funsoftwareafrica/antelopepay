"""
Intégration des APIs Mobile Money
Support: Orange Money, MTN Mobile Money
"""
import httpx
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional
from abc import ABC, abstractmethod

from app.config import settings


class BaseMobileMoneyAPI(ABC):
    """Classe de base pour les APIs Mobile Money"""
    
    @abstractmethod
    async def request_payment(self, amount: float, phone: str, reference: str) -> Dict:
        """Demande un paiement (dépôt)"""
        pass
    
    @abstractmethod
    async def check_status(self, reference: str) -> Dict:
        """Vérifie le statut d'une transaction"""
        pass
    
    @abstractmethod
    async def transfer(self, amount: float, phone: str, reference: str) -> Dict:
        """Effectue un transfert (retrait)"""
        pass


class OrangeMoneyAPI(BaseMobileMoneyAPI):
    """
    API Orange Money
    
    Documentation: https://developer.orange.com
    """
    
    def __init__(self):
        self.client_id = settings.ORANGE_CLIENT_ID
        self.client_secret = settings.ORANGE_CLIENT_SECRET
        self.merchant_key = settings.ORANGE_MERCHANT_KEY
        self.base_url = settings.ORANGE_API_URL
        self._token = None
        self._token_expires = None
    
    async def _get_token(self) -> str:
        """Obtient un token OAuth2"""
        
        # Vérifier si le token est encore valide
        if self._token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._token
        
        # Encoder les credentials
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    headers={
                        "Authorization": f"Basic {credentials}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={"grant_type": "client_credentials"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._token = data.get("access_token")
                    # Token expire dans 3600 secondes (1h)
                    self._token_expires = datetime.utcnow() + timedelta(seconds=3500)
                    return self._token
                else:
                    raise Exception(f"Auth Orange échouée: {response.text}")
                    
            except Exception as e:
                raise Exception(f"Erreur connexion Orange: {str(e)}")
    
    async def request_payment(self, amount: float, phone: str, reference: str) -> Dict:
        """
        Initie une demande de paiement
        Le client reçoit une notification USSD pour confirmer
        
        Returns:
            {
                "success": bool,
                "pay_token": str,  # Token à utiliser pour vérifier le statut
                "message": str
            }
        """
        token = await self._get_token()
        
        payload = {
            "merchant_key": self.merchant_key,
            "amount": str(int(amount)),
            "currency": "XOF",
            "order_id": reference,
            "return_url": f"{settings.FRONTEND_URL}/deposit/success",
            "cancel_url": f"{settings.FRONTEND_URL}/deposit/cancel",
            "notif_url": f"{settings.API_URL}/webhook/orange/deposit",
            "lang": "fr"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/webpayment",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        "success": True,
                        "pay_token": data.get("pay_token"),
                        "order_id": reference,
                        "message": "Demande de paiement envoyée. Confirmez sur votre téléphone."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur Orange: {response.text}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Erreur: {str(e)}"
                }
    
    async def check_status(self, reference: str) -> Dict:
        """
        Vérifie le statut d'une transaction
        
        Returns:
            {
                "status": "PENDING"|"SUCCESS"|"FAILED"|"CANCELLED",
                "transaction_id": str,
                "amount": float
            }
        """
        token = await self._get_token()
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/order/{reference}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Mapper les statuts Orange vers nos statuts
                    status_map = {
                        "INITIATED": "PENDING",
                        "PENDING": "PENDING",
                        "SUCCESS": "SUCCESS",
                        "FAILED": "FAILED",
                        "CANCELLED": "CANCELLED",
                        "EXPIRED": "FAILED"
                    }
                    
                    return {
                        "status": status_map.get(data.get("status"), "PENDING"),
                        "transaction_id": data.get("txnid"),
                        "amount": float(data.get("amount", 0)),
                        "raw": data
                    }
                else:
                    return {"status": "PENDING", "message": "En attente"}
                    
            except Exception as e:
                return {"status": "PENDING", "error": str(e)}
    
    async def transfer(self, amount: float, phone: str, reference: str) -> Dict:
        """
        Effectue un transfert vers un compte Orange Money (retrait)
        Nécessite un compte marchand préfinancé
        
        Returns:
            {
                "success": bool,
                "transaction_id": str,
                "message": str
            }
        """
        token = await self._get_token()
        
        # Nettoyer le numéro
        phone = phone.replace("+", "").replace(" ", "")
        
        payload = {
            "merchant_key": self.merchant_key,
            "amount": str(int(amount)),
            "currency": "XOF",
            "order_id": reference,
            "recipient_phone": phone,
            "notif_url": f"{settings.API_URL}/webhook/orange/withdraw"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/disbursement",  # Endpoint pour les transferts sortants
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "transaction_id": data.get("txnid"),
                        "reference": reference,
                        "message": "Transfert initié"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur transfert Orange: {response.text}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }


class MTNMoMoAPI(BaseMobileMoneyAPI):
    """
    API MTN Mobile Money
    
    Documentation: https://momodeveloper.mtn.com
    """
    
    def __init__(self):
        self.subscription_key = settings.MTN_SUBSCRIPTION_KEY
        self.api_user = settings.MTN_API_USER
        self.api_key = settings.MTN_API_KEY
        self.base_url = settings.MTN_API_URL
        self._token = None
        self._token_expires = None
    
    async def _get_token(self) -> str:
        """Obtient un token d'accès"""
        
        if self._token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._token
        
        # Encoder la clé API
        credentials = base64.b64encode(
            f"{self.api_user}:{self.api_key}".encode()
        ).decode()
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/collection/token/",
                    headers={
                        "Ocp-Apim-Subscription-Key": self.subscription_key,
                        "Authorization": f"Basic {credentials}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._token = data.get("access_token")
                    self._token_expires = datetime.utcnow() + timedelta(seconds=3500)
                    return self._token
                else:
                    raise Exception(f"Auth MTN échouée: {response.text}")
                    
            except Exception as e:
                raise Exception(f"Erreur connexion MTN: {str(e)}")
    
    async def request_payment(self, amount: float, phone: str, reference: str) -> Dict:
        """
        Demande au client de payer (Request to Pay)
        Notification USSD envoyée au téléphone
        
        Returns:
            {
                "success": bool,
                "reference": str,
                "message": str
            }
        """
        token = await self._get_token()
        
        # Formater le numéro
        phone = phone.replace("+", "").replace(" ", "")
        
        payload = {
            "amount": str(int(amount)),
            "currency": "XOF",
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": f"Depot AntelopePay - {reference}",
            "payeeNote": "Depot AntelopePay"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/collection/v1_0/requesttopay",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Reference-Id": reference,
                        "X-Target-Environment": "mtnci",  # MTN Côte d'Ivoire
                        "Ocp-Apim-Subscription-Key": self.subscription_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                # 202 Accepted = demande envoyée avec succès
                if response.status_code == 202:
                    return {
                        "success": True,
                        "reference": reference,
                        "message": "Demande envoyée. Confirmez sur votre téléphone MTN."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur MTN: {response.text}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }
    
    async def check_status(self, reference: str) -> Dict:
        """
        Vérifie le statut d'une transaction MTN
        
        Returns:
            {
                "status": "PENDING"|"SUCCESS"|"FAILED"|"CANCELLED",
                "transaction_id": str,
                "amount": float
            }
        """
        token = await self._get_token()
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/collection/v1_0/requesttopay/{reference}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Target-Environment": "mtnci",
                        "Ocp-Apim-Subscription-Key": self.subscription_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Mapper les statuts MTN
                    status_map = {
                        "PENDING": "PENDING",
                        "SUCCESSFUL": "SUCCESS",
                        "FAILED": "FAILED",
                        "CANCELLED": "CANCELLED",
                        "TIMEOUT": "FAILED",
                        "REJECTED": "FAILED"
                    }
                    
                    return {
                        "status": status_map.get(data.get("status"), "PENDING"),
                        "transaction_id": data.get("financialTransactionId"),
                        "amount": float(data.get("amount", 0)),
                        "raw": data
                    }
                else:
                    return {"status": "PENDING"}
                    
            except Exception as e:
                return {"status": "PENDING", "error": str(e)}
    
    async def transfer(self, amount: float, phone: str, reference: str) -> Dict:
        """
        Effectue un transfert vers un compte MTN (retrait)
        
        Returns:
            {
                "success": bool,
                "transaction_id": str,
                "message": str
            }
        """
        token = await self._get_token()
        
        phone = phone.replace("+", "").replace(" ", "")
        
        payload = {
            "amount": str(int(amount)),
            "currency": "XOF",
            "externalId": reference,
            "payee": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": f"Retrait AntelopePay - {reference}",
            "payeeNote": "Retrait AntelopePay"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/disbursement/v1_0/transfer",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Reference-Id": reference,
                        "X-Target-Environment": "mtnci",
                        "Ocp-Apim-Subscription-Key": self.subscription_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 202:
                    return {
                        "success": True,
                        "reference": reference,
                        "message": "Transfert initié"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erreur transfert MTN: {response.text}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }


class MobileMoneyService:
    """
    Service unifié pour tous les opérateurs Mobile Money
    """
    
    def __init__(self):
        self._orange = None
        self._mtn = None
    
    @property
    def orange(self) -> OrangeMoneyAPI:
        if self._orange is None:
            self._orange = OrangeMoneyAPI()
        return self._orange
    
    @property
    def mtn(self) -> MTNMoMoAPI:
        if self._mtn is None:
            self._mtn = MTNMoMoAPI()
        return self._mtn
    
    def get_api(self, operator: str) -> Optional[BaseMobileMoneyAPI]:
        """Retourne l'API pour un opérateur donné"""
        if operator == "orange_money":
            return self.orange
        elif operator == "mtn_money":
            return self.mtn
        return None
    
    async def request_deposit(
        self, 
        operator: str, 
        amount: float, 
        phone: str, 
        reference: str
    ) -> Dict:
        """Initie une demande de dépôt"""
        api = self.get_api(operator)
        
        if api is None:
            return {
                "success": False,
                "message": f"Opérateur {operator} non supporté pour les dépôts automatiques"
            }
        
        return await api.request_payment(amount, phone, reference)
    
    async def check_deposit_status(self, operator: str, reference: str) -> Dict:
        """Vérifie le statut d'un dépôt"""
        api = self.get_api(operator)
        
        if api is None:
            return {"status": "UNKNOWN"}
        
        return await api.check_status(reference)
    
    async def process_withdrawal(
        self, 
        operator: str, 
        amount: float, 
        phone: str, 
        reference: str
    ) -> Dict:
        """Effectue un retrait"""
        api = self.get_api(operator)
        
        if api is None:
            return {
                "success": False,
                "message": f"Opérateur {operator} non supporté pour les retraits automatiques"
            }
        
        return await api.transfer(amount, phone, reference)


# Instance globale
mm_service = MobileMoneyService()