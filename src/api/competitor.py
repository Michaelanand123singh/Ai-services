"""
Competitor analysis API endpoints - ANALYSIS ONLY
Backend handles data collection, AI services focus on analysis and insights
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
from src.services.rag_service import RAGService
from src.models.multi_llm_client import MultiLLMClient
from src.core.auth import verify_api_key, get_service_info

router = APIRouter(prefix="/ai/competitor-analysis", tags=["competitor-analysis"])


class CompetitorData(BaseModel):
    """Competitor data structure received from backend"""
    platform: str
    username: str
    profile_url: str
    profile_metrics: Dict[str, Any]
    content_analysis: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    recent_posts: List[Dict[str, Any]]
    data_quality: Dict[str, Any]


class CompetitorAnalysisRequest(BaseModel):
    """Request model for competitor analysis - receives pre-collected data"""
    user_id: str = Field(..., description="User ID requesting the analysis")
    campaign_id: Optional[str] = Field(None, description="Campaign ID if analysis is for a specific campaign")
    competitors_data: List[CompetitorData] = Field(..., description="Pre-collected competitor data from backend")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")
    analysis_options: Dict[str, bool] = Field(default={}, description="Analysis options")
    collected_at: str = Field(..., description="When the data was collected")


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


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


def get_multi_llm_client() -> MultiLLMClient:
    """Get Multi-LLM client instance"""
    return MultiLLMClient()


# ----- Internal helper routines (lightweight placeholders) -----
async def analyze_single_competitor(
    competitor: CompetitorData,
    llm_client: MultiLLMClient,
    rag_service: RAGService
) -> Dict[str, Any]:
    """Create a concise analysis for one competitor using LLM (mocked/summary)."""
    prompt = (
        f"Summarize strengths/weaknesses for @{competitor.username} on {competitor.platform}. "
        "Provide 3 short bullets for strengths and weaknesses."
    )
    try:
        result = await llm_client.generate_text(prompt=prompt, provider="gemini", max_tokens=200)
        summary = result.get("content", "")
    except Exception:
        summary = "- Strength: Consistent posting\n- Weakness: Low hashtag relevance"
    return {
        "competitor": competitor.username,
        "platform": competitor.platform,
        "summary": summary,
        "metrics": competitor.profile_metrics,
    }


async def generate_market_insights(
    competitors: List[CompetitorData],
    llm_client: MultiLLMClient,
    rag_service: RAGService
) -> Dict[str, Any]:
    """Aggregate basic market-level insights (mocked)."""
    platforms = list({c.platform for c in competitors})
    return {
        "platforms": platforms,
        "themes": ["influencer_collabs", "short_form_video"],
        "risk": "moderate"
    }


async def analyze_competitive_landscape(
    competitors: List[CompetitorData],
    llm_client: MultiLLMClient,
    rag_service: RAGService
) -> Dict[str, Any]:
    """Produce a minimal landscape view (mocked)."""
    return {
        "top_creators": [c.username for c in competitors[:3]],
        "avg_engagement_rate": 0.045
    }


async def generate_strategic_recommendations(
    competitor_insights: List[Dict[str, Any]],
    market_insights: Dict[str, Any],
    competitive_landscape: Dict[str, Any],
    llm_client: MultiLLMClient,
    user_context: Dict[str, Any]
) -> List[str]:
    """Generate simple strategy bullets using LLM; fallback to defaults."""
    prompt = (
        "Based on competitor summaries and market insights, list 5 strategic recommendations.\n"
        f"Context: {str(user_context)[:500]}\n"
        f"Market: {str(market_insights)[:500]}\n"
        f"Landscape: {str(competitive_landscape)[:500]}\n"
        "Return a bullet list."
    )
    try:
        result = await llm_client.generate_text(prompt=prompt, provider="gemini", max_tokens=200)
        lines = [line.strip("- ") for line in result.get("content", "").splitlines() if line.strip()]
        return lines[:5] or [
            "Post consistently at peak times.",
            "Leverage trending tags relevant to your niche.",
            "Collaborate with micro-influencers.",
            "Test short-form video formats.",
            "Iterate creatives weekly based on metrics.",
        ]
    except Exception:
        return [
            "Post consistently at peak times.",
            "Leverage trending tags relevant to your niche.",
            "Collaborate with micro-influencers.",
            "Test short-form video formats.",
            "Iterate creatives weekly based on metrics.",
        ]


@router.post("/", response_model=CompetitorAnalysisResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    rag_service: RAGService = Depends(get_rag_service),
    llm_client: MultiLLMClient = Depends(get_multi_llm_client)
):
    """
    Analyze competitor data and generate AI insights
    
    This endpoint receives pre-collected competitor data from the backend
    and focuses purely on AI analysis and insight generation.
    """
    start_time = time.time()
    log_api_request("/ai/competitor-analysis", "POST", request.user_id)
    
    try:
        # Validate request
        if not request.competitors_data:
            raise ValidationError("competitors_data", request.competitors_data, "Competitor data is required")
        
        # Check feature flag
        if not settings.enable_competitor_analysis:
            raise HTTPException(status_code=503, detail="Competitor analysis is currently disabled")
        
        # Generate analysis ID
        analysis_id = f"comp_analysis_{int(time.time())}_{request.user_id}"
        
        # Step 1: Analyze individual competitors
        competitor_insights = []
        for competitor_data in request.competitors_data:
            insights = await analyze_single_competitor(
                competitor_data, llm_client, rag_service
            )
            competitor_insights.append(insights)
        
        # Step 2: Generate market-level insights
        market_insights = await generate_market_insights(
            request.competitors_data, llm_client, rag_service
        )
        
        # Step 3: Analyze competitive landscape
        competitive_landscape = await analyze_competitive_landscape(
            request.competitors_data, llm_client, rag_service
        )
        
        # Step 4: Generate strategic recommendations
        strategic_recommendations = await generate_strategic_recommendations(
            competitor_insights, market_insights, competitive_landscape, llm_client,
            user_context={
                "user_id": request.user_id,
                "campaign_id": request.campaign_id,
                "analysis_type": request.analysis_type
            }
        )
        
        # Combine results
        combined_results = {
            "competitors": competitor_insights,
            "ai_insights": {
                "market_insights": market_insights,
                "competitive_landscape": competitive_landscape,
                "strategic_recommendations": strategic_recommendations
            },
            "summary": {
                "total_competitors": len(request.competitors_data),
                "platforms_analyzed": request.platforms,
                "analysis_type": request.analysis_type,
                "time_period_days": request.time_period_days
            }
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log successful analysis
        ai_logger.log_competitor_analysis(
            user_id=request.user_id,
            competitors_count=len(request.competitors_data),
            analysis_type=request.analysis_type,
            duration_ms=processing_time
        )
        
        response = CompetitorAnalysisResponse(
            analysis_id=analysis_id,
            user_id=request.user_id,
            campaign_id=request.campaign_id,
            competitors_analyzed=[c.username for c in request.competitors_data],
            platforms_analyzed=list({c.platform for c in request.competitors_data}),
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
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        log_api_response("/ai/competitor-analysis", "POST", 500, processing_time, request.user_id)
        ai_logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{analysis_id}")
async def get_competitor_analysis(
    analysis_id: str,
    user_id: str,
    # Placeholder for future service injection (not required in stateless analysis-only mode)
    # competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
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
    # competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
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
    # competitor_service: CompetitorAnalysisService = Depends(get_competitor_service)
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
