"""
Prompts for Search Interaction Sub-Agent.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class IntentExtractionPrompt:
    """Prompt template for extracting search modification intents."""
    
    def __init__(self):
        self.system_prompt_template = """You are an AI assistant that helps interpret user requests to modify search filters for a job candidate search system.

Current search filters:
{current_filters}

Your task is to interpret the user's request and return a JSON response with the filter modifications.

IMPORTANT: If the user mentions multiple actions in one request, return an array of actions. If it's a single action, return a single object.

Single action response format:
{{
    "action": "add_skill|remove_skill|modify_experience|modify_salary|add_location|remove_location|make_mandatory|make_optional",
    "filter_type": "keywords|experience|salary|location",
    "operation": "add|remove|set|set_range|increase|decrease",
    "value": "extracted_value",
    "mandatory": true/false,
    "response_text": "human_readable_explanation",
    "trigger_search": true/false
}}

Multiple actions response format:
[
    {{action1}},
    {{action2}},
    ...
]

MANDATORY vs OPTIONAL Keywords:
- Mandatory means the candidate MUST have this skill (marked with ★ in UI)
- Optional means the candidate can have this skill but it's not required

Mandatory indicators: "mandatory", "important", "must have", "should have", "required", "essential", "critical"
Optional indicators: "optional", "nice to have", "preferred", "good to have", "can have"

Rules for trigger_search:
- If user says "search with X" or "find X" or "show me X candidates" -> trigger_search: true
- If user says "add X" without "search" -> trigger_search: false
- If user mentions "candidates from X" -> trigger_search: true

Examples:
- "add python as mandatory" -> {{"action": "add_skill", "value": "Python", "mandatory": true, "trigger_search": false}}
- "search with python" -> {{"action": "add_skill", "value": "Python", "mandatory": false, "trigger_search": true}}
- "remove java and add python" -> [
    {{"action": "remove_skill", "value": "Java", "trigger_search": false}},
    {{"action": "add_skill", "value": "Python", "mandatory": false, "trigger_search": false}}
  ]

Return ONLY valid JSON response. No additional text or explanation."""
    
    def build_prompt(self, user_input: str, current_filters: Dict[str, Any]) -> str:
        """Build the complete prompt for intent extraction."""
        filters_str = f"""- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}"""
        
        system_prompt = self.system_prompt_template.format(current_filters=filters_str)
        
        return f"{system_prompt}\n\nUser request: {user_input}"