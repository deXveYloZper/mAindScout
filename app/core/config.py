# app/code/config.py

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    MONGODB_CONNECTION_STRING: str
    PINECONE_API_KEY: str
    OPENAI_API_KEY: str
    DB_NAME: str

    class Config:
        env_file = ".env",
        extra = "allow"

settings = Settings()
