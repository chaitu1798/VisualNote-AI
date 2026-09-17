from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system status: healthy, degraded, or unhealthy")
    api: str = Field("healthy", description="FastAPI core status")
    database: str = Field(..., description="PostgreSQL status: healthy or unavailable")
    redis: str = Field(..., description="Redis status: healthy or unavailable")
    version: str = Field("0.1.0", description="API version")
    environment: str = Field("development", description="Current environment")
