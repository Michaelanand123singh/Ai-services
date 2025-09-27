"""
Constants for Bloocube AI Service
"""

# API Response Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# Success Messages
SUCCESS_MESSAGES = {
    "ANALYSIS_COMPLETED": "Analysis completed successfully",
    "SUGGESTIONS_GENERATED": "Suggestions generated successfully",
    "MATCHMAKING_COMPLETED": "Matchmaking analysis completed",
    "TRENDS_ANALYZED": "Trend analysis completed",
    "PREDICTION_GENERATED": "Performance prediction generated",
    "EMBEDDINGS_CREATED": "Embeddings created successfully",
    "VECTOR_SEARCH_COMPLETED": "Vector search completed successfully",
    "DATA_SYNCED": "Data synchronized successfully"
}

# Error Messages
ERROR_MESSAGES = {
    "INVALID_INPUT": "Invalid input data provided",
    "AI_SERVICE_ERROR": "AI service encountered an error",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "MODEL_NOT_AVAILABLE": "AI model not available",
    "INSUFFICIENT_DATA": "Insufficient data for analysis",
    "AUTHENTICATION_FAILED": "Authentication failed",
    "PERMISSION_DENIED": "Permission denied",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "VALIDATION_ERROR": "Input validation failed",
    "EXTERNAL_SERVICE_ERROR": "External service error",
    "VECTOR_DATABASE_ERROR": "Vector database error",
    "EMBEDDING_ERROR": "Text embedding error",
    "COMPETITOR_ANALYSIS_ERROR": "Competitor analysis error",
    "CONTENT_SUGGESTION_ERROR": "Content suggestion error",
    "MATCHMAKING_ERROR": "Matchmaking analysis error",
    "TREND_ANALYSIS_ERROR": "Trend analysis error",
    "PERFORMANCE_PREDICTION_ERROR": "Performance prediction error"
}

# Supported Platforms
PLATFORMS = {
    "INSTAGRAM": "instagram",
    "YOUTUBE": "youtube",
    "TWITTER": "twitter",
    "LINKEDIN": "linkedin",
    "FACEBOOK": "facebook",
    "TIKTOK": "tiktok"
}

# Content Types
CONTENT_TYPES = {
    "POST": "post",
    "STORY": "story",
    "REEL": "reel",
    "VIDEO": "video",
    "LIVE": "live",
    "CAROUSEL": "carousel",
    "TWEET": "tweet",
    "THREAD": "thread",
    "ARTICLE": "article"
}

# Analysis Types
ANALYSIS_TYPES = {
    "COMPREHENSIVE": "comprehensive",
    "BASIC": "basic",
    "CONTENT_ONLY": "content_only",
    "ENGAGEMENT_ONLY": "engagement_only",
    "AUDIENCE_ONLY": "audience_only"
}

# Content Tones
CONTENT_TONES = {
    "PROFESSIONAL": "professional",
    "CASUAL": "casual",
    "HUMOROUS": "humorous",
    "INSPIRATIONAL": "inspirational",
    "EDUCATIONAL": "educational",
    "FRIENDLY": "friendly",
    "AUTHORITATIVE": "authoritative"
}

# Content Goals
CONTENT_GOALS = {
    "ENGAGEMENT": "engagement",
    "REACH": "reach",
    "CONVERSION": "conversion",
    "AWARENESS": "awareness",
    "TRAFFIC": "traffic",
    "SALES": "sales",
    "BRAND_AWARENESS": "brand_awareness"
}

# Result Types
RESULT_TYPES = {
    "SUGGESTION": "suggestion",
    "ANALYSIS": "analysis",
    "MATCHMAKING": "matchmaking",
    "COMPETITOR_ANALYSIS": "competitor_analysis",
    "CONTENT_OPTIMIZATION": "content_optimization",
    "TREND_ANALYSIS": "trend_analysis"
}

# Priority Levels
PRIORITY_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical"
}

# Impact Levels
IMPACT_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high"
}

# Competition Levels
COMPETITION_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high"
}

# Difficulty Levels
DIFFICULTY_LEVELS = {
    "EASY": "easy",
    "MEDIUM": "medium",
    "HARD": "hard"
}

# Risk Levels
RISK_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high"
}

# Status Types
STATUS_TYPES = {
    "PROCESSING": "processing",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "EXPIRED": "expired"
}

# Data Sources
DATA_SOURCES = {
    "API": "api",
    "MANUAL": "manual",
    "SCRAPED": "scraped",
    "IMPORTED": "imported"
}

# AI Model Types
AI_MODEL_TYPES = {
    "LLM": "llm",
    "EMBEDDING": "embedding",
    "CLASSIFICATION": "classification",
    "GENERATION": "generation"
}

# Vector Database Types
VECTOR_DB_TYPES = {
    "PINECONE": "pinecone",
    "FAISS": "faiss",
    "CHROMA": "chroma",
    "WEAVIATE": "weaviate"
}

# Cache Keys
CACHE_KEYS = {
    "USER_PROFILE": "user_profile",
    "COMPETITOR_ANALYSIS": "competitor_analysis",
    "CONTENT_SUGGESTIONS": "content_suggestions",
    "HASHTAG_SUGGESTIONS": "hashtag_suggestions",
    "POSTING_TIMES": "posting_times",
    "TRENDING_TOPICS": "trending_topics"
}

# Rate Limiting
RATE_LIMITS = {
    "COMPETITOR_ANALYSIS": 10,  # per minute
    "CONTENT_SUGGESTIONS": 20,  # per minute
    "HASHTAG_SUGGESTIONS": 30,  # per minute
    "POSTING_TIME_SUGGESTIONS": 15,  # per minute
    "CONTENT_IDEAS": 25,  # per minute
    "VECTOR_SEARCH": 100  # per minute
}

