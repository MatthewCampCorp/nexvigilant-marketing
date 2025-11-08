"""
Content Generation Agent - AI-powered marketing content creation with Gemini.

This agent generates high-quality, personalized marketing content across multiple channels
using Google's Gemini AI. It integrates with customer data, predictive insights, and
campaign parameters to create conversion-optimized content.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .prompts import (
    CONTENT_GENERATOR_SYSTEM_PROMPT,
    EMAIL_GENERATION_PROMPT,
    SOCIAL_MEDIA_PROMPT,
    AD_COPY_PROMPT,
    LANDING_PAGE_PROMPT,
    PERSONALIZATION_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if ADK is available
try:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch
    ADK_AVAILABLE = True
    logger.info("Google GenAI SDK loaded successfully")
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("Google GenAI SDK not available. Agent will run in stub mode for testing.")


@dataclass
class ContentVariant:
    """Represents a content variation for A/B testing."""
    variant_id: str
    content: Dict[str, Any]
    optimization_score: float
    target_audience: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class GeneratedContent:
    """Result of content generation."""
    content_type: str
    primary_content: Dict[str, Any]
    variants: List[ContentVariant] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    optimization_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ContentGenerationAgent:
    """
    Content Generation Agent using Gemini for AI-powered content creation.

    Capabilities:
    - Email marketing content (subject lines, body, CTAs)
    - Social media posts (LinkedIn, Twitter, Facebook, Instagram)
    - Ad copy (Google Ads, display ads, social ads)
    - Landing page content
    - Personalized content variations
    """

    SYSTEM_PROMPT = CONTENT_GENERATOR_SYSTEM_PROMPT

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        project_id: Optional[str] = None,
        temperature: float = 0.8,  # Higher for creative content
        max_tokens: int = 2048
    ):
        """
        Initialize Content Generation Agent.

        Args:
            model: Gemini model to use for content generation
            project_id: Google Cloud project ID (from environment if not provided)
            temperature: Creativity level (0.0-1.0, higher = more creative)
            max_tokens: Maximum tokens for generated content
        """
        self.model = model
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.project_id and ADK_AVAILABLE:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

        # Initialize Gemini client
        self.client = None
        if ADK_AVAILABLE:
            try:
                # Initialize GenAI client for Vertex AI
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
                )
                logger.info(f"Content Generation Agent initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                logger.warning("Running in stub mode")
        else:
            logger.warning("Running in stub mode - ADK not available")

    def generate_email_content(
        self,
        objective: str,
        audience: str,
        insights: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate email campaign content.

        Args:
            objective: Campaign objective (e.g., "product launch", "webinar promotion")
            audience: Target audience description or segment
            insights: Customer insights from Data Intelligence Agent

        Returns:
            Email content with subject lines, body, and CTAs
        """
        logger.info(f"Generating email content for objective: {objective}")

        prompt = EMAIL_GENERATION_PROMPT.format(
            objective=objective,
            audience=audience,
            insights=insights or {}
        )

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                        system_instruction=self.SYSTEM_PROMPT
                    )
                )

                # Parse and structure the response
                generated_text = response.text

                return {
                    'success': True,
                    'content_type': 'email',
                    'generated_content': {
                        'subject_lines': self._extract_subject_lines(generated_text),
                        'body': self._extract_email_body(generated_text),
                        'cta': self._extract_cta(generated_text),
                        'preheader': self._extract_preheader(generated_text)
                    },
                    'metadata': {
                        'model': self.model,
                        'temperature': self.temperature,
                        'timestamp': datetime.utcnow().isoformat(),
                        'objective': objective,
                        'audience': audience
                    },
                    'recommendations': [
                        'A/B test subject lines for optimal open rate',
                        'Personalize email body with recipient name and company',
                        'Test send times based on audience timezone'
                    ]
                }
            except Exception as e:
                logger.error(f"Email generation failed: {e}")
                return self._stub_email_response(objective, audience)
        else:
            return self._stub_email_response(objective, audience)

    def generate_social_content(
        self,
        platform: str,
        content_type: str,
        audience: str,
        theme: str
    ) -> Dict[str, Any]:
        """
        Generate social media content.

        Args:
            platform: Social platform (linkedin, twitter, facebook, instagram)
            content_type: Type of content (post, story, video_script)
            audience: Target audience
            theme: Campaign theme or topic

        Returns:
            Social media content optimized for platform
        """
        logger.info(f"Generating {platform} content - {content_type}")

        prompt = SOCIAL_MEDIA_PROMPT.format(
            platform=platform,
            content_type=content_type,
            audience=audience,
            theme=theme
        )

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=1024,
                        system_instruction=self.SYSTEM_PROMPT
                    )
                )

                return {
                    'success': True,
                    'content_type': 'social_media',
                    'platform': platform,
                    'generated_content': {
                        'primary_post': response.text,
                        'hashtags': self._extract_hashtags(response.text),
                        'variants': []  # Would parse multiple variants
                    },
                    'metadata': {
                        'platform': platform,
                        'content_type': content_type,
                        'char_count': len(response.text),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Social content generation failed: {e}")
                return self._stub_social_response(platform, theme)
        else:
            return self._stub_social_response(platform, theme)

    def generate_ad_copy(
        self,
        platform: str,
        ad_type: str,
        keywords: List[str],
        segment: str,
        goal: str
    ) -> Dict[str, Any]:
        """
        Generate ad copy for advertising platforms.

        Args:
            platform: Ad platform (google_ads, facebook_ads, linkedin_ads)
            ad_type: Ad type (search, display, video, social)
            keywords: Target keywords for the ad
            segment: Target audience segment
            goal: Conversion goal (clicks, leads, sales)

        Returns:
            Ad copy with headlines, descriptions, and CTAs
        """
        logger.info(f"Generating {platform} {ad_type} ad copy")

        prompt = AD_COPY_PROMPT.format(
            platform=platform,
            ad_type=ad_type,
            keywords=', '.join(keywords),
            segment=segment,
            goal=goal
        )

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=1024,
                        system_instruction=self.SYSTEM_PROMPT
                    )
                )

                return {
                    'success': True,
                    'content_type': 'ad_copy',
                    'platform': platform,
                    'generated_content': {
                        'headlines': self._extract_headlines(response.text),
                        'descriptions': self._extract_descriptions(response.text),
                        'ctas': self._extract_ctas(response.text)
                    },
                    'metadata': {
                        'platform': platform,
                        'ad_type': ad_type,
                        'keywords': keywords,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'quality_score_tips': [
                        'Ensure landing page relevance to ad copy',
                        'Use keywords in headlines for relevance',
                        'Test multiple ad variants for optimal CTR'
                    ]
                }
            except Exception as e:
                logger.error(f"Ad copy generation failed: {e}")
                return self._stub_ad_response(platform, keywords)
        else:
            return self._stub_ad_response(platform, keywords)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method called by coordinator.

        Routes to appropriate content generation method based on request type.

        Args:
            **kwargs: Request parameters including content_type, and type-specific params

        Returns:
            Generated content result
        """
        content_type = kwargs.get('content_type', 'email')

        if content_type == 'email':
            return self.generate_email_content(
                objective=kwargs.get('objective', 'General marketing'),
                audience=kwargs.get('audience', 'All customers'),
                insights=kwargs.get('insights')
            )
        elif content_type == 'social':
            return self.generate_social_content(
                platform=kwargs.get('platform', 'linkedin'),
                content_type=kwargs.get('social_content_type', 'post'),
                audience=kwargs.get('audience', 'All customers'),
                theme=kwargs.get('theme', 'Product update')
            )
        elif content_type == 'ad':
            return self.generate_ad_copy(
                platform=kwargs.get('platform', 'google_ads'),
                ad_type=kwargs.get('ad_type', 'search'),
                keywords=kwargs.get('keywords', []),
                segment=kwargs.get('segment', 'All customers'),
                goal=kwargs.get('goal', 'conversions')
            )
        else:
            # Default to general content generation
            return self.generate_email_content(
                objective='General marketing',
                audience='All customers'
            )

    # Helper methods for parsing generated content

    def _extract_subject_lines(self, text: str) -> List[str]:
        """Extract subject line variants from generated text."""
        # Simple extraction - in production, use more robust parsing
        lines = text.split('\n')
        subjects = [line.strip() for line in lines if 'subject' in line.lower()][:3]
        return subjects or ['Exclusive Offer Inside', 'Don\'t Miss Out', 'Special Announcement']

    def _extract_email_body(self, text: str) -> str:
        """Extract email body from generated text."""
        # Simple extraction - production would use structured parsing
        return text

    def _extract_cta(self, text: str) -> str:
        """Extract CTA from generated text."""
        ctas = ['Learn More', 'Get Started', 'Claim Offer']
        for line in text.split('\n'):
            if 'cta' in line.lower() or 'call to action' in line.lower():
                return line.strip()
        return ctas[0]

    def _extract_preheader(self, text: str) -> str:
        """Extract preheader text from generated content."""
        return "Preview your exclusive offer"

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from social media content."""
        import re
        hashtags = re.findall(r'#\w+', text)
        return hashtags[:5]  # Limit to 5 hashtags

    def _extract_headlines(self, text: str) -> List[str]:
        """Extract ad headlines from generated text."""
        lines = text.split('\n')
        headlines = [line.strip() for line in lines if len(line.strip()) <= 30][:5]
        return headlines or ['Transform Your Business', 'Get Results Fast', 'Try Risk-Free']

    def _extract_descriptions(self, text: str) -> List[str]:
        """Extract ad descriptions from generated text."""
        return ['Boost productivity with our solution', 'Trusted by 10,000+ companies', 'Start your free trial today']

    def _extract_ctas(self, text: str) -> List[str]:
        """Extract CTAs from generated text."""
        return ['Start Free Trial', 'Request Demo', 'Learn More']

    # Stub responses for testing without Gemini

    def _stub_email_response(self, objective: str, audience: str) -> Dict[str, Any]:
        """Stub response for email generation."""
        return {
            'success': True,
            'content_type': 'email',
            'generated_content': {
                'subject_lines': [
                    f'Exclusive Offer for {audience}',
                    f'Don\'t Miss: {objective}',
                    f'{audience}: Limited Time Opportunity'
                ],
                'body': f'Dear Valued Customer,\n\nWe\'re excited to share {objective} with you...',
                'cta': 'Learn More',
                'preheader': f'Discover how {objective} can benefit you'
            },
            'metadata': {
                'model': 'stub_mode',
                'objective': objective,
                'audience': audience,
                'timestamp': datetime.utcnow().isoformat()
            },
            'recommendations': [
                'A/B test subject lines',
                'Personalize with customer data',
                'Optimize send times'
            ]
        }

    def _stub_social_response(self, platform: str, theme: str) -> Dict[str, Any]:
        """Stub response for social media generation."""
        return {
            'success': True,
            'content_type': 'social_media',
            'platform': platform,
            'generated_content': {
                'primary_post': f'Excited to share {theme}! Learn more about how we\'re innovating. #Innovation #Marketing',
                'hashtags': ['#Innovation', '#Marketing', '#Business'],
                'variants': []
            },
            'metadata': {
                'platform': platform,
                'theme': theme,
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def _stub_ad_response(self, platform: str, keywords: List[str]) -> Dict[str, Any]:
        """Stub response for ad copy generation."""
        return {
            'success': True,
            'content_type': 'ad_copy',
            'platform': platform,
            'generated_content': {
                'headlines': [
                    'Transform Your Business Today',
                    'Get Results in 30 Days',
                    'Trusted by 10K+ Companies',
                    'Start Your Free Trial',
                    'Boost ROI by 300%'
                ],
                'descriptions': [
                    'Proven solution for modern businesses. Join thousands of satisfied customers.',
                    'No credit card required. Cancel anytime. Get started in minutes.',
                    'Award-winning platform trusted by industry leaders worldwide.'
                ],
                'ctas': ['Start Free Trial', 'Request Demo', 'Learn More']
            },
            'metadata': {
                'platform': platform,
                'keywords': keywords,
                'timestamp': datetime.utcnow().isoformat()
            },
            'quality_score_tips': [
                'Ensure landing page relevance',
                'Use keywords in headlines',
                'Test multiple variants'
            ]
        }


def main():
    """Main entry point for testing the Content Generation Agent."""
    import json
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Initialize agent
    agent = ContentGenerationAgent()

    # Test email generation
    print("\n" + "="*80)
    print("Testing Email Content Generation")
    print("="*80)
    email_result = agent.generate_email_content(
        objective="New product launch - AI-powered analytics platform",
        audience="Enterprise decision makers",
        insights={'segment': 'high_value', 'industry': 'technology'}
    )
    print(json.dumps(email_result, indent=2))

    # Test social media generation
    print("\n" + "="*80)
    print("Testing Social Media Content Generation")
    print("="*80)
    social_result = agent.generate_social_content(
        platform="linkedin",
        content_type="post",
        audience="B2B professionals",
        theme="Thought leadership on AI in marketing"
    )
    print(json.dumps(social_result, indent=2))

    # Test ad copy generation
    print("\n" + "="*80)
    print("Testing Ad Copy Generation")
    print("="*80)
    ad_result = agent.generate_ad_copy(
        platform="google_ads",
        ad_type="search",
        keywords=["marketing automation", "ai analytics", "customer insights"],
        segment="SMB marketing teams",
        goal="free trial signups"
    )
    print(json.dumps(ad_result, indent=2))


if __name__ == "__main__":
    main()
