"""
Tests for competitor analysis functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.services.competitor_service import CompetitorAnalysisService
from src.pipelines.competitor_analysis import CompetitorAnalysisPipeline, CompetitorAnalysisPipelineConfig


class TestCompetitorAnalysisService:
    """Test cases for CompetitorAnalysisService"""
    
    @pytest.fixture
    def competitor_service(self):
        """Create competitor service instance for testing"""
        return CompetitorAnalysisService()
    
    @pytest.mark.asyncio
    async def test_analyze_competitors_success(self, competitor_service):
        """Test successful competitor analysis"""
        # Mock the platform services
        with patch.object(competitor_service, '_analyze_single_competitor') as mock_analyze:
            mock_analyze.return_value = {
                "username": "test_competitor",
                "platforms": {},
                "overall_metrics": {},
                "analysis_type": "comprehensive"
            }
            
            result = await competitor_service.analyze_competitors(
                user_id="test_user",
                campaign_id="test_campaign",
                competitors=["competitor1", "competitor2"],
                platforms=["instagram", "youtube"],
                analysis_type="comprehensive"
            )
            
            assert result["user_id"] == "test_user"
            assert result["campaign_id"] == "test_campaign"
            assert len(result["competitors"]) == 2
            assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_analyze_competitors_validation_error(self, competitor_service):
        """Test competitor analysis with validation errors"""
        with pytest.raises(ValueError):
            await competitor_service.analyze_competitors(
                user_id="test_user",
                campaign_id="test_campaign",
                competitors=[],  # Empty competitors list
                platforms=["instagram"],
                analysis_type="comprehensive"
            )
    
    @pytest.mark.asyncio
    async def test_get_analysis_results(self, competitor_service):
        """Test getting analysis results"""
        result = await competitor_service.get_analysis_results("test_id", "test_user")
        assert "error" in result  # Should return error for non-existent analysis


class TestCompetitorAnalysisPipeline:
    """Test cases for CompetitorAnalysisPipeline"""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing"""
        return CompetitorAnalysisPipeline()
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return CompetitorAnalysisPipelineConfig(
            user_id="test_user",
            campaign_id="test_campaign",
            competitors=["competitor1", "competitor2"],
            platforms=["instagram", "youtube"],
            analysis_type="comprehensive"
        )
    
    def test_validate_config_success(self, pipeline, config):
        """Test successful config validation"""
        # Should not raise any exception
        pipeline._validate_config(config)
    
    def test_validate_config_missing_user_id(self, pipeline):
        """Test config validation with missing user ID"""
        config = CompetitorAnalysisPipelineConfig(
            user_id="",  # Empty user ID
            competitors=["competitor1"],
            platforms=["instagram"]
        )
        
        with pytest.raises(ValueError, match="User ID is required"):
            pipeline._validate_config(config)
    
    def test_validate_config_missing_competitors(self, pipeline):
        """Test config validation with missing competitors"""
        config = CompetitorAnalysisPipelineConfig(
            user_id="test_user",
            competitors=[],  # Empty competitors list
            platforms=["instagram"]
        )
        
        with pytest.raises(ValueError, match="At least one competitor must be specified"):
            pipeline._validate_config(config)
    
    def test_validate_config_invalid_time_period(self, pipeline):
        """Test config validation with invalid time period"""
        config = CompetitorAnalysisPipelineConfig(
            user_id="test_user",
            competitors=["competitor1"],
            platforms=["instagram"],
            time_period_days=400  # Invalid time period
        )
        
        with pytest.raises(ValueError, match="Time period must be between 1 and 365 days"):
            pipeline._validate_config(config)
    
    @pytest.mark.asyncio
    async def test_run_analysis_success(self, pipeline, config):
        """Test successful pipeline execution"""
        with patch.object(pipeline.competitor_service, 'analyze_competitors') as mock_analyze:
            mock_analyze.return_value = {
                "user_id": "test_user",
                "competitors": {},
                "summary": {}
            }
            
            with patch.object(pipeline.rag_service, 'generate_competitor_insights') as mock_insights:
                mock_insights.return_value = {"insights": "test insights"}
                
                result = await pipeline.run_analysis(config)
                
                assert result["status"] == "completed"
                assert result["user_id"] == "test_user"
                assert "analysis_id" in result
                assert "processing_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_run_analysis_validation_error(self, pipeline):
        """Test pipeline execution with validation error"""
        config = CompetitorAnalysisPipelineConfig(
            user_id="",  # Invalid config
            competitors=["competitor1"],
            platforms=["instagram"]
        )
        
        with pytest.raises(ValueError):
            await pipeline.run_analysis(config)
    
    @pytest.mark.asyncio
    async def test_perform_advanced_analysis(self, pipeline):
        """Test advanced analysis functionality"""
        competitor_data = {
            "competitors": {
                "competitor1": {
                    "platforms": {
                        "instagram": {
                            "profile": {"followers": 1000},
                            "posts": []
                        }
                    }
                }
            }
        }
        
        result = await pipeline._perform_advanced_analysis(competitor_data)
        
        assert "market_positioning" in result
        assert "content_gaps" in result
        assert "engagement_patterns" in result
        assert "audience_overlap" in result
        assert "trending_topics" in result
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, pipeline):
        """Test recommendation generation"""
        competitor_data = {
            "competitors": {
                "competitor1": {
                    "platforms": {
                        "instagram": {
                            "profile": {"followers": 1000},
                            "posts": []
                        }
                    }
                }
            }
        }
        
        config = CompetitorAnalysisPipelineConfig(
            user_id="test_user",
            competitors=["competitor1"],
            platforms=["instagram"]
        )
        
        result = await pipeline._generate_recommendations(competitor_data, config)
        
        assert "content_strategy" in result
        assert "engagement_strategy" in result
        assert "audience_strategy" in result
        assert "timing_strategy" in result
        assert "competitive_advantages" in result


@pytest.mark.asyncio
async def test_integration_competitor_analysis():
    """Integration test for competitor analysis"""
    # This would be a more comprehensive integration test
    # that tests the entire flow with real (or mocked) data
    
    pipeline = CompetitorAnalysisPipeline()
    config = CompetitorAnalysisPipelineConfig(
        user_id="integration_test_user",
        campaign_id="integration_test_campaign",
        competitors=["test_competitor"],
        platforms=["instagram"],
        analysis_type="comprehensive",
        time_period_days=7,
        max_posts_per_competitor=10
    )
    
    # Mock all external dependencies
    with patch.object(pipeline.competitor_service, 'analyze_competitors') as mock_analyze:
        mock_analyze.return_value = {
            "user_id": "integration_test_user",
            "competitors": {
                "test_competitor": {
                    "platforms": {
                        "instagram": {
                            "profile": {"followers": 5000, "following": 500},
                            "posts": [
                                {"likes": 100, "comments": 10, "shares": 5}
                            ]
                        }
                    }
                }
            },
            "summary": {"total_competitors": 1}
        }
        
        with patch.object(pipeline.rag_service, 'generate_competitor_insights') as mock_insights:
            mock_insights.return_value = {
                "insights": "AI-generated insights",
                "recommendations": ["Test recommendation"]
            }
            
            result = await pipeline.run_analysis(config)
            
            assert result["status"] == "completed"
            assert result["user_id"] == "integration_test_user"
            assert len(result["results"]["competitors"]) == 1
            assert "ai_insights" in result["results"]
            assert "recommendations" in result["results"]