# Default Values
DEFAULT_VALUES = {
    "MAX_TOKENS": 4000,
    "TEMPERATURE": 0.7,
    "TOP_P": 0.9,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.0,
    "MAX_CONTENT_LENGTH": 10000,
    "BATCH_SIZE": 32,
    "EMBEDDING_BATCH_SIZE": 100,
    "VECTOR_DIMENSION": 1536,
    "CACHE_TTL": 3600,
    "CACHE_MAX_SIZE": 1000,
    "MAX_COMPETITORS": 20,
    "MAX_PLATFORMS": 5,
    "MAX_POSTS_PER_COMPETITOR": 100,
    "MAX_SUGGESTIONS": 10,
    "MAX_HASHTAGS": 30,
    "MAX_MENTIONS": 20
}

# Time Periods
TIME_PERIODS = {
    "HOUR": 3600,  # seconds
    "DAY": 86400,  # seconds
    "WEEK": 604800,  # seconds
    "MONTH": 2592000,  # seconds
    "YEAR": 31536000  # seconds
}

# Engagement Metrics
ENGAGEMENT_METRICS = {
    "LIKES": "likes",
    "COMMENTS": "comments",
    "SHARES": "shares",
    "SAVES": "saves",
    "VIEWS": "views",
    "REACH": "reach",
    "IMPRESSIONS": "impressions",
    "CLICKS": "clicks"
}

# Performance Indicators
PERFORMANCE_INDICATORS = {
    "IS_VIRAL": "is_viral",
    "IS_TRENDING": "is_trending",
    "GROWTH_RATE": "growth_rate",
    "QUALITY_SCORE": "quality_score"
}

# Content Categories
CONTENT_CATEGORIES = {
    "TECHNOLOGY": "technology",
    "LIFESTYLE": "lifestyle",
    "BUSINESS": "business",
    "EDUCATION": "education",
    "ENTERTAINMENT": "entertainment",
    "HEALTH": "health",
    "FASHION": "fashion",
    "FOOD": "food",
    "TRAVEL": "travel",
    "SPORTS": "sports"
}

# Hashtag Categories
HASHTAG_CATEGORIES = {
    "GENERAL": "general",
    "NICHE": "niche",
    "TRENDING": "trending",
    "BRANDED": "branded",
    "LOCATION": "location",
    "EVENT": "event"
}

# Posting Frequency
POSTING_FREQUENCY = {
    "DAILY": "daily",
    "WEEKLY": "weekly",
    "BI_WEEKLY": "bi_weekly",
    "MONTHLY": "monthly",
    "IRREGULAR": "irregular"
}

# Audience Demographics
AUDIENCE_DEMOGRAPHICS = {
    "AGE_GROUPS": ["13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    "GENDERS": ["male", "female", "other"],
    "LOCATIONS": ["country", "city", "region"]
}

# Content Quality Scores
QUALITY_SCORES = {
    "EXCELLENT": 90,
    "GOOD": 70,
    "FAIR": 50,
    "POOR": 30,
    "VERY_POOR": 10
}

# Engagement Rate Thresholds
ENGAGEMENT_THRESHOLDS = {
    "HIGH": 5.0,
    "MEDIUM": 2.0,
    "LOW": 1.0,
    "VERY_LOW": 0.5
}

# Viral Content Thresholds
VIRAL_THRESHOLDS = {
    "VIEWS_MULTIPLIER": 10,  # 10x average views
    "ENGAGEMENT_MULTIPLIER": 5,  # 5x average engagement
    "SHARE_RATE": 0.1  # 10% share rate
}

# Trending Content Thresholds
TRENDING_THRESHOLDS = {
    "GROWTH_RATE": 0.2,  # 20% growth rate
    "ENGAGEMENT_SPIKE": 2.0,  # 2x normal engagement
    "HASHTAG_VELOCITY": 100  # 100 mentions per hour
}

# API Endpoints
API_ENDPOINTS = {
    "HEALTH": "/health",
    "COMPETITOR_ANALYSIS": "/ai/competitor-analysis",
    "CONTENT_SUGGESTIONS": "/ai/suggestions",
    "HASHTAG_SUGGESTIONS": "/ai/suggestions/hashtags",
    "CAPTION_SUGGESTIONS": "/ai/suggestions/captions",
    "POSTING_TIMES": "/ai/suggestions/posting-times",
    "CONTENT_IDEAS": "/ai/suggestions/content-ideas",
    "METRICS": "/metrics"
}

# Database Collections
DATABASE_COLLECTIONS = {
    "USERS": "users",
    "CAMPAIGNS": "campaigns",
    "BIDS": "bids",
    "ANALYTICS": "analytics",
    "AI_RESULTS": "ai_results",
    "EMBEDDINGS": "embeddings",
    "VECTOR_INDEX": "vector_index"
}

# Log Levels
LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL"
}

# Feature Flags
FEATURE_FLAGS = {
    "ENABLE_COMPETITOR_ANALYSIS": "enable_competitor_analysis",
    "ENABLE_CONTENT_SUGGESTIONS": "enable_content_suggestions",
    "ENABLE_MATCHMAKING": "enable_matchmaking",
    "ENABLE_TREND_ANALYSIS": "enable_trend_analysis",
    "ENABLE_PERFORMANCE_PREDICTION": "enable_performance_prediction",
    "ENABLE_VECTOR_SEARCH": "enable_vector_search",
    "ENABLE_CACHING": "enable_caching"
}
