from fastapi import APIRouter

from .health.router import router as health_router
from .metrics.router import router as metrics_router

router = APIRouter()

router.include_router(health_router, prefix="/health")
router.include_router(metrics_router, prefix="/metrics")
