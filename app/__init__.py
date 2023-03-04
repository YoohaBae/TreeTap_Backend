"""
prefix: /apps
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .advertisement import router as advertisement_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(advertisement_router, prefix="/advertisement")
