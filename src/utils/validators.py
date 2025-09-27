"""
Validation utilities for Bloocube AI Service
"""
from typing import Any, Dict, List, Optional, Union
import re
from src.core.exceptions import ValidationError


def validate_user_id(user_id: str) -> bool:
    """Validate user ID format"""
    if not user_id or not isinstance(user_id, str):
        raise ValidationError("user_id", user_id, "User ID must be a non-empty string")
    
    if len(user_id) < 3 or len(user_id) > 50:
        raise ValidationError("user_id", user_id, "User ID must be between 3 and 50 characters")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise ValidationError("user_id", user_id, "User ID can only contain alphanumeric characters, underscores, and hyphens")
    
    return True


def validate_campaign_id(campaign_id: str) -> bool:
    """Validate campaign ID format"""
    if not campaign_id or not isinstance(campaign_id, str):
        raise ValidationError("campaign_id", campaign_id, "Campaign ID must be a non-empty string")
    
    if len(campaign_id) < 3 or len(campaign_id) > 50:
        raise ValidationError("campaign_id", campaign_id, "Campaign ID must be between 3 and 50 characters")
    
    return True


def validate_platform(platform: str) -> bool:
    """Validate social media platform"""
    valid_platforms = ["instagram", "youtube", "twitter", "linkedin", "facebook", "tiktok"]
    
    if not platform or not isinstance(platform, str):
        raise ValidationError("platform", platform, "Platform must be a non-empty string")
    
    if platform.lower() not in valid_platforms:
        raise ValidationError("platform", platform, f"Platform must be one of: {', '.join(valid_platforms)}")
    
    return True


def validate_platforms(platforms: List[str]) -> bool:
    """Validate list of social media platforms"""
    if not platforms or not isinstance(platforms, list):
        raise ValidationError("platforms", platforms, "Platforms must be a non-empty list")
    
    if len(platforms) == 0:
        raise ValidationError("platforms", platforms, "At least one platform must be specified")
    
    for platform in platforms:
        validate_platform(platform)
    
    return True


def validate_competitors(competitors: List[str]) -> bool:
    """Validate list of competitor usernames"""
    if not competitors or not isinstance(competitors, list):
        raise ValidationError("competitors", competitors, "Competitors must be a non-empty list")
    
    if len(competitors) == 0:
        raise ValidationError("competitors", competitors, "At least one competitor must be specified")
    
    if len(competitors) > 20:
        raise ValidationError("competitors", competitors, "Maximum 20 competitors allowed per analysis")
    
    for competitor in competitors:
        if not competitor or not isinstance(competitor, str):
            raise ValidationError("competitors", competitors, "Each competitor must be a non-empty string")
        
        if len(competitor) < 1 or len(competitor) > 50:
            raise ValidationError("competitors", competitors, "Each competitor username must be between 1 and 50 characters")
    
    return True


def validate_content_type(content_type: str) -> bool:
    """Validate content type"""
    valid_types = ["post", "story", "reel", "video", "live", "carousel", "tweet", "thread", "article"]
    
    if not content_type or not isinstance(content_type, str):
        raise ValidationError("content_type", content_type, "Content type must be a non-empty string")
    
    if content_type.lower() not in valid_types:
        raise ValidationError("content_type", content_type, f"Content type must be one of: {', '.join(valid_types)}")
    
    return True


def validate_analysis_type(analysis_type: str) -> bool:
    """Validate analysis type"""
    valid_types = ["comprehensive", "basic", "content_only", "engagement_only", "audience_only"]
    
    if not analysis_type or not isinstance(analysis_type, str):
        raise ValidationError("analysis_type", analysis_type, "Analysis type must be a non-empty string")
    
    if analysis_type.lower() not in valid_types:
        raise ValidationError("analysis_type", analysis_type, f"Analysis type must be one of: {', '.join(valid_types)}")
    
    return True


