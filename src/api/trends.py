"""
Trend Analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException,
    TrendAnalysisError,
    ValidationError,
    InsufficientDataError
)
from src.services.trend_analysis_service import TrendAnalysisService
from src.services.rag_service import RAGService

router = APIRouter(prefix="/ai/trends", tags=["trend-analysis"])


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    user_id: str = Field(..., description="User ID requesting the analysis")
    platforms: List[str] = Field(..., description="Social media platforms to analyze")
    categories: List[str] = Field(default=[], description="Content categories to analyze")
    hashtags: List[str] = Field(default=[], description="Specific hashtags to analyze")
    time_period_days: int = Field(default=7, description="Time period for trend analysis")
    analysis_type: str = Field(default="comprehensive", description="Type of trend analysis")
    include_competitor_trends: bool = Field(default=True, description="Include competitor trend analysis")
    include_audience_trends: bool = Field(default=True, description="Include audience trend analysis")
    include_content_trends: bool = Field(default=True, description="Include content trend analysis")


class TrendingHashtag(BaseModel):
    """Trending hashtag model"""
    hashtag: str
    current_volume: int
    growth_rate: float
    engagement_rate: float
    competition_level: str
    trend_direction: str
    peak_time: str
    related_hashtags: List[str]
    platform: str


class TrendingContent(BaseModel):
    """Trending content model"""
    content_type: str
    topic: str
    engagement_score: float
    viral_potential: float
    competition_level: str
    optimal_posting_time: str
    target_audience: List[str]
    platform: str
    examples: List[str]


class AudienceTrend(BaseModel):
    """Audience trend model"""
    demographic: str
    interest_categories: List[str]
    engagement_patterns: Dict[str, Any]
    growth_trend: str
    platform_preferences: Dict[str, float]
    content_preferences: List[str]


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis"""
    analysis_id: str
    user_id: str
    platforms: List[str]
    trending_hashtags: List[TrendingHashtag]
    trending_content: List[TrendingContent]
    audience_trends: List[AudienceTrend]
    competitor_insights: Dict[str, Any]
    recommendations: List[str]
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


class HashtagTrendRequest(BaseModel):
    """Request model for hashtag trend analysis"""
    hashtag: str
    platform: str
    time_period_days: int = Field(default=7, description="Time period for analysis")
    include_related: bool = Field(default=True, description="Include related hashtags")


class HashtagTrendResponse(BaseModel):
    """Response model for hashtag trend analysis"""
    hashtag: str
    platform: str
    trend_data: Dict[str, Any]
    related_hashtags: List[str]
    optimal_posting_times: List[str]
    engagement_predictions: Dict[str, float]
    generated_at: float
    processing_time_ms: int


# Dependency injection
def get_trend_service() -> TrendAnalysisService:
    """Get trend analysis service instance"""
    return TrendAnalysisService()


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


