"""
Tests for AgentBuilder - Meta-agent system generator.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_builder.main import AgentBuilderAgent, AgentSpec, AgentSystemSpec


def test_agent_builder_initialization():
    """Test AgentBuilder can be initialized."""
    print("\n=== Test 1: AgentBuilder Initialization ===")

    builder = AgentBuilderAgent()

    assert builder is not None
    assert builder.model == "gemini-2.0-flash-exp"

    print("[PASS] AgentBuilder initialization test passed")
    return True


def test_spec_parsing():
    """Test specification parsing."""
    print("\n=== Test 2: Specification Parsing ===")

    builder = AgentBuilderAgent()

    spec_data = {
        'system_name': 'TestSystem',
        'domain': 'test_domain',
        'agents': [
            {
                'name': 'TestAgent',
                'service': 'Test Service',
                'function': 'Test function',
            }
        ],
    }

    spec = builder._parse_spec(**spec_data)

    assert spec.system_name == 'TestSystem'
    assert spec.domain == 'test_domain'
    assert len(spec.agents) == 1
    assert spec.agents[0].name == 'TestAgent'

    print("[PASS] Specification parsing test passed")
    return True


def test_agent_system_generation_stub():
    """Test agent system generation in stub mode."""
    print("\n=== Test 3: Agent System Generation (Stub Mode) ===")

    builder = AgentBuilderAgent()
    # Force stub mode
    builder.client = None

    spec_data = {
        'system_name': 'CustomerService',
        'domain': 'customer_service',
        'agents': [
            {
                'name': 'TicketClassification',
                'service': 'Vertex AI',
                'function': 'Classify support tickets',
            },
            {
                'name': 'ResponseGeneration',
                'service': 'Gemini',
                'function': 'Generate responses',
            },
        ],
        'routing_strategy': 'keyword_based',
        'output_path': '../test_output/',
    }

    result = builder.execute(**spec_data)

    assert result['success'] is True
    assert 'result' in result
    assert result['result']['system_name'] == 'CustomerService'
    assert result['result']['num_agents'] == 2

    print("[PASS] Agent system generation (stub) test passed")
    print(f"   - System: {result['result']['system_name']}")
    print(f"   - Domain: {result['result']['domain']}")
    print(f"   - Agents: {result['result']['num_agents']}")

    return True


def test_requirements_generation():
    """Test requirements.txt generation."""
    print("\n=== Test 4: Requirements Generation ===")

    builder = AgentBuilderAgent()

    spec = AgentSystemSpec(
        system_name='TestSystem',
        domain='test',
        agents=[
            AgentSpec(name='Agent1', service='BigQuery', function='Test'),
            AgentSpec(name='Agent2', service='Vertex AI', function='Test'),
        ],
    )

    requirements = builder._generate_requirements(spec)

    assert 'google-cloud-bigquery' in requirements
    assert 'google-cloud-aiplatform' in requirements
    assert 'pytest' in requirements

    print("[PASS] Requirements generation test passed")
    return True


def test_readme_generation():
    """Test README.md generation."""
    print("\n=== Test 5: README Generation ===")

    builder = AgentBuilderAgent()

    spec = AgentSystemSpec(
        system_name='TestSystem',
        domain='test_domain',
        agents=[
            AgentSpec(name='Agent1', service='BigQuery', function='Test function 1'),
            AgentSpec(name='Agent2', service='Gemini', function='Test function 2'),
        ],
    )

    readme = builder._generate_readme(spec)

    assert 'TestSystem' in readme
    assert 'test_domain' in readme
    assert 'Agent1' in readme
    assert 'Agent2' in readme
    assert 'Quick Start' in readme

    print("[PASS] README generation test passed")
    return True


def test_execute_method_contract():
    """Test that execute() method follows agent contract."""
    print("\n=== Test 6: Execute Method Contract ===")

    builder = AgentBuilderAgent()

    spec_data = {
        'system_name': 'TestSystem',
        'domain': 'test',
        'agents': [
            {
                'name': 'TestAgent',
                'service': 'Test',
                'function': 'Test function',
            }
        ],
    }

    result = builder.execute(**spec_data)

    # Validate standard agent contract
    assert 'success' in result
    assert isinstance(result['success'], bool)
    assert 'metadata' in result

    if result['success']:
        assert 'result' in result
    else:
        assert 'error' in result

    print("[PASS] Execute method contract test passed")
    return True


def test_error_handling():
    """Test error handling for invalid input."""
    print("\n=== Test 7: Error Handling ===")

    builder = AgentBuilderAgent()

    # Test missing required fields
    result = builder.execute(domain='test')  # Missing system_name and agents

    assert result['success'] is False
    assert 'error' in result
    assert 'system_name' in result['error']

    print("[PASS] Error handling test passed")
    print(f"   - Error message: {result['error']}")

    return True


def run_tests():
    """Run all AgentBuilder tests."""
    print("\n" + "="*60)
    print("AGENTBUILDER - UNIT TESTS")
    print("="*60)

    tests = [
        test_agent_builder_initialization,
        test_spec_parsing,
        test_agent_system_generation_stub,
        test_requirements_generation,
        test_readme_generation,
        test_execute_method_contract,
        test_error_handling,
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
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed / (passed + failed) * 100):.1f}%")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
