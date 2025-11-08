"""
AgentBuilder - Meta-agent that generates complete agent systems.

This agent uses the Agent Adaptation Playbook methodology to generate
production-ready multi-agent systems with coordinator, specialized agents,
tests, and documentation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import google.genai as genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("google-genai not installed. AgentBuilder will run in stub mode.")

from .prompts import (
    AGENT_BUILDER_SYSTEM_PROMPT,
    SERVICE_INITIALIZATION_PROMPT,
    PRODUCTION_IMPLEMENTATION_PROMPT,
    STUB_IMPLEMENTATION_PROMPT,
    MOCK_AGENT_PROMPT,
    KEYWORD_MAPPING_PROMPT,
    CAPABILITIES_PROMPT,
    EXAMPLE_REQUESTS_PROMPT,
    TEST_PARAMETERS_PROMPT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentSpec:
    """Specification for a specialized agent."""
    name: str
    service: str
    function: str
    description: Optional[str] = None
    parameters: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


@dataclass
class AgentSystemSpec:
    """Complete specification for an agent system."""
    system_name: str
    domain: str
    agents: List[AgentSpec]
    routing_strategy: str = "keyword_based"  # or "llm_powered", "ml_classifier"
    output_path: str = "../generated_agents/"


class AgentBuilderAgent:
    """
    AgentBuilder - Meta-agent that generates complete agent systems.

    Capabilities:
    - Guides through 5-phase Agent Adaptation Playbook methodology
    - Generates coordinator with hierarchical delegation
    - Generates specialized agents with stub mode
    - Creates comprehensive integration tests
    - Produces documentation automatically
    - Uses Gemini for intelligent code generation

    Service Integration: Gemini (for code generation)
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        project_id: Optional[str] = None,
        location: str = "us-central1",
    ):
        """Initialize AgentBuilder Agent."""
        self.model = model
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location

        # Initialize Gemini client (with stub mode fallback)
        if GENAI_AVAILABLE:
            try:
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
                logger.info(f"{self.__class__.__name__} initialized (production mode)")
            except Exception as e:
                logger.warning(f"Gemini unavailable: {e}. Using stub mode.")
                self.client = None
        else:
            self.client = None
            logger.info(f"{self.__class__.__name__} initialized (stub mode)")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main entry point called by coordinator.

        Args:
            system_name (str): Name of the agent system (e.g., "CustomerService")
            domain (str): Domain area (e.g., "customer_service", "operations")
            agents (List[Dict]): List of agent specifications
                Each agent dict should have:
                - name (str): Agent name
                - service (str): Cloud service used
                - function (str): What the agent does
                - description (str, optional): Detailed description
                - parameters (List[str], optional): Input parameters
                - keywords (List[str], optional): Routing keywords
            routing_strategy (str, optional): "keyword_based" (default), "llm_powered", "ml_classifier"
            output_path (str, optional): Where to generate the code (default: "../generated_agents/")

        Returns:
            Dict with 'success': bool and generation results
        """
        try:
            # Parse and validate input
            spec = self._parse_spec(**kwargs)

            # Generate the complete agent system
            if self.client:
                result = self._execute_production(spec)
            else:
                result = self._execute_stub(spec)

            return {
                'success': True,
                'result': result,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent': self.__class__.__name__,
                    'mode': 'production' if self.client else 'stub',
                }
            }

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent': self.__class__.__name__,
                }
            }

    def _parse_spec(self, **kwargs) -> AgentSystemSpec:
        """Parse and validate agent system specification."""
        system_name = kwargs.get('system_name')
        if not system_name:
            raise ValueError("system_name is required")

        domain = kwargs.get('domain')
        if not domain:
            raise ValueError("domain is required")

        agents_data = kwargs.get('agents', [])
        if not agents_data:
            raise ValueError("At least one agent specification is required")

        # Parse agent specs
        agents = []
        for agent_data in agents_data:
            agents.append(AgentSpec(
                name=agent_data['name'],
                service=agent_data['service'],
                function=agent_data['function'],
                description=agent_data.get('description'),
                parameters=agent_data.get('parameters', []),
                keywords=agent_data.get('keywords', []),
            ))

        return AgentSystemSpec(
            system_name=system_name,
            domain=domain,
            agents=agents,
            routing_strategy=kwargs.get('routing_strategy', 'keyword_based'),
            output_path=kwargs.get('output_path', '../generated_agents/'),
        )

    def _execute_production(self, spec: AgentSystemSpec) -> Dict[str, Any]:
        """Production implementation using Gemini for code generation."""
        logger.info(f"Generating agent system: {spec.system_name}")

        # Create output directory structure
        files_created = self._create_directory_structure(spec)

        # Generate coordinator
        coordinator_code = self._generate_coordinator(spec)
        coordinator_path = Path(spec.output_path) / spec.domain / "coordinator" / "main.py"
        coordinator_path.write_text(coordinator_code)
        files_created.append(str(coordinator_path))

        # Generate each specialized agent
        agent_files = []
        for agent in spec.agents:
            agent_code = self._generate_agent(agent, spec)
            agent_dir = Path(spec.output_path) / spec.domain / agent.name.lower()
            agent_path = agent_dir / "main.py"
            agent_path.write_text(agent_code)
            files_created.append(str(agent_path))
            agent_files.append({
                'name': agent.name,
                'path': str(agent_path),
                'service': agent.service,
            })

        # Generate integration tests
        test_code = self._generate_integration_tests(spec)
        test_path = Path(spec.output_path) / spec.domain / "tests" / "test_integration.py"
        test_path.write_text(test_code)
        files_created.append(str(test_path))

        # Generate requirements.txt
        requirements = self._generate_requirements(spec)
        req_path = Path(spec.output_path) / spec.domain / "requirements.txt"
        req_path.write_text(requirements)
        files_created.append(str(req_path))

        # Generate README.md
        readme = self._generate_readme(spec)
        readme_path = Path(spec.output_path) / spec.domain / "README.md"
        readme_path.write_text(readme)
        files_created.append(str(readme_path))

        return {
            'system_name': spec.system_name,
            'domain': spec.domain,
            'num_agents': len(spec.agents),
            'agents': agent_files,
            'output_path': spec.output_path,
            'files_created': files_created,
            'routing_strategy': spec.routing_strategy,
            'next_steps': [
                f"cd {spec.output_path}/{spec.domain}",
                "python -m venv venv",
                "./venv/Scripts/activate",
                "pip install -r requirements.txt",
                "pytest tests/test_integration.py -v",
            ],
        }

    def _execute_stub(self, spec: AgentSystemSpec) -> Dict[str, Any]:
        """Stub implementation for testing without Gemini."""
        logger.info(f"Generating agent system (stub mode): {spec.system_name}")

        return {
            'system_name': spec.system_name,
            'domain': spec.domain,
            'num_agents': len(spec.agents),
            'agents': [
                {
                    'name': agent.name,
                    'path': f'{spec.output_path}/{spec.domain}/{agent.name.lower()}/main.py',
                    'service': agent.service,
                }
                for agent in spec.agents
            ],
            'output_path': spec.output_path,
            'files_created': ['(stub mode - files not actually created)'],
            'routing_strategy': spec.routing_strategy,
            'note': 'Stub mode: Files not actually generated. Install google-genai for production.',
        }

    def _create_directory_structure(self, spec: AgentSystemSpec) -> List[str]:
        """Create the directory structure for the agent system."""
        base_path = Path(spec.output_path) / spec.domain

        directories = [
            base_path,
            base_path / "coordinator" / "tests",
            base_path / "tests",
        ]

        # Create directory for each specialized agent
        for agent in spec.agents:
            agent_dir = base_path / agent.name.lower()
            directories.extend([
                agent_dir,
                agent_dir / "tests",
            ])

        # Create all directories
        created = []
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Create __init__.py in each
            init_file = directory / "__init__.py"
            if not init_file.exists() and directory.name != "tests":
                init_file.write_text(f'"""{directory.name.replace("_", " ").title()} package."""\n')
                created.append(str(init_file))

        return created

    def _generate_coordinator(self, spec: AgentSystemSpec) -> str:
        """Generate coordinator code using template and Gemini."""
        # Load template
        template_path = Path(__file__).parent / "templates" / "coordinator_template.py"
        template = template_path.read_text()

        # Generate keyword mappings using Gemini
        keyword_mappings = self._generate_keyword_mappings(spec)

        # Generate example requests
        example_requests = self._generate_example_requests(spec)

        # Format template
        coordinator_class_name = f"{spec.system_name.replace(' ', '')}Coordinator"
        agent_list = "\n".join([f"    - {agent.name}: {agent.function}" for agent in spec.agents])

        keyword_mapping_lines = []
        for agent_name, keywords in keyword_mappings.items():
            keywords_str = ", ".join([f"'{kw}'" for kw in keywords])
            keyword_mapping_lines.append(f"            '{agent_name}': [{keywords_str}],")
        keyword_mappings_str = "\n".join(keyword_mapping_lines)

        example_requests_str = "\n".join([f'        "{req}",' for req in example_requests])

        routing_comment = {
            'keyword_based': 'Phase 1: Keyword-based routing',
            'llm_powered': 'Phase 2: LLM-powered routing (upgrade from keyword-based)',
            'ml_classifier': 'Phase 3: ML classifier routing (trained on historical data)',
        }.get(spec.routing_strategy, 'Keyword-based routing')

        code = template.format(
            system_name=spec.system_name,
            num_agents=len(spec.agents),
            coordinator_class_name=coordinator_class_name,
            agent_list=agent_list,
            routing_strategy_comment=routing_comment,
            keyword_mappings=keyword_mappings_str,
            default_agent=spec.agents[0].name.lower().replace(' ', '_') if spec.agents else 'default',
            example_requests=example_requests_str,
            timestamp=datetime.utcnow().isoformat(),
        )

        return code

    def _generate_agent(self, agent: AgentSpec, spec: AgentSystemSpec) -> str:
        """Generate specialized agent code using template and Gemini."""
        # Load template
        template_path = Path(__file__).parent / "templates" / "agent_template.py"
        template = template_path.read_text()

        # Generate code sections using Gemini
        service_init = self._generate_service_initialization(agent)
        production_impl = self._generate_production_implementation(agent)
        stub_impl = self._generate_stub_implementation(agent)
        capabilities = self._generate_capabilities(agent)
        test_params = self._generate_test_parameters(agent)

        # Format template
        agent_class_name = f"{agent.name.replace(' ', '')}Agent"

        capabilities_list = "\n".join([f"    - {cap}" for cap in capabilities])
        param_docs = "\n".join([f"            {param}: {param} value" for param in (agent.parameters or [])])
        test_params_str = "\n".join([f"        '{k}': {repr(v)}," for k, v in test_params.items()])

        code = template.format(
            agent_name=agent.name,
            description=agent.description or agent.function,
            function=agent.function,
            service=agent.service,
            agent_class_name=agent_class_name,
            purpose=agent.function,
            capabilities=capabilities_list,
            service_initialization=service_init,
            parameter_docs=param_docs,
            production_implementation=production_impl,
            stub_implementation=stub_impl,
            test_parameters=test_params_str,
            timestamp=datetime.utcnow().isoformat(),
        )

        return code

    def _generate_integration_tests(self, spec: AgentSystemSpec) -> str:
        """Generate integration tests using template and Gemini."""
        # Load template
        template_path = Path(__file__).parent / "templates" / "integration_test_template.py"
        template = template_path.read_text()

        # Generate mock agent classes
        mock_classes = []
        for agent in spec.agents:
            mock_code = self._generate_mock_agent(agent)
            mock_classes.append(mock_code)

        mock_agent_classes_str = "\n\n".join(mock_classes)

        # Format registrations
        agent_registrations = "\n".join([
            f"    coordinator.register_specialized_agent('{agent.name.lower().replace(' ', '_')}', Mock{agent.name.replace(' ', '')}Agent())"
            for agent in spec.agents
        ])

        # Format mock results
        mock_results = []
        for agent in spec.agents:
            mock_results.append(f"""        AgentResult(
            agent_name='{agent.name.lower().replace(' ', '_')}',
            task='{agent.function}',
            success=True,
            result={{'test': 'data'}}
        ),""")
        mock_results_str = "\n".join(mock_results)

        # Format workflow requests
        workflow_requests_list = [f'        "{agent.function}",' for agent in spec.agents]
        workflow_requests_str = "\n".join(workflow_requests_list)

        coordinator_class_name = f"{spec.system_name.replace(' ', '')}Coordinator"
        first_agent_name = spec.agents[0].name.lower().replace(' ', '_')
        first_mock_agent = f"Mock{spec.agents[0].name.replace(' ', '')}Agent"

        code = template.format(
            system_name=spec.system_name,
            timestamp=datetime.utcnow().isoformat(),
            coordinator_class_name=coordinator_class_name,
            mock_agent_classes=mock_agent_classes_str,
            first_agent_name=first_agent_name,
            first_mock_agent=first_mock_agent,
            first_test_request=f"Test {spec.agents[0].function}",
            agent_registrations=agent_registrations,
            multi_agent_test_request=f"Complex request requiring multiple {spec.domain} agents",
            mock_results=mock_results_str,
            num_agents=len(spec.agents),
            stats_agent_registrations=agent_registrations,
            stats_test_requests="\n".join([f'    coordinator.process_request("{agent.function}")' for agent in spec.agents[:3]]),
            complete_workflow_registrations=agent_registrations,
            workflow_requests=workflow_requests_str,
        )

        return code

    def _generate_keyword_mappings(self, spec: AgentSystemSpec) -> Dict[str, List[str]]:
        """Generate keyword mappings for routing using Gemini."""
        if not self.client:
            # Stub fallback
            return {
                agent.name.lower().replace(' ', '_'): agent.keywords or ['keyword1', 'keyword2']
                for agent in spec.agents
            }

        prompt = KEYWORD_MAPPING_PROMPT.format(
            domain=spec.domain,
            agents="\n".join([f"- {agent.name}: {agent.function}" for agent in spec.agents])
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )

            # Parse response (expected to be Python dict format)
            result_text = response.text.strip()
            # Remove code blocks if present
            if '```' in result_text:
                result_text = result_text.split('```python')[-1].split('```')[0].strip()

            # Evaluate as Python dict
            keyword_map = eval(result_text)
            return keyword_map

        except Exception as e:
            logger.warning(f"Failed to generate keyword mappings: {e}. Using defaults.")
            return {
                agent.name.lower().replace(' ', '_'): agent.keywords or ['keyword1', 'keyword2']
                for agent in spec.agents
            }

    def _generate_service_initialization(self, agent: AgentSpec) -> str:
        """Generate service initialization code using Gemini."""
        if not self.client:
            return "            self.client = None  # Stub mode"

        prompt = SERVICE_INITIALIZATION_PROMPT.format(
            service=agent.service,
            agent_name=agent.name,
            purpose=agent.function,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=512,
                )
            )

            code = response.text.strip()
            # Remove code blocks if present
            if '```' in code:
                code = code.split('```python')[-1].split('```')[0].strip()

            return code

        except Exception as e:
            logger.warning(f"Failed to generate service initialization: {e}")
            return "            self.client = None  # Generated in stub mode"

    def _generate_production_implementation(self, agent: AgentSpec) -> str:
        """Generate production implementation using Gemini."""
        if not self.client:
            return "        # TODO: Implement production logic\n        return {'data': 'production_stub'}"

        prompt = PRODUCTION_IMPLEMENTATION_PROMPT.format(
            agent_name=agent.name,
            service=agent.service,
            function=agent.function,
            parameters=", ".join(agent.parameters or ['query']),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )

            code = response.text.strip()
            if '```' in code:
                code = code.split('```python')[-1].split('```')[0].strip()

            return code

        except Exception as e:
            logger.warning(f"Failed to generate production implementation: {e}")
            return "        # TODO: Implement production logic\n        return {'data': 'production_stub'}"

    def _generate_stub_implementation(self, agent: AgentSpec) -> str:
        """Generate stub implementation using Gemini."""
        if not self.client:
            return "        return {'data': 'test_stub', 'mode': 'stub'}"

        prompt = STUB_IMPLEMENTATION_PROMPT.format(
            agent_name=agent.name,
            service=agent.service,
            function=agent.function,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=512,
                )
            )

            code = response.text.strip()
            if '```' in code:
                code = code.split('```python')[-1].split('```')[0].strip()

            return code

        except Exception as e:
            logger.warning(f"Failed to generate stub implementation: {e}")
            return "        return {'data': 'test_stub', 'mode': 'stub'}"

    def _generate_mock_agent(self, agent: AgentSpec) -> str:
        """Generate mock agent class for testing using Gemini."""
        if not self.client:
            class_name = f"Mock{agent.name.replace(' ', '')}Agent"
            return f"""class {class_name}:
    def execute(self, **kwargs):
        return {{'success': True, 'result': {{'test': 'data'}}, 'mode': 'mock'}}"""

        prompt = MOCK_AGENT_PROMPT.format(
            agent_name=agent.name,
            function=agent.function,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=512,
                )
            )

            code = response.text.strip()
            if '```' in code:
                code = code.split('```python')[-1].split('```')[0].strip()

            return code

        except Exception as e:
            logger.warning(f"Failed to generate mock agent: {e}")
            class_name = f"Mock{agent.name.replace(' ', '')}Agent"
            return f"""class {class_name}:
    def execute(self, **kwargs):
        return {{'success': True, 'result': {{'test': 'data'}}, 'mode': 'mock'}}"""

    def _generate_capabilities(self, agent: AgentSpec) -> List[str]:
        """Generate capabilities list using Gemini."""
        if not self.client:
            return [
                f"Capability 1 for {agent.name}",
                f"Capability 2 for {agent.name}",
                f"Capability 3 for {agent.name}",
            ]

        prompt = CAPABILITIES_PROMPT.format(
            agent_name=agent.name,
            service=agent.service,
            function=agent.function,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=256,
                )
            )

            text = response.text.strip()
            # Parse as list
            capabilities = [line.strip('- ').strip() for line in text.split('\n') if line.strip()]
            return capabilities[:5]  # Max 5 capabilities

        except Exception as e:
            logger.warning(f"Failed to generate capabilities: {e}")
            return [f"{agent.function} capability {i+1}" for i in range(3)]

    def _generate_example_requests(self, spec: AgentSystemSpec) -> List[str]:
        """Generate example requests using Gemini."""
        if not self.client:
            return [f"Example request for {agent.name}" for agent in spec.agents[:3]]

        prompt = EXAMPLE_REQUESTS_PROMPT.format(
            system_name=spec.system_name,
            domain=spec.domain,
            agents="\n".join([f"- {agent.name}: {agent.function}" for agent in spec.agents]),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                )
            )

            text = response.text.strip()
            if '```' in text:
                text = text.split('```python')[-1].split('```')[0].strip()

            # Evaluate as Python list
            requests = eval(text)
            return requests[:5]  # Max 5 example requests

        except Exception as e:
            logger.warning(f"Failed to generate example requests: {e}")
            return [f"Example request {i+1}" for i in range(3)]

    def _generate_test_parameters(self, agent: AgentSpec) -> Dict[str, Any]:
        """Generate test parameters using Gemini."""
        if not self.client:
            return {param: f"test_{param}" for param in (agent.parameters or ['query'])}

        prompt = TEST_PARAMETERS_PROMPT.format(
            agent_name=agent.name,
            service=agent.service,
            function=agent.function,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=256,
                )
            )

            text = response.text.strip()
            if '```' in text:
                text = text.split('```python')[-1].split('```')[0].strip()

            # Evaluate as Python dict
            params = eval(text)
            return params

        except Exception as e:
            logger.warning(f"Failed to generate test parameters: {e}")
            return {param: f"test_{param}" for param in (agent.parameters or ['query'])}

    def _generate_requirements(self, spec: AgentSystemSpec) -> str:
        """Generate requirements.txt based on services used."""
        requirements = [
            "# Core agent framework",
            "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",
            "google-genai>=1.9.0",
            "",
            "# Cloud services",
        ]

        services_used = {agent.service for agent in spec.agents}

        service_packages = {
            'BigQuery': 'google-cloud-bigquery>=3.11.0',
            'Vertex AI': 'google-cloud-aiplatform>=1.93.0',
            'Cloud Storage': 'google-cloud-storage>=2.10.0',
            'Pub/Sub': 'google-cloud-pubsub>=2.18.0',
            'Cloud Logging': 'google-cloud-logging>=3.5.0',
        }

        for service in services_used:
            if service in service_packages:
                requirements.append(service_packages[service])

        requirements.extend([
            "",
            "# Data validation",
            "pydantic>=2.10.6",
            "",
            "# Testing",
            "pytest>=8.3.2",
            "pytest-asyncio>=0.23.7",
            "pytest-cov>=4.1.0",
            "",
            "# Development",
            "black>=24.0.0",
            "ruff>=0.4.6",
        ])

        return "\n".join(requirements)

    def _generate_readme(self, spec: AgentSystemSpec) -> str:
        """Generate README.md for the agent system."""
        agent_list = "\n".join([
            f"- **{agent.name}**: {agent.function} (using {agent.service})"
            for agent in spec.agents
        ])

        return f"""# {spec.system_name} Agent System

