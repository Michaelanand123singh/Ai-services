"""
Competitor analysis service for social media competitor research
"""
from typing import List, Dict, Any, Optional
import asyncio
import time
from dataclasses import dataclass

from src.core.config import settings
from src.core.logger import ai_logger, log_ai_operation
from src.core.exceptions import AIServiceException, CompetitorAnalysisError, InsufficientDataError
from src.services.social.instagram import InstagramService
from src.services.social.youtube import YouTubeService
from src.services.social.twitter import TwitterService
from src.services.social.linkedin import LinkedInService
from src.services.social.facebook import FacebookService
from src.utils.helpers import clean_text, extract_hashtags, calculate_engagement_rate


@dataclass
class CompetitorProfile:
    """Competitor profile data structure"""
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
    profile_pic_url: Optional[str] = None


@dataclass
class ContentMetrics:
    """Content performance metrics"""
    likes: int
    comments: int
    shares: int
    views: int
    reach: int
    engagement_rate: float
    posted_at: str
    content_type: str
    caption: str
    hashtags: List[str]


class CompetitorAnalysisService:
    """Service for analyzing competitor social media profiles"""
    
    def __init__(self):
        self.instagram_service = InstagramService()
        self.youtube_service = YouTubeService()
        self.twitter_service = TwitterService()
        self.linkedin_service = LinkedInService()
        self.facebook_service = FacebookService()
        self.logger = ai_logger
    
    async def analyze_competitors(
        self,
        user_id: str,
        campaign_id: Optional[str],
        competitors: List[str],
        platforms: List[str],
        analysis_type: str = "comprehensive",
        include_content_analysis: bool = True,
        include_engagement_analysis: bool = True,
        include_audience_analysis: bool = True,
        time_period_days: int = 30,
        max_posts_per_competitor: int = 50
    ) -> Dict[str, Any]:
        """Analyze multiple competitors across platforms"""
        try:
            start_time = time.time()
            
            # Validate inputs
            if not competitors:
                raise InsufficientDataError("competitors", "At least one competitor must be specified")
            
            if not platforms:
                raise InsufficientDataError("platforms", "At least one platform must be specified")
            
            # Initialize results structure
            analysis_results = {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "analysis_type": analysis_type,
                "platforms": platforms,
                "time_period_days": time_period_days,
                "competitors": {},
                "summary": {},
                "generated_at": time.time()
            }
            
            # Analyze each competitor
            for competitor in competitors:
                try:
                    competitor_data = await self._analyze_single_competitor(
                        competitor=competitor,
                        platforms=platforms,
                        analysis_type=analysis_type,
                        include_content_analysis=include_content_analysis,
                        include_engagement_analysis=include_engagement_analysis,
                        include_audience_analysis=include_audience_analysis,
                        time_period_days=time_period_days,
                        max_posts_per_competitor=max_posts_per_competitor
                    )
                    analysis_results["competitors"][competitor] = competitor_data
                    
                except Exception as e:
                    self.logger.log_error(e, {"competitor": competitor})
                    analysis_results["competitors"][competitor] = {
                        "error": str(e),
                        "status": "failed"
                    }
            
            # Generate summary analysis
            analysis_results["summary"] = await self._generate_summary_analysis(
                analysis_results["competitors"], platforms
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            self.logger.log_competitor_analysis(
                user_id=user_id,
                competitors_count=len(competitors),
                analysis_type=analysis_type,
                duration_ms=processing_time
            )
            
            return analysis_results
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "analyze_competitors"})
            raise CompetitorAnalysisError("Multiple competitors", str(e))
    
    async def _analyze_single_competitor(
        self,
        competitor: str,
        platforms: List[str],
        analysis_type: str,
        include_content_analysis: bool,
        include_engagement_analysis: bool,
        include_audience_analysis: bool,
        time_period_days: int,
        max_posts_per_competitor: int
    ) -> Dict[str, Any]:
        """Analyze a single competitor across platforms"""
        competitor_data = {
            "username": competitor,
            "platforms": {},
            "overall_metrics": {},
            "analysis_type": analysis_type
        }
        
        # Analyze each platform
        for platform in platforms:
            try:
                platform_data = await self._analyze_competitor_platform(
                    competitor=competitor,
                    platform=platform,
                    analysis_type=analysis_type,
                    include_content_analysis=include_content_analysis,
                    include_engagement_analysis=include_engagement_analysis,
                    include_audience_analysis=include_audience_analysis,
                    time_period_days=time_period_days,
                    max_posts_per_competitor=max_posts_per_competitor
                )
                competitor_data["platforms"][platform] = platform_data
                
            except Exception as e:
                self.logger.log_error(e, {"competitor": competitor, "platform": platform})
                competitor_data["platforms"][platform] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # Calculate overall metrics
        competitor_data["overall_metrics"] = await self._calculate_overall_metrics(
            competitor_data["platforms"]
        )
        
        return competitor_data
    
    async def _analyze_competitor_platform(
        self,
        competitor: str,
        platform: str,
        analysis_type: str,
        include_content_analysis: bool,
        include_engagement_analysis: bool,
        include_audience_analysis: bool,
        time_period_days: int,
        max_posts_per_competitor: int
    ) -> Dict[str, Any]:
        """Analyze competitor on a specific platform"""
        try:
            # Get platform service
            platform_service = self._get_platform_service(platform)
            
            # Get competitor profile
            profile = await platform_service.get_user_profile(competitor)
            
            # Get recent posts
            posts = await platform_service.get_user_posts(
                competitor, 
                limit=max_posts_per_competitor,
                days_back=time_period_days
            )
            
            platform_data = {
                "profile": profile,
                "posts": posts,
                "analysis": {}
            }
            
            # Content analysis
            if include_content_analysis:
                platform_data["analysis"]["content"] = await self._analyze_content(
                    posts, platform
                )
            
            # Engagement analysis
            if include_engagement_analysis:
                platform_data["analysis"]["engagement"] = await self._analyze_engagement(
                    posts, profile
                )
            
            # Audience analysis
            if include_audience_analysis:
                platform_data["analysis"]["audience"] = await self._analyze_audience(
                    profile, posts, platform
                )
            
            # Generate insights
            platform_data["analysis"]["insights"] = await self._generate_platform_insights(
                platform_data["analysis"], platform
            )
            
            return platform_data
            
        except Exception as e:
            self.logger.log_error(e, {"competitor": competitor, "platform": platform})
            raise CompetitorAnalysisError(competitor, platform, str(e))
    
    def _get_platform_service(self, platform: str):
        """Get the appropriate platform service"""
        services = {
            "instagram": self.instagram_service,
            "youtube": self.youtube_service,
            "twitter": self.twitter_service,
            "linkedin": self.linkedin_service,
            "facebook": self.facebook_service
        }
        
        if platform not in services:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return services[platform]
    
    async def _analyze_content(
        self, 
        posts: List[Dict[str, Any]], 
        platform: str
    ) -> Dict[str, Any]:
        """Analyze content patterns and themes"""
        if not posts:
            return {"error": "No posts available for analysis"}
        
        # Extract content themes
        themes = await self._extract_content_themes(posts)
        
        # Analyze posting patterns
        posting_patterns = await self._analyze_posting_patterns(posts)
        
        # Analyze hashtag usage
        hashtag_analysis = await self._analyze_hashtag_usage(posts)
        
        # Analyze content types
        content_types = await self._analyze_content_types(posts, platform)
        
        return {
            "themes": themes,
            "posting_patterns": posting_patterns,
            "hashtag_analysis": hashtag_analysis,
            "content_types": content_types,
            "total_posts_analyzed": len(posts)
        }
    
    async def _analyze_engagement(
        self, 
        posts: List[Dict[str, Any]], 
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze engagement patterns and metrics"""
        if not posts:
            return {"error": "No posts available for analysis"}
        
        # Calculate engagement metrics
        total_likes = sum(post.get("likes", 0) for post in posts)
        total_comments = sum(post.get("comments", 0) for post in posts)
        total_shares = sum(post.get("shares", 0) for post in posts)
        total_views = sum(post.get("views", 0) for post in posts)
        
        avg_likes = total_likes / len(posts)
        avg_comments = total_comments / len(posts)
        avg_shares = total_shares / len(posts)
        avg_views = total_views / len(posts)
        
        # Calculate engagement rate
        followers = profile.get("followers", 1)
        total_engagement = total_likes + total_comments + total_shares
        engagement_rate = (total_engagement / (followers * len(posts))) * 100
        
        # Find best performing posts
        best_posts = sorted(posts, key=lambda x: x.get("likes", 0) + x.get("comments", 0) + x.get("shares", 0), reverse=True)[:5]
        
        return {
            "total_posts": len(posts),
            "avg_likes": round(avg_likes, 2),
            "avg_comments": round(avg_comments, 2),
            "avg_shares": round(avg_shares, 2),
            "avg_views": round(avg_views, 2),
            "engagement_rate": round(engagement_rate, 2),
            "total_engagement": total_engagement,
            "best_posts": best_posts
        }
    
    async def _analyze_audience(
        self, 
        profile: Dict[str, Any], 
        posts: List[Dict[str, Any]], 
        platform: str
    ) -> Dict[str, Any]:
        """Analyze audience demographics and behavior"""
        # This would typically involve more sophisticated audience analysis
        # For now, return basic metrics
        
        return {
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "follower_ratio": round(profile.get("followers", 0) / max(profile.get("following", 1), 1), 2),
            "verified": profile.get("verified", False),
            "bio": profile.get("bio", ""),
            "category": profile.get("category", "Unknown")
        }
    
    async def _generate_platform_insights(
        self, 
        analysis: Dict[str, Any], 
        platform: str
    ) -> Dict[str, Any]:
        """Generate insights from platform analysis"""
        insights = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "recommendations": []
        }
        
        # Generate insights based on analysis data
        if "engagement" in analysis:
            engagement_rate = analysis["engagement"].get("engagement_rate", 0)
            if engagement_rate > 5:
                insights["strengths"].append("High engagement rate")
            elif engagement_rate < 2:
                insights["weaknesses"].append("Low engagement rate")
        
        if "content" in analysis:
            themes = analysis["content"].get("themes", [])
            if len(themes) > 3:
                insights["strengths"].append("Diverse content themes")
            else:
                insights["opportunities"].append("Expand content themes")
        
        return insights
    
    async def _extract_content_themes(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Extract content themes from posts"""
        # This would use NLP to extract themes
        # For now, return placeholder
        return ["Technology", "Lifestyle", "Business"]
    
    async def _analyze_posting_patterns(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting frequency and timing patterns"""
        if not posts:
            return {}
        
        # Analyze posting times
        posting_times = [post.get("posted_at", "") for post in posts if post.get("posted_at")]
        
        return {
            "total_posts": len(posts),
            "posting_frequency": "Daily",  # This would be calculated
            "best_posting_times": ["6:00 PM", "8:00 PM"]  # This would be calculated
        }
    
    async def _analyze_hashtag_usage(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hashtag usage patterns"""
        all_hashtags = []
        for post in posts:
            hashtags = extract_hashtags(post.get("caption", ""))
            all_hashtags.extend(hashtags)
        
        # Count hashtag frequency
        hashtag_counts = {}
        for hashtag in all_hashtags:
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
        
        # Get top hashtags
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_hashtags": len(all_hashtags),
            "unique_hashtags": len(hashtag_counts),
            "avg_hashtags_per_post": len(all_hashtags) / len(posts) if posts else 0,
            "top_hashtags": [{"hashtag": h, "count": c} for h, c in top_hashtags]
        }
    
    async def _analyze_content_types(self, posts: List[Dict[str, Any]], platform: str) -> Dict[str, Any]:
        """Analyze content type distribution"""
        content_types = {}
        for post in posts:
            content_type = post.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            "distribution": content_types,
            "most_common": max(content_types.items(), key=lambda x: x[1])[0] if content_types else "unknown"
        }
    
    async def _calculate_overall_metrics(self, platforms_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall metrics across all platforms"""
        total_followers = 0
        total_engagement = 0
        total_posts = 0
        platform_count = 0
        
        for platform, data in platforms_data.items():
            if "error" not in data and "profile" in data:
                profile = data["profile"]
                total_followers += profile.get("followers", 0)
                platform_count += 1
                
                if "analysis" in data and "engagement" in data["analysis"]:
                    engagement = data["analysis"]["engagement"]
                    total_engagement += engagement.get("total_engagement", 0)
                    total_posts += engagement.get("total_posts", 0)
        
        return {
            "total_followers": total_followers,
            "total_engagement": total_engagement,
            "total_posts": total_posts,
            "platforms_analyzed": platform_count,
            "avg_engagement_per_post": total_engagement / max(total_posts, 1)
        }
    
    async def _generate_summary_analysis(
        self, 
        competitors_data: Dict[str, Any], 
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Generate summary analysis across all competitors"""
        successful_analyses = {k: v for k, v in competitors_data.items() if "error" not in v}
        
        if not successful_analyses:
            return {"error": "No successful competitor analyses"}
        
        # Calculate benchmark metrics
        total_followers = sum(
            comp.get("overall_metrics", {}).get("total_followers", 0) 
            for comp in successful_analyses.values()
        )
        
        avg_engagement = sum(
            comp.get("overall_metrics", {}).get("avg_engagement_per_post", 0) 
            for comp in successful_analyses.values()
        ) / len(successful_analyses)
        
        return {
            "competitors_analyzed": len(successful_analyses),
            "platforms_analyzed": platforms,
            "total_followers_analyzed": total_followers,
            "avg_engagement_per_post": round(avg_engagement, 2),
            "benchmark_metrics": {
                "high_engagement_threshold": 5.0,
                "medium_engagement_threshold": 2.0,
                "low_engagement_threshold": 1.0
            }
        }
    
    async def get_analysis_results(self, analysis_id: str, user_id: str) -> Dict[str, Any]:
        """Get previously generated analysis results"""
        # This would typically query a database
        # For now, return a placeholder
        return {"error": "Analysis not found"}
    
    async def delete_analysis_results(self, analysis_id: str, user_id: str) -> bool:
        """Delete analysis results"""
        # This would typically delete from a database
        # For now, return True
        return True
    
    async def get_user_analysis_history(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's analysis history"""
        # This would typically query a database
        # For now, return a placeholder
        return {
            "user_id": user_id,
            "analyses": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
