from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")
    JWT_SECRET_KEY: str = Field(default="polar-twin-secret-key-antigravity", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    MQTT_BROKER: str = Field(default="localhost", env="MQTT_BROKER")
    MQTT_PORT: int = Field(default=1883, env="MQTT_PORT")
    MQTT_USERNAME: str = Field(default="", env="MQTT_USERNAME")
    MQTT_PASSWORD: str = Field(default="", env="MQTT_PASSWORD")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Centralized alert threshold defaults
    ALERT_FUEL_CRITICAL_THRESHOLD: float = Field(
        default=20.0,
        env="ALERT_FUEL_CRITICAL_THRESHOLD",
        description="Fuel percentage below which a CRITICAL alert is triggered",
    )
    ALERT_FUEL_EMERGENCY_THRESHOLD: float = Field(
        default=10.0,
        env="ALERT_FUEL_EMERGENCY_THRESHOLD",
        description="Fuel percentage below which a high-priority CRITICAL emergency alert is triggered",
    )
    ALERT_TEMP_SAFE_MIN_THRESHOLD: float = Field(
        default=-50.0,
        env="ALERT_TEMP_SAFE_MIN_THRESHOLD",
        description="Temperature in °C below which a WARNING alert is triggered",
    )
    ALERT_WIND_MAX_THRESHOLD: float = Field(
        default=40.0,
        env="ALERT_WIND_MAX_THRESHOLD",
        description="Wind speed in m/s above which a CRITICAL blizzard alert is triggered",
    )
    ALERT_GENERATOR_LOAD_MAX_THRESHOLD: float = Field(
        default=95.0,
        env="ALERT_GENERATOR_LOAD_MAX_THRESHOLD",
        description="Generator load percentage above which a WARNING overload alert is triggered",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# singleton instance for easy import
settings = Settings()
