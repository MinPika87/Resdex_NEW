# resdx_agent/agent.py - COMPLETE Enhanced Agent with Memory Integration
"""
Complete Enhanced Root ResDex Agent with all original methods + Memory Integration
"""

from typing import Dict, Any, List, Optional
import logging
import uuid
import asyncio
from datetime import datetime

# NEW IMPORTS for Google ADK Memory
from .memory.memory_service import InMemoryMemoryService
from .memory.session_manager import ADKSessionManager
from .tools.memory_tools import MemoryTool

# Existing imports
from .utils.step_logger import step_logger

logger = logging.getLogger(__name__)


class Content:
    """Simple content wrapper for agent communication."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data


class BaseAgent:
    """Simple base agent class without Pydantic."""
    def __init__(self, name: str, description: str = "", tools: List = None):
        self.name = name
        self.description = description
        # Store tools as dict
        self.tools = {}
        if tools:
            for tool in tools:
                self.tools[tool.name] = tool
        
        print(f"🔍 {name} initialized with tools: {list(self.tools.keys())}")


class ResDexRootAgent(BaseAgent):
    """
    Complete Enhanced Root agent with Memory + all original functionality
    """

    def __init__(self, config=None):
        from .config import AgentConfig
        self._config = config or AgentConfig.from_env()

        # Initialize memory service FIRST
        from .memory.singleton_memory import memory_singleton
        self.memory_service = memory_singleton.get_memory_service()
        self.session_manager = memory_singleton.get_session_manager(self._config.name)

        # Initialize tools including new memory tool
        from .tools.search_tools import SearchTool
        from .tools.llm_tools import LLMTool
        from .tools.validation_tools import ValidationTool
        from .tools.memory_tools import MemoryTool
        tools_list = [
            SearchTool("search_tool"),
            LLMTool("root_llm_tool"),
            ValidationTool("validation_tool"),
            MemoryTool("memory_tool", self.memory_service)
        ]

        # Call parent constructor
        super().__init__(
            name=self._config.name,
            description=self._config.description,
            tools=tools_list
        )

        # Initialize sub-agents
        self.sub_agents = {}
        self._initialize_sub_agents()

        logger.info(f"Enhanced {self._config.name} v{self._config.version} with Memory integration")

    @property
    def config(self):
        """Read-only access to config."""
        return self._config
    
    def _initialize_sub_agents(self):
        """Initialize all enabled sub-agents with memory access."""
        if self.config.is_sub_agent_enabled("search_interaction"):
            from .sub_agents.search_interaction.config import SearchInteractionConfig
            from .sub_agents.search_interaction.agent import SearchInteractionAgent
            
            sub_config = SearchInteractionConfig()
            search_agent = SearchInteractionAgent(sub_config)
            search_agent.memory_service = self.memory_service  # Share memory service
            self.sub_agents["search_interaction"] = search_agent
            logger.info("Initialized SearchInteractionAgent with memory access")
        
        logger.info(f"Initialized {len(self.sub_agents)} sub-agents with memory capabilities")
    
    async def execute(self, content: Content) -> Content:
        """ENHANCED execute with Memory integration + all original functionality."""
        try:
            # NEW: Extract or generate session ID for memory tracking
            session_id = content.data.get('session_id') or str(uuid.uuid4())
            user_id = content.data.get('user_id', 'default_user')
            
            # NEW: Get or create session for memory tracking
            session = await self.session_manager.get_or_create_session(
                user_id=user_id,
                session_id=session_id
            )
            
            # Check if this is a direct API call (has explicit request_type)
            if "request_type" in content.data and content.data["request_type"] != "auto_route":
                return await self._handle_direct_request_with_memory(content, session_id, user_id)
            
            # Enhanced LLM-driven routing for user inputs with memory integration
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            if user_input:
                return await self._handle_intelligent_routing_with_memory(
                    user_input, session_state, session_id, user_id
                )
            
            # Fallback to search interaction
            return await self._handle_search_interaction_with_memory(content, session_id)
                
        except Exception as e:
            if session_id:
                step_logger.log_error(f"Root agent execution failed: {str(e)}")
            logger.error(f"Enhanced root agent execution failed: {e}")
            import traceback
            traceback.print_exc()
            return Content(data={
                "success": False,
                "error": "Root agent execution failed",
                "details": str(e)
            })
    
    # NEW MEMORY METHODS
    async def _handle_direct_request_with_memory(self, content: Content, session_id: str, user_id: str) -> Content:
        """Handle direct API requests with memory integration."""
        request_type = content.data.get("request_type")
        
        if session_id:
            step_logger.log_step(f"🎯 Direct request with memory: {request_type}", "system")
        
        logger.info(f"Enhanced root agent processing direct request type: {request_type}")
        
        # NEW: Add user interaction to session for memory
        await self.session_manager.add_interaction(
            user_id=user_id,
            session_id=session_id,
            interaction_type="direct_request",
            content=content.data
        )
        
        if request_type == "search_interaction":
            return await self._handle_search_interaction_with_memory(content, session_id)
        elif request_type == "candidate_search":
            return await self._handle_candidate_search_with_memory(content, session_id, user_id)
        elif request_type == "health_check":
            return await self._handle_health_check_with_memory(content)
        elif request_type == "memory_query":  # NEW: Memory-specific requests
            return await self._handle_memory_query(content, user_id)
        else:
            if session_id:
                step_logger.log_error(f"Unknown request type: {request_type}")
            return Content(data={
                "success": False,
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["search_interaction", "candidate_search", "health_check", "memory_query"]
            })
    async def _handle_chat_message_complete(self, user_input: str, response: str, user_id: str, session_id: str):
        """Save chat interaction to memory immediately."""
        try:
            # Add user message to session
            await self.session_manager.add_interaction(
                user_id=user_id,
                session_id=session_id,
                interaction_type="user_message",
                content={"message": user_input}
            )
            
            # Add assistant response to session
            await self.session_manager.add_interaction(
                user_id=user_id,
                session_id=session_id,
                interaction_type="assistant_response",
                content={"message": response}
            )
            
            # CRITICAL: Save to long-term memory immediately
            await self.save_session_to_memory(user_id, session_id)
            print(f"💾 Saved conversation to memory: user={user_id}")
            
        except Exception as e:
            print(f"❌ Failed to save conversation: {e}")

    async def _handle_intelligent_routing_with_memory(self, user_input: str, session_state: Dict[str, Any], session_id: str, user_id: str) -> Content:
        if session_id:
            step_logger.current_session_id = session_id
            step_logger.log_step(f"🧠 Analyzing input with memory context", "routing")
        
        print(f"🧠 ENHANCED ROOT AGENT: Intelligent routing with MEMORY for '{user_input}'")
        
        # NEW: Add user input to session for memory
        await self.session_manager.add_interaction(
            user_id=user_id,
            session_id=session_id,
            interaction_type="user_input",
            content={"message": user_input, "session_state": session_state}
        )
        
        # NEW: Check if this is a memory-related query
        if self._is_memory_query(user_input):
            if session_id:
                step_logger.log_step("🧠 Memory query detected", "decision")
            return await self._handle_memory_query_from_input(user_input, user_id, session_id)
        
        # Step 1: Route the request using LLM with memory context
        routing_result = await self._route_request_with_memory_context(user_input, session_state, session_id, user_id)
        
        if not routing_result["success"]:
            return Content(data=routing_result)
        
        request_type = routing_result["request_type"]
        confidence = routing_result.get("confidence", 0.0)
        
        if session_id:
            step_logger.log_step(f"✅ Route determined: {request_type}", "decision")
        
        print(f"🎯 ENHANCED ROUTING DECISION: {request_type} (confidence: {confidence:.2f})")
        
        if request_type == "search_interaction":
            # Step 2: Task breakdown for complex search operations with memory
            return await self._handle_search_with_task_breakdown_and_memory(user_input, session_state, session_id, user_id)
        
        elif request_type == "general_query":
            # Step 3: Handle general queries with memory context
            return await self._handle_general_query_with_memory(user_input, session_state, session_id, user_id)
        
        else:
            if session_id:
                step_logger.log_error(f"Unknown routed request type: {request_type}")
            return Content(data={
                "success": False,
                "error": f"Unknown routed request type: {request_type}"
            })

    def _is_memory_query(self, user_input: str) -> bool:
        """Check if the user input is asking about past conversations or memory."""
        memory_keywords = [
            "remember", "recall", "what did we discuss", "previous conversation",
            "last time", "before", "earlier", "history", "past", "mentioned",
            "talked about", "said before", "previous search", "last search"
        ]
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in memory_keywords)

    async def _handle_memory_query_from_input(self, user_input: str, user_id: str, session_id: str) -> Content:
        """Handle memory-related queries from user input."""
        try:
            if session_id:
                step_logger.log_step("🔍 Searching conversation memory", "search")
            
            # Extract search query from user input
            search_query = self._extract_memory_search_query(user_input)
            
            # Search memory using the memory tool
            memory_results = await self.tools["memory_tool"](
                user_id=user_id,
                query=search_query,
                max_results=5
            )
            
            if memory_results["success"] and memory_results["results"]:
                results = memory_results["results"]
                
                if session_id:
                    step_logger.log_step(f"📚 Found {len(results)} relevant memories", "results")
                
                # Format the memory results for user
                memory_response = self._format_memory_response(results, search_query)
                
                # Add this interaction to session
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type="memory_response",
                    content={"query": search_query, "results_count": len(results)}
                )
                
                if session_id:
                    step_logger.log_completion("Memory query completed")
                
                return Content(data={
                    "success": True,
                    "message": memory_response,
                    "type": "memory_query",
                    "trigger_search": False,
                    "session_state": {},
                    "memory_results": results
                })
            else:
                if session_id:
                    step_logger.log_step("📭 No relevant memories found", "info")
                
                return Content(data={
                    "success": True,
                    "message": f"I don't have any previous conversations about '{search_query}'. This might be our first discussion on this topic!",
                    "type": "memory_query",
                    "trigger_search": False,
                    "session_state": {}
                })
                
        except Exception as e:
            if session_id:
                step_logger.log_error(f"Memory query failed: {str(e)}")
            
            return Content(data={
                "success": False,
                "error": f"Memory query failed: {str(e)}",
                "message": "I had trouble searching through our conversation history. Please try rephrasing your question."
            })

    def _extract_memory_search_query(self, user_input: str) -> str:
        """Extract the key search terms from a memory-related query."""
        memory_phrases = [
            "what did we discuss about", "do you remember", "recall",
            "what did we talk about", "previous conversation about",
            "last time we talked about", "before when we discussed",
            "earlier when we mentioned", "what did i say about",
            "what did you say about"
        ]
        
        query = user_input.lower()
        for phrase in memory_phrases:
            if phrase in query:
                parts = query.split(phrase, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                break
        
        query = query.replace("?", "").strip()
        stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = [word for word in query.split() if word not in stop_words and len(word) > 2]
        
        return " ".join(words) if words else user_input

    def _format_memory_response(self, results: List[Dict[str, Any]], search_query: str) -> str:
        """Format memory search results into a user-friendly response."""
        response_parts = [f"📚 **Found {len(results)} relevant memories about '{search_query}':**\n"]
        
        for i, result in enumerate(results[:3], 1):  # Show top 3 results
            session_info = result.get("session_id", "Unknown session")
            timestamp = result.get("timestamp", "Unknown time")
            content = result.get("content", "")
            
            # Extract key information from the content
            if isinstance(content, dict):
                if "user_input" in content:
                    summary = f"You asked: '{content['user_input'][:100]}...'"
                elif "message" in content:
                    summary = f"We discussed: '{content['message'][:100]}...'"
                else:
                    summary = "General conversation"
            else:
                summary = str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
            
            response_parts.append(f"**{i}.** {summary}")
            response_parts.append(f"   *Session: {session_info[:8]}... on {timestamp}*\n")
        
        if len(results) > 3:
            response_parts.append(f"*...and {len(results) - 3} more related conversations.*")
        
        response_parts.append("\n💡 Would you like me to help you with something related to these past discussions?")
        
        return "\n".join(response_parts)    

    async def _route_request_with_memory_context(self, user_input: str, session_state: Dict[str, Any], session_id: str, user_id: str) -> Dict[str, Any]:
        try:
            if session_id:
                step_logger.log_step("🤖 Consulting routing LLM with memory context", "llm")
            
            # Get recent memory context
            memory_context = await self._get_recent_memory_context(user_id)
            
            # FIX: Use fallback prompts if enhanced prompts fail
            try:
                from .prompts import RootAgentPrompts
                routing_prompt = RootAgentPrompts.get_routing_prompt_with_memory(
                    user_input, session_state, memory_context
                )
            except (ImportError, AttributeError):
                # Fallback to simple routing prompt
                routing_prompt = self._get_simple_routing_prompt(user_input, session_state)
            
            # Call LLM for routing decision
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=routing_prompt,
                task="routing_with_memory"
            )
            
            if llm_result["success"]:
                # FIX: Handle missing parsed_response key
                parsed_response = llm_result.get("parsed_response")
                if parsed_response:
                    return {
                        "success": True,
                        "request_type": parsed_response.get("request_type", "general_query"),
                        "confidence": parsed_response.get("confidence", 0.5),
                        "reasoning": parsed_response.get("reasoning", ""),
                        "memory_influenced": parsed_response.get("memory_influenced", False)
                    }
                else:
                    # If no parsed response, use fallback
                    print("⚠️ No parsed response from LLM, using fallback routing")
                    return self._fallback_routing(user_input)
            else:
                return self._fallback_routing(user_input)
                
        except Exception as e:
            print(f"❌ LLM routing with memory failed: {e}")
            return self._fallback_routing(user_input)

    async def _get_recent_memory_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent memory context for better routing decisions."""
        try:
            # Search for recent general interactions
            memory_results = await self.tools["memory_tool"](
                user_id=user_id,
                query="search interaction general",  # Broad query to get recent activity
                max_results=limit
            )
            
            if memory_results["success"]:
                return memory_results["results"]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get memory context: {e}")
            return []

    async def _handle_search_with_task_breakdown_and_memory(self, user_input: str, session_state: Dict[str, Any], session_id: str, user_id: str) -> Content:
        """Handle search requests with memory integration."""
        try:
            if session_id:
                step_logger.log_step("🔧 Activating Search Interaction Agent with memory", "tool")
            
            print(f"🔧 MEMORY-ENHANCED SEARCH INTERACTION: Processing '{user_input}'")
            
            if session_id:
                step_logger.log_step("🔄 Using memory-enhanced search processing", "tool")
            
            # NEW: Add search context to memory
            await self.session_manager.add_interaction(
                user_id=user_id,
                session_id=session_id,
                interaction_type="search_request",
                content={"query": user_input, "session_state": session_state}
            )
            
            # Go to enhanced search interaction with memory
            return await self._fallback_to_search_interaction_with_memory(user_input, session_state, session_id, user_id)
                
        except Exception as e:
            if session_id:
                step_logger.log_error(f"Memory-enhanced search processing failed: {str(e)}")
            logger.error(f"Memory-enhanced search processing failed: {e}")
            return await self._fallback_to_search_interaction_with_memory(user_input, session_state, session_id, user_id)

    async def _handle_general_query_with_memory(self, user_input: str, session_state: Dict[str, Any], session_id: str, user_id: str) -> Content:
        try:
            if session_id:
                step_logger.current_session_id = session_id
                step_logger.log_step("🤖 Generating response with memory context", "llm")
            
            # NEW: Get relevant memory context for the query
            memory_context = await self._get_query_specific_memory_context(user_input, user_id)
            
            from .prompts import RootAgentPrompts
            
            general_prompt = RootAgentPrompts.get_general_query_prompt_with_memory(
                user_input, session_state, memory_context
            )
            
            print(f"💬 MEMORY-ENHANCED GENERAL QUERY: Processing '{user_input}'")
            
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=general_prompt,
                task="general_conversation_with_memory"
            )
            
            if llm_result["success"]:
                response_text = llm_result.get("response_text", "I'm here to help!")
                
                # NEW: Add this interaction to memory
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type="general_response",
                    content={"query": user_input, "response": response_text}
                )
                
                if session_id:
                    step_logger.log_step("🎯 Memory-enhanced response generated", "completion")
                    step_logger.log_completion("Response ready")
                
                return Content(data={
                    "success": True,
                    "message": response_text,
                    "type": "general_query",
                    "trigger_search": False,
                    "session_state": session_state,
                    "llm_response": True,
                    "memory_enhanced": True
                })
            else:
                if session_id:
                    step_logger.log_step("⚠️ LLM response failed, using fallback", "decision")
                
                # Enhanced fallback with memory awareness
                fallback_message = await self._get_memory_aware_fallback_response(user_input, user_id)
                
                if session_id:
                    step_logger.log_completion("Memory-aware fallback response provided")
                
                return Content(data={
                    "success": True,
                    "message": fallback_message,
                    "type": "general_query",
                    "trigger_search": False,
                    "session_state": session_state,
                    "fallback_response": True,
                    "memory_enhanced": True
                })
                
        except Exception as e:
            if session_id:
                step_logger.log_error(f"Memory-enhanced general query processing failed: {str(e)}")
            logger.error(f"Memory-enhanced general query processing failed: {e}")
            return Content(data={
                "success": False,
                "error": "Failed to process general query",
                "message": "I encountered an error. Please try rephrasing your question."
            })

    async def _get_query_specific_memory_context(self, user_input: str, user_id: str) -> List[Dict[str, Any]]:
        """Get memory context relevant to the specific query."""
        try:
            # Extract key terms from user input for memory search
            key_terms = self._extract_key_terms_for_memory_search(user_input)
            
            if key_terms:
                memory_results = await self.tools["memory_tool"](
                    user_id=user_id,
                    query=" ".join(key_terms),
                    max_results=3
                )
                
                if memory_results["success"]:
                    return memory_results["results"]
            
            return []
        except Exception as e:
            logger.error(f"Failed to get query-specific memory context: {e}")
            return []

    def _extract_key_terms_for_memory_search(self, user_input: str) -> List[str]:
        """Extract key terms from user input for memory search."""
        # Simple keyword extraction - remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "i", "you", "me", "my", "your"}
        words = user_input.lower().split()
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        return key_terms[:5]  # Return top 5 key terms

    async def _get_memory_aware_fallback_response(self, user_input: str, user_id: str) -> str:
        """Generate a fallback response that's aware of conversation history."""
        try:
            # Check if user has any conversation history
            memory_results = await self.tools["memory_tool"](
                user_id=user_id,
                query="general interaction",
                max_results=1
            )
            
            if memory_results["success"] and memory_results["results"]:
                return f"I understand you're asking about '{user_input}'. Based on our previous conversations, I'm here to help with candidate search and analysis. Could you please rephrase your question or let me know what specific help you need?"
            else:
                return f"I understand you're asking about '{user_input}'. I'm your AI assistant for candidate search. I can help you search for candidates, analyze results, and modify filters. What would you like to do?"
        except:
            return "I'm here to help with candidate search! You can ask me to search for candidates, modify filters, or analyze results."

    async def _handle_candidate_search_with_memory(self, content: Content, session_id: str, user_id: str) -> Content:
        """Handle candidate search requests with memory logging."""
        search_filters = content.data.get("search_filters", {})
        
        if session_id:
            step_logger.log_step("🔍 Preparing candidate search with memory", "search")
            step_logger.log_search_execution(search_filters)
        
        # NEW: Log search to memory
        await self.session_manager.add_interaction(
            user_id=user_id,
            session_id=session_id,
            interaction_type="candidate_search",
            content={"filters": search_filters}
        )
        
        search_result = await self.tools["search_tool"](search_filters=search_filters)
        
        # NEW: Log search results to memory
        if search_result["success"]:
            await self.session_manager.add_interaction(
                user_id=user_id,
                session_id=session_id,
                interaction_type="search_results",
                content={
                    "candidates_found": len(search_result.get("candidates", [])),
                    "total_count": search_result.get("total_count", 0),
                    "search_successful": True
                }
            )
        
        if session_id:
            if search_result["success"]:
                step_logger.log_results(
                    len(search_result.get("candidates", [])),
                    search_result.get("total_count", 0)
                )
                step_logger.log_completion("Search completed with memory")
            else:
                step_logger.log_error(f"Search failed: {search_result.get('error', 'Unknown error')}")
        
        response_data = {
            "success": search_result["success"],
            "candidates": search_result.get("candidates", []),
            "total_count": search_result.get("total_count", 0),
            "message": search_result.get("message", ""),
            "root_agent": {
                "name": self.config.name,
                "version": self.config.version,
                "tool_used": "search_tool",
                "memory_enabled": True
            }
        }
        
        if not search_result["success"]:
            response_data["error"] = search_result.get("error", "Search failed")
        
        return Content(data=response_data)

    async def _handle_health_check_with_memory(self, content: Content) -> Content:
        """Handle health check requests with memory status."""
        from .utils.db_manager import db_manager
        db_status = await db_manager.test_connection()
        
        sub_agent_status = {}
        for name, agent in self.sub_agents.items():
            sub_agent_status[name] = {
                "available": True,
                "name": getattr(agent, 'name', name),
                "memory_enabled": hasattr(agent, 'memory_service')
            }
        
        # NEW: Get memory service status
        memory_status = await self._get_memory_service_status()
        
        health_data = {
            "success": True,
            "status": "healthy",
            "root_agent": {
                "name": self.config.name,
                "version": self.config.version,
                "config_valid": True,
                "enhanced_features": ["llm_routing", "task_breakdown", "general_queries", "step_logging", "memory_integration"]
            },
            "database": {
                "status": "connected" if db_status["success"] else "error",
                "details": db_status
            },
            "memory_service": memory_status,
            "sub_agents": sub_agent_status,
            "tools": list(self.tools.keys()),
            "system_info": {
                "debug_mode": self.config.debug_mode,
                "max_execution_time": self.config.max_execution_time,
                "parallel_execution": self.config.enable_parallel_execution,
                "memory_type": "InMemoryMemoryService"
            }
        }
        
        return Content(data=health_data)

    async def _get_memory_service_status(self) -> Dict[str, Any]:
        """Get the status of the memory service."""
        try:
            # Test memory service functionality
            test_user = "health_check_user"
            
            # Try to search memory (should not fail even if empty)
            test_search = await self.tools["memory_tool"](
                user_id=test_user,
                query="test",
                max_results=1
            )
            
            return {
                "status": "operational" if test_search["success"] else "error",
                "type": "InMemoryMemoryService",
                "sessions_active": len(self.session_manager.sessions),
                "memory_entries": len(getattr(self.memory_service, 'memory_store', {})),
                "search_functional": test_search["success"]
            }
        except Exception as e:
            return {
                "status": "error",
                "type": "InMemoryMemoryService",
                "error": str(e),
                "sessions_active": 0,
                "memory_entries": 0,
                "search_functional": False
            }

    async def _handle_memory_query(self, content: Content, user_id: str) -> Content:
        """Handle direct memory query requests."""
        try:
            query = content.data.get("query", "")
            max_results = content.data.get("max_results", 10)
            
            if not query:
                return Content(data={
                    "success": False,
                    "error": "Query parameter is required for memory search"
                })
            
            # Use memory tool to search
            memory_results = await self.tools["memory_tool"](
                user_id=user_id,
                query=query,
                max_results=max_results
            )
            
            return Content(data={
                "success": memory_results["success"],
                "results": memory_results.get("results", []),
                "total_found": len(memory_results.get("results", [])),
                "query": query,
                "root_agent": {
                    "name": self.config.name,
                    "version": self.config.version,
                    "memory_enabled": True
                }
            })
            
        except Exception as e:
            return Content(data={
                "success": False,
                "error": f"Memory query failed: {str(e)}",
                "results": [],
                "total_found": 0
            })

    async def _fallback_to_search_interaction_with_memory(self, user_input: str, session_state: Dict[str, Any], session_id: str, user_id: str) -> Content:
        """ENHANCED: Fallback to search interaction agent with memory integration."""
        try:
            if session_id:
                step_logger.log_step("🔄 Using memory-enhanced search processing", "tool")
            
            content = Content(data={
                "request_type": "search_interaction",
                "user_input": user_input,
                "session_state": session_state,
                "session_id": session_id,
                "user_id": user_id  # NEW: Pass user_id for memory
            })
            
            result = await self._handle_search_interaction_with_memory(content, session_id)
            
            # NEW: Add interaction result to memory
            if result.data.get("success"):
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_type="search_interaction_result",
                    content={
                        "user_input": user_input,
                        "modifications": result.data.get("modifications", []),
                        "trigger_search": result.data.get("trigger_search", False)
                    }
                )
            
            return result
            
        except Exception as fallback_error:
            if session_id:
                step_logger.log_error(f"Memory-enhanced fallback processing failed: {str(fallback_error)}")
            
            return Content(data={
                "success": False,
                "error": f"Processing failed: {str(fallback_error)}",
                "message": "Sorry, I couldn't process that request. Please try rephrasing it."
            })

    async def _handle_search_interaction_with_memory(self, content: Content, session_id: str) -> Content:
        """Handle search interaction requests through sub-agent with memory."""
        if "search_interaction" not in self.sub_agents:
            return Content(data={
                "success": False,
                "error": "Search interaction sub-agent not available"
            })
        
        # NEW: Pass memory context to sub-agent
        if hasattr(self.sub_agents["search_interaction"], 'memory_service'):
            self.sub_agents["search_interaction"].current_session_id = session_id
        
        result = await self.sub_agents["search_interaction"].execute(content)
        
        if result.data:
            result.data["root_agent"] = {
                "name": self.config.name,
                "version": self.config.version,
                "delegated_to": "search_interaction",
                "memory_enabled": True
            }
        
        return result

    # ORIGINAL METHODS FROM YOUR EXISTING AGENT.PY - ALL PRESERVED
    
    def _fallback_routing(self, user_input: str) -> Dict[str, Any]:
        """Fallback routing using keyword detection."""
        search_keywords = ["search", "find", "add", "remove", "filter", "set", "modify", "candidates"]
        general_keywords = ["hi", "hello", "analyze", "explain", "what", "how", "help"]
        memory_keywords = ["remember", "recall", "previous", "before", "last time", "discussed"]
        
        input_lower = user_input.lower()
        
        if any(keyword in input_lower for keyword in memory_keywords):
            return {"success": True, "request_type": "memory_query", "confidence": 0.8}
        elif any(keyword in input_lower for keyword in search_keywords):
            return {"success": True, "request_type": "search_interaction", "confidence": 0.7}
        elif any(keyword in input_lower for keyword in general_keywords):
            return {"success": True, "request_type": "general_query", "confidence": 0.7}
        else:
            return {"success": True, "request_type": "general_query", "confidence": 0.5}
    
    async def _execute_filter_modification(self, parameters: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute filter modification."""
        try:
            from .tools.filter_tools import FilterTool
            filter_tool = FilterTool()
            
            # Determine action type from parameters
            if "skill" in parameters:
                action = "add_skill"
                result = await filter_tool(action, session_state, **parameters)
            elif "experience_range" in parameters:
                action = "modify_experience"
                result = await filter_tool(action, session_state, **parameters)
            elif "salary_range" in parameters:
                action = "modify_salary" 
                result = await filter_tool(action, session_state, **parameters)
            elif "locations" in parameters:
                action = "add_location"
                # Add multiple locations
                all_mods = []
                for location in parameters["locations"]:
                    loc_result = await filter_tool("add_location", session_state, location=location)
                    if loc_result["success"]:
                        all_mods.extend(loc_result["modifications"])
                result = {"success": True, "modifications": all_mods, "message": f"Added {len(parameters['locations'])} locations"}
            else:
                result = {"success": False, "error": "Unknown filter modification parameters"}
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_location_analysis(self, parameters: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute intelligent location analysis using Qwen LLM."""
        try:
            base_location = parameters.get("base_location", "Mumbai")
            analysis_type = parameters.get("analysis_type", "similar")
            criteria = parameters.get("criteria", "job market and tech industry")
            
            # Use the new intelligent location analysis tool
            from .tools.location_tools import LocationAnalysisTool
            location_tool = LocationAnalysisTool()
            
            print(f"🗺️ INTELLIGENT LOCATION ANALYSIS: {analysis_type} locations for {base_location}")
            
            result = await location_tool(
                base_location=base_location,
                analysis_type=analysis_type,
                criteria=criteria
            )
            
            if result["success"]:
                if analysis_type == "similar":
                    locations = result.get("similar_locations", [])
                elif analysis_type == "nearby":
                    locations = result.get("nearby_locations", [])
                elif analysis_type == "metro_area":
                    locations = result.get("metro_area_locations", [])
                elif analysis_type == "industry_hubs":
                    locations = result.get("industry_hubs", [])
                else:
                    locations = result.get("similar_locations", [])
                
                method_used = result.get("method", "unknown")
                print(f"🎯 LOCATION ANALYSIS RESULT ({method_used}):")
                print(f"  - Base: {base_location}")
                print(f"  - Found: {locations}")
                
                if "reasoning" in result:
                    print(f"  - Reasoning: {result['reasoning']}")
                
                return {
                    "success": True,
                    "base_location": base_location,
                    "similar_locations": locations,  # Keep this key for backward compatibility
                    "analysis_result": result,
                    "method": method_used,
                    "message": result.get("message", f"Found {len(locations)} locations")
                }
            else:
                # Fallback to simple mapping
                return await self._fallback_simple_location_mapping(base_location)
                
        except Exception as e:
            logger.error(f"Intelligent location analysis failed: {e}")
            return await self._fallback_simple_location_mapping(base_location)
    
    async def _fallback_simple_location_mapping(self, base_location: str) -> Dict[str, Any]:
        """Simple fallback location mapping."""
        simple_mapping = {
            "Mumbai": ["Pune", "Thane", "Navi Mumbai"],
            "Bangalore": ["Mysore", "Hubli", "Mangalore"],
            "Delhi": ["Gurgaon", "Noida", "Faridabad"],
            "Chennai": ["Coimbatore", "Madurai", "Trichy"],
            "Hyderabad": ["Vijayawada", "Visakhapatnam", "Warangal"],
            "Pune": ["Mumbai", "Nashik", "Aurangabad"]
        }
        
        similar_locations = simple_mapping.get(base_location, [base_location])
        
        return {
            "success": True,
            "base_location": base_location,
            "similar_locations": similar_locations,
            "method": "simple_fallback",
            "message": f"Found {len(similar_locations)} similar locations (fallback)"
        }
    
    async def _execute_search(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute candidate search."""
        search_filters = {
            'keywords': session_state.get('keywords', []),
            'min_exp': session_state.get('min_exp', 0),
            'max_exp': session_state.get('max_exp', 10),
            'min_salary': session_state.get('min_salary', 0),
            'max_salary': session_state.get('max_salary', 15),
            'current_cities': session_state.get('current_cities', []),
            'preferred_cities': session_state.get('preferred_cities', []),
            'recruiter_company': session_state.get('recruiter_company', '')
        }
        
        return await self.tools["search_tool"](search_filters=search_filters)
    
    # NEW MEMORY METHODS FOR SESSION MANAGEMENT
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old memory sessions to prevent memory leaks."""
        try:
            await self.session_manager.cleanup_old_sessions(max_age_hours)
            logger.info(f"Cleaned up sessions older than {max_age_hours} hours")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory service statistics."""
        try:
            stats = {
                "total_sessions": len(self.session_manager.sessions),
                "memory_entries": len(getattr(self.memory_service, 'memory_store', {})),
                "active_sessions": len([s for s in self.session_manager.sessions.values() if s.get('active', False)]),
                "memory_service_type": "InMemoryMemoryService"
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    async def save_session_to_memory(self, user_id: str, session_id: str):
        """Save the current session to long-term memory."""
        try:
            await self.session_manager.save_session_to_memory(user_id, session_id)
            logger.info(f"Saved session {session_id} to memory for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save session to memory: {e}")
    
    async def _execute_task_plan_with_logging(self, task_plan: Dict[str, Any], user_input: str, session_state: Dict[str, Any], session_id: str = None) -> Content:
        """Execute task plan with logging."""
        try:
            # FIXED: Handle both dict and list responses from LLM properly
            if isinstance(task_plan, list):
                # If task_plan is a list, wrap it in the expected structure
                task_plan = {
                    "tasks": task_plan,
                    "final_goal": "Process user request",
                    "requires_search": False
                }
            elif not isinstance(task_plan, dict):
                # If it's neither list nor dict, create a fallback structure
                if session_id:
                    step_logger.log_error("Invalid task plan format received")
                return await self._fallback_to_search_interaction_with_memory(user_input, session_state, session_id, session_state.get('user_id', 'default_user'))
            
            tasks = task_plan.get("tasks", [])
            final_goal = task_plan.get("final_goal", "Process user request")
            requires_search = task_plan.get("requires_search", False)
            
            if session_id:
                step_logger.log_step(f"🚀 Executing {len(tasks)} tasks", "system")
            
            print(f"🚀 ENHANCED EXECUTING {len(tasks)} tasks for: {final_goal}")
            
            # If no tasks or invalid tasks, fall back to search interaction
            if not tasks or not isinstance(tasks, list):
                if session_id:
                    step_logger.log_step("⚠️ No valid tasks found, using fallback processing", "decision")
                return await self._fallback_to_search_interaction_with_memory(user_input, session_state, session_id, session_state.get('user_id', 'default_user'))
            
            all_modifications = []
            final_message = ""
            
            for i, task in enumerate(tasks, 1):
                # FIXED: Handle task being a dict or having missing keys with better error handling
                if not isinstance(task, dict):
                    if session_id:
                        step_logger.log_step(f"⚠️ Skipping invalid task {i}", "decision")
                    continue
                    
                step = task.get("step", i)
                action = task.get("action", "")
                description = task.get("description", f"Task {i}")
                parameters = task.get("parameters", {})
                
                if session_id:
                    step_logger.log_step(f"⚙️ Step {step}: {description}", "tool")
                
                print(f"📍 Enhanced Step {step}: {description}")
                
                try:
                    if action == "filter_modification":
                        mod_result = await self._execute_filter_modification(parameters, session_state)
                        if mod_result["success"]:
                            all_modifications.extend(mod_result.get("modifications", []))
                    
                    elif action == "location_analysis":
                        loc_result = await self._execute_location_analysis(parameters, session_state)
                        if loc_result["success"]:
                            # Add discovered locations to next filter step
                            for next_task in tasks:
                                if (isinstance(next_task, dict) and 
                                    next_task.get("action") == "filter_modification" and 
                                    "locations" in next_task.get("parameters", {})):
                                    next_task["parameters"]["locations"] = loc_result.get("similar_locations", [])
                    
                    elif action == "search_execution":
                        if session_id:
                            step_logger.log_step("🔍 Executing candidate search", "search")
                        # Execute search with current filters
                        search_result = await self._execute_search(session_state)
                        if search_result["success"]:
                            session_state.update({
                                'candidates': search_result["candidates"],
                                'total_results': search_result["total_count"],
                                'search_applied': True,
                                'page': 0
                            })
                            if session_id:
                                step_logger.log_results(
                                    len(search_result["candidates"]),
                                    search_result["total_count"]
                                )
                            final_message = search_result.get("message", "Search completed")
                    
                    else:
                        if session_id:
                            step_logger.log_step(f"⚠️ Unknown action: {action}", "decision")
                        
                except Exception as task_error:
                    if session_id:
                        step_logger.log_error(f"Task {i} failed: {str(task_error)}")
                    print(f"❌ Task {i} failed: {task_error}")
                    continue
            
            if session_id:
                step_logger.log_completion("All tasks completed successfully")
            
            # Prepare final response
            response_data = {
                "success": True,
                "message": final_message or f"Completed {len(tasks)} tasks: {final_goal}",
                "modifications": all_modifications,
                "trigger_search": False,  # Search already executed if needed
                "session_state": session_state,
                "task_breakdown": {
                    "tasks_executed": len(tasks),
                    "final_goal": final_goal,
                    "plan": task_plan
                }
            }
            
            return Content(data=response_data)
            
        except Exception as e:
            if session_id:
                step_logger.log_error(f"Task plan execution failed: {str(e)}")
            logger.error(f"Enhanced task plan execution failed: {e}")
            
            # ENHANCED: Always fall back to search interaction on error
            print(f"⚠️ Task plan failed, falling back to search interaction for: {user_input}")
            return await self._fallback_to_search_interaction_with_memory(user_input, session_state, session_id, session_state.get('user_id', 'default_user'))

    async def _handle_triggered_search_with_steps(self, result_data: Dict[str, Any], session_id: str, update_all_steps):
        """Handle search triggered by AI agent with live step updates."""
        try:
            step_logger.log_step("⚙️ Preparing search execution", "search")
            update_all_steps()
            await asyncio.sleep(0.1)
            
            updated_state = result_data.get("session_state", {})
            if not isinstance(updated_state, dict):
                updated_state = {}
            
            search_filters = {
                'keywords': updated_state.get('keywords', []),
                'min_exp': updated_state.get('min_exp', 0),
                'max_exp': updated_state.get('max_exp', 10),
                'min_salary': updated_state.get('min_salary', 0),
                'max_salary': updated_state.get('max_salary', 15),
                'current_cities': updated_state.get('current_cities', []),
                'preferred_cities': updated_state.get('preferred_cities', []),
                'recruiter_company': updated_state.get('recruiter_company', '')
            }
            
            step_logger.log_search_execution(search_filters)
            update_all_steps()
            await asyncio.sleep(0.1)
            
            # Execute search
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters,
                "session_id": session_id
            })
            
            step_logger.log_step("📡 Calling ResDex API", "search")
            update_all_steps()
            await asyncio.sleep(0.1)
            
            search_result = await self.execute(search_content)
            
            if search_result.data["success"]:
                candidates = search_result.data["candidates"]
                total_count = search_result.data["total_count"]
                
                step_logger.log_results(len(candidates), total_count)
                update_all_steps()
                await asyncio.sleep(0.1)
                
                step_logger.log_completion("Search completed successfully")
                update_all_steps()
            else:
                error_msg = search_result.data.get('error', 'Unknown error')
                step_logger.log_error(f"Search failed: {error_msg}")
                update_all_steps()
                
        except Exception as e:
            step_logger.log_error(f"Search execution failed: {str(e)}")
            update_all_steps()

    # UTILITY METHOD FOR SESSION STATE
    def _get_clean_session_state(self) -> Dict[str, Any]:
        """Get clean session state for agent processing."""
        # This is a simplified version - in practice this would be called from the UI
        return {
            'keywords': [],
            'min_exp': 0,
            'max_exp': 10,
            'min_salary': 0,
            'max_salary': 15,
            'current_cities': [],
            'preferred_cities': [],
            'recruiter_company': '',
            'candidates': [],
            'total_results': 0,
            'search_applied': False,
            'page': 0
        }