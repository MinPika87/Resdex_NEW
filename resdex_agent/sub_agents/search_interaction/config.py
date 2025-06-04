# Use this for resdex_agent/sub_agents/search_interaction/config.py
# (Your original was already correct!)

"""
Configuration for Search Interaction Sub-Agent.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class SearchInteractionConfig(BaseModel):
    """Configuration for Search Interaction Sub-Agent."""
    
    # Basic agent info
    name: str = "SearchInteractionAgent"
    version: str = "1.0.0"
    description: str = "Process natural language search filter modifications"
    
    # Processing settings
    max_modifications_per_request: int = 5
    enable_auto_search: bool = True
    enable_multi_intent_processing: bool = True
    enable_filter_validation: bool = True
    
    # LLM settings
    llm_temperature: float = 0.4
    llm_max_tokens: int = 4000
    
    # Validation rules
    validation_rules: Dict[str, Any] = Field(default_factory=lambda: {
        "min_experience": 0,
        "max_experience": 50,
        "min_salary": 0,
        "max_salary": 100,
        "max_skills_per_request": 5,
        "max_locations_per_request": 3
    })
    
    def get_validation_rule(self, rule_name: str, default: Any = None) -> Any:
        """Get a specific validation rule."""
        return self.validation_rules.get(rule_name, default)