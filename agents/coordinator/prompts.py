"""
Prompt templates for the Marketing Coordinator Agent.
"""

COORDINATOR_SYSTEM_PROMPT = """You are the Marketing Coordinator Agent for NexVigilant's autonomous marketing system.

Your role is to:
1. Understand marketing objectives and requirements from users
2. Break down complex marketing tasks into specialized subtasks
3. Delegate subtasks to appropriate specialized agents
4. Aggregate results from specialized agents into cohesive strategies
5. Ensure all marketing activities align with business goals and ethical guidelines

Available Specialized Agents:
- **Data Intelligence Agent**: Queries BigQuery for customer insights, segmentation, and trends
- **Predictive Insights Agent**: Provides ML predictions (lead scoring, churn, CLV)
- **Content Generation Agent**: Creates personalized marketing content using Gemini
- **Campaign Design Agent**: Designs multi-channel campaigns (Google Ads, DV360, SA360)
- **Performance Optimization Agent**: Analyzes performance and optimizes campaigns

Delegation Strategy:
- For data-driven questions → Data Intelligence Agent
- For predictions → Predictive Insights Agent
- For content creation → Content Generation Agent
- For campaign setup → Campaign Design Agent
- For performance analysis → Performance Optimization Agent

Human Approval Required For:
- Campaign launches
- Budget changes over $1,000
- Major targeting changes
- Sensitive content categories

Always:
- Explain your reasoning for delegation decisions
- Aggregate insights from multiple agents when needed
- Flag when human approval is required
- Ensure GDPR/CCPA compliance in all activities
- Maintain brand voice: innovative, trustworthy, data-driven
"""

DATA_ANALYSIS_PROMPT = """Analyze the following marketing data request and determine what information is needed from BigQuery:

User Request: {user_request}

Please specify:
1. What data tables/models need to be queried
2. What insights are being requested
3. Any segmentation or filtering criteria
4. Expected output format

Delegate to the Data Intelligence Agent with clear instructions.
"""

PREDICTIVE_ANALYSIS_PROMPT = """For the following prediction request, determine which ML models are needed:

User Request: {user_request}

Available Models:
- Lead Scoring: Predicts conversion probability
- Churn Prediction: Identifies at-risk customers
- CLV Forecast: Estimates customer lifetime value

Specify:
1. Which model(s) to use
2. Required input features
3. How to interpret results
4. Any thresholds or filters

Delegate to the Predictive Insights Agent.
"""

CONTENT_CREATION_PROMPT = """Create marketing content based on this request:

User Request: {user_request}

Guidelines:
- Brand Voice: Innovative, trustworthy, data-driven
- Tone: {tone}
- Content Type: {content_type}
- Target Audience: {target_audience}
- Key Messages: {key_messages}

Delegate to the Content Generation Agent with detailed specifications.
"""

CAMPAIGN_DESIGN_PROMPT = """Design a marketing campaign for the following objective:

Objective: {objective}
Target Audience: {target_audience}
Budget: {budget}
Channels: {channels}
Timeline: {timeline}

Campaign Requirements:
1. Channel strategy and budget allocation
2. Targeting criteria
3. Creative requirements
4. Success metrics and KPIs
5. A/B testing plan

Delegate to the Campaign Design Agent.
"""

PERFORMANCE_ANALYSIS_PROMPT = """Analyze campaign performance and provide optimization recommendations:

Campaign: {campaign_name}
Date Range: {date_range}
Metrics Focus: {metrics}

Analysis Required:
1. Current performance vs. targets
2. Channel-level performance
3. Attribution insights
4. Optimization opportunities
5. Budget reallocation recommendations

Delegate to the Performance Optimization Agent.
"""

MULTI_AGENT_WORKFLOW_PROMPT = """This request requires coordination of multiple specialized agents.

User Request: {user_request}

Workflow Plan:
{workflow_steps}

Execute the workflow in the following sequence:
1. {step_1}
2. {step_2}
3. {step_3}
...

Aggregate results at each step and proceed to the next.
"""

HUMAN_APPROVAL_REQUIRED_PROMPT = """⚠️ HUMAN APPROVAL REQUIRED ⚠️

The following action requires human review and approval:

Action: {action}
Reason: {reason}
Details: {details}

Recommended Decision: {recommendation}

Please review and provide approval before proceeding.
"""

ERROR_HANDLING_PROMPT = """An error occurred while executing a subtask:

Agent: {agent_name}
Task: {task_description}
Error: {error_message}

Possible Recovery Strategies:
1. Retry with modified parameters
2. Delegate to alternative agent
3. Request clarification from user
4. Escalate to human operator

Recommended Action: {recommended_action}
"""

AGGREGATION_PROMPT = """Aggregate insights from multiple specialized agents into a unified response:

Data Intelligence Insights:
{data_insights}

Predictive Insights:
{predictive_insights}

Content Suggestions:
{content_suggestions}

Campaign Recommendations:
{campaign_recommendations}

Performance Analysis:
{performance_analysis}

Synthesize these insights into:
1. Executive Summary
2. Key Findings
3. Actionable Recommendations
4. Next Steps
5. Success Metrics
"""
