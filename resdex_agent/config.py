# resdex_agent/config.py - UPDATED for Phase 1 Agents + Refinement
"""
Configuration management for ResDex Agent - UPDATED with new agent support including Refinement.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "172.10.112.169:3306"))
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
    """Root agent configuration following ADK patterns - UPDATED for Phase 1 + Refinement."""
    
    # Basic agent info
    name: str = "ResDexRootAgent"
    version: str = "2.1.0"  # Updated for Refinement support
    description: str = "AI-powered orchestrator for specialized candidate search agents with refinement capabilities"
    
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
    
    # UPDATED: Sub-agent configurations for Phase 1 + Refinement
    sub_agent_configs: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "search_interaction": {
            "enabled": True,
            "priority": 1,
            "description": "Handle filter operations and candidate search",
            "max_modifications_per_request": 5,
            "enable_auto_search": True,
            "features": ["filter_operations", "candidate_search", "result_sorting"]
        },
        "expansion": {
            "enabled": True,
            "priority": 2,
            "description": "Handle skill, location, and title expansion",
            "max_skills_expansion": 5,
            "max_locations_expansion": 4,
            "max_titles_expansion": 3,
            "features": ["skill_expansion", "location_expansion", "title_expansion"]
        },
        "general_query": {
            "enabled": True,
            "priority": 3,
            "description": "Handle conversational queries and explanations",
            "conversation_temperature": 0.7,
            "max_response_length": 1000,
            "features": ["conversational_ai", "help_system", "memory_queries"]
        },
        "refinement": {  # NEW: Refinement agent configuration
            "enabled": True,
            "priority": 4,
            "description": "Handle facet generation and query relaxation for search refinement",
            "max_facet_categories": 10,
            "max_relaxation_suggestions": 5,
            "facet_api_url": os.getenv("FACET_API_URL", "http://10.10.112.238:8004/generate"),
            "facet_api_timeout": int(os.getenv("FACET_API_TIMEOUT", "30")),
            "enable_prefiltering": os.getenv("FACET_PREFILTERING", "false").lower() == "true",
            "enable_llm_clean": os.getenv("FACET_LLM_CLEAN", "false").lower() == "true",
            "features": ["facet_generation", "query_relaxation", "search_refinement"]
        },
        # Future agents (disabled for now)
        "skill_expansion": {
            "enabled": False,  # Will be part of expansion agent
            "priority": 5,
            "max_suggestions": 10,
            "clustering_threshold": 0.7
        },
        "query_refinement": {
            "enabled": False,  # Future enhancement
            "priority": 6,
            "auto_apply_threshold": 0.8
        }
    })
    
    # UPDATED: Agent routing configuration with refinement support
    routing_config: Dict[str, Any] = Field(default_factory=lambda: {
        "enable_intelligent_routing": True,
        "enable_agent_chaining": True,
        "max_chain_length": 3,
        "routing_confidence_threshold": 0.7,
        "fallback_agent": "search_interaction",
        "refinement_indicators": [
            # Facet generation indicators
            "facets", "categories", "drill down", "refine", "breakdown",
            "show categories", "categorize", "group by", "segment",
            "facet generation", "generate facets", "show facets",
            # Query relaxation indicators
            "relax", "broaden", "more results", "expand search",
            "fewer filters", "less strict", "widen", "loosen",
            "relax search", "broaden search", "get more candidates"
        ]
    })
    
    # UPDATED: Memory configuration
    memory_config: Dict[str, Any] = Field(default_factory=lambda: {
        "enable_memory": True,
        "memory_type": "InMemoryMemoryService",
        "max_memory_entries_per_user": 500,
        "session_timeout_hours": 24,
        "enable_cross_session_memory": True
    })
    
    # NEW: Orchestration configuration with refinement intents
    orchestration_config: Dict[str, Any] = Field(default_factory=lambda: {
        "enable_multi_intent": True,
        "max_parallel_agents": 3,
        "timeout_seconds": 60,
        "enable_auto_routing": True,
        "fallback_to_search": True,
        "supported_intents": [
            "skill_expansion",
            "title_expansion", 
            "location_expansion",
            "facet_generation",      # NEW: Refinement intent
            "query_relaxation",      # NEW: Refinement intent
            "filter_operation",
            "search_execution"
        ],
        "auto_triggers": {
            "expansion": {
                "skill_threshold": 1,
                "title_threshold": 1,
                "location_threshold": 1
            },
            "refinement": {               # NEW: Auto-trigger settings
                "facet_threshold": 20,       # Min results for auto facet generation
                "relaxation_threshold": 5    # Max results before auto relaxation
            },
            "search": {
                "auto_search_after_expansion": True,
                "auto_search_after_refinement": False
            }
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
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled sub-agent names."""
        return [
            name for name, config in self.sub_agent_configs.items() 
            if config.get("enabled", False)
        ]
    
    def get_agent_priority(self, agent_name: str) -> int:
        """Get priority of a specific agent."""
        return self.get_sub_agent_config(agent_name).get("priority", 999)
    
    def get_routing_config(self) -> Dict[str, Any]:
        """Get routing configuration."""
        return self.routing_config
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory configuration."""
        return self.memory_config
    
    def get_orchestration_config(self) -> Dict[str, Any]:
        """Get orchestration configuration."""
        return self.orchestration_config
    
    def get_refinement_config(self) -> Dict[str, Any]:
        """Get refinement agent configuration."""
        return self.get_sub_agent_config("refinement")
    
    def get_facet_api_url(self) -> str:
        """Get facet generation API URL."""
        return self.get_refinement_config().get("facet_api_url", "http://10.10.112.238:8004/generate")
    
    def model_post_init(self, __context):
        """Post-initialization validation to ensure Qwen is configured."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Log the actual LLM configuration being used
        logger.info("=== PHASE 1 AGENT + REFINEMENT CONFIGURATION ===")
        logger.info(f"Root Agent: {self.name} v{self.version}")
        logger.info(f"Enabled Agents: {self.get_enabled_agents()}")
        logger.info(f"LLM Model: {self.llm.model}")
        logger.info(f"Memory Enabled: {self.memory_config['enable_memory']}")
        logger.info(f"Intelligent Routing: {self.routing_config['enable_intelligent_routing']}")
        logger.info(f"Refinement Enabled: {self.is_sub_agent_enabled('refinement')}")
        logger.info(f"Facet API URL: {self.get_facet_api_url()}")
        logger.info("=== END CONFIGURATION ===")
        
        # Validate Qwen configuration
        if not self.llm.base_url or self.llm.base_url == "":
            logger.error("❌ LLM_BASE_URL is empty! Check your .env file")
            raise ValueError("LLM_BASE_URL cannot be empty")
        
        if "gpt" in self.llm.model.lower():
            logger.error("❌ GPT model detected! Should be using Qwen model")
            raise ValueError(f"Expected Qwen model, got: {self.llm.model}")
        
        if "qwen" not in self.llm.model.lower():
            logger.warning(f"⚠️ Model name doesn't contain 'Qwen': {self.llm.model}")
        
        # Validate enabled agents
        enabled_agents = self.get_enabled_agents()
        if not enabled_agents:
            logger.warning("⚠️ No sub-agents enabled!")
        else:
            logger.info(f"✅ Phase 1 + Refinement agents enabled: {enabled_agents}")
        
        # Validate refinement configuration
        if self.is_sub_agent_enabled("refinement"):
            refinement_config = self.get_refinement_config()
            facet_api_url = refinement_config.get("facet_api_url")
            if not facet_api_url:
                logger.warning("⚠️ Refinement enabled but no facet API URL configured")
            else:
                logger.info(f"✅ Refinement API configured: {facet_api_url}")


