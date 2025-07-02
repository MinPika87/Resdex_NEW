# resdex_agent/sub_agents/refinement/config.py - UPDATED with query relaxation settings
"""
Configuration for Refinement Sub-Agent with Query Relaxation support.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class RefinementConfig(BaseModel):
    """Configuration for Refinement Sub-Agent with both facet generation and query relaxation."""
    
    # Basic agent info
    name: str = "RefinementAgent"
    version: str = "1.1.0"  # Updated version
    description: str = "Handle facet generation and query relaxation for search refinement"
    
    # Facet generation settings
    facet_api_url: str = "http://10.10.112.238:8004/generate"
    facet_api_timeout: int = 30
    max_facet_categories: int = 10
    
    # NEW: Query relaxation settings
    relaxation_api_url: str = "http://10.10.112.202:8125/get_relaxed_query_optimized"
    relaxation_api_timeout: int = 30
    relaxation_transaction_id: str = "3113ea131"
    max_relaxation_suggestions: int = 5
    
    # Company/Recruiter defaults for relaxation API
    default_company_info: Dict[str, Any] = Field(default_factory=lambda: {
        'company_id': 3812074,
        'comnotGroupId': 4634055,
        'recruiter_id': 124271564,
        'preference_key': 'e7d47e8e-4728-4a9f-9bfe-d9e8e9586a2b'
    })
    
    # Auto-trigger settings
    auto_facet_threshold: int = 20  # Min candidates for auto facet generation
    auto_relaxation_threshold: int = 5  # Max candidates before suggesting relaxation
    
    # API settings
    prefiltering_enabled: bool = False
    llm_clean_enabled: bool = False
    num_results: int = 5
    
    # UPDATED: Refinement types with query relaxation
    enabled_refinements: Dict[str, bool] = Field(default_factory=lambda: {
        "facet_generation": True,
        "query_relaxation": True  # NEW: Enable query relaxation
    })
    
    # NEW: Query relaxation specific settings
    relaxation_strategies: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "skill_relaxation": {
            "enabled": True,
            "priority": 1,
            "description": "Convert mandatory skills to optional",
            "max_skills_to_relax": 3
        },
        "experience_relaxation": {
            "enabled": True,
            "priority": 2,
            "description": "Expand experience range",
            "max_expansion_years": 5
        },
        "location_relaxation": {
            "enabled": True,
            "priority": 3,
            "description": "Add more locations or enable remote",
            "suggest_remote": True
        },
        "salary_relaxation": {
            "enabled": True,
            "priority": 4,
            "description": "Expand salary range",
            "max_expansion_percent": 30
        }
    })
    
    # NEW: City mapping for API requests (subset of major cities)
    city_mapping: Dict[str, str] = Field(default_factory=lambda: {
        'bangalore': '9501', 'mumbai': '6', 'delhi': '17', 
        'pune': '139', 'hyderabad': '220', 'chennai': '4',
        'kolkata': '11', 'gurgaon': '122', 'noida': '123',
        'ahmedabad': '15', 'kochi': '52', 'thiruvananthapuram': '53',
        'coimbatore': '46', 'nashik': '141', 'nagpur': '142'
    })
    
    def is_refinement_enabled(self, refinement_type: str) -> bool:
        """Check if refinement type is enabled."""
        return self.enabled_refinements.get(refinement_type, False)
    
    def is_relaxation_strategy_enabled(self, strategy_name: str) -> bool:
        """Check if relaxation strategy is enabled."""
        return self.relaxation_strategies.get(strategy_name, {}).get("enabled", False)
    
    def get_relaxation_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for specific relaxation strategy."""
        return self.relaxation_strategies.get(strategy_name, {})
    
    def get_city_id(self, city_name: str) -> str:
        """Get API city ID for city name."""
        return self.city_mapping.get(city_name.lower(), '9501')  