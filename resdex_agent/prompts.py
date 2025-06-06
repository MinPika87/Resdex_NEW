# Create resdex_agent/prompts.py

"""
Prompts for Root Agent routing and general query handling.
"""

from typing import Dict, Any


class RootAgentPrompts:
    """Prompts for root agent routing and general query processing."""
    
    @staticmethod
    def get_routing_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """Prompt to determine if input is search interaction or general query."""
        current_candidates_count = len(session_state.get('candidates', []))
        current_filters = {
            'keywords': session_state.get('keywords', []),
            'experience': f"{session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years",
            'salary': f"{session_state.get('min_salary', 0)}-{session_state.get('max_salary', 15)} lakhs",
            'cities': session_state.get('current_cities', [])
        }
        
        return f"""You are a routing assistant for a candidate search system. Determine the request type and respond with JSON.

Current context:
- Active search filters: {current_filters}
- Current candidates: {current_candidates_count} results
- User location: Mumbai, India (if needed for location queries)

User input: "{user_input}"

ROUTING RULES:
1. If input involves SEARCH/FILTER operations → route to "search_interaction"
2. If input is general conversation/analysis → route to "general_query"

SEARCH/FILTER indicators:
- Adding/removing skills, experience, salary, location filters
- Search commands: "search with", "find", "show me", "filter by"
- Location queries: "similar location", "nearby cities", "from bangalore"
- Modifying any search criteria

GENERAL QUERY indicators:
- Greetings: "hi", "hello", "hey"
- Analysis: "analyze results", "explain", "what do you think"
- Questions: "how does this work", "what can you do"
- Casual conversation that doesn't modify search

Response format:
{{
    "request_type": "search_interaction" | "general_query",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Examples:
Input: "search with python" → {{"request_type": "search_interaction", "confidence": 0.95, "reasoning": "Clear search command"}}
Input: "add java skill" → {{"request_type": "search_interaction", "confidence": 0.9, "reasoning": "Filter modification request"}}
Input: "hello" → {{"request_type": "general_query", "confidence": 0.95, "reasoning": "Greeting message"}}
Input: "analyze these results" → {{"request_type": "general_query", "confidence": 0.85, "reasoning": "Analysis request, not filter modification"}}

Return ONLY the JSON response."""

    @staticmethod
    def get_general_query_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """Prompt for handling general queries and conversations."""
        current_candidates = session_state.get('candidates', [])
        current_filters = session_state.get('keywords', [])
        total_results = session_state.get('total_results', 0)
        
        # Sample candidate info for analysis
        sample_candidates = []
        for i, candidate in enumerate(current_candidates[:3]):
            sample_candidates.append({
                'name': candidate.get('name', 'Unknown'),
                'role': candidate.get('current_role', 'Not specified'),
                'company': candidate.get('current_company', 'Not specified'),
                'experience': candidate.get('experience', 0),
                'salary': candidate.get('salary', 0),
                'skills': candidate.get('skills', [])[:5]  # First 5 skills
            })
        
        return f"""You are a helpful AI assistant for a candidate search system. Respond naturally to user queries.

Current search context:
- Active filters: {current_filters}
- Total results found: {total_results:,}
- Candidates displayed: {len(current_candidates)}
- Sample candidates: {sample_candidates}

User input: "{user_input}"

RESPONSE GUIDELINES:
1. Be conversational and helpful
2. Reference current search context when relevant
3. Provide insights about candidates/results if asked
4. Answer general questions about the system
5. Be friendly for greetings and casual conversation
6. Offer suggestions for search improvements if appropriate

CAPABILITIES YOU CAN MENTION:
- "I can help you modify search filters by adding skills, experience ranges, locations"
- "I can analyze your current search results and provide insights"
- "I can explain why certain candidates match your criteria"
- "I can suggest related skills or locations to broaden/narrow your search"

EXAMPLES:
Input: "Hi" → "Hello! I'm your AI assistant for candidate search. I can see you have {len(current_candidates)} candidates in your results. How can I help you today?"

Input: "Analyze these results" → "Looking at your current {len(current_candidates)} candidates, I notice [insights about skills, experience levels, locations, etc.]. Would you like me to suggest ways to refine your search?"

Input: "What can you do?" → "I can help you with candidate search in several ways: [list capabilities]. What would you like to try?"

Respond naturally and helpfully. Keep responses conversational but informative."""

    @staticmethod 
    def get_task_breakdown_prompt(user_input: str, session_state: Dict[str, Any]) -> str:
        """Prompt for LLM to break down complex tasks and decide tool calls."""
        current_location = "Mumbai"  # Could be extracted from session_state
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

