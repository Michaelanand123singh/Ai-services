"""
Competitor analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException, 
    CompetitorAnalysisError,
    InsufficientDataError,
    ValidationError
)
from src.services.competitor_service import CompetitorAnalysisService
from src.services.rag_service import RAGService

router = APIRouter(prefix="/ai/competitor-analysis", tags=["competitor-analysis"])


class CompetitorAnalysisRequest(BaseModel):
    """Request model for competitor analysis"""
    user_id: str = Field(..., description="User ID requesting the analysis")
    campaign_id: Optional[str] = Field(None, description="Campaign ID if analysis is for a specific campaign")
    competitors: List[str] = Field(..., description="List of competitor usernames/handles to analyze")
    platforms: List[str] = Field(..., description="Social media platforms to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")
    include_content_analysis: bool = Field(default=True, description="Include content analysis")
    include_engagement_analysis: bool = Field(default=True, description="Include engagement analysis")
    include_audience_analysis: bool = Field(default=True, description="Include audience analysis")
    time_period_days: int = Field(default=30, description="Time period for analysis in days")
    max_posts_per_competitor: int = Field(default=50, description="Maximum posts to analyze per competitor")


class CompetitorAnalysisResponse(BaseModel):
    """Response model for competitor analysis"""
    analysis_id: str
    user_id: str
    campaign_id: Optional[str]
    competitors_analyzed: List[str]
    platforms_analyzed: List[str]
    analysis_type: str
    results: Dict[str, Any]
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


class CompetitorProfile(BaseModel):
    """Competitor profile model"""
    username: str
    platform: str
    followers: int
    following: int
    posts_count: int
    engagement_rate: float
    avg_likes: int
    avg_comments: int
    avg_shares: int
    bio: Optional[str] = None
    verified: bool = False
    category: Optional[str] = None


class ContentAnalysis(BaseModel):
    """Content analysis model"""
    content_type: str
    posting_frequency: str
    best_posting_times: List[str]
    popular_hashtags: List[Dict[str, Any]]
    content_themes: List[str]
    engagement_patterns: Dict[str, Any]
    viral_content_characteristics: List[str]


class AudienceAnalysis(BaseModel):
    """Audience analysis model"""
    demographics: Dict[str, Any]
    interests: List[str]
    locations: List[Dict[str, Any]]
    activity_patterns: Dict[str, Any]
    engagement_behavior: Dict[str, Any]


class CompetitorInsights(BaseModel):
    """Competitor insights model"""
    competitor: str
    platform: str
    profile: CompetitorProfile
    content_analysis: ContentAnalysis
    audience_analysis: AudienceAnalysis
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    competitive_score: float
    recommendations: List[str]


# Dependency injection
def get_competitor_service() -> CompetitorAnalysisService:
    """Get competitor analysis service instance"""
    return CompetitorAnalysisService()


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


@router.post("/", response_model=CompetitorAnalysisResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    background_tasks: BackgroundTasks,
    competitor_service: CompetitorAnalysisService = Depends(get_competitor_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Analyze competitor profiles and strategies
    
    This endpoint performs comprehensive analysis of competitor social media profiles,
    including content analysis, engagement patterns, audience demographics, and strategic insights.
    """
    start_time = time.time()
    log_api_request("/ai/competitor-analysis", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.competitors:
            raise ValidationError("competitors", request.competitors, "At least one competitor must be specified")
        
        if not request.platforms:
            raise ValidationError("platforms", request.platforms, "At least one platform must be specified")
        
        if request.time_period_days <= 0 or request.time_period_days > 365:
            raise ValidationError("time_period_days", request.time_period_days, "Time period must be between 1 and 365 days")
        
        # Check feature flag
        if not settings.enable_competitor_analysis:
            raise HTTPException(status_code=503, detail="Competitor analysis is currently disabled")
        
        # Perform competitor analysis
        analysis_results = await competitor_service.analyze_competitors(
            user_id=request.user_id,
            campaign_id=request.campaign_id,
            competitors=request.competitors,
            platforms=request.platforms,
            analysis_type=request.analysis_type,
            include_content_analysis=request.include_content_analysis,
            include_engagement_analysis=request.include_engagement_analysis,
            include_audience_analysis=request.include_audience_analysis,
            time_period_days=request.time_period_days,
            max_posts_per_competitor=request.max_posts_per_competitor
        )
        
        # Generate AI-powered insights using RAG
        ai_insights = await rag_service.generate_competitor_insights(
            analysis_results=analysis_results,
            user_context={
                "user_id": request.user_id,
                "campaign_id": request.campaign_id,
                "analysis_type": request.analysis_type
            }
        )
        
        # Combine results
        combined_results = {
            "competitors": analysis_results,
            "ai_insights": ai_insights,
            "summary": {
                "total_competitors": len(request.competitors),
                "platforms_analyzed": request.platforms,
                "analysis_type": request.analysis_type,
                "time_period_days": request.time_period_days
            }
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log successful analysis
        ai_logger.log_competitor_analysis(
            user_id=request.user_id,
            competitors_count=len(request.competitors),
            analysis_type=request.analysis_type,
            duration_ms=processing_time
        )
        
        response = CompetitorAnalysisResponse(
            analysis_id=f"comp_analysis_{int(time.time())}_{request.user_id}",
            user_id=request.user_id,
            campaign_id=request.campaign_id,
            competitors_analyzed=request.competitors,
            platforms_analyzed=request.platforms,
            analysis_type=request.analysis_type,
            results=combined_results,
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/competitor-analysis", "POST", 200, processing_time, request.user_id)
        return response
        
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/competitor-analysis", "POST", 400, processing_time, request.user_id)
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/competitor-analysis", "POST", 422, processing_time, request.user_id)
        raise HTTPException(status_code=422, detail=str(e))
    
    except CompetitorAnalysisError as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/competitor-analysis", "POST", 500, processing_time, request.user_id)
        ai_logger.log_error(e, {"user_id": request.user_id, "competitors": request.competitors})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/competitor-analysis", "POST", 500, processing_time, request.user_id)
        ai_logger.log_error(e, {"user_id": request.user_id, "competitors": request.competitors})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{analysis_id}")
async def get_competitor_analysis(
    analysis_id: str,
    user_id: str,
    competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
):
    """
    Get previously generated competitor analysis results
    """
    try:
        results = await competitor_service.get_analysis_results(analysis_id, user_id)
        return results
    except Exception as e:
        ai_logger.log_error(e, {"analysis_id": analysis_id, "user_id": user_id})
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.delete("/{analysis_id}")
async def delete_competitor_analysis(
    analysis_id: str,
    user_id: str,
    competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
):
    """
    Delete competitor analysis results
    """
    try:
        await competitor_service.delete_analysis_results(analysis_id, user_id)
        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        ai_logger.log_error(e, {"analysis_id": analysis_id, "user_id": user_id})
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/user/{user_id}/history")
async def get_user_analysis_history(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
):
    """
    Get user's competitor analysis history
    """
    try:
        history = await competitor_service.get_user_analysis_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return history
    except Exception as e:
        ai_logger.log_error(e, {"user_id": user_id})
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis history")
