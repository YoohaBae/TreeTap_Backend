"""
prefix: /apps
"""

from fastapi import APIRouter
from .auth import router as auth_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
