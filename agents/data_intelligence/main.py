"""
Data Intelligence Agent - Specialized agent for querying BigQuery and dbt models.

Provides customer insights, segmentation, and trend analysis from the data warehouse.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .bigquery_tool import BigQueryTool, QueryResult

try:
    from google.genai import types
    from google_adk.agents import LlmAgent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logging.warning("Google ADK not installed")

logger = logging.getLogger(__name__)


@dataclass
class DataInsight:
    """Represents an insight extracted from data."""
    insight_type: str
    summary: str
    data: Dict[str, Any]
    recommendations: List[str]
    confidence: float


class DataIntelligenceAgent:
    """
    Data Intelligence Agent for querying and analyzing marketing data.

    Responsibilities:
    - Query BigQuery for customer, campaign, and performance data
    - Perform customer segmentation analysis
    - Identify trends and patterns
    - Generate data-driven insights
    - Provide recommendations based on data
    """

    SYSTEM_PROMPT = """You are the Data Intelligence Agent for NexVigilant's marketing system.

Your role is to analyze marketing data from BigQuery and provide actionable insights.

Available Data Sources:
- customer_360: Comprehensive customer profiles with LTV, engagement, churn risk
- campaign_performance: Multi-channel campaign metrics and ROI
- attribution_model: Multi-touch attribution data
- ml_features: Feature engineered data for predictive models

Analysis Capabilities:
- Customer segmentation and profiling
- Campaign performance analysis
- Trend identification
- ROI calculation
- Churn risk analysis
- Lifetime value analysis

When analyzing data:
1. Always validate data quality and freshness
2. Look for statistically significant patterns
3. Provide context with comparisons (YoY, period-over-period)
4. Flag any data quality issues
5. Suggest follow-up analyses

