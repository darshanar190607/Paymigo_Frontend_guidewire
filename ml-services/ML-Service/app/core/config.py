from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ML Service"
    model_dir: str = "app/models"
    data_dir: str = "app/data"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
