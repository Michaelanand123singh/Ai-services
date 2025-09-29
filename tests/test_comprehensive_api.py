"""
Comprehensive test suite for AI Services API endpoints
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.api.matchmaking import MatchmakingRequest, BrandProfile, CreatorProfile
from src.api.trends import TrendAnalysisRequest
from src.api.predictions import ContentPredictionRequest, CampaignPredictionRequest
from src.api.suggestions import ContentSuggestionRequest


class TestMatchmakingAPI:
    """Test suite for matchmaking API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
        self.brand_profile = BrandProfile(
            brand_id="brand_123",
            name="Test Brand",
            industry="Technology",
            target_audience=["18-34", "tech enthusiasts"],
            content_preferences=["educational", "entertaining"],
            budget_range="medium",
            campaign_goals=["brand awareness", "engagement"],
            brand_values=["innovation", "quality"],
            preferred_content_types=["video", "posts"],
            social_media_presence={"instagram": True, "youtube": True}
        )
    
    def test_match_brand_creator_success(self):
        """Test successful brand-creator matching"""
        request_data = {
            "brand_profile": self.brand_profile.__dict__,
            "max_matches": 5,
            "min_compatibility_score": 0.6,
            "platforms": ["instagram", "youtube"]
        }
        
        with patch('src.api.matchmaking.MatchmakingService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            # Mock the service response
            mock_instance.find_compatible_creators.return_value = [
                {
                    "creator_profile": {
                        "creator_id": "creator_1",
                        "username": "test_creator",
                        "platforms": ["instagram", "youtube"],
                        "follower_count": {"instagram": 50000, "youtube": 25000},
                        "engagement_rate": {"instagram": 0.05, "youtube": 0.03},
                        "content_categories": ["tech", "lifestyle"],
                        "audience_demographics": {"age_range": "18-34", "gender": "mixed"},
                        "content_style": "professional",
                        "collaboration_history": [],
                        "availability": "available",
                        "rates": {"instagram": 2000, "youtube": 4000}
                    },
                    "compatibility_score": {
                        "overall_score": 0.8,
                        "audience_alignment": 0.9,
                        "content_style_match": 0.7,
                        "platform_reach": 0.8,
                        "engagement_potential": 0.6,
                        "budget_fit": 0.8,
                        "brand_values_alignment": 0.7,
                        "collaboration_history_score": 0.5
                    },
                    "match_reasons": ["High audience alignment", "Good engagement rates"],
                    "potential_campaign_ideas": ["Tech tutorial series", "Product showcase"],
                    "estimated_performance": {
                        "estimated_reach": 40000,
                        "estimated_engagement": 2000,
                        "estimated_clicks": 800,
                        "estimated_conversions": 40
                    },
                    "recommended_budget": 2400.0,
                    "risk_assessment": "Low risk - High compatibility"
                }
            ]
            
            response = self.client.post("/ai/matchmaking/brand-creator", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "matchmaking_id" in data
            assert "matches" in data
            assert len(data["matches"]) == 1
            assert data["matches"][0]["compatibility_score"]["overall_score"] == 0.8
    
    def test_match_brand_creator_validation_error(self):
        """Test brand-creator matching with validation error"""
        request_data = {
            "brand_profile": self.brand_profile.__dict__,
            "max_matches": 0,  # Invalid value
            "min_compatibility_score": 0.6
        }
        
        response = self.client.post("/ai/matchmaking/brand-creator", json=request_data)
        
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_get_compatibility_score_success(self):
        """Test successful compatibility score retrieval"""
        with patch('src.api.matchmaking.MatchmakingService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.analyze_compatibility.return_value = {
                "compatibility_score": {
                    "overall_score": 0.75,
                    "audience_alignment": 0.8,
                    "content_style_match": 0.7,
                    "platform_reach": 0.8,
                    "engagement_potential": 0.6,
                    "budget_fit": 0.8,
                    "brand_values_alignment": 0.7,
                    "collaboration_history_score": 0.5
                },
                "detailed_analysis": {
                    "audience_overlap": "High overlap in target demographics",
                    "content_synergy": "Strong alignment in content preferences"
                },
                "recommendations": ["Consider targeting different audience segments"]
            }
            
            response = self.client.get("/ai/matchmaking/compatibility/brand_123/creator_456")
            
            assert response.status_code == 200
            data = response.json()
            assert "compatibility_score" in data
            assert data["compatibility_score"]["overall_score"] == 0.75
    
    def test_get_trending_creators_success(self):
        """Test successful trending creators retrieval"""
        with patch('src.api.matchmaking.MatchmakingService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.get_trending_creators.return_value = [
                {
                    "creator_id": "creator_1",
                    "username": "trending_creator_1",
                    "platforms": ["instagram", "youtube"],
                    "follower_count": {"instagram": 100000, "youtube": 50000},
                    "engagement_rate": {"instagram": 0.05, "youtube": 0.03},
                    "content_categories": ["lifestyle", "fashion"],
                    "trend_score": 0.8,
                    "growth_rate": 0.15,
                    "recent_performance": {
                        "avg_views": 100000,
                        "avg_engagement": 5000,
                        "viral_posts": 2
                    }
                }
            ]
            
            response = self.client.get("/ai/matchmaking/trending-creators?platform=instagram&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "trending_creators" in data
            assert len(data["trending_creators"]) == 1


class TestTrendAnalysisAPI:
    """Test suite for trend analysis API endpoints"""
    
    def test_analyze_trends_success(self):
        """Test successful trend analysis"""
        request_data = {
            "user_id": "user_123",
            "platforms": ["instagram", "youtube"],
            "categories": ["tech", "lifestyle"],
            "time_period_days": 7,
            "analysis_type": "comprehensive",
            "include_competitor_trends": True,
            "include_audience_trends": True,
            "include_content_trends": True
        }
        
        with patch('src.api.trends.TrendAnalysisService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.analyze_trends.return_value = {
                "trending_hashtags": [
                    {
                        "hashtag": "#tech",
                        "current_volume": 10000,
                        "growth_rate": 0.15,
                        "engagement_rate": 0.05,
                        "competition_level": "medium",
                        "trend_direction": "rising",
                        "peak_time": "18:00-20:00",
                        "related_hashtags": ["#technology", "#innovation"],
                        "platform": "instagram"
                    }
                ],
                "trending_content": [
                    {
                        "content_type": "video",
                        "topic": "tech",
                        "engagement_score": 0.7,
                        "viral_potential": 0.6,
                        "competition_level": "medium",
                        "optimal_posting_time": "19:00-21:00",
                        "target_audience": ["18-34"],
                        "platform": "instagram",
                        "examples": ["Tech tutorial video"]
                    }
                ],
                "audience_trends": [
                    {
                        "demographic": "18-24",
                        "interest_categories": ["tech", "gaming"],
                        "engagement_patterns": {
                            "peak_hours": "18:00-22:00",
                            "peak_days": ["Friday", "Saturday"],
                            "avg_session_duration": 15
                        },
                        "growth_trend": "increasing",
                        "platform_preferences": {"instagram": 0.4, "youtube": 0.3},
                        "content_preferences": ["video", "image"]
                    }
                ],
                "competitor_insights": {
                    "top_performing_content": ["video", "story"],
                    "trending_hashtags": ["#competitor1", "#competitor2"],
                    "audience_growth": 0.15,
                    "engagement_trends": {"instagram": 0.05, "youtube": 0.03}
                }
            }
            
            response = self.client.post("/ai/trends/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert "trending_hashtags" in data
            assert "trending_content" in data
            assert "audience_trends" in data
            assert "competitor_insights" in data
    
    def test_analyze_hashtag_trend_success(self):
        """Test successful hashtag trend analysis"""
        request_data = {
            "hashtag": "#tech",
            "platform": "instagram",
            "time_period_days": 7,
            "include_related": True
        }
        
        with patch('src.api.trends.TrendAnalysisService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.analyze_hashtag_trend.return_value = {
                "trend_data": {
                    "volume": 10000,
                    "growth_rate": 0.15,
                    "engagement_rate": 0.05,
                    "competition_level": "medium",
                    "trend_direction": "rising",
                    "peak_time": "18:00-20:00",
                    "related_hashtags": ["#technology", "#innovation"]
                },
                "related_hashtags": ["#technology", "#innovation", "#AI"],
                "optimal_posting_times": ["18:00-20:00", "12:00-14:00"],
                "engagement_predictions": {
                    "likes": 0.05,
                    "comments": 0.01,
                    "shares": 0.005,
                    "saves": 0.002
                }
            }
            
            response = self.client.post("/ai/trends/hashtag", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "hashtag" in data
            assert data["hashtag"] == "#tech"
            assert "trend_data" in data
            assert "related_hashtags" in data
    
    def test_get_trending_hashtags_success(self):
        """Test successful trending hashtags retrieval"""
        with patch('src.api.trends.TrendAnalysisService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.get_trending_hashtags.return_value = [
                {
                    "hashtag": "#fashion",
                    "current_volume": 10000,
                    "growth_rate": 0.1,
                    "engagement_rate": 0.05,
                    "competition_level": "medium",
                    "trend_direction": "rising",
                    "peak_time": "18:00-20:00",
                    "related_hashtags": ["#style", "#outfit"],
                    "platform": "instagram"
                }
            ]
            
            response = self.client.get("/ai/trends/trending-hashtags?platform=instagram&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "trending_hashtags" in data
            assert len(data["trending_hashtags"]) == 1


class TestPerformancePredictionAPI:
    """Test suite for performance prediction API endpoints"""
    
    def test_predict_content_performance_success(self):
        """Test successful content performance prediction"""
        request_data = {
            "user_id": "user_123",
            "content_type": "post",
            "platform": "instagram",
            "content_description": "Tech tutorial post about AI",
            "hashtags": ["#tech", "#AI", "#tutorial"],
            "caption": "Learn about AI in this quick tutorial!",
            "target_audience": "tech enthusiasts",
            "campaign_goals": ["engagement", "education"],
            "budget": 1000.0
        }
        
        with patch('src.api.predictions.PerformancePredictionService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.predict_content_performance.return_value = {
                "performance_metrics": {
                    "estimated_reach": 10000,
                    "estimated_impressions": 15000,
                    "estimated_engagement_rate": 0.05,
                    "estimated_likes": 500,
                    "estimated_comments": 50,
                    "estimated_shares": 25,
                    "estimated_saves": 10,
                    "estimated_clicks": 200,
                    "estimated_conversions": 20,
                    "confidence_score": 0.8
                },
                "optimal_timing": {
                    "best_posting_time": "18:00-20:00",
                    "best_posting_day": "Friday",
                    "alternative_times": ["12:00-14:00", "21:00-23:00"],
                    "timezone": "UTC",
                    "reasoning": "Optimal for Instagram audience engagement",
                    "expected_performance_boost": 0.25
                },
                "content_optimization": {
                    "hashtag_suggestions": ["#tech", "#AI", "#tutorial"],
                    "caption_improvements": ["Add call-to-action", "Include emojis"],
                    "content_format_suggestions": ["Use carousel posts"],
                    "visual_elements": ["High-quality images"],
                    "call_to_action_suggestions": ["Follow for more"],
                    "expected_improvement": 0.2
                },
                "risk_factors": ["Low trending potential"],
                "success_probability": 0.75
            }
            
            response = self.client.post("/ai/predictions/content", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "prediction_id" in data
            assert "performance_metrics" in data
            assert "optimal_timing" in data
            assert "content_optimization" in data
            assert data["success_probability"] == 0.75
    
    def test_predict_campaign_performance_success(self):
        """Test successful campaign performance prediction"""
        request_data = {
            "user_id": "user_123",
            "campaign_id": "campaign_456",
            "campaign_type": "brand_awareness",
            "platforms": ["instagram", "youtube"],
            "budget": 10000.0,
            "duration_days": 30,
            "target_audience": {
                "age_range": "18-34",
                "interests": ["tech", "lifestyle"],
                "size": 1000000
            },
            "content_strategy": {
                "content_types": ["video", "posts"],
                "posting_frequency": "daily"
            }
        }
        
        with patch('src.api.predictions.PerformancePredictionService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.predict_campaign_performance.return_value = {
                "campaign_metrics": {
                    "estimated_total_reach": 500000,
                    "estimated_total_impressions": 750000,
                    "estimated_engagement_rate": 0.05,
                    "estimated_clicks": 10000,
                    "estimated_conversions": 1000,
                    "estimated_roi": 2.5,
                    "estimated_cpm": 13.33,
                    "estimated_cpc": 1.0,
                    "estimated_cpa": 10.0,
                    "confidence_score": 0.8
                },
                "platform_breakdown": {
                    "instagram": {
                        "allocated_budget": 5000.0,
                        "estimated_reach": 300000,
                        "estimated_engagement_rate": 0.05,
                        "estimated_clicks": 6000,
                        "estimated_conversions": 600
                    },
                    "youtube": {
                        "allocated_budget": 5000.0,
                        "estimated_reach": 200000,
                        "estimated_engagement_rate": 0.03,
                        "estimated_clicks": 4000,
                        "estimated_conversions": 400
                    }
                },
                "optimal_budget_allocation": {
                    "instagram": 0.6,
                    "youtube": 0.4
                },
                "risk_assessment": {
                    "budget_risk": "Low",
                    "audience_risk": "Low",
                    "platform_risk": "Low",
                    "timeline_risk": "Low"
                },
                "success_probability": 0.8
            }
            
            response = self.client.post("/ai/predictions/campaign", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "prediction_id" in data
            assert "campaign_metrics" in data
            assert "platform_breakdown" in data
            assert data["success_probability"] == 0.8
    
    def test_predict_creator_performance_success(self):
        """Test successful creator performance prediction"""
        request_data = {
            "creator_id": "creator_789",
            "brand_id": "brand_123",
            "campaign_type": "product_launch",
            "platform": "instagram",
            "content_type": "video",
            "budget": 5000.0,
            "target_audience": {
                "age_range": "18-34",
                "interests": ["tech", "lifestyle"]
            }
        }
        
        with patch('src.api.predictions.PerformancePredictionService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.predict_creator_performance.return_value = {
                "predicted_performance": {
                    "estimated_reach": 40000,
                    "estimated_engagement": 2000,
                    "estimated_clicks": 800,
                    "estimated_conversions": 40,
                    "estimated_roi": 2.0
                },
                "compatibility_score": 0.85,
                "risk_factors": ["Low follower count"],
                "recommendations": ["High compatibility - recommended for collaboration"]
            }
            
            response = self.client.post("/ai/predictions/creator", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "creator_id" in data
            assert data["creator_id"] == "creator_789"
            assert "predicted_performance" in data
            assert data["compatibility_score"] == 0.85


class TestContentSuggestionsAPI:
    """Test suite for content suggestions API endpoints"""
    
    def test_generate_hashtag_suggestions_success(self):
        """Test successful hashtag suggestions generation"""
        request_data = {
            "user_id": "user_123",
            "content_type": "post",
            "platform": "instagram",
            "content": "Tech tutorial about AI",
            "target_audience": "tech enthusiasts",
            "goals": ["engagement", "education"],
            "max_suggestions": 10
        }
        
        with patch('src.api.suggestions.RAGService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.generate_hashtag_suggestions.return_value = [
                {
                    "hashtag": "#tech",
                    "popularity_score": 0.8,
                    "relevance_score": 0.9,
                    "competition_level": "medium",
                    "estimated_reach": 10000,
                    "category": "technology"
                },
                {
                    "hashtag": "#AI",
                    "popularity_score": 0.7,
                    "relevance_score": 0.95,
                    "competition_level": "high",
                    "estimated_reach": 15000,
                    "category": "technology"
                }
            ]
            
            response = self.client.post("/ai/suggestions/hashtags", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["hashtag"] == "#tech"
            assert data[1]["hashtag"] == "#AI"
    
    def test_generate_caption_suggestions_success(self):
        """Test successful caption suggestions generation"""
        request_data = {
            "user_id": "user_123",
            "content_type": "post",
            "platform": "instagram",
            "content": "Tech tutorial about AI",
            "tone": "professional",
            "target_audience": "tech enthusiasts",
            "goals": ["engagement", "education"],
            "max_suggestions": 5
        }
        
        with patch('src.api.suggestions.RAGService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.generate_caption_suggestions.return_value = [
                {
                    "caption": "Discover the key insights about AI that every tech enthusiast should know. #ProfessionalTips #ExpertAdvice",
                    "tone": "professional",
                    "length": 95,
                    "engagement_potential": 0.8,
                    "readability_score": 0.9,
                    "emoji_count": 0
                }
            ]
            
            response = self.client.post("/ai/suggestions/captions", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert "caption" in data[0]
            assert data[0]["tone"] == "professional"
    
    def test_generate_posting_time_suggestions_success(self):
        """Test successful posting time suggestions generation"""
        request_data = {
            "user_id": "user_123",
            "platform": "instagram",
            "target_audience": "tech enthusiasts",
            "content_type": "post",
            "goals": ["engagement"]
        }
        
        with patch('src.api.suggestions.RAGService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.generate_posting_time_suggestions.return_value = {
                "platform": "instagram",
                "optimal_times": ["18:00-20:00", "12:00-14:00"],
                "best_days": ["Friday", "Saturday"],
                "frequency": "daily",
                "reasoning": "Optimal for Instagram audience engagement"
            }
            
            response = self.client.post("/ai/suggestions/posting-times", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "platform" in data
            assert data["platform"] == "instagram"
            assert "optimal_times" in data
    
    def test_generate_content_ideas_success(self):
        """Test successful content ideas generation"""
        request_data = {
            "user_id": "user_123",
            "platform": "instagram",
            "content_type": "post",
            "target_audience": "tech enthusiasts",
            "goals": ["engagement", "education"],
            "tone": "professional",
            "max_suggestions": 5
        }
        
        with patch('src.api.suggestions.RAGService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            mock_instance.generate_content_ideas.return_value = [
                {
                    "title": "How AI is Transforming Industries",
                    "description": "Explore the impact of AI across different sectors",
                    "format": "carousel post",
                    "estimated_engagement": 0.8,
                    "difficulty": "medium",
                    "time_to_create": "2-3 hours",
                    "trending_potential": 0.7
                }
            ]
            
            response = self.client.post("/ai/suggestions/content-ideas", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert "title" in data[0]
            assert data[0]["format"] == "carousel post"


class TestHealthAPI:
    """Test suite for health check API endpoints"""
    
    def test_health_check_success(self):
        """Test successful health check"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_detailed_health_check_success(self):
        """Test successful detailed health check"""
        response = self.client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
    
    def test_readiness_check_success(self):
        """Test successful readiness check"""
        response = self.client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert data["ready"] is True
    
    def test_liveness_check_success(self):
        """Test successful liveness check"""
        response = self.client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert "alive" in data
        assert data["alive"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
