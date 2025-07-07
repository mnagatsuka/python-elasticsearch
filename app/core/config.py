import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "app"
    
    class Config:
        env_file = ".env"


settings = Settings()