# Global configuration instance
config = AgentConfig.from_env()


# UPDATED: Agent registry for dynamic agent management with refinement support
class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._agent_classes = {}
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register default Phase 1 + Refinement agents."""
        try:
            # SearchInteractionAgent
            from .sub_agents.search_interaction.agent import SearchInteractionAgent
            from .sub_agents.search_interaction.config import SearchInteractionConfig
            self._agent_classes["search_interaction"] = {
                "class": SearchInteractionAgent,
                "config_class": SearchInteractionConfig
            }
            
            # ExpansionAgent
            from .sub_agents.expansion.agent import ExpansionAgent
            from .sub_agents.expansion.config import ExpansionConfig
            self._agent_classes["expansion"] = {
                "class": ExpansionAgent,
                "config_class": ExpansionConfig
            }
            
            # GeneralQueryAgent
            from .sub_agents.general_query.agent import GeneralQueryAgent
            from .sub_agents.general_query.config import GeneralQueryConfig
            self._agent_classes["general_query"] = {
                "class": GeneralQueryAgent,
                "config_class": GeneralQueryConfig
            }
            
            # NEW: RefinementAgent
            from .sub_agents.refinement.agent import RefinementAgent
            from .sub_agents.refinement.config import RefinementConfig
            self._agent_classes["refinement"] = {
                "class": RefinementAgent,
                "config_class": RefinementConfig
            }
            
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Some agents not available during registration: {e}")
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return list(self._agent_classes.keys())
    
    def is_agent_available(self, agent_name: str) -> bool:
        """Check if agent is available."""
        return agent_name in self._agent_classes
    
    def create_agent(self, agent_name: str):
        """Create an instance of the specified agent."""
        if not self.is_agent_available(agent_name):
            raise ValueError(f"Agent '{agent_name}' not available")
        
        agent_info = self._agent_classes[agent_name]
        agent_class = agent_info["class"]
        config_class = agent_info["config_class"]
        
        # Create agent with its specific config
        agent_config = config_class()
        return agent_class(agent_config)
    
    def get_enabled_agent_instances(self) -> Dict[str, Any]:
        """Get instances of all enabled agents."""
        enabled_agents = {}
        
        for agent_name in self.config.get_enabled_agents():
            if self.is_agent_available(agent_name):
                try:
                    enabled_agents[agent_name] = self.create_agent(agent_name)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create agent '{agent_name}': {e}")
        
        return enabled_agents


# Global agent registry
agent_registry = AgentRegistry(config)