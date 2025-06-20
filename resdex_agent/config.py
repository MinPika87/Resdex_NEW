"""
Configuration management for ResDex Agent - FIXED to ensure Qwen API usage.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "172.10.112.103:3306"))
    user: str = Field(default_factory=lambda: os.getenv("DB_USER", "user_analytics"))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", "anaKm7Iv80l"))
    database: str = Field(default_factory=lambda: os.getenv("DB_NAME", "ja_LSI"))


class LLMConfig(BaseModel):
    """LLM client configuration - FIXED to ensure Qwen usage."""
    api_key: str = Field(default_factory=lambda: os.getenv("LLM_API_KEY", "llama3-token"))
    base_url: str = Field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://10.10.112.193:8000/v1"))
    model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "Qwen/Qwen3-32B"))
    temperature: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.4")))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4000")))


class APIConfig(BaseModel):
    """External API configuration."""
    search_api_url: str = Field(default_factory=lambda: os.getenv("SEARCH_API_URL", "http://staging1-ni-resdexsearch-exp-services.restapis.services.resdex.com/naukri-resdexsearch-simulator-services/v1/search/doSearch?source=es8"))
    user_details_api_url: str = Field(default_factory=lambda: os.getenv("USER_DETAILS_API_URL", "http://staging1-search-data-services.restapis.services.resdex.com/search-data-simulator-services/v0/search/profile/getDetails"))
    location_api_url: str = Field(default_factory=lambda: os.getenv("LOCATION_API_URL", "http://test.taxonomy.services.analytics.resdex.com/taxonomy-other-entities-service/v0/locationNormalization"))


class AgentConfig(BaseModel):
    """Root agent configuration following ADK patterns."""
    
    # Basic agent info
    name: str = "ResDexRootAgent"
    version: str = "1.0.0"
    description: str = "AI-powered candidate search and filtering system"
    
    # Sub-configuration objects
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    
    # Agent behavior settings
    max_execution_time: float = Field(default_factory=lambda: float(os.getenv("MAX_EXECUTION_TIME", "30")))
    enable_parallel_execution: bool = Field(default_factory=lambda: os.getenv("ENABLE_PARALLEL_EXECUTION", "False").lower() == "true")
    max_agents_per_intent: int = Field(default_factory=lambda: int(os.getenv("MAX_AGENTS_PER_INTENT", "3")))
    debug_mode: bool = Field(default_factory=lambda: os.getenv("ENABLE_DEBUG_MODE", "False").lower() == "true")
    
    # UI settings
    ui_pagination_size: int = 5
    ui_max_candidates_display: int = 20
    ui_max_skills_display: int = 15
    
    # Sub-agent configurations
    sub_agent_configs: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "search_interaction": {
            "enabled": True,
            "priority": 1,
            "max_modifications_per_request": 5,
            "enable_auto_search": True
        },
        "skill_expansion": {
            "enabled": False,  # Will be enabled in future
            "priority": 2,
            "max_suggestions": 10,
            "clustering_threshold": 0.7
        },
        "query_refinement": {
            "enabled": False,  # Will be enabled in future
            "priority": 3,
            "auto_apply_threshold": 0.8
        }
    })
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables."""
        return cls()
    
    def get_sub_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific sub-agent."""
        return self.sub_agent_configs.get(agent_name, {})
    
    def is_sub_agent_enabled(self, agent_name: str) -> bool:
        """Check if a sub-agent is enabled."""
        return self.get_sub_agent_config(agent_name).get("enabled", False)
    
    def model_post_init(self, __context):
        """Post-initialization validation to ensure Qwen is configured."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Log the actual LLM configuration being used
        logger.info("=== LLM CONFIGURATION LOADED ===")
        logger.info(f"API Key: {self.llm.api_key}")
        logger.info(f"Base URL: {self.llm.base_url}")
        logger.info(f"Model: {self.llm.model}")
        logger.info(f"Temperature: {self.llm.temperature}")
        logger.info(f"Max Tokens: {self.llm.max_tokens}")
        logger.info("=== END LLM CONFIG ===")
        
        # Validate Qwen configuration
        if not self.llm.base_url or self.llm.base_url == "":
            logger.error("❌ LLM_BASE_URL is empty! Check your .env file")
            raise ValueError("LLM_BASE_URL cannot be empty")
        
        if "gpt" in self.llm.model.lower():
            logger.error("❌ GPT model detected! Should be using Qwen model")
            raise ValueError(f"Expected Qwen model, got: {self.llm.model}")
        
        if "qwen" not in self.llm.model.lower():
            logger.warning(f"⚠️ Model name doesn't contain 'Qwen': {self.llm.model}")


# Global configuration instance
config = AgentConfig.from_env()