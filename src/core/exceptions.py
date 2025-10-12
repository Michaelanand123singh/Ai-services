"""
Custom exceptions for Bloocube AI Service
"""
from typing import Any, Dict, Optional


class AIServiceException(Exception):
    """Base exception for AI service errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "AI_SERVICE_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class AIProviderError(AIServiceException):
    """Raised when AI provider operation fails"""
    
    def __init__(self, message: str, provider: str = None):
        self.provider = provider
        super().__init__(
            message,
            "AI_PROVIDER_ERROR",
            {"provider": provider}
        )


class ModelNotAvailableError(AIServiceException):
    """Raised when AI model is not available"""
    
    def __init__(self, model_name: str, message: str = None):
        self.model_name = model_name
        super().__init__(
            message or f"AI model '{model_name}' is not available",
            "MODEL_NOT_AVAILABLE",
            {"model_name": model_name}
        )


class InsufficientDataError(AIServiceException):
    """Raised when there's insufficient data for analysis"""
    
    def __init__(self, required_data: str, available_data: str = None):
        self.required_data = required_data
        self.available_data = available_data
        super().__init__(
            f"Insufficient data for analysis. Required: {required_data}",
            "INSUFFICIENT_DATA",
            {
                "required_data": required_data,
                "available_data": available_data
            }
        )


class RateLimitExceededError(AIServiceException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, service: str, retry_after: int = None):
        self.service = service
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for {service}",
            "RATE_LIMIT_EXCEEDED",
            {
                "service": service,
                "retry_after": retry_after
            }
        )


