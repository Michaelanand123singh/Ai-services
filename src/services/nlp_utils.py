"""
NLP utilities and text processing service
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import string
from collections import Counter
import nltk
from textblob import TextBlob
import spacy
from src.core.config import settings
from src.core.logger import ai_logger


class NLPService:
    """Natural Language Processing service for text analysis and processing"""
    
    def __init__(self):
        self.logger = ai_logger
        self.nlp = None  # Lazy-loaded
    
    def _load_models(self):
        """Load NLP models"""
        try:
            # Load spaCy model (optional). If unavailable, continue with basic NLP.
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = None
            
            # Download required NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords')
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger')
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "load_nlp_models"})
            # Fallback to basic text processing
            self.nlp = None

    def _ensure_loaded(self):
        """Ensure heavy models are loaded lazily."""
        if self.nlp is None:
            self._load_models()
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Normalize case
        text = text.lower()
        
        return text
    
    def extract_hashtags(self, text: str) -> List[str]:
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
    
    def extract_mentions(self, text: str) -> List[str]:
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
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        if not text:
            return []
        
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        return urls
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if not text:
            return []
        
        self._ensure_loaded()
        if self.nlp:
            doc = self.nlp(text)
            return [token.text for token in doc if not token.is_space]
        else:
            # Fallback to simple tokenization
            return text.split()
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords from tokenized text"""
        try:
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words('english'))
            return [token for token in tokens if token.lower() not in stop_words]
        except:
            # Fallback: basic stopword removal
            basic_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            return [token for token in tokens if token.lower() not in basic_stopwords]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords from text with importance scores"""
        if not text:
            return []
        
        # Clean and tokenize text
        cleaned_text = self.clean_text(text)
        tokens = self.tokenize_text(cleaned_text)
        tokens = self.remove_stopwords(tokens)
        
        # Count word frequency
        word_counts = Counter(tokens)
        
        # Calculate importance scores (simple TF-based scoring)
        total_words = len(tokens)
        keywords = []
        
        for word, count in word_counts.most_common(max_keywords):
            if len(word) > 2:  # Filter out very short words
                importance_score = count / total_words
                keywords.append({
                    "word": word,
                    "count": count,
                    "importance_score": round(importance_score, 4)
                })
        
        return keywords
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not text:
            return {"sentiment": "neutral", "score": 0.0}
        
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Categorize sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "confidence": round(abs(polarity), 3)
            }
        except Exception as e:
            self.logger.log_error(e, {"operation": "analyze_sentiment"})
            return {"sentiment": "neutral", "score": 0.0}
    
    def calculate_readability_score(self, text: str) -> Dict[str, Any]:
        """Calculate readability score using Flesch Reading Ease"""
        if not text:
            return {"score": 0, "level": "unknown"}
        
        try:
            blob = TextBlob(text)
            
            # Count sentences, words, and syllables
            sentences = len(blob.sentences)
            words = len(blob.words)
            
            if sentences == 0 or words == 0:
                return {"score": 0, "level": "unknown"}
            
            # Estimate syllables (simplified)
            syllables = sum(self._count_syllables(word) for word in blob.words)
            
            # Calculate Flesch Reading Ease
            score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
            
            # Categorize readability level
            if score >= 90:
                level = "very_easy"
            elif score >= 80:
                level = "easy"
            elif score >= 70:
                level = "fairly_easy"
            elif score >= 60:
                level = "standard"
            elif score >= 50:
                level = "fairly_difficult"
            elif score >= 30:
                level = "difficult"
            else:
                level = "very_difficult"
            
            return {
                "score": round(score, 2),
                "level": level,
                "sentences": sentences,
                "words": words,
                "syllables": syllables
            }
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_readability_score"})
            return {"score": 0, "level": "unknown"}
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        if not text:
            return []
        self._ensure_loaded()
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "description": spacy.explain(ent.label_)
                })
            
            return entities
        except Exception as e:
            self.logger.log_error(e, {"operation": "extract_entities"})
            return []
    
    def analyze_content_quality(
        self, 
        content: str, 
        content_type: str, 
        platform: str
    ) -> Dict[str, Any]:
        """Analyze content quality and provide suggestions"""
        if not content:
            return {"error": "No content provided"}
        
        # Basic metrics
        word_count = len(content.split())
        char_count = len(content)
        
        # Extract elements
        hashtags = self.extract_hashtags(content)
        mentions = self.extract_mentions(content)
        urls = self.extract_urls(content)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(content)
        
        # Calculate readability
        readability = self.calculate_readability_score(content)
        
        # Extract keywords
        keywords = self.extract_keywords(content, max_keywords=5)
        
        # Platform-specific analysis
        platform_analysis = self._analyze_for_platform(content, content_type, platform)
        
        # Generate suggestions
        suggestions = self._generate_content_suggestions(
            content, content_type, platform, {
                "word_count": word_count,
                "hashtags": len(hashtags),
                "mentions": len(mentions),
                "sentiment": sentiment,
                "readability": readability
            }
        )
        
        return {
            "metrics": {
                "word_count": word_count,
                "char_count": char_count,
                "hashtag_count": len(hashtags),
                "mention_count": len(mentions),
                "url_count": len(urls)
            },
            "elements": {
                "hashtags": hashtags,
                "mentions": mentions,
                "urls": urls,
                "keywords": keywords
            },
            "analysis": {
                "sentiment": sentiment,
                "readability": readability,
                "platform_analysis": platform_analysis
            },
            "suggestions": suggestions
        }
    
    def _analyze_for_platform(self, content: str, content_type: str, platform: str) -> Dict[str, Any]:
        """Analyze content for platform-specific requirements"""
        analysis = {
            "platform": platform,
            "content_type": content_type,
            "recommendations": []
        }
        
        # Platform-specific rules
        if platform == "instagram":
            if len(content) > 2200:
                analysis["recommendations"].append("Content is too long for Instagram (max 2200 characters)")
            if len(self.extract_hashtags(content)) > 30:
                analysis["recommendations"].append("Too many hashtags (max 30 recommended)")
        
        elif platform == "twitter":
            if len(content) > 280:
                analysis["recommendations"].append("Content exceeds Twitter character limit (280 characters)")
        
        elif platform == "linkedin":
            if len(content) < 150:
                analysis["recommendations"].append("Content might be too short for LinkedIn (recommended 150+ characters)")
        
        return analysis
    
    def _generate_content_suggestions(
        self, 
        content: str, 
        content_type: str, 
        platform: str, 
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate content improvement suggestions"""
        suggestions = []
        
        # Word count suggestions
        word_count = metrics["word_count"]
        if word_count < 10:
            suggestions.append("Consider adding more descriptive content")
        elif word_count > 200:
            suggestions.append("Content might be too long for social media")
        
        # Hashtag suggestions
        hashtag_count = metrics["hashtags"]
        if hashtag_count == 0:
            suggestions.append("Consider adding relevant hashtags to increase discoverability")
        elif hashtag_count > 20:
            suggestions.append("Consider reducing hashtag count for better readability")
        
        # Sentiment suggestions
        sentiment = metrics["sentiment"]["sentiment"]
        if sentiment == "negative":
            suggestions.append("Consider adjusting tone to be more positive or neutral")
        
        # Readability suggestions
        readability = metrics["readability"]["level"]
        if readability in ["difficult", "very_difficult"]:
            suggestions.append("Consider simplifying language for better readability")
        
        return suggestions
    
    def extract_hashtags_from_text(self, text: str) -> List[str]:
        """Extract hashtags from text (alias for extract_hashtags)"""
        return self.extract_hashtags(text)
    
    def clean_text_for_analysis(self, text: str) -> str:
        """Clean text for analysis (alias for clean_text)"""
        return self.clean_text(text)
