"""
AI Provider Management API endpoints
Allows super admin to manage AI service configurations
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import AIServiceException, ValidationError
from src.core.auth import verify_api_key
from src.models.multi_llm_client import MultiLLMClient

router = APIRouter(prefix="/ai/providers", tags=["ai-providers"])


class ProviderConfigRequest(BaseModel):
    """Request model for updating provider configuration"""
    provider: str = Field(..., description="AI provider name (openai, gemini)")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    model: Optional[str] = Field(None, description="Default model for the provider")
    enabled: bool = Field(True, description="Whether the provider is enabled")


class ProviderSwitchRequest(BaseModel):
    """Request model for switching primary provider"""
    provider: str = Field(..., description="New primary provider")
    model: Optional[str] = Field(None, description="Model to use with the provider")


class ProviderTestRequest(BaseModel):
    """Request model for testing provider"""
    provider: str = Field(..., description="Provider to test")
    model: Optional[str] = Field(None, description="Model to test")
    test_prompt: str = Field(default="Hello, this is a test.", description="Test prompt")


class ProviderStatusResponse(BaseModel):
    """Response model for provider status"""
    providers: Dict[str, Any]
    current_primary: str
    current_fallback: Optional[str]
    timestamp: float


class ProviderConfigResponse(BaseModel):
    """Response model for provider configuration"""
    provider: str
    status: str
    message: str
    configuration: Dict[str, Any]


# Dependency injection
def get_multi_llm_client() -> MultiLLMClient:
    """Get MultiLLMClient instance"""
    return MultiLLMClient()


@router.get("/status", response_model=ProviderStatusResponse)
async def get_providers_status(
    api_key: str = Depends(verify_api_key),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Get status of all AI providers
    
    Returns information about available providers, their status,
    and current configuration.
    """
    start_time = time.time()
    log_api_request("/ai/providers/status", "GET", "system")
    
    try:
        # Get provider status
        providers = await llm_client.get_available_providers()
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = ProviderStatusResponse(
            providers=providers,
            current_primary=llm_client.primary_provider,
            current_fallback=llm_client.fallback_provider,
            timestamp=time.time()
        )
        
        log_api_response("/ai/providers/status", "GET", 200, processing_time, "system")
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/status", "GET", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "get_providers_status"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch", response_model=ProviderConfigResponse)
async def switch_primary_provider(
    request: ProviderSwitchRequest,
    api_key: str = Depends(verify_api_key),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Switch the primary AI provider
    
    Allows super admin to change which AI provider is used as primary.
    Includes validation and testing of the new provider.
    """
    start_time = time.time()
    log_api_request("/ai/providers/switch", "POST", "system")
    
    try:
        # Validate provider
        if request.provider not in ["openai", "gemini"]:
            raise ValidationError("provider", request.provider, "Must be 'openai' or 'gemini'")
        
        # Switch provider
        switch_result = await llm_client.switch_primary_provider(
            provider=request.provider,
            model=request.model
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log the switch
        ai_logger.logger.info(
            "AI provider switched by admin",
            old_provider=switch_result["old_provider"],
            new_provider=switch_result["new_provider"],
            model=switch_result["model"]
        )
        
        response = ProviderConfigResponse(
            provider=request.provider,
            status="success",
            message=f"Successfully switched primary provider to {request.provider}",
            configuration=switch_result
        )
        
        log_api_response("/ai/providers/switch", "POST", 200, processing_time, "system")
        return response
        
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/switch", "POST", 400, processing_time, "system")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/switch", "POST", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "switch_primary_provider"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=Dict[str, Any])
async def test_provider(
    request: ProviderTestRequest,
    api_key: str = Depends(verify_api_key),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Test an AI provider
    
    Allows super admin to test connectivity and functionality
    of a specific AI provider before switching to it.
    """
    start_time = time.time()
    log_api_request("/ai/providers/test", "POST", "system")
    
    try:
        # Validate provider
        if request.provider not in ["openai", "gemini"]:
            raise ValidationError("provider", request.provider, "Must be 'openai' or 'gemini'")
        
        # Test the provider
        test_result = await llm_client.generate_text(
            prompt=request.test_prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=100
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = {
            "provider": request.provider,
            "model": test_result["model"],
            "status": "success",
            "test_prompt": request.test_prompt,
            "response": test_result["content"][:200] + "..." if len(test_result["content"]) > 200 else test_result["content"],
            "tokens_used": test_result["tokens_used"],
            "processing_time_ms": test_result["processing_time_ms"],
            "timestamp": time.time()
        }
        
        log_api_response("/ai/providers/test", "POST", 200, processing_time, "system")
        return response
        
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/test", "POST", 400, processing_time, "system")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/test", "POST", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "test_provider"})
        raise HTTPException(status_code=500, detail=f"Provider test failed: {str(e)}")


@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(
    provider: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Get available models for providers
    
    Returns information about available models for each provider
    or a specific provider if specified.
    """
    start_time = time.time()
    log_api_request("/ai/providers/models", "GET", "system")
    
    try:
        # Get model information
        model_info = await llm_client.get_model_info(provider=provider)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/providers/models", "GET", 200, processing_time, "system")
        return model_info
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/models", "GET", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "get_available_models"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def health_check_providers(
    api_key: str = Depends(verify_api_key),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Perform health check on all AI providers
    
    Tests connectivity and basic functionality of all configured providers.
    """
    start_time = time.time()
    log_api_request("/ai/providers/health", "GET", "system")
    
    try:
        # Perform health check
        health_status = await llm_client.health_check()
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/providers/health", "GET", 200, processing_time, "system")
        return health_status
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/health", "GET", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "health_check_providers"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage-stats", response_model=Dict[str, Any])
async def get_usage_statistics(
    api_key: str = Depends(verify_api_key)
):
    """
    Get usage statistics for AI providers
    
    Returns usage statistics, costs, and performance metrics
    for all configured AI providers.
    """
    start_time = time.time()
    log_api_request("/ai/providers/usage-stats", "GET", "system")
    
    try:
        # This would typically query a database or monitoring system
        # For now, return mock data structure
        usage_stats = {
            "timestamp": time.time(),
            "period": "last_30_days",
            "providers": {
                "openai": {
                    "requests": 1250,
                    "tokens_used": 125000,
                    "estimated_cost": 12.50,
                    "average_response_time": 850,
                    "success_rate": 99.2
                },
                "gemini": {
                    "requests": 750,
                    "tokens_used": 75000,
                    "estimated_cost": 0.0,  # Free tier
                    "average_response_time": 1200,
                    "success_rate": 97.8
                }
            },
            "total": {
                "requests": 2000,
                "tokens_used": 200000,
                "estimated_cost": 12.50,
                "average_response_time": 975
            }
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/providers/usage-stats", "GET", 200, processing_time, "system")
        return usage_stats
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/providers/usage-stats", "GET", 500, processing_time, "system")
        ai_logger.log_error(e, {"operation": "get_usage_statistics"})
        raise HTTPException(status_code=500, detail=str(e))
