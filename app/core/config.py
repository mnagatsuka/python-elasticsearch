import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "app"
    
    model_config = {"env_file": ".env"}


settings = Settings()