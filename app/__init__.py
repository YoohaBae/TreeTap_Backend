"""
prefix: /apps
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .contact import router as contact_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(contact_router, prefix="/contact")
