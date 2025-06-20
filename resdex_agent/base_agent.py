# resdex_agent/base_agent.py - COMPATIBILITY VERSION
"""
Base agent class for all ResDex agents with shared memory integration.
COMPATIBILITY VERSION - Minimal conflicts with existing code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class Content:
    """Content wrapper for agent communication."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data


class BaseResDexAgent(ABC):
    """
    Base class for all ResDex agents with memory integration.
    
    COMPATIBILITY VERSION - Minimal setup to avoid conflicts.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools = {}
        
        # Initialize shared memory service
        self._setup_memory()
        
        # Initialize common tools  
        self._setup_common_tools()
        
        logger.info(f"Initialized {name} with memory integration")
        print(f"🤖 {name} initialized with shared memory")
    
    def _setup_memory(self):
        """Setup shared memory service access."""
        try:
            from .memory.singleton_memory import memory_singleton
            self.memory_service = memory_singleton.get_memory_service()
            self.session_manager = memory_singleton.get_session_manager(self.name)
            
            # Add memory tool
            from .tools.memory_tools import MemoryTool
            self.memory_tool = MemoryTool("memory_tool", self.memory_service)
            
            print(f"🧠 {self.name} connected to shared memory service")
        except Exception as e:
            logger.error(f"Failed to setup memory for {self.name}: {e}")
            self.memory_service = None
            self.session_manager = None
            self.memory_tool = None
    
    def _setup_common_tools(self):
        """Setup tools that all agents need."""
        try:
            from .tools.validation_tools import ValidationTool
            self.tools["validation_tool"] = ValidationTool("validation_tool")
            
            # Only add LLM tool if not already present
            if "llm_tool" not in self.tools:
                from .tools.llm_tools import LLMTool
                self.tools["llm_tool"] = LLMTool(f"{self.name}_llm_tool")
                
        except Exception as e:
            logger.error(f"Failed to setup common tools for {self.name}: {e}")
    
    async def execute_with_memory_context(self, content: Content, session_id: str, user_id: str) -> Content:
        """
        Execute with memory context - can be called by subclasses.
        """
        try:
            # Get or create session for memory tracking
            if self.session_manager:
                session = await self.session_manager.get_or_create_session(
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Add interaction to session
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type=f"{self.name}_request",
                    content=content.data
                )
            
            # Get memory context for this request
            memory_context = await self.get_memory_context(content, user_id)
            
            # Execute core agent logic with memory context
            result = await self.execute_core(content, memory_context, session_id, user_id)
            
            # Add result to session memory
            if self.session_manager and result.data.get("success"):
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type=f"{self.name}_response",
                    content=result.data
                )
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} execution failed: {e}")
            return Content(data={
                "success": False,
                "error": f"{self.name} execution failed",
                "details": str(e)
            })
    
    async def get_memory_context(self, content: Content, user_id: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Get relevant memory context for the current request."""
        try:
            if not self.memory_tool:
                return []
            
            # Extract search terms for memory context
            search_terms = self.extract_memory_search_terms(content)
            
            if not search_terms:
                return []
            
            # Search memory
            memory_result = await self.memory_tool(
                user_id=user_id,
                query=search_terms,
                max_results=max_results
            )
            
            if memory_result["success"]:
                return memory_result["results"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get memory context for {self.name}: {e}")
            return []
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """
        Extract search terms for memory context.
        Override this in subclasses for agent-specific term extraction.
        """
        user_input = content.data.get("user_input", "")
        if user_input:
            # Simple keyword extraction
            words = user_input.lower().split()
            # Remove common words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            return " ".join(keywords[:5])  # Top 5 keywords
        return ""
    
    @abstractmethod
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Core execution logic for the agent.
        This method must be implemented by all subclasses.
        """
        pass
    
    def create_content(self, data: Dict[str, Any]) -> Content:
        """Helper method to create Content objects."""
        return Content(data=data)
    
    async def save_interaction_to_memory(self, user_id: str, session_id: str, 
                                       interaction_type: str, content: Dict[str, Any]):
        """Save an interaction to memory."""
        try:
            if self.session_manager:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type=interaction_type,
                    content=content
                )
        except Exception as e:
            logger.error(f"Failed to save interaction to memory: {e}")


# For backward compatibility with existing root agent
class Content:
    """Simple content wrapper for agent communication."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data


# Minimal mixin for existing agents
class MemoryMixin:
    """Memory capabilities that can be mixed into existing agents."""
    
    def __init__(self):
        self._setup_memory_mixin()
    
    def _setup_memory_mixin(self):
        """Setup memory for existing agents."""
        try:
            from .memory.singleton_memory import memory_singleton
            self.memory_service = memory_singleton.get_memory_service()
            self.session_manager = memory_singleton.get_session_manager(
                getattr(self, 'name', 'UnknownAgent')
            )
            
            from .tools.memory_tools import MemoryTool
            self.memory_tool = MemoryTool("memory_tool", self.memory_service)
            
            print(f"🧠 Added memory capabilities to {getattr(self, 'name', 'agent')}")
        except Exception as e:
            logger.error(f"Failed to setup memory mixin: {e}")
            self.memory_service = None
            self.session_manager = None
            self.memory_tool = None
    
    async def get_memory_context_mixin(self, user_input: str, user_id: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Get memory context - mixin version."""
        try:
            if not self.memory_tool or not user_input:
                return []
            
            # Simple search terms extraction
            words = user_input.lower().split()
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            search_terms = " ".join(keywords[:5])
            
            if not search_terms:
                return []
            
            memory_result = await self.memory_tool(
                user_id=user_id,
                query=search_terms,
                max_results=max_results
            )
            
            return memory_result.get("results", []) if memory_result.get("success") else []
            
        except Exception as e:
            logger.error(f"Memory context mixin failed: {e}")
            return []