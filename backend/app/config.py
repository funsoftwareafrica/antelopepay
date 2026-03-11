from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # === Application ===
    APP_NAME: str = "AntelopePay"
    APP_VERSION: str = "1.0.0"
    API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # === Base de données ===
    DATABASE_URL: str = "sqlite:///./antelopepay.db"
    
    # === Sécurité ===
    SECRET_KEY: str = "changez_cette_cle_secrete_tres_longue"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # === Limites ===
    DAILY_DEPOSIT_LIMIT: float = 500000.0
    DAILY_WITHDRAW_LIMIT: float = 300000.0
    MONTHLY_DEPOSIT_LIMIT: float = 5000000.0
    MONTHLY_WITHDRAW_LIMIT: float = 3000000.0
    AUTO_APPROVE_DEPOSIT_LIMIT: float = 100000.0
    AUTO_APPROVE_WITHDRAW_LIMIT: float = 50000.0
    MAX_AUTO_TRANSACTIONS_PER_DAY: int = 10
    
    # === Frais ===
    TRANSFER_FEE_PERCENT: float = 0.015
    TRANSFER_FEE_MIN: float = 50.0
    TRANSFER_FEE_MAX: float = 2500.0
    WITHDRAW_FEE_PERCENT: float = 0.01 # Ajouté pour wallet.py
    WITHDRAW_FEE_MIN: float = 50.0
    WITHDRAW_FEE_MAX: float = 2500.0
    
    # === Détection de Fraude ===
    RISK_LOW_THRESHOLD: float = 0.3
    RISK_MEDIUM_THRESHOLD: float = 0.6
    RISK_HIGH_THRESHOLD: float = 0.8
    LARGE_AMOUNT_THRESHOLD: float = 200000.0
    VERY_LARGE_AMOUNT_THRESHOLD: float = 1000000.0
    MAX_TRANSACTIONS_PER_HOUR: int = 10
    MAX_TRANSACTIONS_PER_DAY: int = 50
    MAX_FAILED_ATTEMPTS: int = 3
    
    # === APIs Externes (Optionnel) ===
    ORANGE_CLIENT_ID: str = ""
    ORANGE_CLIENT_SECRET: str = ""
    ORANGE_MERCHANT_KEY: str = ""
    ORANGE_API_URL: str = ""
    
    MTN_SUBSCRIPTION_KEY: str = ""
    MTN_API_USER: str = ""
    MTN_API_KEY: str = ""
    MTN_API_URL: str = ""
    
    MOOV_API_KEY: str = ""
    MOOV_API_URL: str = ""
    
    TELECEL_API_KEY: str = ""
    TELECEL_API_URL: str = ""
    
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_SENDER_ID: str = ""
    
    # === Email ===
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@antelopepay.com"

    # Configuration Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False, # Permet de lire 'FRONTEND_URL' du .env et de l'assigner à 'FRONTEND_URL'
        extra="ignore"        # Ignore les variables du .env non listées ici
    )

settings = Settings()