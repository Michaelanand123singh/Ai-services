"""
RAG (Retrieval-Augmented Generation) service for AI-powered insights
"""
from typing import List, Dict, Any, Optional
import asyncio
import time
from dataclasses import dataclass

from src.core.config import settings
from src.core.logger import ai_logger, log_ai_model_call
from src.core.exceptions import AIServiceException, EmbeddingError, VectorDatabaseError
from src.models.multi_llm_client import MultiLLMClient
from src.models.embedding_model import EmbeddingModel
from src.models.vector_store import get_vector_store
from src.utils.helpers import clean_text, extract_keywords


@dataclass
class RAGContext:
    """Context for RAG operations"""
    user_id: str
    query: str
    context_documents: List[Dict[str, Any]]
    max_tokens: int = 4000
    temperature: float = 0.7


class RAGService:
    """RAG service for generating AI-powered insights"""
    
    def __init__(self):
        # Use multi-provider client so Gemini works without OpenAI
        self.llm_client = MultiLLMClient()
        # Initialize embedding model only if OpenAI key is configured
        self.embedding_model = EmbeddingModel() if settings.openai_api_key else None
        # Use configured vector store implementation (FAISS/Chroma/Pinecone)
        try:
            # Initialize vector store asynchronously
            self.vector_store = None  # Will be initialized on first use
        except Exception as e:
            self.logger.log_error(e, {"operation": "vector_store_init"})
            # Create a minimal fallback vector store
            from src.models.vector_store import FAISSVectorStore
            self.vector_store = FAISSVectorStore()
        self.logger = ai_logger
    
    async def _ensure_vector_store(self):
        """Ensure vector store is initialized"""
        if self.vector_store is None:
            try:
                self.vector_store = await get_vector_store()
            except Exception as e:
                self.logger.log_error(e, {"operation": "vector_store_lazy_init"})
                # Create a minimal fallback vector store
                from src.models.vector_store import FAISSVectorStore
                self.vector_store = FAISSVectorStore()
    
    async def generate_competitor_insights(
        self, 
        analysis_results: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights from competitor analysis results"""
        try:
            start_time = time.time()
            
            # Prepare context for RAG
            context_documents = self._prepare_competitor_context(analysis_results)
            
            # Create RAG context
            rag_context = RAGContext(
                user_id=user_context.get("user_id"),
                query=f"Analyze competitor strategies and provide actionable insights for {user_context.get('analysis_type', 'comprehensive')} analysis",
                context_documents=context_documents
            )
            
            # Generate insights using RAG
            insights = await self._generate_insights_with_rag(rag_context)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="competitor_insights_generation",
                model=settings.primary_ai_provider,
                tokens_used=insights.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return insights
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_competitor_insights"})
            raise AIServiceException(f"Failed to generate competitor insights: {str(e)}")
    
    async def generate_hashtag_suggestions(
        self,
        content: Optional[str],
        content_type: str,
        platform: str,
        target_audience: Optional[str],
        goals: List[str],
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate hashtag suggestions using RAG"""
        try:
            start_time = time.time()
            
            # Prepare query for hashtag generation
            query = self._build_hashtag_query(content, content_type, platform, target_audience, goals)
            
            # Retrieve relevant context from vector store
            context_documents = await self._retrieve_hashtag_context(
                content_type, platform, target_audience
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id="system",  # System-generated
                query=query,
                context_documents=context_documents,
                max_tokens=2000
            )
            
            # Generate hashtag suggestions
            suggestions = await self._generate_hashtag_suggestions_with_rag(rag_context, max_suggestions)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="hashtag_suggestions_generation",
                model=settings.primary_ai_provider,
                tokens_used=suggestions.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return suggestions.get("hashtags", [])
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_hashtag_suggestions"})
            raise AIServiceException(f"Failed to generate hashtag suggestions: {str(e)}")
    
    async def generate_caption_suggestions(
        self,
        content: Optional[str],
        content_type: str,
        platform: str,
        tone: str,
        target_audience: Optional[str],
        goals: List[str],
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate caption suggestions using RAG"""
        try:
            start_time = time.time()
            
            # Prepare query for caption generation
            query = self._build_caption_query(content, content_type, platform, tone, target_audience, goals)
            
            # Retrieve relevant context
            context_documents = await self._retrieve_caption_context(
                content_type, platform, tone, target_audience
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id="system",
                query=query,
                context_documents=context_documents,
                max_tokens=3000
            )
            
            # Generate caption suggestions
            suggestions = await self._generate_caption_suggestions_with_rag(rag_context, max_suggestions)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="caption_suggestions_generation",
                model=settings.primary_ai_provider,
                tokens_used=suggestions.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return suggestions.get("captions", [])
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_caption_suggestions"})
            raise AIServiceException(f"Failed to generate caption suggestions: {str(e)}")
    
    async def generate_posting_time_suggestions(
        self,
        platform: str,
        content_type: str,
        target_audience: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Generate optimal posting time suggestions"""
        try:
            start_time = time.time()
            
            # Retrieve user's historical posting data and platform-specific insights
            context_documents = await self._retrieve_posting_time_context(
                platform, content_type, target_audience, user_id
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id=user_id,
                query=f"Determine optimal posting times for {content_type} on {platform}",
                context_documents=context_documents,
                max_tokens=1500
            )
            
            # Generate posting time suggestions
            suggestions = await self._generate_posting_time_suggestions_with_rag(rag_context)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="posting_time_suggestions_generation",
                model=settings.primary_ai_provider,
                tokens_used=suggestions.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return suggestions
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_posting_time_suggestions"})
            raise AIServiceException(f"Failed to generate posting time suggestions: {str(e)}")
    
    async def generate_content_ideas(
        self,
        content_type: str,
        platform: str,
        target_audience: Optional[str],
        goals: List[str],
        tone: str,
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate content ideas using RAG"""
        try:
            start_time = time.time()
            
            # Retrieve trending content and successful content patterns
            context_documents = await self._retrieve_content_ideas_context(
                content_type, platform, target_audience, goals
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id="system",
                query=f"Generate creative content ideas for {content_type} on {platform} targeting {target_audience or 'general audience'}",
                context_documents=context_documents,
                max_tokens=4000
            )
            
            # Generate content ideas
            ideas = await self._generate_content_ideas_with_rag(rag_context, max_suggestions)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="content_ideas_generation",
                model=settings.primary_ai_provider,
                tokens_used=ideas.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return ideas.get("content_ideas", [])
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_content_ideas"})
            raise AIServiceException(f"Failed to generate content ideas: {str(e)}")
    
    async def predict_engagement(
        self,
        content: Optional[str],
        content_type: str,
        platform: str,
        hashtags: List[Dict[str, Any]],
        target_audience: Optional[str]
    ) -> Dict[str, Any]:
        """Predict engagement for content using RAG"""
        try:
            start_time = time.time()
            
            # Retrieve similar content performance data
            context_documents = await self._retrieve_engagement_context(
                content_type, platform, target_audience
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id="system",
                query=f"Predict engagement for {content_type} content on {platform}",
                context_documents=context_documents,
                max_tokens=2000
            )
            
            # Generate engagement prediction
            prediction = await self._generate_engagement_prediction_with_rag(rag_context)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="engagement_prediction",
                model=settings.primary_ai_provider,
                tokens_used=prediction.get("tokens_used", 0),
                duration_ms=processing_time,
                success=True
            )
            
            return prediction
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "predict_engagement"})
            raise AIServiceException(f"Failed to predict engagement: {str(e)}")
    
    async def get_user_suggestion_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's suggestion history"""
        try:
            # This would typically query a database for user's suggestion history
            # For now, return a placeholder
            return {
                "user_id": user_id,
                "suggestions": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_user_suggestion_history"})
            raise AIServiceException(f"Failed to retrieve suggestion history: {str(e)}")
    
    async def generate_trend_recommendations(
        self,
        trend_analysis: Dict[str, Any],
        user_id: str
    ) -> List[str]:
        """Generate simple recommendations based on trend analysis using the active LLM."""
        try:
            prompt = (
                "Provide 5 concise, actionable social media recommendations based on this trend analysis: \n"
                f"{str(trend_analysis)[:2000]}\nReturn a bullet list."
            )
            result = await self.llm_client.generate_text(prompt=prompt, provider="gemini", max_tokens=300)
            lines = [line.strip("- ") for line in result.get("content", "").splitlines() if line.strip()]
            return lines[:5] or ["Focus on consistent posting during peak times.", "Leverage trending hashtags with relevance."]
        except Exception:
            return [
                "Focus on consistent posting during peak times.",
                "Leverage trending hashtags with relevance.",
                "Experiment with 2-3 content formats from trending content.",
            ]

    async def generate_performance_recommendations(
        self,
        prediction: Dict[str, Any],
        user_id: str
    ) -> List[str]:
        """Generate simple recommendations based on performance prediction."""
        try:
            prompt = (
                "Provide 5 concise recommendations to improve predicted performance: \n"
                f"{str(prediction)[:2000]}\nReturn a bullet list."
            )
            result = await self.llm_client.generate_text(prompt=prompt, provider="gemini", max_tokens=300)
            lines = [line.strip("- ") for line in result.get("content", "").splitlines() if line.strip()]
            return lines[:5] or ["Refine caption with a strong CTA.", "Test posting at the top predicted time."]
        except Exception:
            return [
                "Refine caption with a strong CTA.",
                "Test posting at the top predicted time.",
                "Reduce number of hashtags to most relevant.",
            ]

    async def generate_campaign_recommendations(
        self,
        prediction: Dict[str, Any],
        user_id: str
    ) -> List[str]:
        """Generate simple recommendations for campaigns."""
        try:
            prompt = (
                "Provide 5 concise campaign recommendations based on this analysis: \n"
                f"{str(prediction)[:2000]}\nReturn a bullet list."
            )
            result = await self.llm_client.generate_text(prompt=prompt, provider="gemini", max_tokens=300)
            lines = [line.strip("- ") for line in result.get("content", "").splitlines() if line.strip()]
            return lines[:5] or ["Allocate budget to top-performing platform.", "Iterate creatives weekly based on metrics."]
        except Exception:
            return [
                "Allocate budget to top-performing platform.",
                "Iterate creatives weekly based on metrics.",
                "Monitor frequency caps to avoid fatigue.",
            ]
    
    # Private helper methods
    
    def _prepare_competitor_context(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare competitor analysis results for RAG context"""
        context_documents = []
        
        for competitor, data in analysis_results.items():
            if isinstance(data, dict):
                context_documents.append({
                    "content": f"Competitor {competitor}: {str(data)}",
                    "metadata": {"type": "competitor_analysis", "competitor": competitor}
                })
        
        return context_documents
    
    def _build_hashtag_query(
        self,
        content: Optional[str],
        content_type: str,
        platform: str,
        target_audience: Optional[str],
        goals: List[str]
    ) -> str:
        """Build query for hashtag generation"""
        query_parts = [
            f"Generate hashtag suggestions for {content_type} content on {platform}",
            f"Content: {content[:200] if content else 'No content provided'}",
            f"Target audience: {target_audience or 'General audience'}",
            f"Goals: {', '.join(goals) if goals else 'General engagement'}"
        ]
        return ". ".join(query_parts)
    
    def _build_caption_query(
        self,
        content: Optional[str],
        content_type: str,
        platform: str,
        tone: str,
        target_audience: Optional[str],
        goals: List[str]
    ) -> str:
        """Build query for caption generation"""
        query_parts = [
            f"Generate caption suggestions for {content_type} content on {platform}",
            f"Tone: {tone}",
            f"Content: {content[:200] if content else 'No content provided'}",
            f"Target audience: {target_audience or 'General audience'}",
            f"Goals: {', '.join(goals) if goals else 'General engagement'}"
        ]
        return ". ".join(query_parts)
    
    async def _retrieve_hashtag_context(
        self,
        content_type: str,
        platform: str,
        target_audience: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for hashtag generation"""
        # This would typically query the vector store for relevant hashtag data
        # For now, return empty list
        return []
    
    async def _retrieve_caption_context(
        self,
        content_type: str,
        platform: str,
        tone: str,
        target_audience: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for caption generation"""
        # This would typically query the vector store for relevant caption data
        return []
    
    async def _retrieve_posting_time_context(
        self,
        platform: str,
        content_type: str,
        target_audience: Optional[str],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for posting time suggestions"""
        # This would typically query the vector store for posting time data
        return []
    
    async def _retrieve_content_ideas_context(
        self,
        content_type: str,
        platform: str,
        target_audience: Optional[str],
        goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for content ideas generation"""
        # This would typically query the vector store for content ideas data
        return []
    
    async def _retrieve_engagement_context(
        self,
        content_type: str,
        platform: str,
        target_audience: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for engagement prediction"""
        # This would typically query the vector store for engagement data
        return []
    
    async def _generate_insights_with_rag(self, rag_context: RAGContext) -> Dict[str, Any]:
        """Generate insights using RAG"""
        # This would implement the actual RAG pipeline
        # For now, return a placeholder
        return {
            "insights": "AI-generated insights based on competitor analysis",
            "tokens_used": 1000
        }
    
    async def _generate_hashtag_suggestions_with_rag(
        self, 
        rag_context: RAGContext, 
        max_suggestions: int
    ) -> Dict[str, Any]:
        """Generate hashtag suggestions using RAG"""
        # This would implement the actual RAG pipeline for hashtags
        return {
            "hashtags": [
                {
                    "hashtag": "#example",
                    "popularity_score": 0.8,
                    "relevance_score": 0.9,
                    "competition_level": "medium",
                    "estimated_reach": 10000,
                    "category": "general"
                }
            ],
            "tokens_used": 500
        }
    
    async def _generate_caption_suggestions_with_rag(
        self, 
        rag_context: RAGContext, 
        max_suggestions: int
    ) -> Dict[str, Any]:
        """Generate caption suggestions using RAG"""
        # This would implement the actual RAG pipeline for captions
        return {
            "captions": [
                {
                    "caption": "Example caption suggestion",
                    "tone": "professional",
                    "length": 50,
                    "engagement_potential": 0.8,
                    "readability_score": 0.9,
                    "emoji_count": 2
                }
            ],
            "tokens_used": 800
        }
    
    async def _generate_posting_time_suggestions_with_rag(
        self, 
        rag_context: RAGContext
    ) -> Dict[str, Any]:
        """Generate posting time suggestions using RAG"""
        # This would implement the actual RAG pipeline for posting times
        return {
            "optimal_times": ["6:00 PM", "8:00 PM"],
            "best_days": ["Tuesday", "Thursday"],
            "frequency": "2-3 times per week",
            "reasoning": "Based on audience activity patterns",
            "tokens_used": 300
        }
    
    async def _generate_content_ideas_with_rag(
        self, 
        rag_context: RAGContext, 
        max_suggestions: int
    ) -> Dict[str, Any]:
        """Generate content ideas using RAG"""
        # This would implement the actual RAG pipeline for content ideas
        return {
            "content_ideas": [
                {
                    "title": "Example Content Idea",
                    "description": "A creative content idea description",
                    "format": "post",
                    "estimated_engagement": 0.7,
                    "difficulty": "medium",
                    "time_to_create": "2-3 hours",
                    "trending_potential": 0.6
                }
            ],
            "tokens_used": 1200
        }
    
    async def _generate_engagement_prediction_with_rag(
        self, 
        rag_context: RAGContext
    ) -> Dict[str, Any]:
        """Generate engagement prediction using RAG"""
        # This would implement the actual RAG pipeline for engagement prediction
        return {
            "predicted_likes": 1000,
            "predicted_comments": 50,
            "predicted_shares": 25,
            "predicted_reach": 5000,
            "confidence_score": 0.8,
            "tokens_used": 400
        }
    
    async def rewrite_content(
        self,
        field: str,
        current_content: str,
        platform: str,
        content_type: str = "post",
        tone: str = "professional",
        goals: List[str] = None,
        max_length: int = 2000,
        user_id: Optional[str] = None
    ) -> str:
        """Rewrite content for a specific field and platform using RAG"""
        try:
            start_time = time.time()
            
            # Prepare query for content rewriting
            query = self._build_rewrite_query(
                field, current_content, platform, content_type, tone, goals, max_length
            )
            
            # Retrieve relevant context from vector store
            context_documents = await self._retrieve_rewrite_context(
                field, platform, content_type, tone, user_id
            )
            
            # Create RAG context
            rag_context = RAGContext(
                user_id=user_id or "anonymous",
                query=query,
                context_documents=context_documents,
                max_tokens=min(max_length * 2, 4000),  # Allow some buffer for generation
                temperature=0.7
            )
            
            # Generate rewritten content using RAG
            rewritten_content = await self._generate_rewrite_with_rag(rag_context, max_length)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_ai_operation(
                operation="content_rewrite",
                model=settings.primary_ai_provider,
                tokens_used=len(rewritten_content.split()) * 1.3,  # Rough estimate
                duration_ms=processing_time,
                success=True
            )
            
            return rewritten_content
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "rewrite_content", "field": field, "platform": platform})
            raise AIServiceException(f"Failed to rewrite content: {str(e)}")
    
    def _build_rewrite_query(
        self,
        field: str,
        current_content: str,
        platform: str,
        content_type: str,
        tone: str,
        goals: List[str],
        max_length: int
    ) -> str:
        """Build query for content rewriting"""
        query_parts = [
            f"Rewrite the {field} for a {content_type} on {platform}",
            f"Current content: {current_content[:300]}",
            f"Tone: {tone}",
            f"Platform: {platform}",
            f"Maximum length: {max_length} characters",
            f"Goals: {', '.join(goals) if goals else 'General engagement'}",
            f"Make it more engaging, platform-appropriate, and aligned with the specified tone"
        ]
        return ". ".join(query_parts)
    
    async def _retrieve_rewrite_context(
        self,
        field: str,
        platform: str,
        content_type: str,
        tone: str,
        user_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for content rewriting"""
        # This would typically query the vector store for relevant content examples
        # For now, return empty list
        return []
    
    async def _generate_rewrite_with_rag(
        self, 
        rag_context: RAGContext,
        max_length: int
    ) -> str:
        """Generate rewritten content using RAG"""
        try:
            # Build the prompt for content rewriting
            prompt = f"""
            You are an expert content writer specializing in social media content creation.
            
            Task: Rewrite the following content to make it more engaging and platform-appropriate.
            
            Original Content: {rag_context.query}
            
            Requirements:
            - Maximum length: {max_length} characters
            - Make it engaging and platform-appropriate
            - Maintain the core message while improving clarity and impact
            - Use appropriate tone and style for the target platform
            - Ensure it follows best practices for the platform
            
            Rewritten Content:
            """
            
            # Generate content using the LLM client
            response = await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=min(max_length * 2, 2000),  # Allow some buffer
                temperature=0.7
            )
            
            # Extract and clean the rewritten content
            rewritten_content = response.content.strip()
            
            # Ensure it doesn't exceed the maximum length
            if len(rewritten_content) > max_length:
                rewritten_content = rewritten_content[:max_length].rsplit(' ', 1)[0] + "..."
            
            return rewritten_content
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_rewrite_with_rag"})
            # Fallback to a simple rewrite if RAG fails
            return self._simple_rewrite_fallback(rag_context.query, max_length)
    
    def _simple_rewrite_fallback(self, content: str, max_length: int) -> str:
        """Simple fallback rewrite when RAG fails"""
        # Basic improvements without AI
        improved = content.strip()
        
        # Add some basic improvements
        if not improved.endswith(('.', '!', '?')):
            improved += '.'
        
        # Ensure it fits within the limit
        if len(improved) > max_length:
            improved = improved[:max_length].rsplit(' ', 1)[0] + "..."
        
        return improved