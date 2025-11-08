"""
Prompts for AgentBuilder - Gemini-powered code generation for agent systems.
"""

AGENT_BUILDER_SYSTEM_PROMPT = """You are an expert AI agent architect specializing in building multi-agent systems using Google Cloud Platform.

Your expertise includes:
- Hierarchical delegation patterns
- Google Agent Development Kit (ADK)
- Vertex AI, BigQuery, Gemini integration
- Test-driven development
- Production-ready code generation

You follow the Agent Adaptation Playbook methodology and generate code that is:
- Clean, well-documented, and type-hinted
- Thoroughly tested (unit + integration)
- Production-ready with error handling
- Secure with proper validation
- Supports stub mode for testing without credentials

Output Format:
Always return valid Python code that can be executed directly.
Include comprehensive docstrings and type hints.
Follow PEP 8 style guidelines.
"""

SERVICE_INITIALIZATION_PROMPT = """Generate Python code to initialize the {service} client with proper error handling and stub mode fallback.

Service: {service}
Agent: {agent_name}
Purpose: {purpose}

Requirements:
1. Try to initialize production client
2. Catch exceptions and fallback to stub mode (self.client = None)
3. Log initialization status
4. Use environment variables for configuration

Return ONLY the Python code for the __init__ method's service initialization section (the try/except block).
Do not include the method signature or other parts of __init__.
"""

PRODUCTION_IMPLEMENTATION_PROMPT = """Generate Python code for the production implementation of {agent_name}.

Agent: {agent_name}
Service: {service}
Function: {function}
Parameters: {parameters}

Requirements:
1. Implement the actual cloud service integration
2. Process input parameters appropriately
3. Return structured data matching the agent contract
4. Include appropriate logging
5. Handle service-specific errors

Return ONLY the Python code for the _execute_production method body.
Do not include the method signature.
"""

STUB_IMPLEMENTATION_PROMPT = """Generate Python code for the stub implementation of {agent_name}.

Agent: {agent_name}
Service: {service}
Function: {function}

Requirements:
1. Return realistic test data that matches production structure
2. Include all expected fields
3. Make data meaningful for testing
4. Log that stub mode is active

Return ONLY the Python code for the _execute_stub method body.
Do not include the method signature.
"""

MOCK_AGENT_PROMPT = """Generate Python code for a mock version of {agent_name} for integration testing.

Agent: {agent_name}
Function: {function}

Requirements:
1. Create a MockXxxAgent class
2. Implement execute(**kwargs) method
3. Return realistic test data matching production structure
4. Include success: True and appropriate result data

Return ONLY the Python class definition for the mock agent.
"""

KEYWORD_MAPPING_PROMPT = """Generate keyword mappings for routing user requests to specialized agents.

Domain: {domain}
Agents: {agents}

For each agent, provide 5-7 keywords that would indicate a user request should be routed to that agent.

Return as Python dict format:
{{'agent_name': ['keyword1', 'keyword2', ...], ...}}
"""

CAPABILITIES_PROMPT = """Generate a bulleted list of capabilities for {agent_name}.

Agent: {agent_name}
Service: {service}
Function: {function}

Return 3-5 specific capabilities as bulleted list items (just the text, not the bullets).
Each capability should be one concise sentence.
"""

EXAMPLE_REQUESTS_PROMPT = """Generate example user requests for {system_name}.

Domain: {domain}
Agents: {agents}

Generate 3-5 example user requests that would demonstrate the multi-agent system capabilities.
Each request should route to at least one agent.

Return as Python list of strings:
["Request 1", "Request 2", ...]
"""

TEST_PARAMETERS_PROMPT = """Generate test parameters for {agent_name}.

Agent: {agent_name}
Service: {service}
Function: {function}

Generate realistic test parameters that would be passed to the execute() method.

Return as Python dict format:
{{'param1': value1, 'param2': value2, ...}}
"""
