"""
Brand-Creator Matchmaking API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException,
    MatchmakingError,
    ValidationError,
    InsufficientDataError
)
from src.services.matchmaking_service import MatchmakingService
from src.services.rag_service import RAGService

router = APIRouter(prefix="/ai/matchmaking", tags=["matchmaking"])


class BrandProfile(BaseModel):
    """Brand profile model"""
    brand_id: str
    name: str
    industry: str
    target_audience: List[str]
    content_preferences: List[str]
    budget_range: str
    campaign_goals: List[str]
    brand_values: List[str]
    preferred_content_types: List[str]
    social_media_presence: Dict[str, Any]


class CreatorProfile(BaseModel):
    """Creator profile model"""
    creator_id: str
    username: str
    platforms: List[str]
    follower_count: Dict[str, int]
    engagement_rate: Dict[str, float]
    content_categories: List[str]
    audience_demographics: Dict[str, Any]
    content_style: str
    collaboration_history: List[Dict[str, Any]]
    availability: str
    rates: Dict[str, float]


class MatchmakingRequest(BaseModel):
    """Request model for brand-creator matchmaking"""
    brand_profile: BrandProfile
    creator_criteria: Optional[Dict[str, Any]] = Field(default={}, description="Specific criteria for creator selection")
    max_matches: int = Field(default=10, description="Maximum number of matches to return")
    min_compatibility_score: float = Field(default=0.6, description="Minimum compatibility score")
    platforms: List[str] = Field(default=[], description="Preferred platforms")
    budget_constraints: Optional[Dict[str, Any]] = Field(default=None, description="Budget constraints")


class CompatibilityScore(BaseModel):
    """Compatibility score model"""
    overall_score: float
    audience_alignment: float
    content_style_match: float
    platform_reach: float
    engagement_potential: float
    budget_fit: float
    brand_values_alignment: float
    collaboration_history_score: float


class MatchResult(BaseModel):
    """Match result model"""
    creator_profile: CreatorProfile
    compatibility_score: CompatibilityScore
    match_reasons: List[str]
    potential_campaign_ideas: List[str]
    estimated_performance: Dict[str, Any]
    recommended_budget: float
    risk_assessment: str


class MatchmakingResponse(BaseModel):
    """Response model for matchmaking"""
    matchmaking_id: str
    brand_id: str
    matches: List[MatchResult]
    total_candidates_evaluated: int
    generated_at: float
    processing_time_ms: int
    status: str = "completed"


class CompatibilityRequest(BaseModel):
    """Request model for compatibility check"""
    brand_id: str
    creator_id: str
    campaign_context: Optional[Dict[str, Any]] = Field(default=None, description="Campaign context for compatibility")


class CompatibilityResponse(BaseModel):
    """Response model for compatibility check"""
    brand_id: str
    creator_id: str
    compatibility_score: CompatibilityScore
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    generated_at: float
    processing_time_ms: int


# Dependency injection
def get_matchmaking_service() -> MatchmakingService:
    """Get matchmaking service instance"""
    return MatchmakingService()


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


@router.post("/brand-creator", response_model=MatchmakingResponse)
async def match_brand_creator(
    request: MatchmakingRequest,
    background_tasks: BackgroundTasks,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Match brands with compatible content creators
    
    This endpoint analyzes brand requirements and finds the most compatible
    content creators based on audience alignment, content style, platform
    reach, and other factors.
    """
    start_time = time.time()
    log_api_request("/ai/matchmaking/brand-creator", "POST", request.brand_profile.brand_id)
    
    try:
        # Validate request
        if not request.brand_profile.brand_id:
            raise ValidationError("brand_id", request.brand_profile.brand_id, "Brand ID is required")
        
        if request.max_matches <= 0 or request.max_matches > 50:
            raise ValidationError("max_matches", request.max_matches, "Max matches must be between 1 and 50")
        
        if request.min_compatibility_score < 0 or request.min_compatibility_score > 1:
            raise ValidationError("min_compatibility_score", request.min_compatibility_score, 
                                "Compatibility score must be between 0 and 1")
        
        # Check feature flag
        if not settings.enable_matchmaking:
            raise HTTPException(status_code=503, detail="Matchmaking is currently disabled")
        
        # Generate matchmaking ID
        matchmaking_id = f"match_{int(time.time())}_{request.brand_profile.brand_id}"
        
        # Perform matchmaking analysis
        matches = await matchmaking_service.find_compatible_creators(
            brand_profile=request.brand_profile,
            creator_criteria=request.creator_criteria,
            max_matches=request.max_matches,
            min_compatibility_score=request.min_compatibility_score,
            platforms=request.platforms,
            budget_constraints=request.budget_constraints
        )
        
        # Generate campaign ideas for each match (fallback to recommendations helper)
        for match in matches:
            try:
                # If RAGService had a dedicated method, it would be used here.
                # Fallback: derive recommendations from compatibility details.
                recs = await rag_service.generate_campaign_recommendations(
                    prediction={
                        "brand": request.brand_profile.model_dump() if hasattr(request.brand_profile, "model_dump") else dict(request.brand_profile),
                        "creator": match.creator_profile.model_dump() if hasattr(match.creator_profile, "model_dump") else dict(match.creator_profile),
                        "compatibility": match.compatibility_score.model_dump() if hasattr(match.compatibility_score, "model_dump") else dict(match.compatibility_score),
                    },
                    user_id=request.brand_profile.brand_id,
                )
                # match could be a dict from service; support both
                if isinstance(match, dict):
                    match["potential_campaign_ideas"] = recs
                else:
                    match.potential_campaign_ideas = recs
            except Exception:
                fallback = [
                    "Run a short-form video teaser campaign",
                    "Cross-post highlights to maximize reach",
                    "A/B test two creative hooks in week 1",
                ]
                if isinstance(match, dict):
                    match["potential_campaign_ideas"] = fallback
                else:
                    match.potential_campaign_ideas = fallback
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Coerce matches into response model shape
        norm_matches = []
        for m in matches:
            mp = m.get("creator_profile") if isinstance(m, dict) else getattr(m, "creator_profile", {})
            cs = m.get("compatibility_score") if isinstance(m, dict) else getattr(m, "compatibility_score", {})
            mr = m.get("match_reasons") if isinstance(m, dict) else getattr(m, "match_reasons", [])
            ideas = m.get("potential_campaign_ideas") if isinstance(m, dict) else getattr(m, "potential_campaign_ideas", [])
            perf = m.get("estimated_performance") if isinstance(m, dict) else getattr(m, "estimated_performance", {})
            rb = m.get("recommended_budget") if isinstance(m, dict) else getattr(m, "recommended_budget", 0.0)
            risk = m.get("risk_assessment") if isinstance(m, dict) else getattr(m, "risk_assessment", "")

            norm_matches.append({
                "creator_profile": mp if isinstance(mp, dict) else getattr(mp, "__dict__", {}),
                "compatibility_score": cs if isinstance(cs, dict) else getattr(cs, "__dict__", {}),
                "match_reasons": mr,
                "potential_campaign_ideas": ideas,
                "estimated_performance": perf,
                "recommended_budget": float(rb),
                "risk_assessment": risk,
            })

        response = MatchmakingResponse(
            matchmaking_id=matchmaking_id,
            brand_id=request.brand_profile.brand_id,
            matches=norm_matches,
            total_candidates_evaluated=len(matches) * 10,  # Estimated
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response("/ai/matchmaking/brand-creator", "POST", request.brand_profile.brand_id, 
                        processing_time, len(matches))
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/brand-creator"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/brand-creator"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except MatchmakingError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/brand-creator"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/brand-creator"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/compatibility/{brand_id}/{creator_id}", response_model=CompatibilityResponse)
async def get_compatibility_score(
    brand_id: str,
    creator_id: str,
    campaign_context: Optional[Dict[str, Any]] = None,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service)
):
    """
    Get compatibility score between a specific brand and creator
    
    This endpoint calculates the compatibility score between a specific
    brand and creator, providing detailed analysis and recommendations.
    """
    start_time = time.time()
    log_api_request(f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}", "GET", brand_id)
    
    try:
        # Validate inputs
        if not brand_id:
            raise ValidationError("brand_id", brand_id, "Brand ID is required")
        
        if not creator_id:
            raise ValidationError("creator_id", creator_id, "Creator ID is required")
        
        # Check feature flag
        if not settings.enable_matchmaking:
            raise HTTPException(status_code=503, detail="Matchmaking is currently disabled")
        
        # Get compatibility analysis
        compatibility_analysis = await matchmaking_service.analyze_compatibility(
            brand_id=brand_id,
            creator_id=creator_id,
            campaign_context=campaign_context
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Normalize compatibility score into structured shape if service returns a float
        raw_cs = compatibility_analysis.get("compatibility_score")
        if isinstance(raw_cs, (int, float)):
            cs_struct = {
                "overall_score": float(raw_cs),
                "audience_alignment": float(raw_cs),
                "content_style_match": float(min(1.0, max(0.0, raw_cs - 0.05))),
                "platform_reach": float(min(1.0, max(0.0, raw_cs - 0.1))),
                "engagement_potential": float(min(1.0, max(0.0, raw_cs - 0.05))),
                "budget_fit": float(min(1.0, max(0.0, raw_cs - 0.1))),
                "brand_values_alignment": float(min(1.0, max(0.0, raw_cs - 0.05))),
                "collaboration_history_score": float(min(1.0, max(0.0, raw_cs - 0.1)))
            }
        else:
            # Assume dataclass-like; coerce to dict
            cs_struct = raw_cs if isinstance(raw_cs, dict) else getattr(raw_cs, "__dict__", {})

        response = CompatibilityResponse(
            brand_id=brand_id,
            creator_id=creator_id,
            compatibility_score=cs_struct,
            detailed_analysis=compatibility_analysis["detailed_analysis"],
            recommendations=compatibility_analysis["recommendations"],
            generated_at=time.time(),
            processing_time_ms=processing_time
        )
        
        log_api_response(f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}", "GET", 
                        brand_id, processing_time, 1)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except InsufficientDataError as e:
        ai_logger.log_error(e, {"endpoint": f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}"})
        raise HTTPException(status_code=422, detail=str(e))
    
    except MatchmakingError as e:
        ai_logger.log_error(e, {"endpoint": f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}"})
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": f"/ai/matchmaking/compatibility/{brand_id}/{creator_id}"})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending-creators")
async def get_trending_creators(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service)
):
    """
    Get trending content creators
    
    This endpoint returns a list of trending creators based on recent
    performance metrics and engagement growth.
    """
    start_time = time.time()
    log_api_request("/ai/matchmaking/trending-creators", "GET", "system")
    
    try:
        # Validate inputs
        if limit <= 0 or limit > 100:
            raise ValidationError("limit", limit, "Limit must be between 1 and 100")
        
        # Get trending creators
        trending_creators = await matchmaking_service.get_trending_creators(
            platform=platform,
            category=category,
            limit=limit
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        log_api_response("/ai/matchmaking/trending-creators", "GET", "system", 
                        processing_time, len(trending_creators))
        
        return {
            "trending_creators": trending_creators,
            "total_count": len(trending_creators),
            "generated_at": time.time(),
            "processing_time_ms": processing_time
        }
        
    except ValidationError as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/trending-creators"})
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        ai_logger.log_error(e, {"endpoint": "/ai/matchmaking/trending-creators"})
        raise HTTPException(status_code=500, detail="Internal server error")
