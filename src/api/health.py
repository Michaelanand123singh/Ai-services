"""
Health check endpoint for Bloocube AI Service
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import time
import psutil
from src.core.config import settings
from src.core.logger import ai_logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns service status and basic information
    """
    try:
        return {
            "status": "healthy",
            "service": settings.ai_service_name,
            "version": settings.ai_service_version,
            "timestamp": time.time(),
            "uptime": time.time() - psutil.Process().create_time()
        }
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "health_check"})
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint
    Returns comprehensive service status including dependencies
    """
    try:
        # Get system information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check feature flags
        features = {
            "competitor_analysis": settings.enable_competitor_analysis,
            "content_suggestions": settings.enable_content_suggestions,
            "matchmaking": settings.enable_matchmaking,
            "trend_analysis": settings.enable_trend_analysis,
            "performance_prediction": settings.enable_performance_prediction
        }
        
        # Check AI model availability (basic check)
        ai_models = {
            "openai_available": bool(settings.openai_api_key),
            "embedding_model": settings.embedding_model,
            "llm_model": settings.openai_model
        }
        
        # Check database connections (basic check)
        databases = {
            "mongodb_configured": bool(settings.mongodb_url),
            "redis_configured": bool(settings.redis_url),
            "postgres_configured": bool(settings.postgres_url)
        }
        
        # Check vector database
        vector_db = {
            "pinecone_configured": bool(settings.pinecone_api_key),
            "faiss_configured": True,  # Local file-based
            "chroma_configured": True  # Local file-based
        }
        
        return {
            "status": "healthy",
            "service": settings.ai_service_name,
            "version": settings.ai_service_version,
            "timestamp": time.time(),
            "uptime": time.time() - psutil.Process().create_time(),
            "system": {
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "cpu_usage_percent": cpu_percent
            },
            "features": features,
            "ai_models": ai_models,
            "databases": databases,
            "vector_database": vector_db,
            "configuration": {
                "log_level": settings.log_level,
                "rate_limit_per_minute": settings.rate_limit_per_minute,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature
            }
        }
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "detailed_health_check"})
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    Verifies that the service is ready to accept requests
    """
    try:
        # Check if critical services are available
        checks = {
            "openai_api": bool(settings.openai_api_key),
            "mongodb": bool(settings.mongodb_url),
            "redis": bool(settings.redis_url),
            "vector_db": bool(settings.pinecone_api_key) or True  # FAISS/Chroma are local
        }
        
        all_ready = all(checks.values())
        
        return {
            "status": "ready" if all_ready else "not_ready",
            "checks": checks,
            "timestamp": time.time()
        }
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "readiness_check"})
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint
    Verifies that the service is alive and responding
    """
    return {
        "status": "alive",
        "timestamp": time.time()
    }
