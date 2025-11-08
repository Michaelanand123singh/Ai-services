"""
AI-powered content scoring API endpoints
Provides real-time scoring for titles, descriptions, and other content fields
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_api_request, log_api_response
from src.core.exceptions import (
    AIServiceException,
    ValidationError
)
from src.services.nlp_utils import NLPService
from src.models.multi_llm_client import MultiLLMClient

router = APIRouter(prefix="/ai/score", tags=["score"])

# Valid platforms and content types
VALID_PLATFORMS = {
    "twitter", "instagram", "linkedin", "facebook", "youtube"
}

VALID_FIELDS = {
    "title", "description", "caption", "content", "text", "body"
}

# Initialize services
nlp_service = NLPService()
llm_client = MultiLLMClient()


class ContentScoreRequest(BaseModel):
    """Request model for content scoring"""
    content: str = Field(..., description="Content to score")
    field: str = Field(..., description="Field type (title, description, caption, etc.)")
    platform: str = Field(..., description="Platform (youtube, instagram, twitter, etc.)")
    content_type: Optional[str] = Field(default="post", description="Content type (post, video, article, etc.)")


class ContentScoreResponse(BaseModel):
    """Response model for content scoring"""
    score: float = Field(..., description="Overall quality score (0-100)")
    field: str = Field(..., description="Field type that was scored")
    platform: str = Field(..., description="Platform the content is for")
    metrics: Dict[str, Any] = Field(..., description="Detailed metrics")
    strengths: list[str] = Field(default_factory=list, description="Content strengths")
    improvements: list[str] = Field(default_factory=list, description="Suggested improvements")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


def normalize_platform(name: str) -> str:
    """Normalize platform name"""
    v = (name or "").strip().lower()
    aliases = {"x": "twitter"}
    return aliases.get(v, v)


def normalize_field(field: str) -> str:
    """Normalize field name"""
    v = (field or "").strip().lower()
    field_map = {
        "text": "content",
        "body": "content"
    }
    return field_map.get(v, v)


async def calculate_ai_score(
    content: str,
    field: str,
    platform: str,
    content_type: str = "post"
) -> Dict[str, Any]:
    """
    Calculate comprehensive AI score for content using multiple factors
    """
    if not content or not content.strip():
        return {
            "score": 0,
            "metrics": {},
            "strengths": [],
            "improvements": ["Content is empty"]
        }
    
    # Basic metrics
    word_count = len(content.split())
    char_count = len(content)
    
    # Extract elements
    hashtags = nlp_service.extract_hashtags(content)
    mentions = nlp_service.extract_mentions(content)
    urls = nlp_service.extract_urls(content)
    
    # Analyze sentiment
    sentiment = nlp_service.analyze_sentiment(content)
    
    # Calculate readability
    readability = nlp_service.calculate_readability_score(content)
    readability_score = readability.get('score', 0.5) if isinstance(readability, dict) else 0.5
    
    # Extract keywords
    keywords = nlp_service.extract_keywords(content, max_keywords=10)
    
    # Platform-specific scoring
    platform_score = _calculate_platform_score(content, field, platform, {
        "word_count": word_count,
        "char_count": char_count,
        "hashtag_count": len(hashtags),
        "mention_count": len(mentions),
        "url_count": len(urls),
        "readability": readability_score,
        "sentiment": sentiment
    })
    
    # Use LLM for advanced scoring and feedback
    llm_score_data = await _get_llm_score(content, field, platform, content_type)
    
    # Combine scores (weighted average)
    # Platform-specific: 30%, Readability: 20%, LLM analysis: 50%
    final_score = (
        platform_score * 0.3 +
        readability_score * 100 * 0.2 +
        llm_score_data.get("score", 50) * 0.5
    )
    
    # Clamp score between 0 and 100
    final_score = max(0, min(100, final_score))
    
    # Combine strengths and improvements
    strengths = llm_score_data.get("strengths", [])
    improvements = llm_score_data.get("improvements", [])
    
    # Add platform-specific feedback
    platform_feedback = _get_platform_feedback(content, field, platform, {
        "word_count": word_count,
        "char_count": char_count,
        "hashtag_count": len(hashtags)
    })
    
    if platform_feedback.get("strengths"):
        strengths.extend(platform_feedback["strengths"])
    if platform_feedback.get("improvements"):
        improvements.extend(platform_feedback["improvements"])
    
    return {
        "score": round(final_score, 1),
        "metrics": {
            "word_count": word_count,
            "char_count": char_count,
            "hashtag_count": len(hashtags),
            "mention_count": len(mentions),
            "url_count": len(urls),
            "readability_score": round(readability_score * 100, 1),
            "sentiment": sentiment.get("label", "neutral") if isinstance(sentiment, dict) else "neutral",
            "sentiment_score": sentiment.get("score", 0) if isinstance(sentiment, dict) else 0,
            "keyword_count": len(keywords),
            "platform_score": round(platform_score, 1)
        },
        "strengths": strengths[:5],  # Limit to top 5
        "improvements": improvements[:5]  # Limit to top 5
    }


def _calculate_platform_score(
    content: str,
    field: str,
    platform: str,
    metrics: Dict[str, Any]
) -> float:
    """Calculate platform-specific score (0-100)"""
    score = 50.0  # Base score
    
    # Length scoring based on platform and field
    char_count = metrics["char_count"]
    word_count = metrics["word_count"]
    
    if platform == "youtube":
        if field == "title":
            # YouTube titles: optimal 50-60 chars, good 40-70
            if 40 <= char_count <= 70:
                score += 30
            elif 30 <= char_count < 40 or 70 < char_count <= 100:
                score += 15
            elif char_count < 30:
                score -= 20
            else:
                score -= 30
        elif field == "description":
            # YouTube descriptions: longer is generally better (up to 5000)
            if char_count >= 200:
                score += 20
            elif char_count >= 100:
                score += 10
            elif char_count < 50:
                score -= 15
    
    elif platform == "instagram":
        if field in ["caption", "content"]:
            # Instagram captions: 125-150 chars optimal for engagement
            if 125 <= char_count <= 150:
                score += 25
            elif 100 <= char_count < 125 or 150 < char_count <= 2200:
                score += 10
            elif char_count < 50:
                score -= 10
    
    elif platform == "twitter":
        if field in ["content", "text"]:
            # Twitter: optimal 71-100 chars
            if 71 <= char_count <= 100:
                score += 30
            elif 50 <= char_count < 71 or 100 < char_count <= 280:
                score += 15
            elif char_count < 20:
                score -= 20
    
    elif platform == "linkedin":
        if field in ["content", "text"]:
            # LinkedIn: 150+ chars recommended
            if char_count >= 150:
                score += 20
            elif char_count >= 100:
                score += 10
            elif char_count < 50:
                score -= 15
    
    # Hashtag scoring
    hashtag_count = metrics["hashtag_count"]
    if platform == "instagram":
        if 5 <= hashtag_count <= 10:
            score += 10
        elif hashtag_count > 30:
            score -= 10
    elif platform == "twitter":
        if 1 <= hashtag_count <= 2:
            score += 5
        elif hashtag_count > 5:
            score -= 5
    
    # Readability bonus
    readability = metrics.get("readability", 0.5)
    if readability > 0.7:
        score += 10
    elif readability < 0.4:
        score -= 10
    
    return max(0, min(100, score))


async def _get_llm_score(
    content: str,
    field: str,
    platform: str,
    content_type: str
) -> Dict[str, Any]:
    """Get AI-powered score and feedback using LLM"""
    try:
        system_prompt = """You are an expert content quality analyzer. Always respond with valid JSON only, no additional text or markdown formatting."""
        
        prompt = f"""Analyze this {field} for a {platform} {content_type} and provide a quality assessment.

