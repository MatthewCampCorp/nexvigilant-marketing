"""
Unit tests for Marketing Coordinator Agent.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coordinator.main import MarketingCoordinator, DelegationDecision, AgentResult


class TestMarketingCoordinator:
    """Test suite for Marketing Coordinator Agent."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator instance for testing."""
        # Use stub mode for testing without GCP credentials
        coordinator = MarketingCoordinator()
        return coordinator

    @pytest.fixture
    def mock_data_agent(self):
        """Mock Data Intelligence Agent."""
        class MockDataAgent:
            def execute(self, **kwargs):
                return {
                    'success': True,
                    'data': [{'customer_id': '123', 'segment': 'high_value'}],
                    'insights': ['Test insight']
                }
        return MockDataAgent()

    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes correctly."""
        assert coordinator is not None
        assert coordinator.model == "gemini-2.0-flash-exp"
        assert coordinator.specialized_agents == {}
        assert coordinator.delegation_history == []

    def test_register_specialized_agent(self, coordinator, mock_data_agent):
        """Test registering specialized agents."""
        coordinator.register_specialized_agent('data_intelligence', mock_data_agent)

        assert 'data_intelligence' in coordinator.specialized_agents
        assert coordinator.specialized_agents['data_intelligence'] == mock_data_agent

    def test_determine_delegation_data_query(self, coordinator):
        """Test delegation decision for data queries."""
        request = "Show me customer segmentation data"
        decisions = coordinator.determine_delegation(request)

        assert len(decisions) > 0
        assert any(d.target_agent == 'data_intelligence' for d in decisions)

    def test_determine_delegation_prediction_query(self, coordinator):
        """Test delegation decision for prediction queries."""
        request = "Predict which leads will convert"
        decisions = coordinator.determine_delegation(request)

        assert len(decisions) > 0
        assert any(d.target_agent == 'predictive_insights' for d in decisions)

    def test_determine_delegation_content_query(self, coordinator):
        """Test delegation decision for content creation."""
        request = "Create an email campaign for our new product"
        decisions = coordinator.determine_delegation(request)

        assert len(decisions) > 0
        assert any(d.target_agent == 'content_generation' for d in decisions)

    def test_determine_delegation_campaign_query(self, coordinator):
        """Test delegation decision for campaign queries."""
        request = "Launch a new Google Ads campaign"
        decisions = coordinator.determine_delegation(request)

        assert len(decisions) > 0
        decision = next(d for d in decisions if d.target_agent == 'campaign_design')
        assert decision.requires_human_approval is True

    def test_execute_delegation_success(self, coordinator, mock_data_agent):
        """Test successful delegation execution."""
        coordinator.register_specialized_agent('data_intelligence', mock_data_agent)

        decision = DelegationDecision(
            target_agent='data_intelligence',
            task_description='Test query',
            parameters={'query': 'test'}
        )

        result = coordinator.execute_delegation(decision)

        assert result.success is True
        assert result.agent_name == 'data_intelligence'
        assert result.result is not None

    def test_execute_delegation_agent_not_found(self, coordinator):
        """Test delegation to unregistered agent."""
        decision = DelegationDecision(
            target_agent='nonexistent_agent',
            task_description='Test query',
            parameters={}
        )

        result = coordinator.execute_delegation(decision)

        assert result.success is False
        assert 'not registered' in result.error

    def test_execute_delegation_human_approval_required(self, coordinator):
        """Test delegation that requires human approval."""
        decision = DelegationDecision(
            target_agent='campaign_design',
            task_description='Launch campaign',
            parameters={},
            requires_human_approval=True,
            approval_reason='Campaign launch requires approval'
        )

        result = coordinator.execute_delegation(decision)

        assert result.success is False
        assert 'Human approval required' in result.error

    def test_aggregate_results_success(self, coordinator):
        """Test aggregating successful results."""
        results = [
            AgentResult(
                agent_name='data_intelligence',
                task='Query data',
                success=True,
                result={'data': [1, 2, 3]}
            ),
            AgentResult(
                agent_name='predictive_insights',
                task='Predict',
                success=True,
                result={'predictions': [0.8, 0.9]}
            )
        ]

        aggregated = coordinator.aggregate_results(results)

        assert aggregated['success'] is True
        assert len(aggregated['insights']) == 2
        assert 'data_intelligence' in aggregated['insights']
        assert 'predictive_insights' in aggregated['insights']

    def test_aggregate_results_with_failures(self, coordinator):
        """Test aggregating results with failures."""
        results = [
            AgentResult(
                agent_name='data_intelligence',
                task='Query data',
                success=True,
                result={'data': [1, 2, 3]}
            ),
            AgentResult(
                agent_name='predictive_insights',
                task='Predict',
                success=False,
                error='Model not found'
            )
        ]

        aggregated = coordinator.aggregate_results(results)

        assert aggregated['success'] is False
        assert len(aggregated['errors']) == 1
        assert aggregated['errors'][0] == 'Model not found'

    def test_process_request_end_to_end(self, coordinator, mock_data_agent):
        """Test complete request processing workflow."""
        coordinator.register_specialized_agent('data_intelligence', mock_data_agent)

        request = "Show me customer data"
        response = coordinator.process_request(request)

        assert response['request'] == request
        assert 'delegations' in response
        assert 'results' in response
        assert 'metadata' in response
        assert response['metadata']['total_delegations'] > 0

    def test_delegation_statistics(self, coordinator, mock_data_agent):
        """Test delegation statistics tracking."""
        coordinator.register_specialized_agent('data_intelligence', mock_data_agent)

        # Process multiple requests
        coordinator.process_request("Show me customer data")
        coordinator.process_request("Analyze campaign performance")

        stats = coordinator.get_delegation_stats()

        assert stats['total_delegations'] >= 2
        assert 'delegations_by_agent' in stats
        assert 'success_rate' in stats

    def test_multiple_delegations_in_single_request(self, coordinator):
        """Test request that triggers multiple delegations."""
        request = "Create a campaign targeting high-value customers with personalized content"
        decisions = coordinator.determine_delegation(request)

        # Should delegate to multiple agents
        assert len(decisions) >= 2
        agent_names = {d.target_agent for d in decisions}

        # Should include at least data and content agents
        assert 'data_intelligence' in agent_names or 'content_generation' in agent_names


class TestDelegationDecision:
    """Test suite for DelegationDecision dataclass."""

    def test_delegation_decision_creation(self):
        """Test creating delegation decision."""
        decision = DelegationDecision(
            target_agent='data_intelligence',
            task_description='Test task',
            parameters={'param1': 'value1'}
        )

        assert decision.target_agent == 'data_intelligence'
        assert decision.task_description == 'Test task'
        assert decision.parameters == {'param1': 'value1'}
        assert decision.requires_human_approval is False

    def test_delegation_decision_with_approval(self):
        """Test delegation decision requiring approval."""
        decision = DelegationDecision(
            target_agent='campaign_design',
            task_description='Launch campaign',
            parameters={},
            requires_human_approval=True,
            approval_reason='Budget over $5000'
        )

        assert decision.requires_human_approval is True
        assert decision.approval_reason == 'Budget over $5000'


class TestAgentResult:
    """Test suite for AgentResult dataclass."""

    def test_agent_result_success(self):
        """Test successful agent result."""
        result = AgentResult(
            agent_name='data_intelligence',
            task='Query data',
            success=True,
            result={'data': [1, 2, 3]}
        )

        assert result.success is True
        assert result.error is None
        assert result.result == {'data': [1, 2, 3]}

    def test_agent_result_failure(self):
        """Test failed agent result."""
        result = AgentResult(
            agent_name='data_intelligence',
            task='Query data',
            success=False,
            error='Connection failed'
        )

        assert result.success is False
        assert result.error == 'Connection failed'
        assert result.result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
