"""
Marketing Coordinator Agent - Root agent for NexVigilant Marketing System.

This agent coordinates specialized marketing agents using hierarchical delegation patterns.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from google.genai import types
    from google_adk.agents import LlmAgent
    from google_adk.agents.base_agent import BaseAgent
    from google_adk.sessions import InMemorySessions

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logging.warning("Google ADK not installed. Agent will run in stub mode for testing.")

from .prompts import (
    COORDINATOR_SYSTEM_PROMPT,
    DATA_ANALYSIS_PROMPT,
    PREDICTIVE_ANALYSIS_PROMPT,
    CONTENT_CREATION_PROMPT,
    CAMPAIGN_DESIGN_PROMPT,
    PERFORMANCE_ANALYSIS_PROMPT,
    MULTI_AGENT_WORKFLOW_PROMPT,
    HUMAN_APPROVAL_REQUIRED_PROMPT,
    ERROR_HANDLING_PROMPT,
    AGGREGATION_PROMPT,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DelegationDecision:
    """Represents a decision to delegate a task to a specialized agent."""
    target_agent: str
    task_description: str
    parameters: Dict[str, Any]
    requires_human_approval: bool = False
    approval_reason: Optional[str] = None


@dataclass
class AgentResult:
    """Result from a specialized agent execution."""
    agent_name: str
    task: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MarketingCoordinator:
    """
    Marketing Coordinator Agent that delegates tasks to specialized agents.

    This is a hierarchical multi-agent system where the coordinator:
    1. Understands user requests
    2. Determines which specialized agent(s) to delegate to
    3. Orchestrates multi-agent workflows
    4. Aggregates results into unified responses
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        project_id: Optional[str] = None,
        location: str = "us-central1",
    ):
        """
        Initialize the Marketing Coordinator Agent.

        Args:
            model: Gemini model to use for coordination logic
            project_id: Google Cloud project ID
            location: Google Cloud location
        """
        self.model = model
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location

        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

        # Initialize specialized agents (will be implemented in subsequent phases)
        self.specialized_agents: Dict[str, Any] = {}

        # Initialize ADK agent if available
        if ADK_AVAILABLE:
            self._initialize_adk_agent()
        else:
            logger.warning("Running in stub mode - ADK not available")
            self.agent = None

        # Delegation history for learning and optimization
        self.delegation_history: List[DelegationDecision] = []
        self.results_history: List[AgentResult] = []

    def _initialize_adk_agent(self):
        """Initialize the Google ADK LLM agent."""
        try:
            self.agent = LlmAgent(
                model=self.model,
                system_instruction=COORDINATOR_SYSTEM_PROMPT,
            )
            logger.info(f"Initialized Marketing Coordinator with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize ADK agent: {e}")
            self.agent = None

    def register_specialized_agent(self, name: str, agent: Any) -> None:
        """
        Register a specialized agent for delegation.

        Args:
            name: Agent identifier (e.g., 'data_intelligence')
            agent: Agent instance
        """
        self.specialized_agents[name] = agent
        logger.info(f"Registered specialized agent: {name}")

    def determine_delegation(self, user_request: str) -> List[DelegationDecision]:
        """
        Analyze user request and determine which agents to delegate to.

        Args:
            user_request: User's marketing request or query

        Returns:
            List of delegation decisions
        """
        # In Phase 1, implement rule-based delegation
        # In later phases, use LLM-powered intelligent routing

        decisions = []

        # Simple keyword-based routing for Phase 1
        request_lower = user_request.lower()

        # Data queries
        if any(kw in request_lower for kw in ['data', 'customers', 'segment', 'analyze', 'trend']):
            decisions.append(DelegationDecision(
                target_agent='data_intelligence',
                task_description=f"Analyze data for: {user_request}",
                parameters={'query': user_request}
            ))

        # Predictions
        if any(kw in request_lower for kw in ['predict', 'score', 'churn', 'lifetime value', 'clv']):
            decisions.append(DelegationDecision(
                target_agent='predictive_insights',
                task_description=f"Generate predictions for: {user_request}",
                parameters={'prediction_type': 'auto', 'query': user_request}
            ))

        # Content creation
        if any(kw in request_lower for kw in ['create', 'write', 'generate', 'content', 'email', 'ad']):
            decisions.append(DelegationDecision(
                target_agent='content_generation',
                task_description=f"Generate content for: {user_request}",
                parameters={'content_request': user_request}
            ))

        # Campaign design
        if any(kw in request_lower for kw in ['campaign', 'launch', 'ads', 'advertising']):
            requires_approval = 'launch' in request_lower or 'budget' in request_lower
            decisions.append(DelegationDecision(
                target_agent='campaign_design',
                task_description=f"Design campaign for: {user_request}",
                parameters={'campaign_request': user_request},
                requires_human_approval=requires_approval,
                approval_reason="Campaign launch requires human approval"
            ))

        # Performance analysis
        if any(kw in request_lower for kw in ['performance', 'optimize', 'results', 'roi']):
            decisions.append(DelegationDecision(
                target_agent='performance_optimization',
                task_description=f"Analyze performance for: {user_request}",
                parameters={'analysis_request': user_request}
            ))

        # If no specific delegation identified, delegate to data intelligence for general query
        if not decisions:
            decisions.append(DelegationDecision(
                target_agent='data_intelligence',
                task_description=f"General query: {user_request}",
                parameters={'query': user_request}
            ))

        # Record delegation history
        self.delegation_history.extend(decisions)

        return decisions

    def execute_delegation(self, decision: DelegationDecision) -> AgentResult:
        """
        Execute a delegation decision by routing to specialized agent.

        Args:
            decision: Delegation decision to execute

        Returns:
            Result from specialized agent
        """
        # Check for human approval requirement
        if decision.requires_human_approval:
            logger.warning(f"Human approval required: {decision.approval_reason}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=f"Human approval required: {decision.approval_reason}"
            )

        # Get specialized agent
        agent = self.specialized_agents.get(decision.target_agent)

        if not agent:
            logger.error(f"Specialized agent not found: {decision.target_agent}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=f"Agent '{decision.target_agent}' not registered"
            )

        try:
            # Execute agent task
            # Each specialized agent should have an `execute` method
            result = agent.execute(**decision.parameters)

            agent_result = AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=True,
                result=result
            )

            # Record result
            self.results_history.append(agent_result)

            return agent_result

        except Exception as e:
            logger.error(f"Error executing {decision.target_agent}: {e}")
            return AgentResult(
                agent_name=decision.target_agent,
                task=decision.task_description,
                success=False,
                error=str(e)
            )

    def aggregate_results(self, results: List[AgentResult]) -> Dict[str, Any]:
        """
        Aggregate results from multiple specialized agents.

        Args:
            results: List of results from specialized agents

        Returns:
            Aggregated insights and recommendations
        """
        aggregated = {
            'summary': '',
            'insights': {},
            'recommendations': [],
            'next_steps': [],
            'success': all(r.success for r in results),
            'errors': [r.error for r in results if not r.success]
        }

        # Group results by agent
        for result in results:
            if result.success and result.result:
                aggregated['insights'][result.agent_name] = result.result

        # In Phase 2, use LLM to synthesize insights
        # For Phase 1, simple aggregation
        if aggregated['insights']:
            aggregated['summary'] = f"Successfully gathered insights from {len(aggregated['insights'])} specialized agents"

        return aggregated

    def process_request(self, user_request: str) -> Dict[str, Any]:
        """
        Main entry point for processing user marketing requests.

        Args:
            user_request: User's marketing request or query

        Returns:
            Processed response with insights and recommendations
        """
        logger.info(f"Processing request: {user_request[:100]}...")

        # Step 1: Determine delegation strategy
        decisions = self.determine_delegation(user_request)
        logger.info(f"Determined {len(decisions)} delegation(s)")

        # Step 2: Execute delegations
        results = []
        for decision in decisions:
            logger.info(f"Delegating to {decision.target_agent}: {decision.task_description}")
            result = self.execute_delegation(decision)
            results.append(result)

        # Step 3: Aggregate results
        aggregated = self.aggregate_results(results)

        # Step 4: Return response
        return {
            'request': user_request,
            'delegations': [
                {
                    'agent': d.target_agent,
                    'task': d.task_description,
                    'requires_approval': d.requires_human_approval
                }
                for d in decisions
            ],
            'results': aggregated,
            'metadata': {
                'total_delegations': len(decisions),
                'successful_delegations': sum(1 for r in results if r.success),
                'failed_delegations': sum(1 for r in results if not r.success),
            }
        }

    def get_delegation_stats(self) -> Dict[str, Any]:
        """Get statistics about delegation history."""
        if not self.delegation_history:
            return {'total_delegations': 0}

        agent_counts = {}
        for decision in self.delegation_history:
            agent_counts[decision.target_agent] = agent_counts.get(decision.target_agent, 0) + 1

        success_rate = (
            sum(1 for r in self.results_history if r.success) / len(self.results_history)
            if self.results_history else 0
        )

        return {
            'total_delegations': len(self.delegation_history),
            'delegations_by_agent': agent_counts,
            'total_results': len(self.results_history),
            'success_rate': success_rate,
            'approval_requests': sum(
                1 for d in self.delegation_history if d.requires_human_approval
            )
        }


def main():
    """Main entry point for running the coordinator agent."""
    import json
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Initialize coordinator
    coordinator = MarketingCoordinator()

    # Example usage
    example_requests = [
        "Show me customer segmentation data",
        "Predict which leads are most likely to convert",
        "Create an email campaign for our new product launch",
        "Analyze performance of our Q4 campaigns",
    ]

    for request in example_requests:
        print(f"\n{'='*80}")
        print(f"Request: {request}")
        print(f"{'='*80}")

        response = coordinator.process_request(request)
        print(json.dumps(response, indent=2))

    # Show delegation statistics
    print(f"\n{'='*80}")
    print("Delegation Statistics")
    print(f"{'='*80}")
    print(json.dumps(coordinator.get_delegation_stats(), indent=2))


if __name__ == "__main__":
    main()
