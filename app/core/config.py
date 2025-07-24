# app/core/config.py

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str
    DB_NAME: str
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Legacy Pinecone Configuration (for backward compatibility)
    PINECONE_API_KEY: str = ""
    
    # Qdrant Vector Database Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "candidate_embeddings"
    QDRANT_VECTOR_SIZE: int = 384  # Match current embedding size
    
    # Neo4j Graph Database Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Authentication Configuration
    SECRET_KEY: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    ALGORITHM: str = "HS256"
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env",
        extra = "allow"

settings = Settings()