Content to analyze: "{content}"

You must respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just pure JSON):
{{
    "score": 75,
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"]
}}

Requirements:
- score: A number between 0-100 representing overall quality
- strengths: Array of exactly 3 specific strengths
- improvements: Array of exactly 3 specific areas for improvement

Evaluation criteria:
- Clarity and engagement
- Platform best practices for {platform}
- SEO potential (especially for titles/descriptions)
- Call-to-action effectiveness
- Emotional appeal and tone
- Length appropriateness for {platform}

Respond with JSON only:"""
        
        llm_response = await llm_client.generate_text(
            prompt=prompt,
            max_tokens=400,
            temperature=0.2,
            system_prompt=system_prompt
        )
        
        # Extract content from AIResponse object
        response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        
        # Parse JSON response
        import json
        import re
        
        # Try to find JSON in the response - handle markdown code blocks and plain JSON
        # First, try to find JSON in markdown code blocks
        data = None
        
        # Method 1: Try to extract from markdown code blocks
        # Improved pattern to handle multiline JSON in code blocks
        code_block_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON code block
            r'```\s*(\{.*?\})\s*```',  # Generic code block
        ]
        for pattern in code_block_patterns:
            code_match = re.search(pattern, response_text, re.DOTALL)
            if code_match:
                try:
                    json_str = code_match.group(1).strip()
                    data = json.loads(json_str)
                    break
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # Method 2: Try to find JSON object in the text (handles nested objects)
        if data is None:
            # Find the first { and try to match balanced braces
            start_idx = response_text.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    try:
                        json_str = response_text[start_idx:end_idx]
                        data = json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        # Method 3: Try parsing the entire cleaned response
        if data is None:
            try:
                cleaned = response_text.strip()
                # Remove markdown code block markers
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
                cleaned = cleaned.strip()
                data = json.loads(cleaned)
            except (json.JSONDecodeError, ValueError):
                pass
        
        if data and isinstance(data, dict):
            return {
                "score": float(data.get("score", 50)),
                "strengths": data.get("strengths", [])[:3] if isinstance(data.get("strengths"), list) else [],
                "improvements": data.get("improvements", [])[:3] if isinstance(data.get("improvements"), list) else []
            }
        
        # Fallback if JSON parsing fails
        return {
            "score": 50,
            "strengths": ["Content is readable"],
            "improvements": ["Could be more engaging"]
        }
        
    except Exception as e:
        ai_logger.logger.warning(f"LLM scoring failed: {e}")
        # Return neutral score on error
        return {
            "score": 50,
            "strengths": [],
            "improvements": []
        }


def _get_platform_feedback(
    content: str,
    field: str,
    platform: str,
    metrics: Dict[str, Any]
) -> Dict[str, list]:
    """Get platform-specific feedback"""
    strengths = []
    improvements = []
    
    char_count = metrics["char_count"]
    word_count = metrics["word_count"]
    hashtag_count = metrics["hashtag_count"]
    
    if platform == "youtube":
        if field == "title":
            if 40 <= char_count <= 70:
                strengths.append("Optimal title length for YouTube")
            elif char_count < 40:
                improvements.append("Title is too short - aim for 40-70 characters")
            elif char_count > 100:
                improvements.append("Title exceeds 100 characters - may be truncated")
            
            # Check for power words
            power_words = ["ultimate", "complete", "best", "top", "how to", "guide", "tutorial", "review"]
            if any(word in content.lower() for word in power_words):
                strengths.append("Contains engaging power words")
            else:
                improvements.append("Consider adding power words to increase click-through rate")
        
        elif field == "description":
            if char_count >= 200:
                strengths.append("Good description length for SEO")
            elif char_count < 100:
                improvements.append("Description is too short - add more details for better SEO")
    
    elif platform == "instagram":
        if field in ["caption", "content"]:
            if 125 <= char_count <= 150:
                strengths.append("Optimal caption length for engagement")
            if 5 <= hashtag_count <= 10:
                strengths.append("Good hashtag count")
            elif hashtag_count > 30:
                improvements.append("Too many hashtags - Instagram recommends 5-10")
    
    elif platform == "twitter":
        if field in ["content", "text"]:
            if 71 <= char_count <= 100:
                strengths.append("Optimal tweet length for engagement")
            if hashtag_count <= 2:
                strengths.append("Appropriate hashtag usage")
    
    return {
        "strengths": strengths,
        "improvements": improvements
    }


@router.post("/", response_model=ContentScoreResponse)
async def score_content(request: ContentScoreRequest):
    """
    Score content quality for a specific field and platform
    Returns a score from 0-100 with detailed metrics and feedback
    """
    start_time = time.time()
    
    try:
        # Log the request
        log_api_request("/ai/score", "POST")
        
        # Validate and normalize inputs
        platform = normalize_platform(request.platform)
        field = normalize_field(request.field)
        
        if platform not in VALID_PLATFORMS:
            raise ValidationError(f"Invalid platform: {request.platform}")
        
        if field not in VALID_FIELDS:
            raise ValidationError(f"Invalid field: {request.field}")
        
        if not request.content or not request.content.strip():
            return ContentScoreResponse(
                score=0,
                field=field,
                platform=platform,
                metrics={},
                strengths=[],
                improvements=["Content is empty"],
                processing_time_ms=0
            )
        
        # Calculate score
        score_data = await calculate_ai_score(
            request.content,
            field,
            platform,
            request.content_type or "post"
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = ContentScoreResponse(
            score=score_data["score"],
            field=field,
            platform=platform,
            metrics=score_data["metrics"],
            strengths=score_data["strengths"],
            improvements=score_data["improvements"],
            processing_time_ms=processing_time
        )
        
        # Log the response
        log_api_response("/ai/score", "POST", 200, processing_time)
        
        return response
        
    except ValidationError as e:
        ai_logger.log_error(e, {"operation": "content_scoring", "error_type": "validation"})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        ai_logger.log_error(e, {"operation": "content_scoring"})
        raise HTTPException(status_code=500, detail="Internal server error")

