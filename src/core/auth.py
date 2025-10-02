"""
Authentication module for stateless AI services
"""
from fastapi import HTTPException, Depends, Header
from typing import Optional
from src.core.config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key for service-to-service authentication
    
    Args:
        x_api_key: API key from request header
        
    Returns:
        str: Verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required. Include 'x-api-key' header."
        )
    
    # In stateless mode, we only validate against configured API key
    if settings.ai_service_api_key and x_api_key != settings.ai_service_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key


async def get_service_info(api_key: str = Depends(verify_api_key)) -> dict:
    """
    Get service information for authenticated requests
    
    Args:
        api_key: Verified API key
        
    Returns:
        dict: Service information
    """
    return {
        "service": "ai-service",
        "authenticated": True,
        "stateless_mode": True
    }


class APIKeyAuth:
    """Simple API key authentication for stateless services"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ai_service_api_key
    
    def verify(self, provided_key: str) -> bool:
        """Verify provided API key"""
        if not self.api_key:
            # If no API key is configured, allow all requests (development mode)
            return True
        
        return provided_key == self.api_key
    
    def get_auth_header(self) -> dict:
        """Get authentication header for outgoing requests"""
        if self.api_key:
            return {"x-api-key": self.api_key}
        return {}


# Global auth instance
api_auth = APIKeyAuth()
