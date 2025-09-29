"""
Content Generation Pipeline for AI-powered content creation
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from src.core.logger import ai_logger
from src.core.exceptions import ContentGenerationError, InsufficientDataError
from src.services.rag_service import RAGService
from src.services.nlp_utils import NLPService


@dataclass
class ContentGenerationRequest:
    """Content generation request model"""
    user_id: str
    content_type: str
    platform: str
    topic: str
    target_audience: str
    tone: str
    goals: List[str]
    brand_guidelines: Optional[Dict[str, Any]] = None
    reference_content: Optional[List[str]] = None
    max_variations: int = 5


@dataclass
class GeneratedContent:
    """Generated content model"""
    content_id: str
    content_type: str
    platform: str
    title: str
    caption: str
    hashtags: List[str]
    visual_suggestions: List[str]
    posting_time_suggestion: str
    engagement_prediction: float
    creativity_score: float
    brand_alignment_score: float


class ContentGenerationPipeline:
    """Pipeline for AI-powered content generation"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.nlp_service = NLPService()
        self.content_templates = self._load_content_templates()
        
    async def generate_content_variations(
        self,
        request: ContentGenerationRequest
    ) -> List[GeneratedContent]:
        """
        Generate multiple content variations
        
        Args:
            request: Content generation request
            
        Returns:
            List of generated content variations
        """
        try:
            ai_logger.logger.info(
                "Starting content generation",
                user_id=request.user_id,
                content_type=request.content_type,
                platform=request.platform,
                topic=request.topic
            )
            
            # Analyze topic and audience
            topic_analysis = await self._analyze_topic(request.topic, request.target_audience)
            
            # Generate content ideas
            content_ideas = await self._generate_content_ideas(
                request.topic, request.target_audience, request.goals
            )
            
            # Generate content variations
            variations = []
            for i in range(request.max_variations):
                variation = await self._generate_single_variation(
                    request, topic_analysis, content_ideas[i % len(content_ideas)]
                )
                variations.append(variation)
            
            # Score and rank variations
            scored_variations = await self._score_content_variations(
                variations, request.brand_guidelines
            )
            
            ai_logger.logger.info(
                "Content generation completed",
                user_id=request.user_id,
                variations_generated=len(scored_variations)
            )
            
            return scored_variations
            
        except Exception as e:
            ai_logger.log_error(e, {
                "user_id": request.user_id,
                "operation": "generate_content_variations"
            })
            raise ContentGenerationError(f"Failed to generate content: {str(e)}")
    
    async def optimize_content_for_platform(
        self,
        content: GeneratedContent,
        platform: str,
        target_audience: str
    ) -> GeneratedContent:
        """
        Optimize content for specific platform
        
        Args:
            content: Original content
            platform: Target platform
            target_audience: Target audience
            
        Returns:
            Optimized content
        """
        try:
            # Platform-specific optimizations
            platform_optimizations = await self._get_platform_optimizations(platform)
            
            # Optimize caption length
            optimized_caption = await self._optimize_caption_length(
                content.caption, platform, platform_optimizations
            )
            
            # Optimize hashtags
            optimized_hashtags = await self._optimize_hashtags(
                content.hashtags, platform, target_audience
            )
            
            # Update posting time suggestion
            optimized_posting_time = await self._optimize_posting_time(
                platform, target_audience
            )
            
            # Create optimized content
            optimized_content = GeneratedContent(
                content_id=content.content_id,
                content_type=content.content_type,
                platform=platform,
                title=content.title,
                caption=optimized_caption,
                hashtags=optimized_hashtags,
                visual_suggestions=content.visual_suggestions,
                posting_time_suggestion=optimized_posting_time,
                engagement_prediction=content.engagement_prediction,
                creativity_score=content.creativity_score,
                brand_alignment_score=content.brand_alignment_score
            )
            
            return optimized_content
            
        except Exception as e:
            ai_logger.log_error(e, {
                "content_id": content.content_id,
                "platform": platform,
                "operation": "optimize_content_for_platform"
            })
            raise ContentGenerationError(f"Failed to optimize content: {str(e)}")
    
    async def _analyze_topic(
        self,
        topic: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """Analyze topic and audience for content generation"""
        return {
            "topic_keywords": topic.split(),
            "audience_interests": target_audience.split(),
            "trending_aspects": ["innovation", "sustainability", "technology"],
            "emotional_triggers": ["inspiration", "curiosity", "excitement"],
            "content_angles": ["educational", "entertaining", "inspirational"]
        }
    
    async def _generate_content_ideas(
        self,
        topic: str,
        target_audience: str,
        goals: List[str]
    ) -> List[str]:
        """Generate content ideas based on topic and audience"""
        ideas = [
            f"How to {topic} for {target_audience}",
            f"The future of {topic}",
            f"5 tips for {topic}",
            f"Why {topic} matters in 2024",
            f"Behind the scenes: {topic}"
        ]
        return ideas[:len(goals) + 2]
    
    async def _generate_single_variation(
        self,
        request: ContentGenerationRequest,
        topic_analysis: Dict[str, Any],
        content_idea: str
    ) -> GeneratedContent:
        """Generate a single content variation"""
        content_id = f"content_{int(time.time())}_{request.user_id}"
        
        # Generate title
        title = await self._generate_title(content_idea, request.tone)
        
        # Generate caption
        caption = await self._generate_caption(
            content_idea, request.tone, request.target_audience
        )
        
        # Generate hashtags
        hashtags = await self._generate_hashtags(
            request.topic, request.platform, request.target_audience
        )
        
        # Generate visual suggestions
        visual_suggestions = await self._generate_visual_suggestions(
            request.content_type, request.topic
        )
        
        # Generate posting time suggestion
        posting_time = await self._generate_posting_time_suggestion(
            request.platform, request.target_audience
        )
        
        # Calculate scores
        engagement_prediction = 0.6 + np.random.random() * 0.4
        creativity_score = 0.5 + np.random.random() * 0.5
        brand_alignment_score = 0.7 + np.random.random() * 0.3
        
        return GeneratedContent(
            content_id=content_id,
            content_type=request.content_type,
            platform=request.platform,
            title=title,
            caption=caption,
            hashtags=hashtags,
            visual_suggestions=visual_suggestions,
            posting_time_suggestion=posting_time,
            engagement_prediction=engagement_prediction,
            creativity_score=creativity_score,
            brand_alignment_score=brand_alignment_score
        )
    
    async def _generate_title(
        self,
        content_idea: str,
        tone: str
    ) -> str:
        """Generate content title"""
        tone_modifiers = {
            "professional": "Expert Guide: ",
            "casual": "Quick Tips: ",
            "inspirational": "Transform Your ",
            "educational": "Learn About ",
            "entertaining": "Fun Facts About "
        }
        
        prefix = tone_modifiers.get(tone, "")
        return f"{prefix}{content_idea}"
    
    async def _generate_caption(
        self,
        content_idea: str,
        tone: str,
        target_audience: str
    ) -> str:
        """Generate content caption"""
        caption_templates = {
            "professional": f"Discover the key insights about {content_idea} that every {target_audience} should know. #ProfessionalTips #ExpertAdvice",
            "casual": f"Hey {target_audience}! Here's what I learned about {content_idea} 👀 #CasualTips #Learning",
            "inspirational": f"Ready to transform your approach to {content_idea}? Here's how to get started! ✨ #Inspiration #Growth",
            "educational": f"Let's dive deep into {content_idea} and explore what makes it important for {target_audience}. #Education #Learning",
            "entertaining": f"Did you know about {content_idea}? Here are some fun facts that will blow your mind! 🤯 #FunFacts #Entertainment"
        }
        
        return caption_templates.get(tone, f"Check out this amazing content about {content_idea}! #Content #Discovery")
    
    async def _generate_hashtags(
        self,
        topic: str,
        platform: str,
        target_audience: str
    ) -> List[str]:
        """Generate relevant hashtags"""
        base_hashtags = [f"#{topic.replace(' ', '')}", f"#{target_audience.replace(' ', '')}"]
        
        platform_hashtags = {
            "instagram": ["#instagood", "#photooftheday", "#instadaily"],
            "youtube": ["#youtube", "#video", "#subscribe"],
            "tiktok": ["#tiktok", "#fyp", "#viral"],
            "twitter": ["#twitter", "#tweet", "#trending"],
            "linkedin": ["#linkedin", "#professional", "#networking"]
        }
        
        platform_specific = platform_hashtags.get(platform, ["#socialmedia"])
        
        return base_hashtags + platform_specific[:3]
    
    async def _generate_visual_suggestions(
        self,
        content_type: str,
        topic: str
    ) -> List[str]:
        """Generate visual suggestions"""
        suggestions = []
        
        if content_type in ["post", "story"]:
            suggestions.extend([
                "High-quality image with text overlay",
                "Infographic with key points",
                "Behind-the-scenes photo",
                "Product showcase image"
            ])
        
        if content_type in ["video", "reel"]:
            suggestions.extend([
                "Quick tutorial video",
                "Time-lapse content",
                "Interview-style video",
                "Demonstration video"
            ])
        
        return suggestions[:3]
    
    async def _generate_posting_time_suggestion(
        self,
        platform: str,
        target_audience: str
    ) -> str:
        """Generate posting time suggestion"""
        optimal_times = {
            "instagram": "18:00-20:00",
            "youtube": "19:00-21:00",
            "tiktok": "18:00-20:00",
            "twitter": "12:00-14:00",
            "linkedin": "8:00-10:00"
        }
        
        return optimal_times.get(platform, "18:00-20:00")
    
    async def _score_content_variations(
        self,
        variations: List[GeneratedContent],
        brand_guidelines: Optional[Dict[str, Any]]
    ) -> List[GeneratedContent]:
        """Score and rank content variations"""
        # Calculate composite score for each variation
        for variation in variations:
            composite_score = (
                variation.engagement_prediction * 0.4 +
                variation.creativity_score * 0.3 +
                variation.brand_alignment_score * 0.3
            )
            variation.composite_score = composite_score
        
        # Sort by composite score
        variations.sort(key=lambda x: x.composite_score, reverse=True)
        
        return variations
    
    async def _get_platform_optimizations(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific optimizations"""
        optimizations = {
            "instagram": {
                "max_caption_length": 2200,
                "optimal_hashtag_count": 5,
                "image_aspect_ratio": "1:1"
            },
            "youtube": {
                "max_title_length": 100,
                "optimal_description_length": 5000,
                "thumbnail_requirements": "1280x720"
            },
            "tiktok": {
                "max_caption_length": 300,
                "optimal_video_length": 15,
                "aspect_ratio": "9:16"
            },
            "twitter": {
                "max_tweet_length": 280,
                "optimal_hashtag_count": 2,
                "image_count": 4
            },
            "linkedin": {
                "max_post_length": 3000,
                "optimal_hashtag_count": 3,
                "professional_tone": True
            }
        }
        
        return optimizations.get(platform, {})
    
    async def _optimize_caption_length(
        self,
        caption: str,
        platform: str,
        optimizations: Dict[str, Any]
    ) -> str:
        """Optimize caption length for platform"""
        max_length = optimizations.get("max_caption_length", 2200)
        
        if len(caption) <= max_length:
            return caption
        
        # Truncate and add ellipsis
        return caption[:max_length-3] + "..."
    
    async def _optimize_hashtags(
        self,
        hashtags: List[str],
        platform: str,
        target_audience: str
    ) -> List[str]:
        """Optimize hashtags for platform"""
        optimal_count = {
            "instagram": 5,
            "youtube": 3,
            "tiktok": 3,
            "twitter": 2,
            "linkedin": 3
        }
        
        max_hashtags = optimal_count.get(platform, 5)
        return hashtags[:max_hashtags]
    
    async def _optimize_posting_time(
        self,
        platform: str,
        target_audience: str
    ) -> str:
        """Optimize posting time for platform and audience"""
        return await self._generate_posting_time_suggestion(platform, target_audience)
    
    def _load_content_templates(self) -> Dict[str, List[str]]:
        """Load content templates"""
        return {
            "post": [
                "Share your thoughts on {topic}",
                "What's your experience with {topic}?",
                "Let's discuss {topic} together"
            ],
            "story": [
                "Behind the scenes: {topic}",
                "Quick tip about {topic}",
                "Swipe up to learn more about {topic}"
            ],
            "video": [
                "Tutorial: How to {topic}",
                "My journey with {topic}",
                "Everything you need to know about {topic}"
            ],
            "reel": [
                "Quick {topic} hack",
                "POV: You're learning about {topic}",
                "This {topic} trick will change everything"
            ]
        }
