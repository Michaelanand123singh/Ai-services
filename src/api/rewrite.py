"""
AI-powered content rewrite API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException,
    ContentSuggestionError,
    ValidationError,
    InsufficientDataError
)
from src.services.rag_service import RAGService
from src.services.nlp_utils import NLPService

router = APIRouter(prefix="/ai/rewrite", tags=["rewrite"])

# Valid platforms and content types
VALID_PLATFORMS = {
    "twitter", "instagram", "linkedin", "facebook", "youtube"
}

VALID_FIELDS = {
    "title", "description", "caption", "content", "text", "body"
}

PLATFORM_CHAR_LIMITS: Dict[str, int] = {
    "twitter": 280,
    "instagram": 2200,
    "linkedin": 3000,
    "facebook": 63000,
    "youtube": 5000,
}

def normalize_platform(name: str) -> str:
    v = (name or "").strip().lower()
    aliases = {"x": "twitter"}
    return aliases.get(v, v)

def normalize_field(field: str) -> str:
    v = (field or "").strip().lower()
    aliases = {"text": "content", "body": "content"}
    return aliases.get(v, v)

def infer_platform_limit(platform: str, field: str) -> int:
    """Infer character limit based on platform and field"""
    platform = normalize_platform(platform)
    field = normalize_field(field)
    
    # Platform-specific limits
    base_limit = PLATFORM_CHAR_LIMITS.get(platform, 2000)
    
    # Field-specific adjustments
    if field in ["title", "caption"]:
        if platform == "twitter":
            return min(base_limit, 100)  # Twitter titles/captions should be shorter
        elif platform == "instagram":
            return min(base_limit, 150)  # Instagram captions
        else:
            return min(base_limit, 200)
    
    return base_limit

# Pydantic models
class ContentRewriteRequest(BaseModel):
    field: str = Field(..., description="Field type to rewrite (title, description, caption, etc.)")
    current_content: str = Field(..., description="Current content to be rewritten")
    platform: str = Field(..., description="Target platform (twitter, instagram, linkedin, facebook, youtube)")
    content_type: Optional[str] = Field("post", description="Type of content (post, tweet, reel, etc.)")
    tone: Optional[str] = Field("professional", description="Desired tone (professional, casual, friendly, etc.)")
    goals: Optional[List[str]] = Field(default_factory=list, description="Content goals (engagement, conversion, etc.)")
    max_length: Optional[int] = Field(None, description="Maximum character length")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    campaign_id: Optional[str] = Field(None, description="Campaign ID for context")

class ContentRewriteResponse(BaseModel):
    success: bool = Field(True, description="Whether the rewrite was successful")
    rewritten_content: str = Field(..., description="The rewritten content")
    original_content: str = Field(..., description="Original content")
    field: str = Field(..., description="Field that was rewritten")
    platform: str = Field(..., description="Target platform")
    character_count: int = Field(..., description="Character count of rewritten content")
    suggestions: List[str] = Field(default_factory=list, description="Additional suggestions")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    confidence_score: float = Field(..., description="Confidence score of the rewrite")

# Initialize services
rag_service = RAGService()
nlp_service = NLPService()

@router.post("/", response_model=ContentRewriteResponse)
async def rewrite_content(
    request: ContentRewriteRequest,
    background_tasks: BackgroundTasks
):
    """
    Rewrite content for a specific field and platform
    """
    start_time = time.time()
    
    try:
        # Log the request
        log_api_request("rewrite_content", request.dict())
        
        # Validate and normalize inputs
        platform = normalize_platform(request.platform)
        field = normalize_field(request.field)
        
        if platform not in VALID_PLATFORMS:
            raise ValidationError(f"Invalid platform: {request.platform}")
        
        if field not in VALID_FIELDS:
            raise ValidationError(f"Invalid field: {request.field}")
        
        if not request.current_content or not request.current_content.strip():
            raise ValidationError("Current content cannot be empty")
        
        # Determine character limit
        max_length = request.max_length or infer_platform_limit(platform, field)
        
        # Generate rewritten content using simple LLM call (bypassing RAG for debugging)
        from src.models.multi_llm_client import MultiLLMClient
        llm_client = MultiLLMClient()
        
        prompt = f"Rewrite this {field} for {platform}: {request.current_content}"
        rewritten_content = await llm_client.generate_text(
            prompt=prompt,
            max_tokens=min(max_length, 1000),
            temperature=0.7
        )
        
        # Generate additional suggestions (temporarily disabled for debugging)
        suggestions = []
        
        # Calculate confidence score based on content quality
        quality_analysis = nlp_service.analyze_content_quality(
            rewritten_content, 
            request.content_type or "post", 
            platform
        )
        # Calculate confidence score based on readability and sentiment
        readability_data = quality_analysis.get('analysis', {}).get('readability', {})
        readability_score = readability_data.get('score', 0.5) if isinstance(readability_data, dict) else 0.5
        confidence_score = min(max(readability_score, 0.5), 1.0)  # Clamp between 0.5 and 1.0
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = ContentRewriteResponse(
            rewritten_content=rewritten_content,
            original_content=request.current_content,
            field=field,
            platform=platform,
            character_count=len(rewritten_content),
            suggestions=suggestions[:3] if suggestions else [],
            processing_time_ms=processing_time,
            confidence_score=confidence_score
        )
        
        # Log the response
        log_api_response("rewrite_content", response.dict(), processing_time)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"operation": "content_rewrite", "error_type": "validation"})
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"operation": "content_rewrite", "error_type": "insufficient_data"})
        raise HTTPException(status_code=400, detail=str(e))
    except ContentSuggestionError as e:
        ai_logger.log_error(e, {"operation": "content_rewrite", "error_type": "content_suggestion"})
        raise HTTPException(status_code=500, detail=str(e))
    except AIServiceException as e:
        ai_logger.log_error(e, {"operation": "content_rewrite", "error_type": "ai_service"})
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ai_logger.log_error(e, {"operation": "content_rewrite"})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch", response_model=List[ContentRewriteResponse])
async def rewrite_content_batch(
    requests: List[ContentRewriteRequest],
    background_tasks: BackgroundTasks
):
    """
    Rewrite multiple content fields in batch
    """
    start_time = time.time()
    
    try:
        # Log the request
        log_api_request("rewrite_content_batch", {"count": len(requests)})
        
        if len(requests) > 10:  # Limit batch size
            raise ValidationError("Batch size cannot exceed 10 items")
        
        results = []
        for request in requests:
            try:
                # Process each request individually
                result = await rewrite_content(request, background_tasks)
                results.append(result)
            except Exception as e:
                # Create error response for failed items
                error_response = ContentRewriteResponse(
                    success=False,
                    rewritten_content=request.current_content,
                    original_content=request.current_content,
                    field=request.field,
                    platform=request.platform,
                    character_count=len(request.current_content),
                    suggestions=[],
                    processing_time_ms=0,
                    confidence_score=0.0
                )
                results.append(error_response)
                ai_logger.error(f"Error processing batch item: {str(e)}")
        
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("rewrite_content_batch", {"count": len(results)}, processing_time)
        
        return results
        
    except Exception as e:
        ai_logger.log_error(e, {"operation": "batch_content_rewrite"})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/platforms")
async def get_supported_platforms():
    """
    Get list of supported platforms for content rewriting
    """
    return {
        "platforms": list(VALID_PLATFORMS),
        "fields": list(VALID_FIELDS),
        "char_limits": PLATFORM_CHAR_LIMITS
    }
