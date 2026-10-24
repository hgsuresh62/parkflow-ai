"""ParkFlow AI — Application Configuration"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "ParkFlow AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "parkflow-dev-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./parkflow.db"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    # IoT
    IOT_MODE: str = "simulation"  # simulation | thingspeak | mqtt | hybrid
    SIMULATION_INTERVAL_SECONDS: float = 5.0
    OCCUPANCY_THRESHOLD_CM: float = 50.0

    # ThingSpeak
    THINGSPEAK_CHANNEL_ID: str = ""
    THINGSPEAK_READ_API_KEY: str = ""
    THINGSPEAK_WRITE_API_KEY: str = ""
    THINGSPEAK_POLL_INTERVAL_SECONDS: int = 15
    THINGSPEAK_BASE_URL: str = "https://api.thingspeak.com"

    # MQTT
    MQTT_BROKER_HOST: str = ""
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_TLS_ENABLED: bool = False
    MQTT_TOPIC_PREFIX: str = "parkflow"

    @property
    def thingspeak_enabled(self) -> bool:
        return bool(self.THINGSPEAK_CHANNEL_ID and self.THINGSPEAK_READ_API_KEY)

    @property
    def mqtt_enabled(self) -> bool:
        return bool(self.MQTT_BROKER_HOST)

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL


settings = Settings()