Output Format:
- Clear, concise insights
- Data visualizations where helpful
- Actionable recommendations
- Confidence levels for insights
"""

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        project_id: Optional[str] = None,
        location: str = "us-central1",
    ):
        """
        Initialize Data Intelligence Agent.

        Args:
            model: Gemini model for analysis
            project_id: Google Cloud project ID
            location: Google Cloud location
        """
        self.model = model
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location

        # Initialize BigQuery tool
        self.bigquery_tool = BigQueryTool(project_id=self.project_id)

        # Initialize ADK agent if available
        if ADK_AVAILABLE:
            self._initialize_adk_agent()
        else:
            self.agent = None

        logger.info("Data Intelligence Agent initialized")

    def _initialize_adk_agent(self):
        """Initialize Google ADK LLM agent."""
        try:
            self.agent = LlmAgent(
                model=self.model,
                system_instruction=self.SYSTEM_PROMPT,
            )
            logger.info(f"ADK agent initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize ADK agent: {e}")
            self.agent = None

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Main execution method called by coordinator.

        Args:
            query: User's data query or analysis request
            **kwargs: Additional parameters

        Returns:
            Analysis results with insights
        """
        logger.info(f"Executing data intelligence query: {query[:100]}...")

        # Determine query type
        query_lower = query.lower()

        # Route to appropriate analysis method
        if 'customer' in query_lower and 'segment' in query_lower:
            return self.analyze_customer_segments()

        elif 'customer' in query_lower:
            return self.analyze_customers(query)

        elif 'campaign' in query_lower or 'performance' in query_lower:
            return self.analyze_campaign_performance(query)

        elif 'trend' in query_lower:
            return self.analyze_trends(query)

        else:
            # General data query
            return self.execute_custom_query(query)

    def analyze_customer_segments(self) -> Dict[str, Any]:
        """Analyze customer segmentation data."""
        logger.info("Analyzing customer segments...")

        # Query customer segments
        result = self.bigquery_tool.get_customer_segments()

        if not result.success:
            return {
                'success': False,
                'error': result.error,
                'insights': []
            }

        # Analyze segment data
        insights = []

        # Find highest value segment
        if result.rows:
            highest_ltv_segment = max(result.rows, key=lambda x: x.get('avg_ltv', 0))
            insights.append(DataInsight(
                insight_type='segment_value',
                summary=f"Highest value segment: {highest_ltv_segment['segment']}",
                data=highest_ltv_segment,
                recommendations=[
                    f"Prioritize retention campaigns for {highest_ltv_segment['segment']} segment",
                    "Analyze characteristics of this segment for lookalike targeting"
                ],
                confidence=0.95
            ))

            # Find at-risk segment
            highest_churn_segment = max(result.rows, key=lambda x: x.get('avg_churn_risk', 0))
            if highest_churn_segment['avg_churn_risk'] > 0.5:
                insights.append(DataInsight(
                    insight_type='segment_risk',
                    summary=f"At-risk segment: {highest_churn_segment['segment']}",
                    data=highest_churn_segment,
                    recommendations=[
                        f"Launch retention campaign for {highest_churn_segment['segment']}",
                        "Conduct customer satisfaction survey",
                        "Analyze reasons for churn risk"
                    ],
                    confidence=0.9
                ))

        return {
            'success': True,
            'analysis_type': 'customer_segmentation',
            'total_segments': len(result.rows),
            'segments': result.rows,
            'insights': [
                {
                    'type': i.insight_type,
                    'summary': i.summary,
                    'data': i.data,
                    'recommendations': i.recommendations,
                    'confidence': i.confidence
                }
                for i in insights
            ],
            'metadata': {
                'rows_analyzed': result.total_rows,
                'execution_time_ms': result.execution_time_ms,
                'bytes_processed': result.bytes_processed
            }
        }

    def analyze_customers(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Analyze customer data."""
        logger.info("Analyzing customer data...")

        # Extract parameters from query (simple keyword extraction)
        segment = None
        if 'high value' in query.lower():
            segment = 'high_value'
        elif 'at risk' in query.lower() or 'churn' in query.lower():
            segment = 'at_risk'

        result = self.bigquery_tool.get_customer_360(segment=segment, limit=limit)

        if not result.success:
            return {
                'success': False,
                'error': result.error
            }

        # Calculate summary statistics
        if result.rows:
            avg_ltv = sum(r.get('lifetime_value', 0) for r in result.rows) / len(result.rows)
            avg_engagement = sum(r.get('engagement_score', 0) for r in result.rows) / len(result.rows)
            avg_churn_risk = sum(r.get('churn_risk', 0) for r in result.rows) / len(result.rows)

            summary_stats = {
                'total_customers': len(result.rows),
                'average_lifetime_value': avg_ltv,
                'average_engagement_score': avg_engagement,
                'average_churn_risk': avg_churn_risk,
            }
        else:
            summary_stats = {}

        return {
            'success': True,
            'analysis_type': 'customer_analysis',
            'customers': result.rows[:10],  # Return top 10 for display
            'total_customers': result.total_rows,
            'summary_statistics': summary_stats,
            'metadata': {
                'execution_time_ms': result.execution_time_ms,
                'bytes_processed': result.bytes_processed
            }
        }

    def analyze_campaign_performance(self, query: str) -> Dict[str, Any]:
        """Analyze campaign performance data."""
        logger.info("Analyzing campaign performance...")

        # Extract date range from query (simplified)
        start_date = None
        end_date = None

        result = self.bigquery_tool.get_campaign_performance(
            start_date=start_date,
            end_date=end_date,
            limit=100
        )

        if not result.success:
            return {
                'success': False,
                'error': result.error
            }

        # Calculate aggregate metrics
        insights = []

        if result.rows:
            total_cost = sum(r.get('cost', 0) for r in result.rows)
            total_revenue = sum(r.get('revenue', 0) for r in result.rows)
            total_conversions = sum(r.get('conversions', 0) for r in result.rows)

            overall_roas = total_revenue / total_cost if total_cost > 0 else 0

            # Find best performing campaign
            best_campaign = max(result.rows, key=lambda x: x.get('roas', 0))

            insights.append(DataInsight(
                insight_type='campaign_performance',
                summary=f"Best performing campaign: {best_campaign.get('campaign_name', 'N/A')}",
                data=best_campaign,
                recommendations=[
                    f"Increase budget for {best_campaign.get('campaign_name')}",
                    "Analyze creative elements for replication",
                    "Test similar audiences"
                ],
                confidence=0.9
            ))

            aggregate_metrics = {
                'total_campaigns': len(set(r.get('campaign_id') for r in result.rows)),
                'total_cost': total_cost,
                'total_revenue': total_revenue,
                'total_conversions': total_conversions,
                'overall_roas': overall_roas
            }
        else:
            aggregate_metrics = {}

        return {
            'success': True,
            'analysis_type': 'campaign_performance',
            'campaigns': result.rows[:10],
            'aggregate_metrics': aggregate_metrics,
            'insights': [
                {
                    'type': i.insight_type,
                    'summary': i.summary,
                    'data': i.data,
                    'recommendations': i.recommendations,
                    'confidence': i.confidence
                }
                for i in insights
            ],
            'metadata': {
                'rows_analyzed': result.total_rows,
                'execution_time_ms': result.execution_time_ms,
                'bytes_processed': result.bytes_processed
            }
        }

    def analyze_trends(self, query: str) -> Dict[str, Any]:
        """Analyze trends in marketing data."""
        logger.info("Analyzing trends...")

        # Placeholder for trend analysis
        # In Phase 2, implement time-series analysis
        return {
            'success': True,
            'analysis_type': 'trend_analysis',
            'message': 'Trend analysis will be implemented in Phase 2',
            'query': query
        }

    def execute_custom_query(self, query: str) -> Dict[str, Any]:
        """Execute a custom SQL query (with validation)."""
        logger.info("Executing custom query...")

        # For Phase 1, return informative message
        # In Phase 2, allow LLM to generate SQL from natural language
        return {
            'success': False,
            'error': 'Custom query generation not yet implemented',
            'message': 'Please use predefined analysis methods or specify customer/campaign queries',
            'query': query
        }

    def close(self):
        """Clean up resources."""
        if self.bigquery_tool:
            self.bigquery_tool.close()


def main():
    """Test Data Intelligence Agent."""
    from dotenv import load_dotenv
    import json

    load_dotenv()

    agent = DataIntelligenceAgent()

    # Test queries
    test_queries = [
        "Show me customer segmentation",
        "Analyze high value customers",
        "What's our campaign performance?",
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        result = agent.execute(query)
        print(json.dumps(result, indent=2, default=str))

    agent.close()


if __name__ == "__main__":
    main()
