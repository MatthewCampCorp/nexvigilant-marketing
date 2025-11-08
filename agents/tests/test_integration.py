"""
End-to-end integration test for Marketing Agent System.

This test validates the complete workflow from user request to agent delegation
and result aggregation without requiring BigQuery credentials.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from coordinator.main import MarketingCoordinator, DelegationDecision, AgentResult


class MockDataIntelligenceAgent:
    """Mock Data Intelligence Agent for integration testing."""

    def execute(self, **kwargs):
        """Simulate data analysis execution."""
        return {
            'success': True,
            'analysis_type': 'customer_segmentation',
            'segments': [
                {'segment': 'high_value', 'count': 1250, 'avg_clv': 5000},
                {'segment': 'medium_value', 'count': 3500, 'avg_clv': 1500},
                {'segment': 'low_value', 'count': 5250, 'avg_clv': 300}
            ],
            'insights': [
                'High value segment represents 12.5% of customers but 40% of revenue',
                'Medium value segment shows highest growth potential',
                'Low value segment has highest churn risk'
            ],
            'metadata': {
                'query_time_ms': 450,
                'rows_analyzed': 10000
            }
        }


class MockPredictiveInsightsAgent:
    """Mock Predictive Insights Agent for integration testing."""

    def execute(self, **kwargs):
        """Simulate predictive model execution."""
        return {
            'success': True,
            'prediction_type': 'lead_scoring',
            'predictions': [
                {'lead_id': 'L001', 'score': 0.85, 'conversion_probability': 0.78},
                {'lead_id': 'L002', 'score': 0.72, 'conversion_probability': 0.65},
                {'lead_id': 'L003', 'score': 0.91, 'conversion_probability': 0.88}
            ],
            'model_metrics': {
                'accuracy': 0.84,
                'precision': 0.82,
                'recall': 0.87
            },
            'recommendations': [
                'Prioritize leads with score > 0.80 for immediate follow-up',
                'Schedule follow-up cadence for leads 0.60-0.80',
                'Nurture leads < 0.60 with educational content'
            ]
        }


class MockContentGenerationAgent:
    """Mock Content Generation Agent for integration testing."""

    def execute(self, **kwargs):
        """Simulate content generation."""
        return {
            'success': True,
            'content_type': 'email_campaign',
            'generated_content': {
                'subject_line': 'Exclusive Offer for Our Valued Customers',
                'body': 'Personalized email content based on customer segment...',
                'cta': 'Claim Your Exclusive Offer Now'
            },
            'variants': 3,
            'metadata': {
                'generation_time_ms': 1200,
                'model_version': 'gemini-2.0-flash-exp'
            }
        }


class MockCampaignDesignAgent:
    """Mock Campaign Design Agent for integration testing."""

    def execute(self, **kwargs):
        """Simulate campaign design."""
        return {
            'success': True,
            'campaign_type': 'multi_channel',
            'channels': ['email', 'google_ads', 'social_media'],
            'targeting': {
                'audience': 'high_value_customers',
                'segments': ['high_conversion_probability']
            },
            'budget_allocation': {
                'email': 0.30,
                'google_ads': 0.50,
                'social_media': 0.20
            },
            'timeline': '2_weeks'
        }


def test_single_agent_delegation():
    """Test delegation to a single agent."""
    print("\n=== Test 1: Single Agent Delegation ===")

    # Initialize coordinator
    coordinator = MarketingCoordinator()

    # Register mock agent
    mock_agent = MockDataIntelligenceAgent()
    coordinator.register_specialized_agent('data_intelligence', mock_agent)

    # Process request
    request = "Show me customer segmentation data"
    response = coordinator.process_request(request)

    # Validate response structure
    assert 'request' in response
    assert 'delegations' in response
    assert 'results' in response
    assert 'metadata' in response
    assert response['request'] == request

    # Validate aggregated results (results is a dict, not a list)
    aggregated = response['results']
    assert aggregated['success'] is True, f"Aggregated result not successful: {aggregated}"
    assert 'insights' in aggregated, f"Missing 'insights' in aggregated: {aggregated}"
    assert len(aggregated['insights']) > 0, f"No insights returned: {aggregated}"

    # Get the first insight (data_intelligence)
    agent_result = aggregated['insights'].get('data_intelligence')
    assert agent_result is not None, "data_intelligence results not found"
    assert 'segments' in agent_result, f"Missing 'segments' in agent result: {agent_result}"
    assert len(agent_result['segments']) == 3

    print("[PASS] Single agent delegation test passed")
    print(f"   - Request processed: {request}")
    print(f"   - Delegations: {len(response['delegations'])}")
    print(f"   - Insights from agents: {list(aggregated['insights'].keys())}")
    print(f"   - Success: {aggregated['success']}")

    return True


def test_multi_agent_delegation():
    """Test delegation to multiple agents."""
    print("\n=== Test 2: Multi-Agent Delegation ===")

    # Initialize coordinator
    coordinator = MarketingCoordinator()

    # Register multiple mock agents
    coordinator.register_specialized_agent('data_intelligence', MockDataIntelligenceAgent())
    coordinator.register_specialized_agent('predictive_insights', MockPredictiveInsightsAgent())
    coordinator.register_specialized_agent('content_generation', MockContentGenerationAgent())
    coordinator.register_specialized_agent('campaign_design', MockCampaignDesignAgent())

    # Process complex request requiring multiple agents
    request = "Create a personalized email campaign targeting high-value customers with high conversion probability"
    response = coordinator.process_request(request)

    # Validate response
    assert response['request'] == request
    assert len(response['delegations']) >= 2  # Should delegate to at least 2 agents

    # Check that multiple agents were invoked in aggregated results
    aggregated = response['results']
    agent_types = set(aggregated['insights'].keys())
    print(f"   - Agents invoked: {agent_types}")

    # Validate all results successful
    assert aggregated['success'] is True, f"Aggregated result not successful: {aggregated}"

    print("[PASS] Multi-agent delegation test passed")
    print(f"   - Request processed: {request}")
    print(f"   - Delegations: {len(response['delegations'])}")
    print(f"   - Agents invoked: {len(agent_types)}")
    print(f"   - All successful: {aggregated['success']}")

    return True


def test_result_aggregation():
    """Test aggregation of results from multiple agents."""
    print("\n=== Test 3: Result Aggregation ===")

    # Initialize coordinator
    coordinator = MarketingCoordinator()

    # Create mock results from different agents
    results = [
        AgentResult(
            agent_name='data_intelligence',
            task='Analyze customer segments',
            success=True,
            result={'segments': [{'segment': 'high_value', 'count': 1250}]}
        ),
        AgentResult(
            agent_name='predictive_insights',
            task='Score leads',
            success=True,
            result={'predictions': [{'lead_id': 'L001', 'score': 0.85}]}
        ),
        AgentResult(
            agent_name='content_generation',
            task='Generate email content',
            success=True,
            result={'subject_line': 'Test Email', 'body': 'Test content'}
        )
    ]

    # Aggregate results
    aggregated = coordinator.aggregate_results(results)

    # Validate aggregation
    assert aggregated['success'] is True
    assert len(aggregated['insights']) == 3
    assert 'data_intelligence' in aggregated['insights']
    assert 'predictive_insights' in aggregated['insights']
    assert 'content_generation' in aggregated['insights']

    print("[PASS] Result aggregation test passed")
    print(f"   - Results aggregated: {len(results)}")
    print(f"   - Insights generated: {len(aggregated['insights'])}")
    print(f"   - Success rate: 100%")

    return True


def test_delegation_statistics():
    """Test delegation statistics tracking."""
    print("\n=== Test 4: Delegation Statistics ===")

    # Initialize coordinator
    coordinator = MarketingCoordinator()

    # Register agents
    coordinator.register_specialized_agent('data_intelligence', MockDataIntelligenceAgent())
    coordinator.register_specialized_agent('predictive_insights', MockPredictiveInsightsAgent())

    # Process multiple requests
    coordinator.process_request("Show me customer data")
    coordinator.process_request("Predict lead conversion")
    coordinator.process_request("Analyze customer segments")

    # Get statistics
    stats = coordinator.get_delegation_stats()

    # Validate statistics
    assert stats['total_delegations'] >= 3
    assert 'delegations_by_agent' in stats
    assert 'success_rate' in stats
    assert stats['success_rate'] == 1.0  # All mock agents succeed

    print("[PASS] Delegation statistics test passed")
    print(f"   - Total delegations: {stats['total_delegations']}")
    print(f"   - Success rate: {stats['success_rate'] * 100}%")
    print(f"   - Agents used: {list(stats['delegations_by_agent'].keys())}")

    return True


def test_error_handling():
    """Test error handling when agent is not registered."""
    print("\n=== Test 5: Error Handling ===")

    # Initialize coordinator (no agents registered)
    coordinator = MarketingCoordinator()

    # Create delegation to non-existent agent
    decision = DelegationDecision(
        target_agent='nonexistent_agent',
        task_description='Test task',
        parameters={}
    )

    # Execute delegation
    result = coordinator.execute_delegation(decision)

    # Validate error handling
    assert result.success is False
    assert result.error is not None
    assert 'not registered' in result.error

    print("[PASS] Error handling test passed")
    print(f"   - Error message: {result.error}")

    return True


def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("MARKETING AGENT SYSTEM - INTEGRATION TESTS")
    print("="*60)

    tests = [
        test_single_agent_delegation,
        test_multi_agent_delegation,
        test_result_aggregation,
        test_delegation_statistics,
        test_error_handling
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] Test failed: {test.__name__}")
            print(f"   Error: {str(e)}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] Test error: {test.__name__}")
            print(f"   Error: {str(e)}")

    # Print summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed / (passed + failed) * 100):.1f}%")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
