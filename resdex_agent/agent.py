"""
Root ResDex Agent following Google ADK patterns.
"""

from typing import Dict, Any, List, Optional
import logging
from google.adk.agents import Agent
from pydantic import BaseModel
class Content(BaseModel):
    """Content wrapper for agent communication."""
    data: Dict[str, Any]
from .config import AgentConfig  # Fixed: removed the 'x' typo
from .tools.search_tools import SearchTool
from .config import AgentConfig
from .tools.search_tools import SearchTool
from .sub_agents.search_interaction.agent import SearchInteractionAgent

logger = logging.getLogger(__name__)


class ResDexRootAgent(Agent):
    """
    Root agent for ResDex candidate search and filtering system.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        _config = config or AgentConfig.from_env()

        # Initialize tools
        tools = [
            SearchTool("search_tool")
        ]

        # Call super with required params
        super().__init__(
            name=_config.name,
            description=_config.description,
            tools=tools
        )

        # Assign config privately
        self._config = _config
        self.sub_agents = {}
        self._initialize_sub_agents()

        logger.info(f"Initialized {_config.name} v{_config.version}")

    @property
    def config(self) -> AgentConfig:
        """Read-only access to config."""
        return self._config
    
    def _initialize_sub_agents(self):
        """Initialize all enabled sub-agents."""
        if self.config.is_sub_agent_enabled("search_interaction"):
            from .sub_agents.search_interaction.config import SearchInteractionConfig
            sub_config = SearchInteractionConfig()
            self.sub_agents["search_interaction"] = SearchInteractionAgent(sub_config)
            logger.info("Initialized SearchInteractionAgent")
        
        # Future sub-agents can be initialized here
        # if self.config.is_sub_agent_enabled("skill_expansion"):
        #     self.sub_agents["skill_expansion"] = SkillExpansionAgent()
        
        logger.info(f"Initialized {len(self.sub_agents)} sub-agents")
    
    async def execute(self, content: Content) -> Content:
        """Execute the root agent logic."""
        try:
            request_type = content.data.get("request_type", "search_interaction")
            
            logger.info(f"Root agent processing request type: {request_type}")
            
            if request_type == "search_interaction":
                return await self._handle_search_interaction(content)
            elif request_type == "candidate_search":
                return await self._handle_candidate_search(content)
            elif request_type == "health_check":
                return await self._handle_health_check(content)
            else:
                return Content(data={
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": ["search_interaction", "candidate_search", "health_check"]
                })
                
        except Exception as e:
            logger.error(f"Root agent execution failed: {e}")
            return Content(data={
                "success": False,
                "error": "Root agent execution failed",
                "details": str(e)
            })
    
    async def _handle_search_interaction(self, content: Content) -> Content:
        """Handle search interaction requests through sub-agent."""
        if "search_interaction" not in self.sub_agents:
            return Content(data={
                "success": False,
                "error": "Search interaction sub-agent not available"
            })
        
        # Delegate to search interaction sub-agent
        result = await self.sub_agents["search_interaction"].execute(content)
        
        # Add root agent metadata
        if result.data:
            result.data["root_agent"] = {
                "name": self.config.name,
                "version": self.config.version,
                "delegated_to": "search_interaction"
            }
        
        return result
    
    async def _handle_candidate_search(self, content: Content) -> Content:
        """Handle candidate search requests."""
        search_filters = content.data.get("search_filters", {})
        
        # Execute search using search tool
        search_result = await self.tools["search_tool"](search_filters=search_filters)
        
        response_data = {
            "success": search_result["success"],
            "candidates": search_result.get("candidates", []),
            "total_count": search_result.get("total_count", 0),
            "message": search_result.get("message", ""),
            "root_agent": {
                "name": self.config.name,
                "version": self.config.version,
                "tool_used": "search_tool"
            }
        }
        
        if not search_result["success"]:
            response_data["error"] = search_result.get("error", "Search failed")
        
        return Content(data=response_data)
    
    async def _handle_health_check(self, content: Content) -> Content:
        """Handle health check requests."""
        # Test database connection
        from .utils.db_manager import db_manager
        db_status = await db_manager.test_connection()
        
        # Check sub-agent status
        sub_agent_status = {}
        for name, agent in self.sub_agents.items():
            sub_agent_status[name] = {
                "available": True,
                "name": agent.name if hasattr(agent, 'name') else name
            }
        
        health_data = {
            "success": True,
            "status": "healthy",
            "root_agent": {
                "name": self.config.name,
                "version": self.config.version,
                "config_valid": True
            },
            "database": {
                "status": "connected" if db_status["success"] else "error",
                "details": db_status
            },
            "sub_agents": sub_agent_status,
            "tools": list(self.tools.keys()),
            "system_info": {
                "debug_mode": self.config.debug_mode,
                "max_execution_time": self.config.max_execution_time,
                "parallel_execution": self.config.enable_parallel_execution
            }
        }
        
        return Content(data=health_data)