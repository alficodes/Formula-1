from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://f1:f1password@localhost:5432/f1pit?schema=public"
    fastf1_cache_dir: str = ".fastf1-cache"
    simulation_iterations: int = 500
    demo_mode: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