def validate_time_period(days: int) -> bool:
    """Validate time period in days"""
    if not isinstance(days, int):
        raise ValidationError("time_period_days", days, "Time period must be an integer")
    
    if days <= 0 or days > 365:
        raise ValidationError("time_period_days", days, "Time period must be between 1 and 365 days")
    
    return True


def validate_max_posts(max_posts: int) -> bool:
    """Validate maximum posts per competitor"""
    if not isinstance(max_posts, int):
        raise ValidationError("max_posts_per_competitor", max_posts, "Max posts must be an integer")
    
    if max_posts <= 0 or max_posts > 1000:
        raise ValidationError("max_posts_per_competitor", max_posts, "Max posts must be between 1 and 1000")
    
    return True


def validate_max_suggestions(max_suggestions: int) -> bool:
    """Validate maximum suggestions"""
    if not isinstance(max_suggestions, int):
        raise ValidationError("max_suggestions", max_suggestions, "Max suggestions must be an integer")
    
    if max_suggestions <= 0 or max_suggestions > 50:
        raise ValidationError("max_suggestions", max_suggestions, "Max suggestions must be between 1 and 50")
    
    return True


def validate_tone(tone: str) -> bool:
    """Validate content tone"""
    valid_tones = ["professional", "casual", "humorous", "inspirational", "educational", "friendly", "authoritative"]
    
    if not tone or not isinstance(tone, str):
        raise ValidationError("tone", tone, "Tone must be a non-empty string")
    
    if tone.lower() not in valid_tones:
        raise ValidationError("tone", tone, f"Tone must be one of: {', '.join(valid_tones)}")
    
    return True


def validate_goals(goals: List[str]) -> bool:
    """Validate content goals"""
    valid_goals = ["engagement", "reach", "conversion", "awareness", "traffic", "sales", "brand_awareness"]
    
    if not goals or not isinstance(goals, list):
        raise ValidationError("goals", goals, "Goals must be a non-empty list")
    
    for goal in goals:
        if not goal or not isinstance(goal, str):
            raise ValidationError("goals", goals, "Each goal must be a non-empty string")
        
        if goal.lower() not in valid_goals:
            raise ValidationError("goals", goals, f"Each goal must be one of: {', '.join(valid_goals)}")
    
    return True


def validate_text_content(text: str, max_length: int = 10000) -> bool:
    """Validate text content"""
    if text is None:
        return True  # Optional field
    
    if not isinstance(text, str):
        raise ValidationError("text", text, "Text content must be a string")
    
    if len(text) > max_length:
        raise ValidationError("text", text, f"Text content must be no more than {max_length} characters")
    
    return True


def validate_hashtags(hashtags: List[str]) -> bool:
    """Validate hashtag list"""
    if not hashtags or not isinstance(hashtags, list):
        raise ValidationError("hashtags", hashtags, "Hashtags must be a list")
    
    if len(hashtags) > 30:
        raise ValidationError("hashtags", hashtags, "Maximum 30 hashtags allowed")
    
    for hashtag in hashtags:
        if not isinstance(hashtag, str):
            raise ValidationError("hashtags", hashtags, "Each hashtag must be a string")
        
        if not hashtag.startswith('#'):
            raise ValidationError("hashtags", hashtags, "Each hashtag must start with #")
        
        if len(hashtag) < 2 or len(hashtag) > 50:
            raise ValidationError("hashtags", hashtags, "Each hashtag must be between 2 and 50 characters")
    
    return True


def validate_mentions(mentions: List[str]) -> bool:
    """Validate mention list"""
    if not mentions or not isinstance(mentions, list):
        raise ValidationError("mentions", mentions, "Mentions must be a list")
    
    if len(mentions) > 20:
        raise ValidationError("mentions", mentions, "Maximum 20 mentions allowed")
    
    for mention in mentions:
        if not isinstance(mention, str):
            raise ValidationError("mentions", mentions, "Each mention must be a string")
        
        if not mention.startswith('@'):
            raise ValidationError("mentions", mentions, "Each mention must start with @")
        
        if len(mention) < 2 or len(mention) > 50:
            raise ValidationError("mentions", mentions, "Each mention must be between 2 and 50 characters")
    
    return True


