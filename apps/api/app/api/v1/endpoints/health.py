from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Probe",
    description="Reports the diagnostic health status of the API, PostgreSQL database, and Redis cache.",
)
def get_health() -> HealthResponse:
    db_ok = check_db_connection()
    redis_ok = check_redis_connection()

    db_status = "healthy" if db_ok else "unavailable"
    redis_status = "healthy" if redis_ok else "unavailable"

    if db_ok and redis_ok:
        overall_status = "healthy"
    elif db_ok or redis_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        api="healthy",
        database=db_status,
        redis=redis_status,
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )
