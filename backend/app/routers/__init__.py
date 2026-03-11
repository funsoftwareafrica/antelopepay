from app.routers.auth import router as auth_router
from app.routers.transfers import router as transfers_router
from app.routers.contacts import router as contacts_router
from app.routers.services import router as services_router
from app.routers.analytics import router as analytics_router

__all__ = [
    'auth_router',
    'transfers_router',
    'contacts_router',
    'services_router',
    'analytics_router'
]
