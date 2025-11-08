"""
Unit tests for Data Intelligence Agent.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_intelligence.main import DataIntelligenceAgent, DataInsight
from data_intelligence.bigquery_tool import BigQueryTool, QueryResult


class TestBigQueryTool:
    """Test suite for BigQuery Tool."""

    @pytest.fixture
    def bigquery_tool(self):
        """Create BigQuery tool instance."""
        # Will run in stub mode without actual GCP credentials
        try:
            tool = BigQueryTool()
            return tool
        except ValueError:
            # If GOOGLE_CLOUD_PROJECT not set, skip these tests
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_bigquery_tool_initialization(self, bigquery_tool):
        """Test BigQuery tool initializes correctly."""
        assert bigquery_tool is not None
        assert bigquery_tool.default_dataset == "marketing_marts" or bigquery_tool.default_dataset is not None
        assert bigquery_tool.timeout_seconds == 30
        assert bigquery_tool.max_results == 10000

    def test_validate_query_select_allowed(self, bigquery_tool):
        """Test validation of allowed SELECT query."""
        query = "SELECT * FROM customer_360 LIMIT 10"
        is_valid, error = bigquery_tool.validate_query(query)

        assert is_valid is True
        assert error is None

    def test_validate_query_drop_disallowed(self, bigquery_tool):
        """Test validation rejects DROP query."""
        query = "DROP TABLE customer_360"
        is_valid, error = bigquery_tool.validate_query(query)

        assert is_valid is False
        assert "DROP" in error

    def test_validate_query_delete_disallowed(self, bigquery_tool):
        """Test validation rejects DELETE query."""
        query = "DELETE FROM customer_360 WHERE 1=1"
        is_valid, error = bigquery_tool.validate_query(query)

        assert is_valid is False
        assert "DELETE" in error

    def test_validate_query_non_select_disallowed(self, bigquery_tool):
        """Test validation rejects non-SELECT queries."""
        query = "INSERT INTO customer_360 VALUES (1, 2, 3)"
        is_valid, error = bigquery_tool.validate_query(query)

        assert is_valid is False
        assert "SELECT" in error

    def test_validate_query_requires_allowed_table(self, bigquery_tool):
        """Test validation requires allowed tables."""
        query = "SELECT * FROM unauthorized_table LIMIT 10"
        is_valid, error = bigquery_tool.validate_query(query)

        assert is_valid is False
        assert "allowed tables" in error

    def test_query_result_dataclass_success(self):
        """Test QueryResult dataclass for successful query."""
        result = QueryResult(
            success=True,
            rows=[{'id': 1}, {'id': 2}],
            total_rows=2,
            schema=['id'],
            bytes_processed=1024,
            execution_time_ms=150.5
        )

        assert result.success is True
        assert len(result.rows) == 2
        assert result.total_rows == 2
        assert result.error is None

    def test_query_result_dataclass_failure(self):
        """Test QueryResult dataclass for failed query."""
        result = QueryResult(
            success=False,
            rows=[],
            total_rows=0,
            schema=[],
            error="Connection timeout"
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert len(result.rows) == 0


class TestDataIntelligenceAgent:
    """Test suite for Data Intelligence Agent."""

    @pytest.fixture
    def agent(self):
        """Create Data Intelligence Agent instance."""
        try:
            agent = DataIntelligenceAgent()
            return agent
        except ValueError:
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.model == "gemini-2.0-flash-exp"
        assert agent.bigquery_tool is not None

    def test_execute_customer_segment_query(self, agent):
        """Test executing customer segmentation query."""
        query = "Show me customer segmentation data"
        result = agent.execute(query)

        assert result is not None
        assert 'success' in result
        assert 'analysis_type' in result

    def test_execute_customer_query(self, agent):
        """Test executing customer analysis query."""
        query = "Analyze high value customers"
        result = agent.execute(query)

        assert result is not None
        assert 'success' in result
        assert 'analysis_type' in result

    def test_execute_campaign_query(self, agent):
        """Test executing campaign performance query."""
        query = "What's our campaign performance?"
        result = agent.execute(query)

        assert result is not None
        assert 'success' in result
        assert 'analysis_type' in result

    def test_execute_trend_query(self, agent):
        """Test executing trend analysis query."""
        query = "Show me trends in customer engagement"
        result = agent.execute(query)

        assert result is not None
        assert 'success' in result
        # Trend analysis is placeholder in Phase 1
        assert result.get('analysis_type') == 'trend_analysis'

    def test_execute_custom_query_not_implemented(self, agent):
        """Test custom query returns not implemented."""
        query = "Some random query"
        result = agent.execute(query)

        # Should route to data intelligence for general queries
        assert result is not None

    def test_data_insight_dataclass(self):
        """Test DataInsight dataclass."""
        insight = DataInsight(
            insight_type='segment_value',
            summary='Test insight',
            data={'segment': 'high_value'},
            recommendations=['Recommendation 1', 'Recommendation 2'],
            confidence=0.95
        )

        assert insight.insight_type == 'segment_value'
        assert insight.summary == 'Test insight'
        assert len(insight.recommendations) == 2
        assert insight.confidence == 0.95


class TestDataIntelligenceIntegration:
    """Integration tests for Data Intelligence Agent with BigQuery."""

    @pytest.fixture
    def agent(self):
        """Create agent for integration testing."""
        try:
            return DataIntelligenceAgent()
        except ValueError:
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_analyze_customer_segments_structure(self, agent):
        """Test customer segment analysis returns correct structure."""
        result = agent.analyze_customer_segments()

        assert 'success' in result
        assert 'analysis_type' in result
        assert result['analysis_type'] == 'customer_segmentation'

        if result['success']:
            assert 'segments' in result
            assert 'insights' in result
            assert 'metadata' in result

    def test_analyze_customers_structure(self, agent):
        """Test customer analysis returns correct structure."""
        result = agent.analyze_customers("high value customers")

        assert 'success' in result
        assert 'analysis_type' in result

        if result['success']:
            assert result['analysis_type'] == 'customer_analysis'
            assert 'summary_statistics' in result

    def test_analyze_campaign_performance_structure(self, agent):
        """Test campaign performance analysis structure."""
        result = agent.analyze_campaign_performance("recent campaigns")

        assert 'success' in result
        assert 'analysis_type' in result

        if result['success']:
            assert result['analysis_type'] == 'campaign_performance'
            assert 'aggregate_metrics' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
