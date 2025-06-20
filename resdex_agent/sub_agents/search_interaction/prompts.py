# resdex_agent/sub_agents/search_interaction/prompts.py - NEW
"""
Search Interaction Agent Specific Prompts
"""

from typing import Dict, Any, List


class SearchInteractionPrompts:
    """Prompts specific to SearchInteractionAgent."""
    
    @staticmethod
    def get_intent_extraction_prompt_with_memory(user_input: str, current_filters: Dict[str, Any], 
                                                memory_context: List[Dict[str, Any]]) -> str:
        """Intent extraction prompt with memory context."""
        
        memory_summary = ""
        if memory_context:
            memory_items = [f"- {mem.get('content', '')[:80]}" for mem in memory_context[:2]]
            memory_summary = f"\nRecent search history:\n{chr(10).join(memory_items)}\n"
        
        filters_str = f"""- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Current Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}"""
        
        return f"""You are a search filter assistant with memory awareness. Extract filter modifications from user requests.

Current filters:
{filters_str}

{memory_summary}

User request: "{user_input}"

IMPORTANT: Return ONLY valid JSON - no explanations, no extra text.

For single action: return one object
For multiple actions: return array of objects

RESPONSE FORMAT:
{{
    "action": "add_skill|remove_skill|modify_experience|modify_salary|add_location|remove_location",
    "filter_type": "keywords|experience|salary|location", 
    "operation": "add|remove|set|set_range|increase|decrease",
    "value": "extracted_value",
    "mandatory": true/false,
    "response_text": "human_readable_explanation",
    "trigger_search": true/false
}}

MANDATORY DETECTION:
- mandatory=true for: "mandatory", "important", "must have", "required", "essential"
- mandatory=false for: "optional", "nice to have", "preferred", default case

TRIGGER_SEARCH LOGIC:
- If user says "search with X" or "find X" or "show me X" → trigger_search: true
- If user says "add X" without "search" → trigger_search: false

EXAMPLES:
"add python" → {{"action": "add_skill", "value": "Python", "mandatory": false, "trigger_search": false}}
"search with java" → {{"action": "add_skill", "value": "Java", "mandatory": false, "trigger_search": true}}
"set experience 5-10 years" → {{"action": "modify_experience", "operation": "set_range", "value": "5-10", "trigger_search": false}}

Return ONLY the JSON response."""
    
    @staticmethod
    def get_candidate_operation_prompt(user_input: str, candidates_count: int) -> str:
        """Prompt for candidate operations like sorting."""
        return f"""You are processing operations on {candidates_count} existing candidates.

User request: "{user_input}"

Determine the operation type:

OPERATIONS:
- sort_by_experience: Sort candidates by experience level
- sort_by_salary: Sort candidates by salary 
- sort_by_name: Sort candidates by name
- filter_results: Filter existing results
- show_more: Show more candidates (pagination)
- no_operation: No specific operation detected

Return ONLY JSON:
{{
    "operation": "sort_by_experience|sort_by_salary|sort_by_name|filter_results|show_more|no_operation",
    "sort_order": "asc|desc",
    "confidence": 0.0-1.0
}}"""