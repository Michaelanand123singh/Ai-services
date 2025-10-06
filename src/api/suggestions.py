"""
AI-powered content suggestions API endpoints
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

router = APIRouter(prefix="/ai/suggestions", tags=["suggestions"])


# Allowlists and simple normalization maps
VALID_PLATFORMS = {
    "twitter", "instagram", "linkedin", "facebook", "youtube"
}

VALID_CONTENT_TYPES = {
    "post", "tweet", "reel", "story", "short", "video", "title", "description"
}

PLATFORM_CHAR_LIMITS: Dict[str, int] = {
    # default top-level caps (field-specific handled on client); server keeps conservative caps
    "twitter": 280,
    "instagram": 2200,
    "linkedin": 3000,
    "facebook": 63000,
    "youtube": 5000,  # treat as description default
}

def normalize_platform(name: str) -> str:
    v = (name or "").strip().lower()
    aliases = {"x": "twitter"}
    return aliases.get(v, v)

def normalize_content_type(ct: str) -> str:
    v = (ct or "").strip().lower()
    aliases = {"tweet": "post", "shorts": "short"}
    return aliases.get(v, v)

def infer_platform_limit(platform: str, content_type: str, requested: Optional[int]) -> int:
    base = PLATFORM_CHAR_LIMITS.get(platform, 3000)
    # Inline overrides for some combinations
    if platform == "youtube" and content_type == "title":
        base = 100
    if requested is not None and requested > 0:
        return min(base, requested)
    return base

class ContentSuggestionRequest(BaseModel):
    """Request model for content suggestions"""
    user_id: str = Field(..., description="User ID requesting suggestions")
    campaign_id: Optional[str] = Field(None, description="Campaign ID if suggestions are for a specific campaign")
    content_type: str = Field(..., description="Type of content (post, story, reel, video, etc.)")
    platform: str = Field(..., description="Social media platform")
    content: Optional[str] = Field(None, description="Existing content to improve")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    goals: List[str] = Field(default=[], description="Content goals (engagement, reach, conversion, etc.)")
    tone: str = Field(default="professional", description="Content tone")
    include_hashtags: bool = Field(default=True, description="Include hashtag suggestions")
    include_captions: bool = Field(default=True, description="Include caption suggestions")
    include_posting_times: bool = Field(default=True, description="Include optimal posting time suggestions")
    include_content_ideas: bool = Field(default=True, description="Include content idea suggestions")
    max_suggestions: int = Field(default=10, description="Maximum number of suggestions per category")
    max_length: Optional[int] = Field(default=None, description="Optional hard cap on generated text length")
    language: Optional[str] = Field(default=None, description="Preferred output language (e.g., 'en')")


class HashtagSuggestion(BaseModel):
    """Hashtag suggestion model"""
    hashtag: str
    popularity_score: float
    relevance_score: float
    competition_level: str
    estimated_reach: int
    category: str


class CaptionSuggestion(BaseModel):
    """Caption suggestion model"""
    caption: str
    tone: str
    length: int
    engagement_potential: float
    readability_score: float
    emoji_count: int


class PostingTimeSuggestion(BaseModel):
    """Posting time suggestion model"""
    platform: str
    optimal_times: List[str]
    best_days: List[str]
    frequency: str
    reasoning: str


class ContentIdea(BaseModel):
    """Content idea model"""
    title: str
    description: str
    format: str
    estimated_engagement: float
    difficulty: str
    time_to_create: str
    trending_potential: float


class ContentSuggestionResponse(BaseModel):
    """Response model for content suggestions"""
    suggestion_id: str
    user_id: str
    campaign_id: Optional[str]
    content_type: str
    platform: str
    suggestions: Dict[str, Any]
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


# Dependency injection
def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


def get_nlp_service() -> NLPService:
    """Get NLP service instance"""
    return NLPService()


@router.post("/", response_model=ContentSuggestionResponse)
async def generate_content_suggestions(
    request: ContentSuggestionRequest,
    background_tasks: BackgroundTasks,
    rag_service: RAGService = Depends(get_rag_service),
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Generate AI-powered content suggestions
    
    This endpoint provides comprehensive content suggestions including hashtags,
    captions, optimal posting times, and content ideas based on the user's
    content type, platform, and goals.
    """
    start_time = time.time()
    log_api_request("/ai/suggestions", "POST", request.user_id)
    
    try:
        # Normalize & validate request
        if not request.content_type:
            raise ValidationError("content_type", request.content_type, "Content type is required")

        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")

        # Normalize values
        platform = normalize_platform(request.platform)
        content_type = normalize_content_type(request.content_type)

        if platform not in VALID_PLATFORMS:
            raise ValidationError("platform", platform, f"Unsupported platform. Allowed: {sorted(VALID_PLATFORMS)}")

        if content_type not in VALID_CONTENT_TYPES:
            raise ValidationError("content_type", content_type, f"Unsupported content_type. Allowed: {sorted(VALID_CONTENT_TYPES)}")

        if request.max_suggestions <= 0 or request.max_suggestions > 50:
            raise ValidationError("max_suggestions", request.max_suggestions, "Max suggestions must be between 1 and 50")
        
        # Check feature flag
        if not settings.enable_content_suggestions:
            raise HTTPException(status_code=503, detail="Content suggestions are currently disabled")
        
        # Generate suggestions based on request parameters
        suggestions = {}
        
        # Generate hashtag suggestions
        if request.include_hashtags:
            hashtag_suggestions = await rag_service.generate_hashtag_suggestions(
                content=request.content,
                content_type=content_type,
                platform=platform,
                target_audience=request.target_audience,
                goals=request.goals,
                max_suggestions=request.max_suggestions
            )
            suggestions["hashtags"] = hashtag_suggestions
        
        # Generate caption suggestions
        if request.include_captions:
            caption_suggestions = await rag_service.generate_caption_suggestions(
                content=request.content,
                content_type=content_type,
                platform=platform,
                tone=request.tone,
                target_audience=request.target_audience,
                goals=request.goals,
                max_suggestions=request.max_suggestions
            )
            # Normalize captions to array of { caption, score?, rationale? }
            norm: List[Dict[str, Any]] = []
            limit = infer_platform_limit(platform, content_type, request.max_length)
            for it in caption_suggestions or []:
                if isinstance(it, str):
                    norm.append({"caption": it[:limit]})
                elif isinstance(it, dict):
                    text = it.get("caption") or it.get("text") or it.get("content") or ""
                    entry = {
                        "caption": (text or "")[:limit]
                    }
                    if "score" in it:
                        entry["score"] = it["score"]
                    if "rationale" in it:
                        entry["rationale"] = it["rationale"]
                    norm.append(entry)
            suggestions["captions"] = norm
        
        # Generate posting time suggestions
        if request.include_posting_times:
            posting_time_suggestions = await rag_service.generate_posting_time_suggestions(
                platform=platform,
                content_type=content_type,
                target_audience=request.target_audience,
                user_id=request.user_id
            )
            suggestions["posting_times"] = posting_time_suggestions
        
        # Generate content ideas
        if request.include_content_ideas:
            content_ideas = await rag_service.generate_content_ideas(
                content_type=content_type,
                platform=platform,
                target_audience=request.target_audience,
                goals=request.goals,
                tone=request.tone,
                max_suggestions=request.max_suggestions
            )
            suggestions["content_ideas"] = content_ideas
        
        # Generate content optimization suggestions
        if request.content:
            optimization_suggestions = nlp_service.analyze_content_quality(
                content=request.content,
                content_type=content_type,
                platform=platform
            )
            suggestions["optimization"] = optimization_suggestions
        
        # Generate engagement predictions
        engagement_predictions = await rag_service.predict_engagement(
            content=request.content,
            content_type=content_type,
            platform=platform,
            hashtags=suggestions.get("hashtags", []),
            target_audience=request.target_audience
        )
        suggestions["engagement_predictions"] = engagement_predictions
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log successful suggestion generation
        ai_logger.log_content_suggestion(
            user_id=request.user_id,
            content_type=request.content_type,
            suggestions_count=sum(len(v) if isinstance(v, list) else 1 for v in suggestions.values()),
            platform=request.platform
        )
        
        # Build response with meta info for client UX
        response = ContentSuggestionResponse(
            suggestion_id=f"content_suggestions_{int(time.time())}_{request.user_id}",
            user_id=request.user_id,
            campaign_id=request.campaign_id,
            content_type=content_type,
            platform=platform,
            suggestions=suggestions,
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/suggestions", "POST", 200, processing_time, request.user_id)
        return response
        
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/suggestions", "POST", 400, processing_time, request.user_id)
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/suggestions", "POST", 422, processing_time, request.user_id)
        raise HTTPException(status_code=422, detail=str(e))
    
    except ContentSuggestionError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/suggestions", "POST", 500, processing_time, request.user_id)
        ai_logger.log_error(e, {"user_id": request.user_id, "content_type": request.content_type})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/suggestions", "POST", 500, processing_time, request.user_id)
        ai_logger.log_error(e, {"user_id": request.user_id, "content_type": request.content_type})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/hashtags")
async def generate_hashtag_suggestions_simple(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate hashtag suggestions only
    """
    try:
        suggestions = await rag_service.generate_hashtag_suggestions(
            content=request.content,
            content_type=request.content_type,
            platform=request.platform,
            target_audience=request.target_audience,
            goals=request.goals,
            max_suggestions=request.max_suggestions
        )
        return {"hashtags": suggestions}
    except Exception as e:
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail="Failed to generate hashtag suggestions")


@router.post("/captions")
async def generate_caption_suggestions_simple(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate caption suggestions only
    """
    try:
        suggestions = await rag_service.generate_caption_suggestions(
            content=request.content,
            content_type=request.content_type,
            platform=request.platform,
            tone=request.tone,
            target_audience=request.target_audience,
            goals=request.goals,
            max_suggestions=request.max_suggestions
        )
        return {"captions": suggestions}
    except Exception as e:
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail="Failed to generate caption suggestions")


@router.post("/posting-times")
async def generate_posting_time_suggestions_simple(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate optimal posting time suggestions
    """
    try:
        suggestions = await rag_service.generate_posting_time_suggestions(
            platform=request.platform,
            content_type=request.content_type,
            target_audience=request.target_audience,
            user_id=request.user_id
        )
        return {"posting_times": suggestions}
    except Exception as e:
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail="Failed to generate posting time suggestions")


@router.post("/content-ideas")
async def generate_content_ideas_simple(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate content ideas
    """
    try:
        suggestions = await rag_service.generate_content_ideas(
            content_type=request.content_type,
            platform=request.platform,
            target_audience=request.target_audience,
            goals=request.goals,
            tone=request.tone,
            max_suggestions=request.max_suggestions
        )
        return {"content_ideas": suggestions}
    except Exception as e:
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail="Failed to generate content ideas")


@router.get("/user/{user_id}/history")
async def get_user_suggestion_history(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get user's content suggestion history
    """
    try:
        history = await rag_service.get_user_suggestion_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return history
    except Exception as e:
        ai_logger.log_error(e, {"user_id": user_id})
        raise HTTPException(status_code=500, detail="Failed to retrieve suggestion history")


@router.post("/hashtags", response_model=List[HashtagSuggestion])
async def generate_hashtag_suggestions_model(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service),
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Generate hashtag suggestions for content
    
    This endpoint provides AI-powered hashtag suggestions based on content,
    platform, target audience, and goals.
    """
    start_time = time.time()
    log_api_request("/ai/suggestions/hashtags", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.content_type:
            raise ValidationError("content_type", request.content_type, "Content type is required")
        
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        # Check feature flag
        if not settings.enable_content_suggestions:
            raise HTTPException(status_code=503, detail="Content suggestions are currently disabled")
        
        # Generate hashtag suggestions
        hashtag_suggestions = await rag_service.generate_hashtag_suggestions(
            content=request.content,
            content_type=request.content_type,
            platform=request.platform,
            target_audience=request.target_audience,
            goals=request.goals,
            max_suggestions=request.max_suggestions
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/suggestions/hashtags", "POST", request.user_id, 
                        processing_time, len(hashtag_suggestions))
        
        return hashtag_suggestions
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/hashtags"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/hashtags"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/captions", response_model=List[CaptionSuggestion])
async def generate_caption_suggestions_model(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service),
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Generate caption suggestions for content
    
    This endpoint provides AI-powered caption suggestions based on content,
    platform, tone, and target audience.
    """
    start_time = time.time()
    log_api_request("/ai/suggestions/captions", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.content_type:
            raise ValidationError("content_type", request.content_type, "Content type is required")
        
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        # Check feature flag
        if not settings.enable_content_suggestions:
            raise HTTPException(status_code=503, detail="Content suggestions are currently disabled")
        
        # Generate caption suggestions
        caption_suggestions = await rag_service.generate_caption_suggestions(
            content=request.content,
            content_type=request.content_type,
            platform=request.platform,
            tone=request.tone,
            target_audience=request.target_audience,
            goals=request.goals,
            max_suggestions=request.max_suggestions
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/suggestions/captions", "POST", request.user_id, 
                        processing_time, len(caption_suggestions))
        
        return caption_suggestions
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/captions"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/captions"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/posting-times", response_model=PostingTimeSuggestion)
async def generate_posting_time_suggestions_model(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate optimal posting time suggestions
    
    This endpoint provides AI-powered posting time suggestions based on
    platform, target audience, and content type.
    """
    start_time = time.time()
    log_api_request("/ai/suggestions/posting-times", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        # Check feature flag
        if not settings.enable_content_suggestions:
            raise HTTPException(status_code=503, detail="Content suggestions are currently disabled")
        
        # Generate posting time suggestions
        posting_time_suggestion = await rag_service.generate_posting_time_suggestions(
            platform=request.platform,
            target_audience=request.target_audience,
            content_type=request.content_type,
            goals=request.goals
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/suggestions/posting-times", "POST", request.user_id, 
                        processing_time, 1)
        
        return posting_time_suggestion
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/posting-times"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/posting-times"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content-ideas", response_model=List[ContentIdea])
async def generate_content_ideas_model(
    request: ContentSuggestionRequest,
    rag_service: RAGService = Depends(get_rag_service),
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Generate content ideas
    
    This endpoint provides AI-powered content ideas based on platform,
    target audience, goals, and trending topics.
    """
    start_time = time.time()
    log_api_request("/ai/suggestions/content-ideas", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        # Check feature flag
        if not settings.enable_content_suggestions:
            raise HTTPException(status_code=503, detail="Content suggestions are currently disabled")
        
        # Generate content ideas
        content_ideas = await rag_service.generate_content_ideas(
            platform=request.platform,
            content_type=request.content_type,
            target_audience=request.target_audience,
            goals=request.goals,
            tone=request.tone,
            max_suggestions=request.max_suggestions
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/suggestions/content-ideas", "POST", request.user_id, 
                        processing_time, len(content_ideas))
        
        return content_ideas
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/content-ideas"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/suggestions/content-ideas"})
        raise HTTPException(status_code=500, detail="Internal server error")