@router.post("/analyze", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    background_tasks: BackgroundTasks,
    trend_service: TrendAnalysisService = Depends(get_trend_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Analyze trending topics and patterns across social media platforms
    
    This endpoint provides comprehensive trend analysis including trending
    hashtags, content types, audience patterns, and competitor insights.
    """
    start_time = time.time()
    log_api_request("/ai/trends/analyze", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.platforms:
            raise ValidationError("platforms", request.platforms, "At least one platform is required")
        
        if request.time_period_days <= 0 or request.time_period_days > 365:
            raise ValidationError("time_period_days", request.time_period_days, 
                                "Time period must be between 1 and 365 days")
        
        # Check feature flag
        if not settings.enable_trend_analysis:
            raise HTTPException(status_code=503, detail="Trend analysis is currently disabled")
        
        # Generate analysis ID
        analysis_id = f"trend_{int(time.time())}_{request.user_id}"
        
        # Perform trend analysis
        trend_analysis = await trend_service.analyze_trends(
            platforms=request.platforms,
            categories=request.categories,
            hashtags=request.hashtags,
            time_period_days=request.time_period_days,
            analysis_type=request.analysis_type,
            include_competitor_trends=request.include_competitor_trends,
            include_audience_trends=request.include_audience_trends,
            include_content_trends=request.include_content_trends
        )
        
        # Generate recommendations
        recommendations = await rag_service.generate_trend_recommendations(
            trend_analysis=trend_analysis,
            user_id=request.user_id
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = TrendAnalysisResponse(
            analysis_id=analysis_id,
            user_id=request.user_id,
            platforms=request.platforms,
            trending_hashtags=trend_analysis["trending_hashtags"],
            trending_content=trend_analysis["trending_content"],
            audience_trends=trend_analysis["audience_trends"],
            competitor_insights=trend_analysis["competitor_insights"],
            recommendations=recommendations,
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/trends/analyze", "POST", request.user_id, 
                        processing_time, len(trend_analysis["trending_hashtags"]))
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/analyze"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/analyze"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except TrendAnalysisError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/analyze"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/analyze"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/hashtag", response_model=HashtagTrendResponse)
async def analyze_hashtag_trend(
    request: HashtagTrendRequest,
    trend_service: TrendAnalysisService = Depends(get_trend_service)
):
    """
    Analyze trend data for a specific hashtag
    
    This endpoint provides detailed trend analysis for a specific hashtag
    including volume, engagement, and optimal posting times.
    """
    start_time = time.time()
    log_api_request("/ai/trends/hashtag", "POST", request.hashtag)
    
    try:
        # Validate request
        if not request.hashtag:
            raise ValidationError("hashtag", request.hashtag, "Hashtag is required")
        
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        if request.time_period_days <= 0 or request.time_period_days > 90:
            raise ValidationError("time_period_days", request.time_period_days, 
                                "Time period must be between 1 and 90 days")
        
        # Check feature flag
        if not settings.enable_trend_analysis:
            raise HTTPException(status_code=503, detail="Trend analysis is currently disabled")
        
        # Analyze hashtag trend
        hashtag_analysis = await trend_service.analyze_hashtag_trend(
            hashtag=request.hashtag,
            platform=request.platform,
            time_period_days=request.time_period_days,
            include_related=request.include_related
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = HashtagTrendResponse(
            hashtag=request.hashtag,
            platform=request.platform,
            trend_data=hashtag_analysis["trend_data"],
            related_hashtags=hashtag_analysis["related_hashtags"],
            optimal_posting_times=hashtag_analysis["optimal_posting_times"],
            engagement_predictions=hashtag_analysis["engagement_predictions"],
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/trends/hashtag", "POST", request.hashtag, 
                        processing_time, 1)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/hashtag"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/hashtag"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except TrendAnalysisError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/hashtag"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/hashtag"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending-hashtags")
async def get_trending_hashtags(
    platform: str,
    category: Optional[str] = None,
    limit: int = 20,
    trend_service: TrendAnalysisService = Depends(get_trend_service)
):
    """
    Get currently trending hashtags
    
    This endpoint returns a list of currently trending hashtags
    for a specific platform and optional category.
    """
    start_time = time.time()
    log_api_request("/ai/trends/trending-hashtags", "GET", platform)
    
    try:
        # Validate inputs
        if not platform:
            raise ValidationError("platform", platform, "Platform is required")
        
        if limit <= 0 or limit > 100:
            raise ValidationError("limit", limit, "Limit must be between 1 and 100")
        
        # Check feature flag
        if not settings.enable_trend_analysis:
            raise HTTPException(status_code=503, detail="Trend analysis is currently disabled")
        
        # Get trending hashtags
        trending_hashtags = await trend_service.get_trending_hashtags(
            platform=platform,
            category=category,
            limit=limit
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/trends/trending-hashtags", "GET", platform, 
                        processing_time, len(trending_hashtags))
        
        return {
            "trending_hashtags": trending_hashtags,
            "platform": platform,
            "category": category,
            "total_count": len(trending_hashtags),
            "generated_at": time.time(),
            "processing_time_ms": processing_time
        }
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/trending-hashtags"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/trending-hashtags"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending-content")
async def get_trending_content(
    platform: str,
    content_type: Optional[str] = None,
    limit: int = 20,
    trend_service: TrendAnalysisService = Depends(get_trend_service)
):
    """
    Get currently trending content types and topics
    
    This endpoint returns trending content types and topics
    for a specific platform.
    """
    start_time = time.time()
    log_api_request("/ai/trends/trending-content", "GET", platform)
    
    try:
        # Validate inputs
        if not platform:
            raise ValidationError("platform", platform, "Platform is required")
        
        if limit <= 0 or limit > 100:
            raise ValidationError("limit", limit, "Limit must be between 1 and 100")
        
        # Check feature flag
        if not settings.enable_trend_analysis:
            raise HTTPException(status_code=503, detail="Trend analysis is currently disabled")
        
        # Get trending content
        trending_content = await trend_service.get_trending_content(
            platform=platform,
            content_type=content_type,
            limit=limit
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/trends/trending-content", "GET", platform, 
                        processing_time, len(trending_content))
        
        return {
            "trending_content": trending_content,
            "platform": platform,
            "content_type": content_type,
            "total_count": len(trending_content),
            "generated_at": time.time(),
            "processing_time_ms": processing_time
        }
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/trending-content"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/trending-content"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audience-insights")
async def get_audience_insights(
    platform: str,
    demographic: Optional[str] = None,
    limit: int = 20,
    trend_service: TrendAnalysisService = Depends(get_trend_service)
):
    """
    Get audience trend insights
    
    This endpoint returns audience trend insights including
    demographic patterns and engagement behaviors.
    """
    start_time = time.time()
    log_api_request("/ai/trends/audience-insights", "GET", platform)
    
    try:
        # Validate inputs
        if not platform:
            raise ValidationError("platform", platform, "Platform is required")
        
        if limit <= 0 or limit > 100:
            raise ValidationError("limit", limit, "Limit must be between 1 and 100")
        
        # Check feature flag
        if not settings.enable_trend_analysis:
            raise HTTPException(status_code=503, detail="Trend analysis is currently disabled")
        
        # Get audience insights
        audience_insights = await trend_service.get_audience_insights(
            platform=platform,
            demographic=demographic,
            limit=limit
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/trends/audience-insights", "GET", platform, 
                        processing_time, len(audience_insights))
        
        return {
            "audience_insights": audience_insights,
            "platform": platform,
            "demographic": demographic,
            "total_count": len(audience_insights),
            "generated_at": time.time(),
            "processing_time_ms": processing_time
        }
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/audience-insights"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/trends/audience-insights"})
        raise HTTPException(status_code=500, detail="Internal server error")
