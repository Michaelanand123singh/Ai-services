"""
Logging configuration for Bloocube AI Service
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict
import structlog
from loguru import logger
from src.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application"""
    
    # Remove default loguru handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure log format based on settings
    if settings.log_format == "json":
        log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
    else:
        log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler
    logger.add(
        settings.log_file,
        format=log_format,
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get a logger instance for the given name"""
    return logger.bind(name=name)


class AIServiceLogger:
    """Custom logger for AI service operations"""
    
    def __init__(self, service_name: str = "ai-service"):
        self.service_name = service_name
        self.logger = get_logger(service_name)
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                    duration_ms: int, user_id: str = None, **kwargs):
        """Log API call details"""
        self.logger.info(
            "API call completed",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            **kwargs
        )
    
    def log_ai_operation(self, operation: str, model: str, tokens_used: int,
                        duration_ms: int, success: bool, **kwargs):
        """Log AI operation details"""
        level = "info" if success else "error"
        getattr(self.logger, level)(
            f"AI operation {operation}",
            operation=operation,
            model=model,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
    
    def log_competitor_analysis(self, user_id: str, competitors_count: int,
                               analysis_type: str, duration_ms: int, **kwargs):
        """Log competitor analysis operation"""
        self.logger.info(
            "Competitor analysis completed",
            user_id=user_id,
            competitors_count=competitors_count,
            analysis_type=analysis_type,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_content_suggestion(self, user_id: str, content_type: str,
                              suggestions_count: int, platform: str, **kwargs):
        """Log content suggestion generation"""
        self.logger.info(
            "Content suggestions generated",
            user_id=user_id,
            content_type=content_type,
            suggestions_count=suggestions_count,
            platform=platform,
            **kwargs
        )
    
    def log_matchmaking(self, brand_id: str, creator_id: str, 
                       compatibility_score: float, **kwargs):
        """Log matchmaking analysis"""
        self.logger.info(
            "Matchmaking analysis completed",
            brand_id=brand_id,
            creator_id=creator_id,
            compatibility_score=compatibility_score,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        self.logger.error(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )
    
    def log_performance(self, operation: str, duration_ms: int, 
                       memory_usage_mb: float = None, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            f"Performance metric: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            **kwargs
        )


# Global logger instance
ai_logger = AIServiceLogger()


# Convenience functions for common logging patterns
def log_api_request(endpoint: str, method: str, user_id: str = None):
    """Log API request start"""
    ai_logger.logger.info(
        "API request started",
        endpoint=endpoint,
        method=method,
        user_id=user_id
    )


def log_api_response(endpoint: str, method: str, status_code: int, 
                    duration_ms: int, user_id: str = None):
    """Log API response"""
    ai_logger.log_api_call(endpoint, method, status_code, duration_ms, user_id)


def log_ai_model_call(model: str, operation: str, tokens_used: int = None, **kwargs):
    """Log AI model call (accepts extra context like provider via kwargs)"""
    ai_logger.log_ai_operation(
        operation=operation,
        model=model,
        tokens_used=tokens_used or 0,
        duration_ms=0,  # Will be updated by caller
        success=True,
        **kwargs
    )


def log_data_processing(operation: str, records_processed: int, 
                       duration_ms: int, **kwargs):
    """Log data processing operations"""
    ai_logger.logger.info(
        f"Data processing: {operation}",
        operation=operation,
        records_processed=records_processed,
        duration_ms=duration_ms,
        **kwargs
    )


def log_vector_operation(operation: str, vector_count: int, 
                        index_name: str = None, **kwargs):
    """Log vector database operations"""
    ai_logger.logger.info(
        f"Vector operation: {operation}",
        operation=operation,
        vector_count=vector_count,
        index_name=index_name,
        **kwargs
    )


def log_cache_operation(operation: str, key: str, hit: bool = None, **kwargs):
    """Log cache operations"""
    ai_logger.logger.info(
        f"Cache operation: {operation}",
        operation=operation,
        key=key,
        hit=hit,
        **kwargs
    )


def log_ai_operation(operation: str, model: str, tokens_used: int = 0,
                    duration_ms: int = 0, success: bool = True, **kwargs):
    """Log AI operation details"""
    ai_logger.log_ai_operation(
        operation=operation,
        model=model,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )
