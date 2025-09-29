"""
Matchmaking Service for Brand-Creator Matching
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from src.core.logger import ai_logger
from src.core.exceptions import MatchmakingError, InsufficientDataError
from src.services.rag_service import RAGService
from src.services.nlp_utils import NLPService


@dataclass
class BrandProfile:
    """Brand profile data structure"""
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


@dataclass
class CreatorProfile:
    """Creator profile data structure"""
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


@dataclass
class CompatibilityScore:
    """Compatibility score data structure"""
    overall_score: float
    audience_alignment: float
    content_style_match: float
    platform_reach: float
    engagement_potential: float
    budget_fit: float
    brand_values_alignment: float
    collaboration_history_score: float


class MatchmakingService:
    """Service for brand-creator matchmaking"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.nlp_service = NLPService()
        self.creator_database = {}  # In production, this would be a real database
        self.brand_database = {}    # In production, this would be a real database
        
    async def find_compatible_creators(
        self,
        brand_profile: BrandProfile,
        creator_criteria: Optional[Dict[str, Any]] = None,
        max_matches: int = 10,
        min_compatibility_score: float = 0.6,
        platforms: List[str] = None,
        budget_constraints: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find compatible creators for a brand
        
        Args:
            brand_profile: Brand profile data
            creator_criteria: Specific criteria for creator selection
            max_matches: Maximum number of matches to return
            min_compatibility_score: Minimum compatibility score
            platforms: Preferred platforms
            budget_constraints: Budget constraints
            
        Returns:
            List of compatible creator matches
        """
        try:
            ai_logger.logger.info(
                "Starting creator matchmaking",
                brand_id=brand_profile.brand_id,
                max_matches=max_matches,
                min_score=min_compatibility_score
            )
            
            # Get potential creators from database
            potential_creators = await self._get_potential_creators(
                platforms=platforms,
                criteria=creator_criteria
            )
            
            if not potential_creators:
                raise InsufficientDataError("No creators found matching criteria")
            
            # Calculate compatibility scores
            matches = []
            for creator in potential_creators:
                compatibility_score = await self._calculate_compatibility(
                    brand_profile, creator, budget_constraints
                )
                
                if compatibility_score.overall_score >= min_compatibility_score:
                    match_reasons = await self._generate_match_reasons(
                        brand_profile, creator, compatibility_score
                    )
                    
                    potential_campaign_ideas = await self._generate_campaign_ideas(
                        brand_profile, creator
                    )
                    
                    estimated_performance = await self._estimate_performance(
                        brand_profile, creator, compatibility_score
                    )
                    
                    recommended_budget = await self._calculate_recommended_budget(
                        brand_profile, creator, budget_constraints
                    )
                    
                    risk_assessment = await self._assess_collaboration_risk(
                        brand_profile, creator, compatibility_score
                    )
                    
                    matches.append({
                        "creator_profile": creator,
                        "compatibility_score": compatibility_score,
                        "match_reasons": match_reasons,
                        "potential_campaign_ideas": potential_campaign_ideas,
                        "estimated_performance": estimated_performance,
                        "recommended_budget": recommended_budget,
                        "risk_assessment": risk_assessment
                    })
            
            # Sort by compatibility score and return top matches
            matches.sort(key=lambda x: x["compatibility_score"].overall_score, reverse=True)
            
            ai_logger.logger.info(
                "Matchmaking completed",
                brand_id=brand_profile.brand_id,
                total_candidates=len(potential_creators),
                compatible_matches=len(matches),
                top_score=matches[0]["compatibility_score"].overall_score if matches else 0
            )
            
            return matches[:max_matches]
            
        except Exception as e:
            ai_logger.log_error(e, {
                "brand_id": brand_profile.brand_id,
                "operation": "find_compatible_creators"
            })
            raise MatchmakingError(f"Failed to find compatible creators: {str(e)}")
    
    async def analyze_compatibility(
        self,
        brand_id: str,
        creator_id: str,
        campaign_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze compatibility between a specific brand and creator
        
        Args:
            brand_id: Brand ID
            creator_id: Creator ID
            campaign_context: Campaign context for analysis
            
        Returns:
            Detailed compatibility analysis
        """
        try:
            # Get brand and creator profiles
            brand_profile = await self._get_brand_profile(brand_id)
            creator_profile = await self._get_creator_profile(creator_id)
            
            if not brand_profile or not creator_profile:
                raise InsufficientDataError("Brand or creator profile not found")
            
            # Calculate compatibility score
            compatibility_score = await self._calculate_compatibility(
                brand_profile, creator_profile, campaign_context
            )
            
            # Generate detailed analysis
            detailed_analysis = await self._generate_detailed_analysis(
                brand_profile, creator_profile, compatibility_score, campaign_context
            )
            
            # Generate recommendations
            recommendations = await self._generate_compatibility_recommendations(
                brand_profile, creator_profile, compatibility_score
            )
            
            return {
                "compatibility_score": compatibility_score,
                "detailed_analysis": detailed_analysis,
                "recommendations": recommendations
            }
            
        except Exception as e:
            ai_logger.log_error(e, {
                "brand_id": brand_id,
                "creator_id": creator_id,
                "operation": "analyze_compatibility"
            })
            raise MatchmakingError(f"Failed to analyze compatibility: {str(e)}")
    
    async def get_trending_creators(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get trending creators based on recent performance
        
        Args:
            platform: Target platform
            category: Content category
            limit: Maximum number of creators to return
            
        Returns:
            List of trending creators
        """
        try:
            # In production, this would query a real database
            # For now, return mock data
            trending_creators = []
            
            for i in range(min(limit, 20)):
                creator = {
                    "creator_id": f"creator_{i+1}",
                    "username": f"trending_creator_{i+1}",
                    "platforms": [platform] if platform else ["instagram", "youtube"],
                    "follower_count": {"instagram": 100000 + i * 10000, "youtube": 50000 + i * 5000},
                    "engagement_rate": {"instagram": 0.05 + i * 0.001, "youtube": 0.03 + i * 0.001},
                    "content_categories": ["lifestyle", "fashion"] if i % 2 == 0 else ["tech", "gaming"],
                    "trend_score": 0.8 + i * 0.01,
                    "growth_rate": 0.15 + i * 0.02,
                    "recent_performance": {
                        "avg_views": 100000 + i * 10000,
                        "avg_engagement": 5000 + i * 500,
                        "viral_posts": 2 + i
                    }
                }
                trending_creators.append(creator)
            
            return trending_creators
            
        except Exception as e:
            ai_logger.log_error(e, {
                "platform": platform,
                "category": category,
                "operation": "get_trending_creators"
            })
            raise MatchmakingError(f"Failed to get trending creators: {str(e)}")
    
    async def _get_potential_creators(
        self,
        platforms: Optional[List[str]] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[CreatorProfile]:
        """Get potential creators from database"""
        # In production, this would query a real database
        # For now, return mock data
        creators = []
        
        for i in range(50):  # Mock 50 creators
            creator = CreatorProfile(
                creator_id=f"creator_{i+1}",
                username=f"creator_{i+1}",
                platforms=["instagram", "youtube", "tiktok"],
                follower_count={"instagram": 10000 + i * 1000, "youtube": 5000 + i * 500},
                engagement_rate={"instagram": 0.03 + i * 0.001, "youtube": 0.02 + i * 0.001},
                content_categories=["lifestyle", "fashion", "beauty"] if i % 3 == 0 else ["tech", "gaming"],
                audience_demographics={"age_range": "18-34", "gender": "mixed"},
                content_style="professional" if i % 2 == 0 else "casual",
                collaboration_history=[],
                availability="available",
                rates={"instagram": 1000 + i * 100, "youtube": 2000 + i * 200}
            )
            creators.append(creator)
        
        return creators
    
    async def _calculate_compatibility(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        budget_constraints: Optional[Dict[str, Any]] = None
    ) -> CompatibilityScore:
        """Calculate compatibility score between brand and creator"""
        
        # Audience alignment (0-1)
        audience_alignment = self._calculate_audience_alignment(
            brand_profile.target_audience, creator_profile.audience_demographics
        )
        
        # Content style match (0-1)
        content_style_match = self._calculate_content_style_match(
            brand_profile.content_preferences, creator_profile.content_categories
        )
        
        # Platform reach (0-1)
        platform_reach = self._calculate_platform_reach(
            brand_profile.social_media_presence, creator_profile.platforms
        )
        
        # Engagement potential (0-1)
        engagement_potential = self._calculate_engagement_potential(
            creator_profile.engagement_rate
        )
        
        # Budget fit (0-1)
        budget_fit = self._calculate_budget_fit(
            brand_profile.budget_range, creator_profile.rates, budget_constraints
        )
        
        # Brand values alignment (0-1)
        brand_values_alignment = self._calculate_brand_values_alignment(
            brand_profile.brand_values, creator_profile.content_categories
        )
        
        # Collaboration history score (0-1)
        collaboration_history_score = self._calculate_collaboration_history_score(
            creator_profile.collaboration_history
        )
        
        # Calculate overall score (weighted average)
        weights = {
            "audience_alignment": 0.25,
            "content_style_match": 0.20,
            "platform_reach": 0.15,
            "engagement_potential": 0.15,
            "budget_fit": 0.10,
            "brand_values_alignment": 0.10,
            "collaboration_history_score": 0.05
        }
        
        overall_score = (
            audience_alignment * weights["audience_alignment"] +
            content_style_match * weights["content_style_match"] +
            platform_reach * weights["platform_reach"] +
            engagement_potential * weights["engagement_potential"] +
            budget_fit * weights["budget_fit"] +
            brand_values_alignment * weights["brand_values_alignment"] +
            collaboration_history_score * weights["collaboration_history_score"]
        )
        
        return CompatibilityScore(
            overall_score=overall_score,
            audience_alignment=audience_alignment,
            content_style_match=content_style_match,
            platform_reach=platform_reach,
            engagement_potential=engagement_potential,
            budget_fit=budget_fit,
            brand_values_alignment=brand_values_alignment,
            collaboration_history_score=collaboration_history_score
        )
    
    def _calculate_audience_alignment(
        self,
        brand_audience: List[str],
        creator_demographics: Dict[str, Any]
    ) -> float:
        """Calculate audience alignment score"""
        # Simplified calculation - in production, this would be more sophisticated
        return 0.7 + np.random.random() * 0.3
    
    def _calculate_content_style_match(
        self,
        brand_preferences: List[str],
        creator_categories: List[str]
    ) -> float:
        """Calculate content style match score"""
        # Simplified calculation
        overlap = len(set(brand_preferences) & set(creator_categories))
        total = len(set(brand_preferences) | set(creator_categories))
        return overlap / total if total > 0 else 0.5
    
    def _calculate_platform_reach(
        self,
        brand_presence: Dict[str, Any],
        creator_platforms: List[str]
    ) -> float:
        """Calculate platform reach score"""
        # Simplified calculation
        return 0.6 + np.random.random() * 0.4
    
    def _calculate_engagement_potential(
        self,
        engagement_rates: Dict[str, float]
    ) -> float:
        """Calculate engagement potential score"""
        avg_engagement = sum(engagement_rates.values()) / len(engagement_rates)
        return min(avg_engagement * 10, 1.0)  # Normalize to 0-1
    
    def _calculate_budget_fit(
        self,
        brand_budget: str,
        creator_rates: Dict[str, float],
        budget_constraints: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate budget fit score"""
        # Simplified calculation
        return 0.8 + np.random.random() * 0.2
    
    def _calculate_brand_values_alignment(
        self,
        brand_values: List[str],
        creator_categories: List[str]
    ) -> float:
        """Calculate brand values alignment score"""
        # Simplified calculation
        return 0.7 + np.random.random() * 0.3
    
    def _calculate_collaboration_history_score(
        self,
        collaboration_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate collaboration history score"""
        if not collaboration_history:
            return 0.5  # Neutral score for new creators
        
        # Calculate based on successful collaborations
        successful_collaborations = sum(1 for collab in collaboration_history 
                                     if collab.get("success_rate", 0) > 0.7)
        return min(successful_collaborations / len(collaboration_history), 1.0)
    
    async def _generate_match_reasons(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        compatibility_score: CompatibilityScore
    ) -> List[str]:
        """Generate reasons why this creator is a good match"""
        reasons = []
        
        if compatibility_score.audience_alignment > 0.8:
            reasons.append("High audience alignment with brand target demographic")
        
        if compatibility_score.content_style_match > 0.7:
            reasons.append("Content style matches brand preferences")
        
        if compatibility_score.engagement_potential > 0.6:
            reasons.append("Strong engagement rates indicate active audience")
        
        if compatibility_score.budget_fit > 0.8:
            reasons.append("Creator rates align well with brand budget")
        
        return reasons
    
    async def _generate_campaign_ideas(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile
    ) -> List[str]:
        """Generate campaign ideas for brand-creator collaboration"""
        # This would use AI to generate creative campaign ideas
        ideas = [
            f"Collaborative {brand_profile.preferred_content_types[0]} campaign",
            f"Behind-the-scenes content with {creator_profile.username}",
            f"Product showcase in {creator_profile.content_categories[0]} style",
            f"Interactive Q&A session about {brand_profile.industry}"
        ]
        return ideas[:3]  # Return top 3 ideas
    
    async def _estimate_performance(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        compatibility_score: CompatibilityScore
    ) -> Dict[str, Any]:
        """Estimate campaign performance"""
        base_reach = sum(creator_profile.follower_count.values())
        estimated_reach = int(base_reach * compatibility_score.overall_score)
        
        return {
            "estimated_reach": estimated_reach,
            "estimated_engagement": int(estimated_reach * 0.05),
            "estimated_clicks": int(estimated_reach * 0.02),
            "estimated_conversions": int(estimated_reach * 0.01)
        }
    
    async def _calculate_recommended_budget(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        budget_constraints: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate recommended budget for collaboration"""
        avg_rate = sum(creator_profile.rates.values()) / len(creator_profile.rates)
        return avg_rate * 1.2  # 20% premium for collaboration
    
    async def _assess_collaboration_risk(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        compatibility_score: CompatibilityScore
    ) -> str:
        """Assess collaboration risk level"""
        if compatibility_score.overall_score > 0.8:
            return "Low risk - High compatibility"
        elif compatibility_score.overall_score > 0.6:
            return "Medium risk - Good compatibility"
        else:
            return "High risk - Low compatibility"
    
    async def _get_brand_profile(self, brand_id: str) -> Optional[BrandProfile]:
        """Get brand profile from database"""
        # Mock implementation
        return BrandProfile(
            brand_id=brand_id,
            name=f"Brand {brand_id}",
            industry="Technology",
            target_audience=["18-34", "tech enthusiasts"],
            content_preferences=["educational", "entertaining"],
            budget_range="medium",
            campaign_goals=["brand awareness", "engagement"],
            brand_values=["innovation", "quality"],
            preferred_content_types=["video", "posts"],
            social_media_presence={"instagram": True, "youtube": True}
        )
    
    async def _get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        """Get creator profile from database"""
        # Mock implementation
        return CreatorProfile(
            creator_id=creator_id,
            username=f"creator_{creator_id}",
            platforms=["instagram", "youtube"],
            follower_count={"instagram": 50000, "youtube": 25000},
            engagement_rate={"instagram": 0.05, "youtube": 0.03},
            content_categories=["tech", "lifestyle"],
            audience_demographics={"age_range": "18-34", "gender": "mixed"},
            content_style="professional",
            collaboration_history=[],
            availability="available",
            rates={"instagram": 2000, "youtube": 4000}
        )
    
    async def _generate_detailed_analysis(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        compatibility_score: CompatibilityScore,
        campaign_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate detailed compatibility analysis"""
        return {
            "audience_overlap": "High overlap in target demographics",
            "content_synergy": "Strong alignment in content preferences",
            "platform_coverage": "Good coverage across brand's target platforms",
            "engagement_potential": "Above-average engagement rates",
            "budget_efficiency": "Cost-effective for expected reach",
            "brand_safety": "Low risk for brand reputation",
            "collaboration_readiness": "Creator is available and experienced"
        }
    
    async def _generate_compatibility_recommendations(
        self,
        brand_profile: BrandProfile,
        creator_profile: CreatorProfile,
        compatibility_score: CompatibilityScore
    ) -> List[str]:
        """Generate recommendations for improving compatibility"""
        recommendations = []
        
        if compatibility_score.audience_alignment < 0.7:
            recommendations.append("Consider targeting different audience segments")
        
        if compatibility_score.content_style_match < 0.6:
            recommendations.append("Align content style preferences")
        
        if compatibility_score.budget_fit < 0.7:
            recommendations.append("Negotiate rates or adjust budget expectations")
        
        return recommendations
