"""
Core configuration module for Bloocube AI Service
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    ai_service_name: str = Field(default="bloocube-ai-service", env="AI_SERVICE_NAME")
    ai_service_version: str = Field(default="1.0.0", env="AI_SERVICE_VERSION")
    ai_service_port: int = Field(default=8001, env="AI_SERVICE_PORT")
    ai_service_host: str = Field(default="0.0.0.0", env="AI_SERVICE_HOST")
    
    # Database Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017/bloocube", env="MONGODB_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    postgres_url: str = Field(default="postgresql://user:password@localhost:5432/bloocube", env="POSTGRES_URL")
    
    # AI Model Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    
    # Vector Database Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="bloocube-embeddings", env="PINECONE_INDEX_NAME")
    
    # Alternative Vector DB
    faiss_index_path: str = Field(default="./data/faiss_index", env="FAISS_INDEX_PATH")
    chroma_persist_directory: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Social Media API Keys
    twitter_api_key: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = Field(default=None, env="TWITTER_API_SECRET")
    twitter_access_token: Optional[str] = Field(default=None, env="TWITTER_ACCESS_TOKEN")
    twitter_access_secret: Optional[str] = Field(default=None, env="TWITTER_ACCESS_SECRET")
    
    instagram_username: Optional[str] = Field(default=None, env="INSTAGRAM_USERNAME")
    instagram_password: Optional[str] = Field(default=None, env="INSTAGRAM_PASSWORD")
    
    youtube_api_key: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")
    facebook_app_id: Optional[str] = Field(default=None, env="FACEBOOK_APP_ID")
    facebook_app_secret: Optional[str] = Field(default=None, env="FACEBOOK_APP_SECRET")
    linkedin_client_id: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_SECRET")
    
    # Backend Service Configuration
    backend_service_url: str = Field(default="http://localhost:3000", env="BACKEND_SERVICE_URL")
    backend_api_key: Optional[str] = Field(default=None, env="BACKEND_API_KEY")
    
    # Security Configuration
    jwt_secret: str = Field(env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, env="JWT_EXPIRE_MINUTES")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=200, env="RATE_LIMIT_BURST")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="./logs/ai-service.log", env="LOG_FILE")
    
    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Feature Flags
    enable_competitor_analysis: bool = Field(default=True, env="ENABLE_COMPETITOR_ANALYSIS")
    enable_content_suggestions: bool = Field(default=True, env="ENABLE_CONTENT_SUGGESTIONS")
    enable_matchmaking: bool = Field(default=True, env="ENABLE_MATCHMAKING")
    enable_trend_analysis: bool = Field(default=True, env="ENABLE_TREND_ANALYSIS")
    enable_performance_prediction: bool = Field(default=True, env="ENABLE_PERFORMANCE_PREDICTION")
    
    # Model Configuration
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    top_p: float = Field(default=0.9, env="TOP_P")
    frequency_penalty: float = Field(default=0.0, env="FREQUENCY_PENALTY")
    presence_penalty: float = Field(default=0.0, env="PRESENCE_PENALTY")
    
    # Data Processing
    max_content_length: int = Field(default=10000, env="MAX_CONTENT_LENGTH")
    batch_size: int = Field(default=32, env="BATCH_SIZE")
    embedding_batch_size: int = Field(default=100, env="EMBEDDING_BATCH_SIZE")
    vector_dimension: int = Field(default=1536, env="VECTOR_DIMENSION")
    
    # Cache Configuration
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Background Tasks
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Platform configurations
PLATFORMS = {
    "instagram": {
        "name": "Instagram",
        "api_required": True,
        "rate_limit": 200,
        "content_types": ["post", "story", "reel", "carousel", "live"]
    },
    "youtube": {
        "name": "YouTube",
        "api_required": True,
        "rate_limit": 100,
        "content_types": ["video", "short", "live", "community"]
    },
    "twitter": {
        "name": "Twitter/X",
        "api_required": True,
        "rate_limit": 300,
        "content_types": ["tweet", "thread", "space"]
    },
    "linkedin": {
        "name": "LinkedIn",
        "api_required": True,
        "rate_limit": 100,
        "content_types": ["post", "article", "video", "poll"]
    },
    "facebook": {
        "name": "Facebook",
        "api_required": True,
        "rate_limit": 200,
        "content_types": ["post", "story", "video", "live", "poll"]
    }
}

# Content type configurations
CONTENT_TYPES = {
    "post": {"max_length": 2200, "hashtag_limit": 30},
    "story": {"max_length": 100, "hashtag_limit": 10},
    "reel": {"max_length": 2200, "hashtag_limit": 30},
    "video": {"max_length": 5000, "hashtag_limit": 15},
    "live": {"max_length": 1000, "hashtag_limit": 20},
    "carousel": {"max_length": 2200, "hashtag_limit": 30},
    "tweet": {"max_length": 280, "hashtag_limit": 10},
    "thread": {"max_length": 280, "hashtag_limit": 10},
    "article": {"max_length": 3000, "hashtag_limit": 5}
}

# AI Model configurations
AI_MODELS = {
    "gpt-4-turbo-preview": {
        "max_tokens": 4000,
        "cost_per_1k_tokens": 0.01,
        "supports_functions": True
    },
    "gpt-3.5-turbo": {
        "max_tokens": 4000,
        "cost_per_1k_tokens": 0.002,
        "supports_functions": True
    },
    "text-embedding-3-large": {
        "dimensions": 3072,
        "cost_per_1k_tokens": 0.00013
    },
    "text-embedding-3-small": {
        "dimensions": 1536,
        "cost_per_1k_tokens": 0.00002
    }
}

# Error codes and messages
ERROR_CODES = {
    "INVALID_INPUT": "Invalid input data provided",
    "AI_SERVICE_ERROR": "AI service encountered an error",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "MODEL_NOT_AVAILABLE": "AI model not available",
    "INSUFFICIENT_DATA": "Insufficient data for analysis",
    "AUTHENTICATION_FAILED": "Authentication failed",
    "PERMISSION_DENIED": "Permission denied",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable"
}

# Success messages
SUCCESS_MESSAGES = {
    "ANALYSIS_COMPLETED": "Analysis completed successfully",
    "SUGGESTIONS_GENERATED": "Suggestions generated successfully",
    "MATCHMAKING_COMPLETED": "Matchmaking analysis completed",
    "TRENDS_ANALYZED": "Trend analysis completed",
    "PREDICTION_GENERATED": "Performance prediction generated"
}
