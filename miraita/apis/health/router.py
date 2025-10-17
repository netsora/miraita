from fastapi import APIRouter

from miraita.apis.schemas import GenericResponse

router = APIRouter(tags=["Health"])


@router.get("/")
async def health_check() -> GenericResponse[dict[str, str]]:
    """Health check endpoint"""
    return GenericResponse(success=True, data={"status": "ok"})
