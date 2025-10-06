"""
Performance Prediction Service for Content and Campaign Performance
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
from src.core.logger import ai_logger
from src.core.exceptions import PerformancePredictionError, InsufficientDataError
from src.services.rag_service import RAGService
from src.services.nlp_utils import NLPService


@dataclass
class PerformanceMetrics:
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


@dataclass
class OptimalTiming:
    """Optimal timing prediction model"""
    best_posting_time: str
    best_posting_day: str
    alternative_times: List[str]
    timezone: str
    reasoning: str
    expected_performance_boost: float


@dataclass
class ContentOptimization:
    """Content optimization suggestions model"""
    hashtag_suggestions: List[str]
    caption_improvements: List[str]
    content_format_suggestions: List[str]
    visual_elements: List[str]
    call_to_action_suggestions: List[str]
    expected_improvement: float


class PerformancePredictionService:
    """Service for predicting content and campaign performance"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.nlp_service = NLPService()
        self.prediction_cache = {}  # In production, this would be Redis
        self.historical_data = {}   # In production, this would be a real database
        
    async def predict_content_performance(
        self,
        content_type: str,
        platform: str,
        content_description: str,
        hashtags: List[str] = None,
        caption: str = None,
        posting_time: str = None,
        target_audience: str = None,
        campaign_goals: List[str] = None,
        budget: float = None,
        creator_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Predict content performance before posting
        
        Args:
            content_type: Type of content
            platform: Social media platform
            content_description: Description of content
            hashtags: Proposed hashtags
            caption: Proposed caption
            posting_time: Proposed posting time
            target_audience: Target audience description
            campaign_goals: Campaign goals
            budget: Campaign budget
            creator_profile: Creator profile data
            
        Returns:
            Performance prediction results
        """
        try:
            ai_logger.logger.info(
                "Starting content performance prediction",
                content_type=content_type,
                platform=platform
            )
            
            # Analyze content characteristics
            content_analysis = await self._analyze_content_characteristics(
                content_type, platform, content_description, hashtags, caption
            )
            
            # Predict performance metrics
            performance_metrics = await self._predict_performance_metrics(
                content_analysis, platform, target_audience, creator_profile
            )
            
            # Calculate optimal timing
            optimal_timing = await self._calculate_optimal_timing(
                platform, target_audience, content_type, posting_time
            )
            
            # Generate content optimization suggestions
            content_optimization = await self._generate_content_optimization(
                content_analysis, platform, target_audience, campaign_goals
            )
            
            # Assess risk factors
            risk_factors = await self._assess_content_risk_factors(
                content_analysis, platform, target_audience
            )
            
            # Calculate success probability
            success_probability = await self._calculate_success_probability(
                performance_metrics, content_analysis, risk_factors
            )
            
            ai_logger.logger.info(
                "Content performance prediction completed",
                content_type=content_type,
                platform=platform,
                estimated_reach=performance_metrics.estimated_reach,
                success_probability=success_probability
            )
            
            return {
                "performance_metrics": performance_metrics,
                "optimal_timing": optimal_timing,
                "content_optimization": content_optimization,
                "risk_factors": risk_factors,
                "success_probability": success_probability
            }
            
        except Exception as e:
            ai_logger.log_error(e, {
                "content_type": content_type,
                "platform": platform,
                "operation": "predict_content_performance"
            })
            raise PerformancePredictionError(f"Failed to predict content performance: {str(e)}")
    
    async def predict_campaign_performance(
        self,
        campaign_id: str,
        campaign_type: str,
        platforms: List[str],
        budget: float,
        duration_days: int,
        target_audience: Dict[str, Any],
        content_strategy: Dict[str, Any],
        creator_requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Predict campaign performance before launch
        
        Args:
            campaign_id: Campaign ID
            campaign_type: Type of campaign
            platforms: Target platforms
            budget: Campaign budget
            duration_days: Campaign duration
            target_audience: Target audience profile
            content_strategy: Content strategy
            creator_requirements: Creator requirements
            
        Returns:
            Campaign performance prediction
        """
        try:
            ai_logger.logger.info(
                "Starting campaign performance prediction",
                campaign_id=campaign_id,
                campaign_type=campaign_type,
                platforms=platforms,
                budget=budget
            )
            
            # Analyze campaign parameters
            campaign_analysis = await self._analyze_campaign_parameters(
                campaign_type, platforms, budget, duration_days, target_audience
            )
            
            # Predict campaign metrics
            campaign_metrics = await self._predict_campaign_metrics(
                campaign_analysis, platforms, budget, duration_days
            )
            
            # Calculate platform breakdown
            platform_breakdown = await self._calculate_platform_breakdown(
                platforms, budget, target_audience, content_strategy
            )
            
            # Optimize budget allocation
            optimal_budget_allocation = await self._optimize_budget_allocation(
                platforms, budget, campaign_metrics
            )
            
            # Assess campaign risks
            risk_assessment = await self._assess_campaign_risks(
                campaign_analysis, platforms, target_audience
            )
            
            # Calculate success probability
            success_probability = await self._calculate_campaign_success_probability(
                campaign_metrics, risk_assessment
            )
            
            ai_logger.logger.info(
                "Campaign performance prediction completed",
                campaign_id=campaign_id,
            estimated_roi=(campaign_metrics.get("estimated_roi") if isinstance(campaign_metrics, dict) else getattr(campaign_metrics, "estimated_roi", None)),
                success_probability=success_probability
            )
            
            return {
                "campaign_metrics": campaign_metrics,
                "platform_breakdown": platform_breakdown,
                "optimal_budget_allocation": optimal_budget_allocation,
                "risk_assessment": risk_assessment,
                "success_probability": success_probability
            }
            
        except Exception as e:
            ai_logger.log_error(e, {
                "campaign_id": campaign_id,
                "operation": "predict_campaign_performance"
            })
            raise PerformancePredictionError(f"Failed to predict campaign performance: {str(e)}")
    
    async def predict_creator_performance(
        self,
        creator_id: str,
        brand_id: str,
        campaign_type: str,
        platform: str,
        content_type: str,
        budget: float,
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict creator performance for a specific campaign
        
        Args:
            creator_id: Creator ID
            brand_id: Brand ID
            campaign_type: Type of campaign
            platform: Target platform
            content_type: Type of content
            budget: Campaign budget
            target_audience: Target audience
            
        Returns:
            Creator performance prediction
        """
        try:
            ai_logger.logger.info(
                "Starting creator performance prediction",
                creator_id=creator_id,
                brand_id=brand_id,
                platform=platform
            )
            
            # Get creator profile
            creator_profile = await self._get_creator_profile(creator_id)
            if not creator_profile:
                raise InsufficientDataError(f"Creator profile not found: {creator_id}")
            
            # Analyze creator capabilities
            creator_analysis = await self._analyze_creator_capabilities(
                creator_profile, platform, content_type
            )
            
            # Predict performance metrics
            predicted_performance = await self._predict_creator_metrics(
                creator_analysis, platform, content_type, budget, target_audience
            )
            
            # Calculate compatibility score
            compatibility_score = await self._calculate_creator_compatibility(
                creator_profile, brand_id, target_audience
            )
            
            # Assess risk factors
            risk_factors = await self._assess_creator_risk_factors(
                creator_profile, campaign_type, platform
            )
            
            # Generate recommendations
            recommendations = await self._generate_creator_recommendations(
                creator_analysis, predicted_performance, compatibility_score
            )
            
            ai_logger.logger.info(
                "Creator performance prediction completed",
                creator_id=creator_id,
                compatibility_score=compatibility_score
            )
            
            return {
                "predicted_performance": predicted_performance,
                "compatibility_score": compatibility_score,
                "risk_factors": risk_factors,
                "recommendations": recommendations
            }
            
        except Exception as e:
            ai_logger.log_error(e, {
                "creator_id": creator_id,
                "brand_id": brand_id,
                "operation": "predict_creator_performance"
            })
            raise PerformancePredictionError(f"Failed to predict creator performance: {str(e)}")
    
    async def get_historical_performance(
        self,
        user_id: str,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance data for predictions
        
        Args:
            user_id: User ID
            platform: Optional platform filter
            content_type: Optional content type filter
            days: Number of days to look back
            
        Returns:
            Historical performance data
        """
        try:
            # Mock implementation - in production, this would query a real database
            historical_data = []
            
            for i in range(min(days, 30)):
                data_point = {
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "platform": platform or "instagram",
                    "content_type": content_type or "post",
                    "reach": 1000 + i * 100,
                    "engagement_rate": 0.05 + i * 0.001,
                    "likes": 50 + i * 5,
                    "comments": 10 + i,
                    "shares": 5 + i,
                    "clicks": 20 + i * 2
                }
                historical_data.append(data_point)
            
            return historical_data
            
        except Exception as e:
            ai_logger.log_error(e, {
                "user_id": user_id,
                "operation": "get_historical_performance"
            })
            raise PerformancePredictionError(f"Failed to get historical performance: {str(e)}")
    
    async def _analyze_content_characteristics(
        self,
        content_type: str,
        platform: str,
        content_description: str,
        hashtags: List[str],
        caption: str
    ) -> Dict[str, Any]:
        """Analyze content characteristics"""
        return {
            "content_type": content_type,
            "platform": platform,
            "description_length": len(content_description),
            "hashtag_count": len(hashtags) if hashtags else 0,
            "caption_length": len(caption) if caption else 0,
            "complexity_score": 0.5 + np.random.random() * 0.5,
            "trending_potential": 0.3 + np.random.random() * 0.7,
            "engagement_potential": 0.4 + np.random.random() * 0.6
        }
    
    async def _predict_performance_metrics(
        self,
        content_analysis: Dict[str, Any],
        platform: str,
        target_audience: str,
        creator_profile: Dict[str, Any]
    ) -> PerformanceMetrics:
        """Predict performance metrics"""
        # Base metrics calculation
        base_reach = 10000 if creator_profile else 1000
        engagement_rate = 0.05 + np.random.random() * 0.05
        
        estimated_reach = int(base_reach * content_analysis["trending_potential"])
        estimated_impressions = int(estimated_reach * 1.5)
        estimated_likes = int(estimated_reach * engagement_rate)
        estimated_comments = int(estimated_likes * 0.1)
        estimated_shares = int(estimated_likes * 0.05)
        estimated_saves = int(estimated_likes * 0.02)
        estimated_clicks = int(estimated_reach * 0.02)
        estimated_conversions = int(estimated_clicks * 0.1)
        
        return PerformanceMetrics(
            estimated_reach=estimated_reach,
            estimated_impressions=estimated_impressions,
            estimated_engagement_rate=engagement_rate,
            estimated_likes=estimated_likes,
            estimated_comments=estimated_comments,
            estimated_shares=estimated_shares,
            estimated_saves=estimated_saves,
            estimated_clicks=estimated_clicks,
            estimated_conversions=estimated_conversions,
            confidence_score=0.7 + np.random.random() * 0.3
        )
    
    async def _calculate_optimal_timing(
        self,
        platform: str,
        target_audience: str,
        content_type: str,
        posting_time: str
    ) -> OptimalTiming:
        """Calculate optimal posting timing"""
        # Platform-specific optimal times
        optimal_times = {
            "instagram": ["18:00-20:00", "12:00-14:00"],
            "youtube": ["19:00-21:00", "14:00-16:00"],
            "tiktok": ["18:00-20:00", "21:00-23:00"],
            "twitter": ["12:00-14:00", "17:00-19:00"]
        }
        
        best_time = optimal_times.get(platform, ["18:00-20:00"])[0]
        
        return OptimalTiming(
            best_posting_time=best_time,
            best_posting_day="Friday",
            alternative_times=optimal_times.get(platform, ["18:00-20:00"]),
            timezone="UTC",
            reasoning=f"Optimal for {platform} audience engagement",
            expected_performance_boost=0.2 + np.random.random() * 0.3
        )
    
    async def _generate_content_optimization(
        self,
        content_analysis: Dict[str, Any],
        platform: str,
        target_audience: str,
        campaign_goals: List[str]
    ) -> ContentOptimization:
        """Generate content optimization suggestions"""
        return ContentOptimization(
            hashtag_suggestions=[f"#{platform}_trending_{i}" for i in range(5)],
            caption_improvements=["Add call-to-action", "Include emojis", "Ask questions"],
            content_format_suggestions=["Use carousel posts", "Add stories", "Create reels"],
            visual_elements=["High-quality images", "Brand colors", "Clear text overlay"],
            call_to_action_suggestions=["Follow for more", "Tag friends", "Share your thoughts"],
            expected_improvement=0.15 + np.random.random() * 0.25
        )
    
    async def _assess_content_risk_factors(
        self,
        content_analysis: Dict[str, Any],
        platform: str,
        target_audience: str
    ) -> List[str]:
        """Assess content risk factors"""
        risk_factors = []
        
        if content_analysis["hashtag_count"] > 30:
            risk_factors.append("Too many hashtags may reduce reach")
        
        if content_analysis["description_length"] < 50:
            risk_factors.append("Short descriptions may reduce engagement")
        
        if content_analysis["trending_potential"] < 0.3:
            risk_factors.append("Low trending potential")
        
        return risk_factors
    
    async def _calculate_success_probability(
        self,
        performance_metrics: PerformanceMetrics,
        content_analysis: Dict[str, Any],
        risk_factors: List[str]
    ) -> float:
        """Calculate success probability"""
        base_probability = performance_metrics.confidence_score
        risk_penalty = len(risk_factors) * 0.05
        return max(0.1, base_probability - risk_penalty)
    
    async def _analyze_campaign_parameters(
        self,
        campaign_type: str,
        platforms: List[str],
        budget: float,
        duration_days: int,
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze campaign parameters"""
        return {
            "campaign_type": campaign_type,
            "platform_count": len(platforms),
            "budget_per_day": budget / duration_days,
            "audience_size": target_audience.get("size", 1000000),
            "complexity_score": 0.5 + np.random.random() * 0.5
        }
    
    async def _predict_campaign_metrics(
        self,
        campaign_analysis: Dict[str, Any],
        platforms: List[str],
        budget: float,
        duration_days: int
    ) -> Dict[str, Any]:
        """Predict campaign metrics"""
        audience_size = max(int(campaign_analysis.get("audience_size", 0)), 0)
        base_reach = int(audience_size * 0.1)
        num_platforms = max(len(platforms or []), 1)
        estimated_total_reach = max(int(base_reach * num_platforms), 0)
        estimated_total_impressions = max(int(estimated_total_reach * 1.5), 0)
        estimated_engagement_rate = float(0.05 + float(np.random.random()) * 0.05)
        estimated_clicks = max(int(estimated_total_reach * 0.02), 0)
        estimated_conversions = max(int(estimated_clicks * 0.1), 0)
        safe_budget = float(budget or 0.0)

        # Guard against division by zero/NaN and return 0 when invalid
        def safe_div(n: float, d: float) -> float:
            try:
                return float(n) / float(d) if d not in (0, 0.0) else 0.0
            except Exception:
                return 0.0

        estimated_roi = safe_div(estimated_conversions * 50.0, safe_budget) if safe_budget > 0 else 0.0
        estimated_cpm = safe_div(safe_budget, (estimated_total_impressions / 1000.0)) if estimated_total_impressions > 0 else 0.0
        estimated_cpc = safe_div(safe_budget, estimated_clicks) if estimated_clicks > 0 else 0.0
        estimated_cpa = safe_div(safe_budget, estimated_conversions) if estimated_conversions > 0 else 0.0

        return {
            "estimated_total_reach": int(estimated_total_reach),
            "estimated_total_impressions": int(estimated_total_impressions),
            "estimated_engagement_rate": float(estimated_engagement_rate),
            "estimated_clicks": int(estimated_clicks),
            "estimated_conversions": int(estimated_conversions),
            "estimated_roi": float(estimated_roi),
            "estimated_cpm": float(estimated_cpm),
            "estimated_cpc": float(estimated_cpc),
            "estimated_cpa": float(estimated_cpa),
            "confidence_score": float(0.7 + float(np.random.random()) * 0.3)
        }
    
    async def _calculate_platform_breakdown(
        self,
        platforms: List[str],
        budget: float,
        target_audience: Dict[str, Any],
        content_strategy: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate platform breakdown"""
        breakdown = {}
        budget_per_platform = budget / len(platforms)
        
        for platform in platforms:
            breakdown[platform] = {
                "allocated_budget": budget_per_platform,
                "estimated_reach": int(target_audience.get("size", 1000000) * 0.1),
                "estimated_engagement_rate": 0.05 + np.random.random() * 0.05,
                "estimated_clicks": int(target_audience.get("size", 1000000) * 0.01),
                "estimated_conversions": int(target_audience.get("size", 1000000) * 0.001)
            }
        
        return breakdown
    
    async def _optimize_budget_allocation(
        self,
        platforms: List[str],
        budget: float,
        campaign_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Optimize budget allocation across platforms"""
        # Simple equal allocation for now
        allocation = {}
        budget_per_platform = budget / len(platforms)
        
        for platform in platforms:
            allocation[platform] = budget_per_platform
        
        return allocation
    
    async def _assess_campaign_risks(
        self,
        campaign_analysis: Dict[str, Any],
        platforms: List[str],
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess campaign risks"""
        return {
            "budget_risk": "Low" if campaign_analysis["budget_per_day"] > 100 else "Medium",
            "audience_risk": "Low" if target_audience.get("size", 0) > 100000 else "Medium",
            "platform_risk": "Low" if len(platforms) <= 3 else "Medium",
            "timeline_risk": "Low" if campaign_analysis.get("duration_days", 0) > 7 else "Medium"
        }
    
    async def _calculate_campaign_success_probability(
        self,
        campaign_metrics: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> float:
        """Calculate campaign success probability"""
        base_probability = campaign_metrics["confidence_score"]
        risk_count = sum(1 for risk in risk_assessment.values() if risk == "High")
        risk_penalty = risk_count * 0.1
        return max(0.1, base_probability - risk_penalty)
    
    async def _get_creator_profile(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get creator profile"""
        # Mock implementation
        return {
            "creator_id": creator_id,
            "username": f"creator_{creator_id}",
            "platforms": ["instagram", "youtube"],
            "follower_count": {"instagram": 50000, "youtube": 25000},
            "engagement_rate": {"instagram": 0.05, "youtube": 0.03},
            "content_categories": ["lifestyle", "fashion"],
            "audience_demographics": {"age_range": "18-34", "gender": "mixed"},
            "content_style": "professional",
            "collaboration_history": [],
            "availability": "available",
            "rates": {"instagram": 2000, "youtube": 4000}
        }
    
    async def _analyze_creator_capabilities(
        self,
        creator_profile: Dict[str, Any],
        platform: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Analyze creator capabilities"""
        return {
            "platform_experience": creator_profile["platforms"],
            "audience_size": creator_profile["follower_count"].get(platform, 0),
            "engagement_rate": creator_profile["engagement_rate"].get(platform, 0.03),
            "content_expertise": creator_profile["content_categories"],
            "style_match": 0.7 + np.random.random() * 0.3
        }
    
    async def _predict_creator_metrics(
        self,
        creator_analysis: Dict[str, Any],
        platform: str,
        content_type: str,
        budget: float,
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict creator performance metrics"""
        base_reach = creator_analysis["audience_size"]
        engagement_rate = creator_analysis["engagement_rate"]
        
        return {
            "estimated_reach": int(base_reach * 0.8),
            "estimated_engagement": int(base_reach * engagement_rate),
            "estimated_clicks": int(base_reach * 0.02),
            "estimated_conversions": int(base_reach * 0.001),
            "estimated_roi": (int(base_reach * 0.001) * 50) / budget
        }
    
    async def _calculate_creator_compatibility(
        self,
        creator_profile: Dict[str, Any],
        brand_id: str,
        target_audience: Dict[str, Any]
    ) -> float:
        """Calculate creator compatibility score"""
        return 0.7 + np.random.random() * 0.3
    
    async def _assess_creator_risk_factors(
        self,
        creator_profile: Dict[str, Any],
        campaign_type: str,
        platform: str
    ) -> List[str]:
        """Assess creator risk factors"""
        risk_factors = []
        
        if creator_profile["follower_count"].get(platform, 0) < 10000:
            risk_factors.append("Low follower count")
        
        if creator_profile["engagement_rate"].get(platform, 0) < 0.03:
            risk_factors.append("Low engagement rate")
        
        return risk_factors
    
    async def _generate_creator_recommendations(
        self,
        creator_analysis: Dict[str, Any],
        predicted_performance: Dict[str, Any],
        compatibility_score: float
    ) -> List[str]:
        """Generate creator recommendations"""
        recommendations = []
        
        if compatibility_score > 0.8:
            recommendations.append("High compatibility - recommended for collaboration")
        
        if predicted_performance["estimated_roi"] > 2.0:
            recommendations.append("Strong ROI potential")
        
        if creator_analysis["style_match"] > 0.8:
            recommendations.append("Content style aligns well with brand")
        
        return recommendations
