# resdex_agent/sub_agents/expansion/config.py
"""
Configuration for Expansion Sub-Agent.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ExpansionConfig(BaseModel):
    """Configuration for Expansion Sub-Agent."""
    
    # Basic agent info
    name: str = "ExpansionAgent"
    version: str = "1.0.0"
    description: str = "Handle skill, location, and title expansion using AI"
    
    # Expansion settings
    max_skills_expansion: int = 5
    max_locations_expansion: int = 4
    max_titles_expansion: int = 3
    
    # LLM settings for expansion
    expansion_temperature: float = 0.6
    expansion_max_tokens: int = 2000
    
    # Expansion types
    enabled_expansions: Dict[str, bool] = Field(default_factory=lambda: {
        "skill_expansion": True,
        "location_expansion": True,
        "title_expansion": True
    })
    
    def is_expansion_enabled(self, expansion_type: str) -> bool:
        """Check if expansion type is enabled."""
        return self.enabled_expansions.get(expansion_type, False)