def validate_pagination(limit: int, offset: int) -> bool:
    """Validate pagination parameters"""
    if not isinstance(limit, int) or limit <= 0 or limit > 100:
        raise ValidationError("limit", limit, "Limit must be between 1 and 100")
    
    if not isinstance(offset, int) or offset < 0:
        raise ValidationError("offset", offset, "Offset must be a non-negative integer")
    
    return True


def validate_competitor_analysis_request(data: Dict[str, Any]) -> bool:
    """Validate competitor analysis request"""
    required_fields = ["user_id", "competitors", "platforms"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_competitors(data["competitors"])
    validate_platforms(data["platforms"])
    
    # Optional fields
    if "campaign_id" in data and data["campaign_id"]:
        validate_campaign_id(data["campaign_id"])
    
    if "analysis_type" in data:
        validate_analysis_type(data["analysis_type"])
    
    if "time_period_days" in data:
        validate_time_period(data["time_period_days"])
    
    if "max_posts_per_competitor" in data:
        validate_max_posts(data["max_posts_per_competitor"])
    
    return True


def validate_content_suggestion_request(data: Dict[str, Any]) -> bool:
    """Validate content suggestion request"""
    required_fields = ["user_id", "content_type", "platform"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_content_type(data["content_type"])
    validate_platform(data["platform"])
    
    # Optional fields
    if "campaign_id" in data and data["campaign_id"]:
        validate_campaign_id(data["campaign_id"])
    
    if "tone" in data:
        validate_tone(data["tone"])
    
    if "goals" in data:
        validate_goals(data["goals"])
    
    if "max_suggestions" in data:
        validate_max_suggestions(data["max_suggestions"])
    
    if "content" in data:
        validate_text_content(data["content"])
    
    return True


def validate_hashtag_suggestion_request(data: Dict[str, Any]) -> bool:
    """Validate hashtag suggestion request"""
    required_fields = ["user_id", "content_type", "platform"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_content_type(data["content_type"])
    validate_platform(data["platform"])
    
    # Optional fields
    if "max_suggestions" in data:
        validate_max_suggestions(data["max_suggestions"])
    
    if "content" in data:
        validate_text_content(data["content"])
    
    return True


def validate_caption_suggestion_request(data: Dict[str, Any]) -> bool:
    """Validate caption suggestion request"""
    required_fields = ["user_id", "content_type", "platform"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_content_type(data["content_type"])
    validate_platform(data["platform"])
    
    # Optional fields
    if "tone" in data:
        validate_tone(data["tone"])
    
    if "max_suggestions" in data:
        validate_max_suggestions(data["max_suggestions"])
    
    if "content" in data:
        validate_text_content(data["content"])
    
    return True


def validate_posting_time_request(data: Dict[str, Any]) -> bool:
    """Validate posting time suggestion request"""
    required_fields = ["user_id", "platform", "content_type"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_platform(data["platform"])
    validate_content_type(data["content_type"])
    
    return True


def validate_content_ideas_request(data: Dict[str, Any]) -> bool:
    """Validate content ideas request"""
    required_fields = ["user_id", "content_type", "platform"]
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(field, None, f"Required field '{field}' is missing")
    
    validate_user_id(data["user_id"])
    validate_content_type(data["content_type"])
    validate_platform(data["platform"])
    
    # Optional fields
    if "goals" in data:
        validate_goals(data["goals"])
    
    if "tone" in data:
        validate_tone(data["tone"])
    
    if "max_suggestions" in data:
        validate_max_suggestions(data["max_suggestions"])
    
    return True