AVAILABLE TOOLS:
1. "filter_modification" - Add/remove skills, modify experience/salary, add/remove locations
2. "search_execution" - Execute candidate search with current filters
3. "location_analysis" - Find similar/nearby locations
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

EXAMPLES:

Input: "search with python"
→ {{
    "tasks": [
        {{"step": 1, "action": "filter_modification", "description": "Add Python skill", "parameters": {{"skill": "Python", "mandatory": false}}, "reasoning": "User wants to search for Python developers"}},
        {{"step": 2, "action": "search_execution", "description": "Execute search", "parameters": {{}}, "reasoning": "User explicitly requested search"}}
    ],
    "final_goal": "Find Python developers",
    "requires_search": true
}}

Input: "filter by similar location to my current location"
→ {{
    "tasks": [
        {{"step": 1, "action": "location_analysis", "description": "Find locations similar to {current_location}", "parameters": {{"base_location": "{current_location}", "analysis_type": "similar", "criteria": "job market and tech industry"}}, "reasoning": "Need to identify similar locations first"}},
        {{"step": 2, "action": "filter_modification", "description": "Add similar locations to filters", "parameters": {{"locations": ["to_be_determined"]}}, "reasoning": "Add discovered similar locations to search criteria"}},
        {{"step": 3, "action": "search_execution", "description": "Search with location filters", "parameters": {{}}, "reasoning": "Execute search with new location criteria"}}
    ],
    "final_goal": "Find candidates from locations similar to user's current location",
    "requires_search": true
}} to search criteria"}},
        {{"step": 3, "action": "search_execution", "description": "Search with location filters", "parameters": {{}}, "reasoning": "Execute search with new location criteria"}}
    ],
    "final_goal": "Find candidates from locations similar to user's current location",
    "requires_search": true
}}

Input: "find candidates from tech hubs like bangalore"
→ {{
    "tasks": [
        {{"step": 1, "action": "location_analysis", "description": "Find tech hubs similar to Bangalore", "parameters": {{"base_location": "Bangalore", "analysis_type": "industry_hubs", "criteria": "technology and software"}}, "reasoning": "Identify cities with similar tech industry presence"}},
        {{"step": 2, "action": "filter_modification", "description": "Add tech hub locations", "parameters": {{"locations": ["to_be_determined"]}}, "reasoning": "Add tech hub cities to search filters"}},
        {{"step": 3, "action": "search_execution", "description": "Search in tech hubs", "parameters": {{}}, "reasoning": "Find candidates from tech-focused cities"}}
    ],
    "final_goal": "Find candidates from major tech hubs",
    "requires_search": true
}}

Input: "search nearby mumbai within 200km"
→ {{
    "tasks": [
        {{"step": 1, "action": "location_analysis", "description": "Find cities within 200km of Mumbai", "parameters": {{"base_location": "Mumbai", "analysis_type": "nearby", "radius_km": 200}}, "reasoning": "Find geographically nearby cities"}},
        {{"step": 2, "action": "filter_modification", "description": "Add nearby locations", "parameters": {{"locations": ["to_be_determined"]}}, "reasoning": "Add nearby cities to location filters"}},
        {{"step": 3, "action": "search_execution", "description": "Search in nearby areas", "parameters": {{}}, "reasoning": "Find candidates from nearby locations"}}
    ],
    "final_goal": "Find candidates within 200km radius of Mumbai",
    "requires_search": true
}} to search criteria"}},
        {{"step": 3, "action": "search_execution", "description": "Search with location filters", "parameters": {{}}, "reasoning": "Execute search with new location criteria"}}
    ],
    "final_goal": "Find candidates from locations similar to user's current location",
    "requires_search": true
}}

Input: "add java as mandatory"
→ {{
    "tasks": [
        {{"step": 1, "action": "filter_modification", "description": "Add Java as mandatory skill", "parameters": {{"skill": "Java", "mandatory": true}}, "reasoning": "User wants Java as required skill"}}
    ],
    "final_goal": "Add Java as mandatory filter",
    "requires_search": false
}}

Return ONLY the JSON response."""