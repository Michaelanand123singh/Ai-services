"""
Main FastAPI application for Bloocube AI Service
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn
from contextlib import asynccontextmanager

from src.core.config import settings
import os
from src.core.logger import setup_logging, ai_logger
from src.core.exceptions import AIServiceException, get_http_status_from_error
from src.api import health, competitor, suggestions, matchmaking, trends, predictions, ai_providers

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        port_env = os.environ.get("PORT")
        ai_port_env = os.environ.get("AI_SERVICE_PORT")
        host_env = os.environ.get("AI_SERVICE_HOST")
        port_to_use = int(port_env or ai_port_env or settings.ai_service_port or 8080)
        host_to_use = host_env or settings.ai_service_host or "0.0.0.0"

        ai_logger.logger.info(
            "Starting Bloocube AI Service",
            version=settings.ai_service_version,
            host=host_to_use,
            port=port_to_use,
            env=os.environ.get("NODE_ENV", "production")
        )

        # Soft validation of optional envs (warn, do not crash)
        if not settings.backend_api_key:
            ai_logger.logger.warning("BACKEND_API_KEY not set; service-to-service auth may be limited")
        if not settings.openai_api_key and not settings.gemini_api_key:
            ai_logger.logger.warning("No primary LLM key configured (OPENAI_API_KEY/GEMINI_API_KEY); using fallbacks only")
        if not settings.chroma_persist_directory:
            ai_logger.logger.warning("CHROMA_PERSIST_DIRECTORY not set; using default in-memory/on-disk path")

        # Initialize services here if needed
        # await initialize_services()
    except Exception as e:
        ai_logger.log_error(e, {"stage": "startup"})
        # Don't block startup; allow probes to catch issues
    
    yield
    
    # Shutdown
    ai_logger.logger.info("Shutting down Bloocube AI Service")


# Create FastAPI application
app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered microservice for social media analysis, competitor research, content suggestions, and brand-creator matchmaking",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware with environment-configured origins
allowed_origins = [o.strip() for o in (settings.allowed_cors_origins or "").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)
# Add GZip compression to reduce payload sizes
app.add_middleware(GZipMiddleware, minimum_size=512)

# Add trusted host middleware with environment-configured hosts
allowed_hosts = [h.strip() for h in (settings.allowed_hosts or "").split(",") if h.strip()] or ["*"]
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses"""
    start_time = time.time()
    
    # Log request
    ai_logger.logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    ai_logger.logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


# Global exception handler
@app.exception_handler(AIServiceException)
async def ai_service_exception_handler(request: Request, exc: AIServiceException):
    """Handle AI service exceptions"""
    ai_logger.log_error(exc, {
        "url": str(request.url),
        "method": request.method,
        "error_code": exc.error_code
    })
    
    return JSONResponse(
        status_code=get_http_status_from_error(exc),
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    ai_logger.logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    ai_logger.log_error(exc, {
        "url": str(request.url),
        "method": request.method,
        "exception_type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(competitor.router)
app.include_router(suggestions.router)
app.include_router(matchmaking.router)
app.include_router(trends.router)
app.include_router(predictions.router)
app.include_router(ai_providers.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.ai_service_name,
        "version": settings.ai_service_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# Metrics endpoint (for Prometheus)
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # This would typically include actual metrics
    # For now, return basic service info
    return {
        "service_name": settings.ai_service_name,
        "version": settings.ai_service_version,
        "uptime": time.time()  # This should be actual uptime
    }


if __name__ == "__main__":
    # Prefer Cloud Run's PORT if present, then AI_SERVICE_PORT, then settings default (finally 8080)
    port_env = os.environ.get("PORT")
    ai_port_env = os.environ.get("AI_SERVICE_PORT")
    port_to_use = int(port_env or ai_port_env or settings.ai_service_port or 8080)
    host_to_use = os.environ.get("AI_SERVICE_HOST", settings.ai_service_host or "0.0.0.0")

    uvicorn.run(
        "src.main:app",
        host=host_to_use,
        port=port_to_use,
        reload=True,
        log_level=settings.log_level.lower()
    )
