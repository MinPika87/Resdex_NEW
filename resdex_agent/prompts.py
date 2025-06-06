# Replace the prompts.py with selective thinking approach

"""
Selective thinking prompts - Think for complex operations, direct for UI responses.
"""

from typing import Dict, Any


class RootAgentPrompts:
    """Prompts with selective thinking based on operation type."""
    
    @staticmethod
    def get_routing_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """Routing prompt - ALLOW thinking for better accuracy."""
        
        return f"""You are a routing assistant for a candidate search system. Think through the classification and respond with JSON.
DONOT HALUCINATE AND RESPOND FAST
Current context:
- Active search filters: {session_state.get('keywords', [])}
- Current candidates: {len(session_state.get('candidates', []))} results

User input: "{user_input}"

<think>
Reason it fast very fast, route to specific tool fast
Analyze the user input to determine if this is:
1. Search/filter operations (adding skills, modifying criteria, searching)
2. General conversation/questions (greetings, help, analysis requests)

Consider the context and user intent carefully.
</think>

ROUTING RULES:
1. If input involves SEARCH/FILTER operations → route to "search_interaction"
2. If input is general conversation/analysis → route to "general_query"

SEARCH/FILTER indicators:
- Adding/removing skills, experience, salary, location filters
- Search commands: "search with", "find", "show me", "filter by"
- Modifying any search criteria

GENERAL QUERY indicators:
- Greetings: "hi", "hello", "hey"
- Analysis: "analyze results", "explain", "what do you think"
- Questions: "how does this work", "what can you do"

Response format:
{{
    "request_type": "search_interaction" | "general_query",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Examples:
"filter by python" → {{"request_type": "search_interaction", "confidence": 0.95, "reasoning": "Clear filter command"}}
"hello" → {{"request_type": "general_query", "confidence": 0.95, "reasoning": "Greeting message"}}"""

    @staticmethod
    def get_general_query_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """General query prompt - NO thinking, direct UI response."""
        total_results = session_state.get('total_results', 0)
        current_filters = session_state.get('keywords', [])
        
        return f"""You are a helpful AI assistant for a candidate search system. Respond directly and naturally to user queries.

Current search context:
- Active filters: {current_filters}
- Total results in database: {total_results:,}

User input: "{user_input}"

CRITICAL RULES FOR UI RESPONSES:
1. NO <think> tags - respond directly to the user
2. NEVER mention displayed/shown candidates - only total results
3. When listing capabilities, use numbered format: "1. ...", "2. ...", "3. ..."
4. Be conversational and helpful
5. Keep responses concise but informative
6. Websearch if the user wants to know about something specific and if you dont know about it 

CAPABILITIES TO MENTION:
1. Add/modify skills, experience ranges, locations
2. Analyze current search results and provide insights
3. Sort candidates by experience, salary, or other criteria
4. Show more candidates from database
5. Explain why certain candidates match criteria

RESPONSE EXAMPLES:
Input: "Hi" → "Hello! I'm your AI assistant for candidate search. You have {total_results:,} total results available. I can help with:

1. Modify search filters by adding skills or criteria
2. Analyze your current search results
3. Sort candidates by different parameters
4. Show more candidates from the database

What would you like to do?"

Input: "What do you know about current company: -> "The current company is a recruiting company deals in  business"

Input: "What can you do?" → "I can assist you in several ways:

1. Filter Management: Add/remove skills, set experience ranges, modify salary criteria
2. Result Analysis: Analyze candidate skills, experience distribution, salary ranges
3. Search Optimization: Suggest related skills, recommend filter adjustments
4. Data Organization: Sort by experience/salary, group by skills
5. Insights: Identify skill gaps, market trends, candidate availability

You currently have {total_results:,} total results to work with. What would you like to try?"

Respond naturally and helpfully. No thinking process - just the direct response."""

    @staticmethod 
    def get_task_breakdown_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """Task breakdown prompt - ALLOW thinking for complex operations."""
        current_location = "Mumbai"
        current_filters = {
            'keywords': session_state.get('keywords', []),
            'experience': f"{session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years",
            'salary': f"{session_state.get('min_salary', 0)}-{session_state.get('max_salary', 15)} lakhs",
            'current_cities': session_state.get('current_cities', []),
            'preferred_cities': session_state.get('preferred_cities', [])
        }
        
        return f"""You are a task breakdown assistant. Analyze the user request and create a step-by-step execution plan.

Current context:
- User location: {current_location}
- Current filters: {current_filters}

User input: "{user_input}"

<think>
Analyze this request carefully:
1. What is the user trying to achieve?
2. What tools are needed?
3. What's the optimal sequence of operations?
4. Should a search be triggered? (only if user mention search anywhere in its message)

Break down complex requests into logical steps.
</think>

AVAILABLE TOOLS:
1. "filter_tools" - Add/remove skills, modify experience/salary, add/remove locations
2. "search_tools" - Execute candidate search with current filters
3. "location_tools" - Find similar/nearby locations
4. "skill_analysis" - Find related/similar skills

TASK BREAKDOWN FORMAT:
{{
    "tasks": [
        {{
            "step": 1,
            "action": "filter_modification|search_execution|location_analysis|skill_analysis",
            "description": "What this step does",
            "parameters": {{"key": "value"}},
            "reasoning": "Why this step is needed"
        }}
    ],
    "final_goal": "Overall objective",
    "requires_search": true/false
}}

Return the JSON task breakdown."""


class IntentExtractionPrompt:
    """Intent extraction - ALLOW thinking for accurate filter operations."""
    
    def __init__(self):
        self.system_prompt_template = """You are an AI assistant that helps interpret user requests to modify search filters for a job candidate search system.

Current search filters:
{current_filters}

<think>
Analyze the user request carefully:
1. What action do they want to perform?
2. What specific values are mentioned?
3. Is this mandatory or optional?
4. Should a search be triggered?
5. How should I respond to the user?

Parse the request thoroughly to extract the correct intent.
</think>

Your task is to interpret the user's request and return a JSON response with the filter modifications.

IMPORTANT: If the user mentions multiple actions in one request, return an array of actions. If it's a single action, return a single object.

Response formats and examples remain the same...

Return ONLY valid JSON response. No additional text or explanation."""
    
    def build_prompt(self, user_input: str, current_filters: Dict[str, Any]) -> str:
        """Build intent extraction prompt with thinking allowed."""
        filters_str = f"""- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}"""
        
        system_prompt = self.system_prompt_template.format(current_filters=filters_str)
        
        return f"{system_prompt}\n\nUser request: {user_input}"