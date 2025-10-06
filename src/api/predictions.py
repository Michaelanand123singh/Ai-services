"""
Performance Prediction API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException,
    PerformancePredictionError,
    ValidationError,
    InsufficientDataError
)
from src.services.performance_prediction_service import PerformancePredictionService
from src.services.rag_service import RAGService

router = APIRouter(prefix="/ai/predictions", tags=["performance-prediction"])


class ContentPredictionRequest(BaseModel):
    """Request model for content performance prediction"""
    user_id: str = Field(..., description="User ID requesting the prediction")
    content_type: str = Field(..., description="Type of content (post, story, reel, video, etc.)")
    platform: str = Field(..., description="Social media platform")
    content_description: str = Field(..., description="Description of the content")
    hashtags: List[str] = Field(default=[], description="Proposed hashtags")
    caption: Optional[str] = Field(None, description="Proposed caption")
    posting_time: Optional[str] = Field(None, description="Proposed posting time")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    campaign_goals: List[str] = Field(default=[], description="Campaign goals")
    budget: Optional[float] = Field(None, description="Campaign budget")
    creator_profile: Optional[Dict[str, Any]] = Field(None, description="Creator profile data")


class PerformanceMetrics(BaseModel):
    """Performance metrics prediction model"""
    estimated_reach: int
    estimated_impressions: int
    estimated_engagement_rate: float
    estimated_likes: int
    estimated_comments: int
    estimated_shares: int
    estimated_saves: int
    estimated_clicks: int
    estimated_conversions: int
    confidence_score: float


class OptimalTiming(BaseModel):
    """Optimal timing prediction model"""
    best_posting_time: str
    best_posting_day: str
    alternative_times: List[str]
    timezone: str
    reasoning: str
    expected_performance_boost: float


class ContentOptimization(BaseModel):
    """Content optimization suggestions model"""
    hashtag_suggestions: List[str]
    caption_improvements: List[str]
    content_format_suggestions: List[str]
    visual_elements: List[str]
    call_to_action_suggestions: List[str]
    expected_improvement: float


class PerformancePredictionResponse(BaseModel):
    """Response model for performance prediction"""
    prediction_id: str
    user_id: str
    content_type: str
    platform: str
    performance_metrics: PerformanceMetrics
    optimal_timing: OptimalTiming
    content_optimization: ContentOptimization
    risk_factors: List[str]
    success_probability: float
    recommendations: List[str]
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


class CampaignPredictionRequest(BaseModel):
    """Request model for campaign performance prediction"""
    user_id: str = Field(..., description="User ID requesting the prediction")
    campaign_id: str = Field(..., description="Campaign ID")
    campaign_type: str = Field(..., description="Type of campaign")
    platforms: List[str] = Field(..., description="Target platforms")
    budget: float = Field(..., description="Campaign budget")
    duration_days: int = Field(..., description="Campaign duration in days")
    target_audience: Dict[str, Any] = Field(..., description="Target audience profile")
    content_strategy: Dict[str, Any] = Field(..., description="Content strategy")
    creator_requirements: Optional[Dict[str, Any]] = Field(None, description="Creator requirements")


class CampaignMetrics(BaseModel):
    """Campaign metrics prediction model"""
    estimated_total_reach: int
    estimated_total_impressions: int
    estimated_engagement_rate: float
    estimated_clicks: int
    estimated_conversions: int
    estimated_roi: float
    estimated_cpm: float
    estimated_cpc: float
    estimated_cpa: float
    confidence_score: float


class CampaignPredictionResponse(BaseModel):
    """Response model for campaign prediction"""
    prediction_id: str
    campaign_id: str
    campaign_metrics: CampaignMetrics
    platform_breakdown: Dict[str, Dict[str, Any]]
    optimal_budget_allocation: Dict[str, float]
    risk_assessment: Dict[str, Any]
    success_probability: float
    recommendations: List[str]
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


class CreatorPerformanceRequest(BaseModel):
    """Request model for creator performance prediction"""
    creator_id: str = Field(..., description="Creator ID")
    brand_id: str = Field(..., description="Brand ID")
    campaign_type: str = Field(..., description="Type of campaign")
    platform: str = Field(..., description="Target platform")
    content_type: str = Field(..., description="Type of content")
    budget: float = Field(..., description="Campaign budget")
    target_audience: Dict[str, Any] = Field(..., description="Target audience")


class CreatorPerformanceResponse(BaseModel):
    """Response model for creator performance prediction"""
    creator_id: str
    brand_id: str
    predicted_performance: Dict[str, Any]
    compatibility_score: float
    risk_factors: List[str]
    recommendations: List[str]
    generated_at: float
    processing_time_ms: int


# Dependency injection
def get_prediction_service() -> PerformancePredictionService:
    """Get performance prediction service instance"""
    return PerformancePredictionService()


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


@router.post("/content", response_model=PerformancePredictionResponse)
async def predict_content_performance(
    request: ContentPredictionRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PerformancePredictionService = Depends(get_prediction_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Predict content performance before posting
    
    This endpoint analyzes content and predicts its performance metrics
    including reach, engagement, and optimal posting times.
    """
    start_time = time.time()
    log_api_request("/ai/predictions/content", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.content_type:
            raise ValidationError("content_type", request.content_type, "Content type is required")
        
        if not request.platform:
            raise ValidationError("platform", request.platform, "Platform is required")
        
        if not request.content_description:
            raise ValidationError("content_description", request.content_description, 
                                "Content description is required")
        
        # Check feature flag
        if not settings.enable_performance_prediction:
            raise HTTPException(status_code=503, detail="Performance prediction is currently disabled")
        
        # Generate prediction ID
        prediction_id = f"pred_{int(time.time())}_{request.user_id}"
        
        # Predict content performance
        performance_prediction = await prediction_service.predict_content_performance(
            content_type=request.content_type,
            platform=request.platform,
            content_description=request.content_description,
            hashtags=request.hashtags,
            caption=request.caption,
            posting_time=request.posting_time,
            target_audience=request.target_audience,
            campaign_goals=request.campaign_goals,
            budget=request.budget,
            creator_profile=request.creator_profile
        )
        
        # Generate recommendations
        recommendations = await rag_service.generate_performance_recommendations(
            prediction=performance_prediction,
            user_id=request.user_id
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Ensure types match the Pydantic models (fill sensible defaults if missing)
        # accept either dict from service or dataclass instance
        raw_pm = performance_prediction.get("performance_metrics", {})
        pm = raw_pm if isinstance(raw_pm, dict) else raw_pm.__dict__
        raw_ot = performance_prediction.get("optimal_timing", {})
        ot = raw_ot if isinstance(raw_ot, dict) else raw_ot.__dict__
        raw_co = performance_prediction.get("content_optimization", {})
        co = raw_co if isinstance(raw_co, dict) else raw_co.__dict__
        rf = performance_prediction.get("risk_factors", [])
        sp = performance_prediction.get("success_probability", 0.5)

        response = PerformancePredictionResponse(
            prediction_id=prediction_id,
            user_id=request.user_id,
            content_type=request.content_type,
            platform=request.platform,
            performance_metrics={
                "estimated_reach": int(pm.get("estimated_reach", 0)),
                "estimated_impressions": int(pm.get("estimated_impressions", 0)),
                "estimated_engagement_rate": float(pm.get("estimated_engagement_rate", 0.0)),
                "estimated_likes": int(pm.get("estimated_likes", 0)),
                "estimated_comments": int(pm.get("estimated_comments", 0)),
                "estimated_shares": int(pm.get("estimated_shares", 0)),
                "estimated_saves": int(pm.get("estimated_saves", 0)),
                "estimated_clicks": int(pm.get("estimated_clicks", 0)),
                "estimated_conversions": int(pm.get("estimated_conversions", 0)),
                "confidence_score": float(pm.get("confidence_score", 0.6)),
            },
            optimal_timing={
                "best_posting_time": ot.get("best_posting_time", "18:00"),
                "best_posting_day": ot.get("best_posting_day", "Tuesday"),
                "alternative_times": ot.get("alternative_times", ["20:00", "21:00"]),
                "timezone": ot.get("timezone", "UTC"),
                "reasoning": ot.get("reasoning", "Based on historical engagement patterns"),
                "expected_performance_boost": float(ot.get("expected_performance_boost", 0.1)),
            },
            content_optimization={
                "hashtag_suggestions": co.get("hashtag_suggestions", []),
                "caption_improvements": co.get("caption_improvements", []),
                "content_format_suggestions": co.get("content_format_suggestions", []),
                "visual_elements": co.get("visual_elements", []),
                "call_to_action_suggestions": co.get("call_to_action_suggestions", []),
                "expected_improvement": float(co.get("expected_improvement", 0.1)),
            },
            risk_factors=list(rf),
            success_probability=float(sp),
            recommendations=recommendations,
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/predictions/content", "POST", request.user_id, 
                        processing_time, 1)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/content"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/content"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except PerformancePredictionError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/content"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/content"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/campaign", response_model=CampaignPredictionResponse)
async def predict_campaign_performance(
    request: CampaignPredictionRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PerformancePredictionService = Depends(get_prediction_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Predict campaign performance before launch
    
    This endpoint analyzes campaign parameters and predicts overall
    performance metrics and ROI.
    """
    start_time = time.time()
    log_api_request("/ai/predictions/campaign", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.campaign_id:
            raise ValidationError("campaign_id", request.campaign_id, "Campaign ID is required")
        
        if not request.platforms:
            raise ValidationError("platforms", request.platforms, "At least one platform is required")
        
        if request.budget <= 0:
            raise ValidationError("budget", request.budget, "Budget must be greater than 0")
        
        if request.duration_days <= 0:
            raise ValidationError("duration_days", request.duration_days, 
                                "Duration must be greater than 0")
        
        # Check feature flag
        if not settings.enable_performance_prediction:
            raise HTTPException(status_code=503, detail="Performance prediction is currently disabled")
        
        # Generate prediction ID
        prediction_id = f"campaign_pred_{int(time.time())}_{request.campaign_id}"
        
        # Predict campaign performance
        campaign_prediction = await prediction_service.predict_campaign_performance(
            campaign_id=request.campaign_id,
            campaign_type=request.campaign_type,
            platforms=request.platforms,
            budget=request.budget,
            duration_days=request.duration_days,
            target_audience=request.target_audience,
            content_strategy=request.content_strategy,
            creator_requirements=request.creator_requirements
        )
        
        # Generate recommendations
        recommendations = await rag_service.generate_campaign_recommendations(
            prediction=campaign_prediction,
            user_id=request.user_id
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Normalize campaign prediction structure to match model
        raw_cm = campaign_prediction.get("campaign_metrics", {})
        cm = raw_cm if isinstance(raw_cm, dict) else getattr(raw_cm, "__dict__", {})
        pb = campaign_prediction.get("platform_breakdown", {})
        oba = campaign_prediction.get("optimal_budget_allocation", {})
        ra = campaign_prediction.get("risk_assessment", {})
        sp = campaign_prediction.get("success_probability", 0.5)

        response = CampaignPredictionResponse(
            prediction_id=prediction_id,
            campaign_id=request.campaign_id,
            campaign_metrics={
                "estimated_total_reach": int(cm.get("estimated_total_reach", 0)),
                "estimated_total_impressions": int(cm.get("estimated_total_impressions", 0)),
                "estimated_engagement_rate": float(cm.get("estimated_engagement_rate", 0.0)),
                "estimated_clicks": int(cm.get("estimated_clicks", 0)),
                "estimated_conversions": int(cm.get("estimated_conversions", 0)),
                "estimated_roi": float(cm.get("estimated_roi", 0.0)),
                "estimated_cpm": float(cm.get("estimated_cpm", 0.0)),
                "estimated_cpc": float(cm.get("estimated_cpc", 0.0)),
                "estimated_cpa": float(cm.get("estimated_cpa", 0.0)),
                "confidence_score": float(cm.get("confidence_score", 0.6)),
            },
            platform_breakdown=pb,
            optimal_budget_allocation={k: float(v) for k, v in oba.items()},
            risk_assessment=ra,
            success_probability=float(sp),
            recommendations=recommendations,
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/predictions/campaign", "POST", request.user_id, 
                        processing_time, 1)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/campaign"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/campaign"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except PerformancePredictionError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/campaign"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/campaign"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/creator", response_model=CreatorPerformanceResponse)
async def predict_creator_performance(
    request: CreatorPerformanceRequest,
    prediction_service: PerformancePredictionService = Depends(get_prediction_service)
):
    """
    Predict creator performance for a specific campaign
    
    This endpoint analyzes creator capabilities and predicts their
    performance for a specific brand collaboration.
    """
    start_time = time.time()
    log_api_request("/ai/predictions/creator", "POST", request.creator_id)
    
    try:
        # Validate request
        if not request.creator_id:
            raise ValidationError("creator_id", request.creator_id, "Creator ID is required")
        
        if not request.brand_id:
            raise ValidationError("brand_id", request.brand_id, "Brand ID is required")
        
        if request.budget <= 0:
            raise ValidationError("budget", request.budget, "Budget must be greater than 0")
        
        # Check feature flag
        if not settings.enable_performance_prediction:
            raise HTTPException(status_code=503, detail="Performance prediction is currently disabled")
        
        # Predict creator performance
        creator_prediction = await prediction_service.predict_creator_performance(
            creator_id=request.creator_id,
            brand_id=request.brand_id,
            campaign_type=request.campaign_type,
            platform=request.platform,
            content_type=request.content_type,
            budget=request.budget,
            target_audience=request.target_audience
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = CreatorPerformanceResponse(
            creator_id=request.creator_id,
            brand_id=request.brand_id,
            predicted_performance=creator_prediction["predicted_performance"],
            compatibility_score=creator_prediction["compatibility_score"],
            risk_factors=creator_prediction["risk_factors"],
            recommendations=creator_prediction["recommendations"],
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/predictions/creator", "POST", request.creator_id, 
                        processing_time, 1)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/creator"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/creator"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except PerformancePredictionError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/creator"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/creator"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/historical-performance/{user_id}")
async def get_historical_performance(
    user_id: str,
    platform: Optional[str] = None,
    content_type: Optional[str] = None,
    days: int = 30,
    prediction_service: PerformancePredictionService = Depends(get_prediction_service)
):
    """
    Get historical performance data for predictions
    
    This endpoint returns historical performance data that can be used
    to improve prediction accuracy.
    """
    start_time = time.time()
    log_api_request("/ai/predictions/historical-performance", "GET", user_id)
    
    try:
        # Validate inputs
        if not user_id:
            raise ValidationError("user_id", user_id, "User ID is required")
        
        if days <= 0 or days > 365:
            raise ValidationError("days", days, "Days must be between 1 and 365")
        
        # Get historical performance
        historical_data = await prediction_service.get_historical_performance(
            user_id=user_id,
            platform=platform,
            content_type=content_type,
            days=days
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/predictions/historical-performance", "GET", user_id, 
                        processing_time, len(historical_data))
        
        return {
            "historical_performance": historical_data,
            "user_id": user_id,
            "platform": platform,
            "content_type": content_type,
            "days": days,
            "total_records": len(historical_data),
            "generated_at": time.time(),
            "processing_time_ms": processing_time
        }
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/historical-performance"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/predictions/historical-performance"})
        raise HTTPException(status_code=500, detail="Internal server error")