## Overview

Multi-agent system for {spec.domain} automation using hierarchical delegation pattern.

**Generated by**: AgentBuilder
**Date**: {datetime.utcnow().isoformat()}
**Domain**: {spec.domain}
**Agents**: {len(spec.agents)} specialized agents

## Architecture

```
{spec.system_name}Coordinator
├── Hierarchical delegation
├── {spec.routing_strategy} routing
└── {len(spec.agents)} specialized agents
```

## Specialized Agents

{agent_list}

## Quick Start

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
./venv/Scripts/activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Authentication

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Run Tests

```bash
# Run all tests
pytest -v

# Run integration tests
pytest tests/test_integration.py -v
```

### Run Coordinator

```bash
python -m coordinator.main
```

## Project Structure

```
{spec.domain}/
├── coordinator/
│   ├── main.py
│   └── tests/
├── {spec.agents[0].name.lower()}/
│   ├── main.py
│   └── tests/
... (more agents)
├── tests/
│   └── test_integration.py
├── requirements.txt
└── README.md
```

## Next Steps

1. Review generated code
2. Customize agent implementations
3. Add domain-specific logic
4. Run tests and validate
5. Deploy to production

## Documentation

- [Agent Adaptation Playbook](../../AGENT_ADAPTATION_PLAYBOOK.md)
- [CLAUDE.md](../../CLAUDE.md)

---

🤖 Generated with AgentBuilder
"""


def main():
    """Test the AgentBuilder directly."""
    import json

    builder = AgentBuilderAgent()

    # Example: Generate a customer service agent system
    test_spec = {
        'system_name': 'CustomerService',
        'domain': 'customer_service',
        'agents': [
            {
                'name': 'TicketClassification',
                'service': 'Vertex AI',
                'function': 'Classify support tickets by category and priority',
                'parameters': ['ticket_text', 'metadata'],
                'keywords': ['classify', 'ticket', 'category', 'priority'],
            },
            {
                'name': 'KnowledgeBase',
                'service': 'Vertex AI Search',
                'function': 'Search internal documentation for solutions',
                'parameters': ['query', 'filters'],
                'keywords': ['search', 'documentation', 'knowledge', 'help'],
            },
            {
                'name': 'ResponseGeneration',
                'service': 'Gemini',
                'function': 'Generate contextual customer responses',
                'parameters': ['context', 'tone'],
                'keywords': ['generate', 'response', 'reply', 'answer'],
            },
        ],
        'routing_strategy': 'keyword_based',
        'output_path': '../customer_service_agents/',
    }

    result = builder.execute(**test_spec)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
