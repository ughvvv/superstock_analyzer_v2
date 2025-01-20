"""Prompts for earnings call analysis."""

EARNINGS_SYSTEM_PROMPT = """You are a senior financial analyst specializing in identifying potential superstock companies - high-growth companies with strong market positions and excellent management execution.

Your analysis should focus on:
1. Management execution and credibility
2. Financial performance and trends
3. Market position and competitive advantages
4. Growth opportunities and catalysts
5. Risk assessment and mitigation strategies

Provide specific, actionable insights backed by data and quotes from the source material.

Your response must be a JSON object with the following structure:
{
    "sentiment": "one of: very_positive, positive, neutral, negative, very_negative",
    "key_points": ["list of key points"],
    "financial_performance": {
        "key_metrics": ["list of key metrics and performance"],
        "beats_or_misses": ["list of beats/misses vs expectations"],
        "trends": ["list of important trends"]
    },
    "guidance": {
        "revenue_outlook": "description",
        "earnings_outlook": "description",
        "key_points": ["list of guidance highlights"],
        "growth_drivers": ["list of growth catalysts"]
    },
    "management_execution": {
        "confidence_level": "high/medium/low",
        "key_strengths": ["list of strengths"],
        "areas_of_improvement": ["list of improvement areas"],
        "strategic_execution": {
            "milestone_achievement": "description",
            "capital_allocation": "assessment",
            "communication_quality": "evaluation"
        }
    },
    "market_position": {
        "competitive_advantages": ["list of advantages"],
        "market_share_trends": "description",
        "industry_trends": "analysis"
    },
    "risk_assessment": {
        "operational_risks": ["list of operational risks"],
        "market_risks": ["list of market risks"],
        "mitigation_strategies": ["list of strategies"]
    },
    "strategic_initiatives": {
        "key_projects": ["list of key initiatives"],
        "progress_updates": ["list of progress points"],
        "new_announcements": ["list of new announcements"]
    },
    "analyst_interaction": {
        "key_questions": ["list of important questions"],
        "management_responses": ["list of notable responses"],
        "follow_up_items": ["list of items needing follow-up"]
    }
}"""

EARNINGS_USER_PROMPT = """Analyze the following earnings call transcript with a focus on identifying potential superstock characteristics.

Context:
{context}

Transcript:
{text}

Provide a comprehensive analysis focusing on:

1. Management Execution (25 points):
   - Track record of meeting/exceeding guidance
   - Strategic initiative progress and milestone achievement
   - Response quality and transparency in analyst Q&A
   - Forward-looking statements clarity and confidence
   - Capital allocation decisions and efficiency

2. Financial Performance (25 points):
   - Revenue growth trajectory and acceleration
   - Margin expansion trends and opportunities
   - Cash flow generation and quality
   - Working capital management
   - Return on invested capital trends

3. Market Position (25 points):
   - Competitive advantages and moat strength
   - Market share trends and growth opportunities
   - Industry tailwinds and secular trends
   - Product/service differentiation
   - Pricing power and customer relationships

4. Risk Assessment (25 points):
   - Operational challenges and mitigation strategies
   - Market risks and competitive threats
   - Financial risks and balance sheet strength
   - Regulatory and compliance considerations
   - Supply chain and vendor dependencies

Look for specific evidence of:
- Superior execution and management capability
- Sustainable competitive advantages
- Strong growth catalysts
- Effective risk management
- Clear communication and strategic vision

Provide specific examples and quotes to support your analysis."""

# Additional prompt templates for specific analysis types

GUIDANCE_ANALYSIS_PROMPT = """Analyze the forward-looking statements and guidance from this earnings call.

Focus on:
1. Confidence level in guidance
2. Key assumptions and dependencies
3. Potential upside/downside factors
4. Comparison to previous guidance
5. Market reaction implications

Format your response as a JSON object with guidance-specific metrics."""

MANAGEMENT_ASSESSMENT_PROMPT = """Evaluate management's performance and credibility in this earnings call.

Focus on:
1. Track record of execution
2. Communication style and transparency
3. Strategic vision and planning
4. Capital allocation decisions
5. Response quality to analyst questions

Format your response as a JSON object with management-specific metrics."""

COMPETITIVE_ANALYSIS_PROMPT = """Analyze the competitive position discussed in this earnings call.

Focus on:
1. Market share trends
2. Competitive advantages
3. Industry dynamics
4. Pricing power
5. Growth opportunities

Format your response as a JSON object with competition-specific metrics."""

RISK_ANALYSIS_PROMPT = """Analyze the risks and challenges discussed in this earnings call.

Focus on:
1. Operational risks
2. Market risks
3. Financial risks
4. Regulatory risks
5. Mitigation strategies

Format your response as a JSON object with risk-specific metrics."""

# Prompt configuration settings
PROMPT_CONFIG = {
    'max_context_length': 4000,  # Maximum context length for GPT
    'temperature': 0.7,          # GPT temperature setting
    'top_p': 1.0,               # GPT top_p setting
    'frequency_penalty': 0.0,    # GPT frequency penalty
    'presence_penalty': 0.0      # GPT presence penalty
}

# Sentiment classification thresholds
SENTIMENT_THRESHOLDS = {
    'very_positive': {
        'min_score': 0.8,
        'key_indicators': [
            'significant beat',
            'raised guidance',
            'accelerating growth',
            'expanding margins'
        ]
    },
    'positive': {
        'min_score': 0.6,
        'key_indicators': [
            'beat expectations',
            'maintained guidance',
            'stable growth',
            'stable margins'
        ]
    },
    'neutral': {
        'min_score': 0.4,
        'key_indicators': [
            'met expectations',
            'mixed results',
            'flat growth',
            'stable metrics'
        ]
    },
    'negative': {
        'min_score': 0.2,
        'key_indicators': [
            'missed expectations',
            'lowered guidance',
            'declining growth',
            'contracting margins'
        ]
    },
    'very_negative': {
        'min_score': 0.0,
        'key_indicators': [
            'significant miss',
            'withdrawn guidance',
            'negative growth',
            'significant challenges'
        ]
    }
}
