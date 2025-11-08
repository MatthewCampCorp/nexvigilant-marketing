"""
Unit tests for Content Generation Agent.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from content_generation.main import ContentGenerationAgent, GeneratedContent, ContentVariant


class TestContentGenerationAgent:
    """Test suite for Content Generation Agent."""

    @pytest.fixture
    def agent(self):
        """Create Content Generation Agent instance."""
        try:
            agent = ContentGenerationAgent()
            return agent
        except ValueError:
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.model == "gemini-2.0-flash-exp"
        assert agent.temperature == 0.8
        assert agent.max_tokens == 2048

    def test_generate_email_content(self, agent):
        """Test email content generation."""
        result = agent.generate_email_content(
            objective="Product launch",
            audience="Enterprise customers"
        )

        assert result is not None
        assert result['success'] is True
        assert result['content_type'] == 'email'
        assert 'generated_content' in result
        assert 'subject_lines' in result['generated_content']
        assert 'body' in result['generated_content']
        assert 'cta' in result['generated_content']
        assert len(result['generated_content']['subject_lines']) >= 1

    def test_generate_email_with_insights(self, agent):
        """Test email generation with customer insights."""
        insights = {
            'segment': 'high_value',
            'industry': 'technology',
            'avg_engagement': 0.75
        }

        result = agent.generate_email_content(
            objective="Webinar invitation",
            audience="Tech executives",
            insights=insights
        )

        assert result['success'] is True
        assert 'metadata' in result
        assert result['metadata']['objective'] == "Webinar invitation"

    def test_generate_social_content_linkedin(self, agent):
        """Test LinkedIn content generation."""
        result = agent.generate_social_content(
            platform="linkedin",
            content_type="post",
            audience="B2B professionals",
            theme="Thought leadership"
        )

        assert result['success'] is True
        assert result['content_type'] == 'social_media'
        assert result['platform'] == 'linkedin'
        assert 'primary_post' in result['generated_content']
        assert 'hashtags' in result['generated_content']

    def test_generate_social_content_twitter(self, agent):
        """Test Twitter content generation."""
        result = agent.generate_social_content(
            platform="twitter",
            content_type="post",
            audience="General audience",
            theme="Product announcement"
        )

        assert result['success'] is True
        assert result['platform'] == 'twitter'
        # Twitter posts should be concise
        post_length = len(result['generated_content']['primary_post'])
        assert post_length > 0

    def test_generate_ad_copy_google(self, agent):
        """Test Google Ads copy generation."""
        result = agent.generate_ad_copy(
            platform="google_ads",
            ad_type="search",
            keywords=["marketing automation", "ai tools"],
            segment="SMB marketers",
            goal="free trial signups"
        )

        assert result['success'] is True
        assert result['content_type'] == 'ad_copy'
        assert result['platform'] == 'google_ads'
        assert 'headlines' in result['generated_content']
        assert 'descriptions' in result['generated_content']
        assert 'ctas' in result['generated_content']
        assert len(result['generated_content']['headlines']) >= 1

    def test_generate_ad_copy_facebook(self, agent):
        """Test Facebook Ads copy generation."""
        result = agent.generate_ad_copy(
            platform="facebook_ads",
            ad_type="social",
            keywords=["business growth", "productivity"],
            segment="Small business owners",
            goal="leads"
        )

        assert result['success'] is True
        assert result['platform'] == 'facebook_ads'

    def test_execute_email_request(self, agent):
        """Test execute method with email content type."""
        result = agent.execute(
            content_type='email',
            objective='Newsletter',
            audience='Subscribers'
        )

        assert result is not None
        assert result['success'] is True
        assert result['content_type'] == 'email'

    def test_execute_social_request(self, agent):
        """Test execute method with social content type."""
        result = agent.execute(
            content_type='social',
            platform='linkedin',
            social_content_type='post',
            audience='Professionals',
            theme='Industry insights'
        )

        assert result['success'] is True
        assert result['content_type'] == 'social_media'

    def test_execute_ad_request(self, agent):
        """Test execute method with ad content type."""
        result = agent.execute(
            content_type='ad',
            platform='google_ads',
            ad_type='search',
            keywords=['test keyword'],
            segment='All users',
            goal='clicks'
        )

        assert result['success'] is True
        assert result['content_type'] == 'ad_copy'

    def test_execute_default_fallback(self, agent):
        """Test execute method with unknown content type falls back to email."""
        result = agent.execute(
            content_type='unknown_type'
        )

        assert result['success'] is True
        assert result['content_type'] == 'email'

    def test_extract_subject_lines(self, agent):
        """Test subject line extraction helper."""
        sample_text = """
        Subject: Exclusive Offer Inside
        Subject: Don't Miss Out
        Subject: Limited Time Only
        """
        subjects = agent._extract_subject_lines(sample_text)

        assert isinstance(subjects, list)
        assert len(subjects) >= 1

    def test_extract_hashtags(self, agent):
        """Test hashtag extraction from social content."""
        sample_text = "Check out our new feature! #Innovation #Marketing #Tech #Business #Growth"
        hashtags = agent._extract_hashtags(sample_text)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 5  # Should limit to 5
        assert all(tag.startswith('#') for tag in hashtags)

    def test_extract_headlines(self, agent):
        """Test headline extraction for ads."""
        sample_text = """
        Headline 1: Transform Your Business
        Headline 2: Get Results Fast
        Headline 3: Try Risk-Free Today
        """
        headlines = agent._extract_headlines(sample_text)

        assert isinstance(headlines, list)
        assert len(headlines) >= 1

    def test_stub_email_response(self, agent):
        """Test stub email response structure."""
        result = agent._stub_email_response(
            objective="Test objective",
            audience="Test audience"
        )

        assert result['success'] is True
        assert result['content_type'] == 'email'
        assert 'generated_content' in result
        assert 'metadata' in result
        assert 'recommendations' in result

    def test_stub_social_response(self, agent):
        """Test stub social response structure."""
        result = agent._stub_social_response(
            platform="linkedin",
            theme="Test theme"
        )

        assert result['success'] is True
        assert result['content_type'] == 'social_media'
        assert result['platform'] == 'linkedin'

    def test_stub_ad_response(self, agent):
        """Test stub ad response structure."""
        result = agent._stub_ad_response(
            platform="google_ads",
            keywords=["test", "keywords"]
        )

        assert result['success'] is True
        assert result['content_type'] == 'ad_copy'
        assert 'quality_score_tips' in result


class TestGeneratedContent:
    """Test suite for GeneratedContent dataclass."""

    def test_generated_content_creation(self):
        """Test creating GeneratedContent instance."""
        content = GeneratedContent(
            content_type='email',
            primary_content={'subject': 'Test', 'body': 'Content'},
            variants=[],
            metadata={'timestamp': '2025-01-08'},
            optimization_scores={'readability': 0.9},
            recommendations=['Test recommendation']
        )

        assert content.content_type == 'email'
        assert content.primary_content['subject'] == 'Test'
        assert isinstance(content.variants, list)
        assert content.optimization_scores['readability'] == 0.9
        assert len(content.recommendations) == 1


class TestContentVariant:
    """Test suite for ContentVariant dataclass."""

    def test_content_variant_creation(self):
        """Test creating ContentVariant instance."""
        variant = ContentVariant(
            variant_id='variant_a',
            content={'subject': 'Test Subject A'},
            optimization_score=0.85,
            target_audience='high_value',
            channel='email'
        )

        assert variant.variant_id == 'variant_a'
        assert variant.content['subject'] == 'Test Subject A'
        assert variant.optimization_score == 0.85
        assert variant.target_audience == 'high_value'
        assert variant.channel == 'email'


class TestContentGenerationIntegration:
    """Integration tests for Content Generation Agent."""

    @pytest.fixture
    def agent(self):
        """Create agent for integration testing."""
        try:
            return ContentGenerationAgent()
        except ValueError:
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_multi_channel_content_generation(self, agent):
        """Test generating content for multiple channels."""
        # Email
        email = agent.generate_email_content(
            objective="Product launch",
            audience="All customers"
        )

        # Social
        social = agent.generate_social_content(
            platform="linkedin",
            content_type="post",
            audience="Professionals",
            theme="Innovation"
        )

        # Ads
        ads = agent.generate_ad_copy(
            platform="google_ads",
            ad_type="search",
            keywords=["test"],
            segment="All",
            goal="conversions"
        )

        # All should succeed
        assert email['success'] is True
        assert social['success'] is True
        assert ads['success'] is True

    def test_content_consistency(self, agent):
        """Test that generated content maintains brand consistency."""
        result = agent.generate_email_content(
            objective="Brand awareness",
            audience="All customers"
        )

        assert result['success'] is True
        # Should have recommendations for brand consistency
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
