from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    timestamp: float
    uptime: float
    version: str = "1.0.0"
