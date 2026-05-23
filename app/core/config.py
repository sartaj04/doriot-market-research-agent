from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 60

    # Monitoring settings
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    HEALTH_CHECK_INTERVAL: int = 30
    # Application settings
    PROJECT_NAME: str = "Funding Research AI"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Database settings
    DATABASE_URL: Optional[str] = None
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    ENVIRONMENT: str # or "production"

    # Redis Configuration
    # For local development
    REDIS_LOCAL_HOST: str = "localhost"
    REDIS_LOCAL_PORT: int = 6379
    
    # For production (ElastiCache)
    REDIS_PRODUCTION_HOST: str 
    REDIS_PRODUCTION_PORT: int 
    REDIS_PRODUCTION_SSL: bool 

    # Rate Limiting
    DAILY_TOKEN_LIMIT: int = 100000
    TOTAL_TOKEN_LIMIT: int = 1000000

    # OpenAI/Azure settings
    OPENAI_TYPE: str = "azure"  # "azure" or "openai"
    OPENAI_API_KEY: Optional[str] = None  # For regular OpenAI

    # OpenAI settings
    AZURE_OPENAI_VERSION: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    AZURE_OPENAI_CHAT_DEPLOYMENT: str

    ENABLE_BACKUP_MODEL: bool = True  # Can be controlled via env
    AZURE_DEEPSEEK_KEY: str 
    AZURE_DEEPSEEK_ENDPOINT: str 
    AZURE_DEEPSEEK_API_VERSION: str 
    AZURE_DEEPSEEK_MODEL: str 

    CELERY_LOCAL_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_LOCAL_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Celery Production (ElastiCache)
    CELERY_PRODUCTION_BROKER_URL: Optional[str] = None
    CELERY_PRODUCTION_RESULT_BACKEND: Optional[str] = None

    ALLOWED_HOSTS: str = "*"
    ALLOWED_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_host(self) -> str:
        return self.REDIS_PRODUCTION_HOST if self.ENVIRONMENT == "production" else self.REDIS_LOCAL_HOST

    @property
    def redis_port(self) -> int:
        return self.REDIS_PRODUCTION_PORT if self.ENVIRONMENT == "production" else self.REDIS_LOCAL_PORT

    @property
    def redis_ssl(self) -> bool:
        return self.REDIS_PRODUCTION_SSL if self.ENVIRONMENT == "production" else False
    
    @property
    def celery_broker_url(self) -> str:
        if self.ENVIRONMENT == "production":
            if not self.CELERY_PRODUCTION_BROKER_URL:
                # Construct ElastiCache URL using Redis production settings
                return f"redis://{self.REDIS_PRODUCTION_HOST}:{self.REDIS_PRODUCTION_PORT}/1"
            return self.CELERY_PRODUCTION_BROKER_URL
        return self.CELERY_LOCAL_BROKER_URL
    
    @property
    def celery_result_backend(self) -> str:
        if self.ENVIRONMENT == "production":
            if not self.CELERY_PRODUCTION_RESULT_BACKEND:
                # Construct ElastiCache URL using Redis production settings
                return f"redis://{self.REDIS_PRODUCTION_HOST}:{self.REDIS_PRODUCTION_PORT}/2"
            return self.CELERY_PRODUCTION_RESULT_BACKEND
        return self.CELERY_LOCAL_RESULT_BACKEND
    @property
    def allowed_origins_list(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return self.ALLOWED_ORIGINS.split(",")

    @property
    def allowed_hosts_list(self) -> List[str]:
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return self.ALLOWED_HOSTS.split(",")
    

def get_settings() -> Settings:
    """Load settings from environment variables"""
    return Settings()

settings = get_settings()
