import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Ticket Booking Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database & Redis Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ticket_db"
    )
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )

    # JWT Authentication Settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "super-secret-jwt-key-ticketsmith-2026-production-secure"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days

    # Seat Hold & TTL Settings
    HOLD_TTL_SECONDS: int = 600  # 10 minutes
    WAITLIST_OFFER_TTL_MINUTES: int = 15

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
