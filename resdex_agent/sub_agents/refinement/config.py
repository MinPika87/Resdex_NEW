# resdex_agent/sub_agents/refinement/config.py
"""
Configuration for Refinement Sub-Agent.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class RefinementConfig(BaseModel):
    """Configuration for Refinement Sub-Agent."""
    
    # Basic agent info
    name: str = "RefinementAgent"
    version: str = "1.0.0"
    description: str = "Handle facet generation and query relaxation for search refinement"
    
    # Facet generation settings
    facet_api_url: str = "http://10.10.112.238:8004/generate"
    facet_api_timeout: int = 30
    max_facet_categories: int = 10
    
    # Query relaxation settings
    enable_query_relaxation: bool = True
    max_relaxation_suggestions: int = 5
    
    # Auto-trigger settings
    auto_facet_threshold: int = 20  # Min candidates for auto facet generation
    auto_relaxation_threshold: int = 5  # Max candidates before suggesting relaxation
    
    # API settings
    prefiltering_enabled: bool = False
    llm_clean_enabled: bool = False
    num_results: int = 5
    
    # Refinement types
    enabled_refinements: Dict[str, bool] = Field(default_factory=lambda: {
        "facet_generation": True,
        "query_relaxation": True
    })
    
    def is_refinement_enabled(self, refinement_type: str) -> bool:
        """Check if refinement type is enabled."""
        return self.enabled_refinements.get(refinement_type, False)