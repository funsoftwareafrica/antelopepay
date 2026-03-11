from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Import des routers (assurez-vous que les fichiers existent dans app/routers/)
from app.routers import auth, transfers, contacts, services, analytics
from app.routers.wallet import router as wallet_router
from app.routers.admin import router as admin_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend pour l'application AntelopePay"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers avec le préfixe API
app.include_router(auth.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")
app.include_router(contacts.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": f"Bienvenue sur {settings.APP_NAME} API", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}