class AuthenticationError(AIServiceException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_FAILED")


class PermissionDeniedError(AIServiceException):
    """Raised when permission is denied"""
    
    def __init__(self, resource: str, action: str = None):
        self.resource = resource
        self.action = action
        super().__init__(
            f"Permission denied for {action or 'access'} on {resource}",
            "PERMISSION_DENIED",
            {"resource": resource, "action": action}
        )


class ValidationError(AIServiceException):
    """Raised when input validation fails"""
    
    def __init__(self, field: str, value: Any, message: str = None):
        self.field = field
        self.value = value
        super().__init__(
            message or f"Validation failed for field '{field}'",
            "VALIDATION_ERROR",
            {"field": field, "value": str(value)}
        )


class ExternalServiceError(AIServiceException):
    """Raised when external service call fails"""
    
    def __init__(self, service: str, status_code: int = None, response: str = None):
        self.service = service
        self.status_code = status_code
        self.response = response
        super().__init__(
            f"External service '{service}' error",
            "EXTERNAL_SERVICE_ERROR",
            {
                "service": service,
                "status_code": status_code,
                "response": response
            }
        )


class VectorDatabaseError(AIServiceException):
    """Raised when vector database operation fails"""
    
    def __init__(self, operation: str, index_name: str = None, message: str = None):
        self.operation = operation
        self.index_name = index_name
        super().__init__(
            message or f"Vector database operation '{operation}' failed",
            "VECTOR_DATABASE_ERROR",
            {"operation": operation, "index_name": index_name}
        )


class EmbeddingError(AIServiceException):
    """Raised when text embedding fails"""
    
    def __init__(self, text: str, model: str = None, message: str = None):
        self.text = text[:100] + "..." if len(text) > 100 else text
        self.model = model
        super().__init__(
            message or f"Failed to generate embedding for text",
            "EMBEDDING_ERROR",
            {"text_preview": self.text, "model": model}
        )


class CompetitorAnalysisError(AIServiceException):
    """Raised when competitor analysis fails"""
    
    def __init__(self, competitor: str, platform: str = None, message: str = None):
        self.competitor = competitor
        self.platform = platform
        super().__init__(
            message or f"Failed to analyze competitor '{competitor}'",
            "COMPETITOR_ANALYSIS_ERROR",
            {"competitor": competitor, "platform": platform}
        )


class ContentSuggestionError(AIServiceException):
    """Raised when content suggestion generation fails"""
    
    def __init__(self, content_type: str, platform: str = None, message: str = None):
        self.content_type = content_type
        self.platform = platform
        super().__init__(
            message or f"Failed to generate suggestions for {content_type}",
            "CONTENT_SUGGESTION_ERROR",
            {"content_type": content_type, "platform": platform}
        )


class MatchmakingError(AIServiceException):
    """Raised when matchmaking analysis fails"""
    
    def __init__(self, brand_id: str, creator_id: str = None, message: str = None):
        self.brand_id = brand_id
        self.creator_id = creator_id
        super().__init__(
            message or f"Failed to perform matchmaking analysis",
            "MATCHMAKING_ERROR",
            {"brand_id": brand_id, "creator_id": creator_id}
        )


class TrendAnalysisError(AIServiceException):
    """Raised when trend analysis fails"""
    
    def __init__(self, platform: str = None, topic: str = None, message: str = None):
        self.platform = platform
        self.topic = topic
        super().__init__(
            message or f"Failed to analyze trends",
            "TREND_ANALYSIS_ERROR",
            {"platform": platform, "topic": topic}
        )


class PerformancePredictionError(AIServiceException):
    """Raised when performance prediction fails"""
    
    def __init__(self, content_id: str = None, message: str = None):
        self.content_id = content_id
        super().__init__(
            message or f"Failed to generate performance prediction",
            "PERFORMANCE_PREDICTION_ERROR",
            {"content_id": content_id}
        )


class CacheError(AIServiceException):
    """Raised when cache operation fails"""
    
    def __init__(self, operation: str, key: str = None, message: str = None):
        self.operation = operation
        self.key = key
        super().__init__(
            message or f"Cache operation '{operation}' failed",
            "CACHE_ERROR",
            {"operation": operation, "key": key}
        )


class DatabaseError(AIServiceException):
    """Raised when database operation fails"""
    
    def __init__(self, operation: str, collection: str = None, message: str = None):
        self.operation = operation
        self.collection = collection
        super().__init__(
            message or f"Database operation '{operation}' failed",
            "DATABASE_ERROR",
            {"operation": operation, "collection": collection}
        )


class ConfigurationError(AIServiceException):
    """Raised when configuration is invalid"""
    
    def __init__(self, setting: str, value: Any = None, message: str = None):
        self.setting = setting
        self.value = value
        super().__init__(
            message or f"Invalid configuration for '{setting}'",
            "CONFIGURATION_ERROR",
            {"setting": setting, "value": str(value) if value else None}
        )


class ServiceUnavailableError(AIServiceException):
    """Raised when service is temporarily unavailable"""
    
    def __init__(self, service: str, retry_after: int = None, message: str = None):
        self.service = service
        self.retry_after = retry_after
        super().__init__(
            message or f"Service '{service}' is temporarily unavailable",
            "SERVICE_UNAVAILABLE",
            {"service": service, "retry_after": retry_after}
        )


# Error code mappings for HTTP status codes
ERROR_CODE_TO_HTTP_STATUS = {
    "INVALID_INPUT": 400,
    "VALIDATION_ERROR": 400,
    "AUTHENTICATION_FAILED": 401,
    "PERMISSION_DENIED": 403,
    "INSUFFICIENT_DATA": 422,
    "RATE_LIMIT_EXCEEDED": 429,
    "MODEL_NOT_AVAILABLE": 503,
    "AI_PROVIDER_ERROR": 502,
    "EXTERNAL_SERVICE_ERROR": 502,
    "SERVICE_UNAVAILABLE": 503,
    "AI_SERVICE_ERROR": 500,
    "VECTOR_DATABASE_ERROR": 500,
    "EMBEDDING_ERROR": 500,
    "COMPETITOR_ANALYSIS_ERROR": 500,
    "CONTENT_SUGGESTION_ERROR": 500,
    "MATCHMAKING_ERROR": 500,
    "TREND_ANALYSIS_ERROR": 500,
    "PERFORMANCE_PREDICTION_ERROR": 500,
    "CACHE_ERROR": 500,
    "DATABASE_ERROR": 500,
    "CONFIGURATION_ERROR": 500
}


def get_http_status_from_error(error: AIServiceException) -> int:
    """Get HTTP status code from AI service exception"""
    return ERROR_CODE_TO_HTTP_STATUS.get(error.error_code, 500)
