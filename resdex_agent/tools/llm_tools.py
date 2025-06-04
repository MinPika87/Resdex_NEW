# Replace the content of resdex_agent/tools/llm_tools.py

"""
LLM interaction tools for ResDex Agent.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json

# Create a simple Tool base class
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

import requests
from ..config import config
from ..utils.data_processing import DataProcessor

logger = logging.getLogger(__name__)


class LLMTool(Tool):
    """Tool for LLM interactions and intent extraction."""
    
    def __init__(self, name: str = "llm_tool"):
        super().__init__(name=name, description="Process natural language using LLM")
        self.api_key = config.llm.api_key
        self.base_url = config.llm.base_url
        self.model_name = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
        self.data_processor = DataProcessor()
    
    async def __call__(self, 
                      user_input: str, 
                      current_filters: Dict[str, Any],
                      task: str = "extract_intent") -> Dict[str, Any]:
        """Process user input using LLM."""
        try:
            if task == "extract_intent":
                return await self._extract_search_intent(user_input, current_filters)
            else:
                return {"success": False, "error": f"Unknown task: {task}"}
                
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_search_intent(self, user_input: str, current_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract search modification intent from user input."""
        system_prompt = self._build_intent_extraction_prompt(current_filters)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current filters: {current_filters}\n\nUser request: {user_input}"}
        ]
        
        try:
            # Using direct HTTP request to match your original setup
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                logger.debug(f"LLM response: {response_text}")
                
                # Parse the response
                intent_data = self.data_processor.extract_json_from_text(response_text)
                
                if intent_data:
                    return {
                        "success": True,
                        "intent_data": intent_data,
                        "raw_response": response_text
                    }
                else:
                    # Return default response if parsing fails
                    return {
                        "success": True,
                        "intent_data": self._default_intent_response(user_input),
                        "raw_response": response_text
                    }
            else:
                logger.error(f"LLM API failed with status {response.status_code}")
                return {
                    "success": False,
                    "error": f"LLM API returned status {response.status_code}",
                    "intent_data": self._default_intent_response(user_input)
                }
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "intent_data": self._default_intent_response(user_input)
            }
    
    def _build_intent_extraction_prompt(self, current_filters: Dict[str, Any]) -> str:
        """Build system prompt for intent extraction."""
        return f"""You are an AI assistant that helps interpret user requests to modify search filters for a job candidate search system.

Current search filters:
- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}

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
    
    def _default_intent_response(self, user_input: str) -> Dict[str, Any]:
        """Return default intent response when LLM fails."""
        return {
            "action": "general_query",
            "filter_type": None,
            "operation": None,
            "value": None,
            "mandatory": False,
            "response_text": f"I understand you're asking about: '{user_input}'. Could you please rephrase your request?",
            "trigger_search": False
        }