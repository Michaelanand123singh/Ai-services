"""
Helper utilities for Bloocube AI Service
"""
import re
import hashlib
import time
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
import validators
from src.core.logger import ai_logger


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    
    # Normalize case
    text = text.lower()
    
    return text


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    if not text:
        return []
    
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text)
    
    # Clean hashtags
    cleaned_hashtags = []
    for hashtag in hashtags:
        # Remove # and clean
        clean_hashtag = hashtag[1:].lower()
        if len(clean_hashtag) > 1:  # Avoid single character hashtags
            cleaned_hashtags.append(clean_hashtag)
    
    return cleaned_hashtags


def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text"""
    if not text:
        return []
    
    mention_pattern = r'@\w+'
    mentions = re.findall(mention_pattern, text)
    
    # Clean mentions
    cleaned_mentions = []
    for mention in mentions:
        clean_mention = mention[1:].lower()
        if len(clean_mention) > 1:
            cleaned_mentions.append(clean_mention)
    
    return cleaned_mentions


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    if not text:
        return []
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    return urls


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
    if not text:
        return []
    
    # Clean text
    cleaned_text = clean_text(text)
    
    # Split into words
    words = cleaned_text.split()
    
    # Filter out common words and short words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    keywords = []
    for word in words:
        if len(word) > 2 and word not in stop_words:
            keywords.append(word)
    
    # Return top keywords
    return keywords[:max_keywords]


def calculate_engagement_rate(likes: int, comments: int, shares: int, followers: int) -> float:
    """Calculate engagement rate"""
    if followers == 0:
        return 0.0
    
    total_engagement = likes + comments + shares
    return (total_engagement / followers) * 100


def format_number(num: Union[int, float]) -> str:
    """Format number with K, M, B suffixes"""
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    elif num < 1000000000:
        return f"{num/1000000:.1f}M"
    else:
        return f"{num/1000000000:.1f}B"


def generate_id(prefix: str = "id") -> str:
    """Generate unique ID with prefix"""
    timestamp = int(time.time() * 1000)
    random_suffix = hashlib.md5(f"{timestamp}{prefix}".encode()).hexdigest()[:8]
    return f"{prefix}_{timestamp}_{random_suffix}"


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        return validators.url(url)
    except:
        return False


def validate_email(email: str) -> bool:
    """Validate email format"""
    try:
        return validators.email(email)
    except:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('.')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support"""
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage"""
    if total == 0:
        return 0.0
    return (value / total) * 100


def normalize_score(score: float, min_score: float = 0, max_score: float = 100) -> float:
    """Normalize score to 0-100 range"""
    if score < min_score:
        return 0.0
    elif score > max_score:
        return 100.0
    else:
        return ((score - min_score) / (max_score - min_score)) * 100


def format_timestamp(timestamp: Union[int, float]) -> str:
    """Format timestamp to readable string"""
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
    except:
        return str(timestamp)


def parse_timestamp(timestamp_str: str) -> Optional[float]:
    """Parse timestamp string to float"""
    try:
        # Try different formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                return time.mktime(time.strptime(timestamp_str, fmt))
            except ValueError:
                continue
        
        return None
    except:
        return None


def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate simple similarity score between two texts"""
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(clean_text(text1).split())
    words2 = set(clean_text(text2).split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return None


def is_valid_username(username: str) -> bool:
    """Validate username format"""
    if not username:
        return False
    
    # Username should be 3-30 characters, alphanumeric and underscores only
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))


def clean_username(username: str) -> str:
    """Clean username for safe use"""
    if not username:
        return ""
    
    # Remove @ symbol if present
    username = username.lstrip('@')
    
    # Keep only alphanumeric and underscores
    username = re.sub(r'[^a-zA-Z0-9_]', '', username)
    
    # Limit length
    username = username[:30]
    
    return username.lower()


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes"""
    if not text:
        return 0
    
    word_count = len(text.split())
    return max(1, word_count // words_per_minute)


def extract_emojis(text: str) -> List[str]:
    """Extract emojis from text"""
    if not text:
        return []
    
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F0F5\U0001F200-\U0001F2FF]'
    emojis = re.findall(emoji_pattern, text)
    
    return emojis


def count_emojis(text: str) -> int:
    """Count number of emojis in text"""
    return len(extract_emojis(text))


def remove_emojis(text: str) -> str:
    """Remove emojis from text"""
    if not text:
        return ""
    
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F0F5\U0001F200-\U0001F2FF]'
    return re.sub(emoji_pattern, '', text)


def calculate_text_complexity(text: str) -> Dict[str, Any]:
    """Calculate text complexity metrics"""
    if not text:
        return {"complexity_score": 0, "level": "unknown"}
    
    # Basic metrics
    word_count = len(text.split())
    char_count = len(text)
    sentence_count = len([s for s in text.split('.') if s.strip()])
    
    # Calculate average words per sentence
    avg_words_per_sentence = word_count / max(sentence_count, 1)
    
    # Calculate average characters per word
    avg_chars_per_word = char_count / max(word_count, 1)
    
    # Simple complexity score (0-100)
    complexity_score = min(100, (avg_words_per_sentence * 2) + (avg_chars_per_word * 5))
    
    # Categorize complexity
    if complexity_score < 30:
        level = "simple"
    elif complexity_score < 60:
        level = "moderate"
    else:
        level = "complex"
    
    return {
        "complexity_score": round(complexity_score, 2),
        "level": level,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": round(avg_words_per_sentence, 2),
        "avg_chars_per_word": round(avg_chars_per_word, 2)
    }
