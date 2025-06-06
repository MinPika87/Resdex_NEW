# Replace resdex_agent/agent.py with this enhanced version

"""
Enhanced Root ResDex Agent with LLM routing and task breakdown.
"""

from typing import Dict, Any, List, Optional
import logging

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
    Enhanced Root agent with LLM routing and task breakdown capabilities.
    """

    def __init__(self, config=None):
        from .config import AgentConfig
        self._config = config or AgentConfig.from_env()

        # Initialize tools including new LLM tool for routing
        from .tools.search_tools import SearchTool
        from .tools.llm_tools import LLMTool
        from .tools.validation_tools import ValidationTool
        
        tools_list = [
            SearchTool("search_tool"),
            LLMTool("root_llm_tool"),  # LLM tool for root agent
            ValidationTool("validation_tool")
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

        logger.info(f"Enhanced {self._config.name} v{self._config.version} with LLM routing")

    @property
    def config(self):
        """Read-only access to config."""
        return self._config
    
    def _initialize_sub_agents(self):
        """Initialize all enabled sub-agents."""
        if self.config.is_sub_agent_enabled("search_interaction"):
            from .sub_agents.search_interaction.config import SearchInteractionConfig
            from .sub_agents.search_interaction.agent import SearchInteractionAgent
            
            sub_config = SearchInteractionConfig()
            self.sub_agents["search_interaction"] = SearchInteractionAgent(sub_config)
            logger.info("Initialized SearchInteractionAgent")
        
        logger.info(f"Initialized {len(self.sub_agents)} sub-agents")
    
    async def execute(self, content: Content) -> Content:
        """Enhanced execute with LLM routing and task breakdown."""
        try:
            # Check if this is a direct API call (has explicit request_type)
            if "request_type" in content.data and content.data["request_type"] != "auto_route":
                return await self._handle_direct_request(content)
            
            # NEW: LLM-driven routing for user inputs
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            if user_input:
                return await self._handle_intelligent_routing(user_input, session_state)
            
            # Fallback to search interaction
            return await self._handle_search_interaction(content)
                
        except Exception as e:
            logger.error(f"Enhanced root agent execution failed: {e}")
            import traceback
            traceback.print_exc()
            return Content(data={
                "success": False,
                "error": "Root agent execution failed",
                "details": str(e)
            })
    
    async def _handle_direct_request(self, content: Content) -> Content:
        """Handle direct API requests (original functionality)."""
        request_type = content.data.get("request_type")
        
        logger.info(f"Root agent processing direct request type: {request_type}")
        
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
    
    async def _handle_intelligent_routing(self, user_input: str, session_state: Dict[str, Any]) -> Content:
        """NEW: Intelligent LLM-driven routing and task breakdown."""
        print(f"🧠 ROOT AGENT: Intelligent routing for '{user_input}'")
        
        # Step 1: Route the request using LLM
        routing_result = await self._route_request(user_input, session_state)
        
        if not routing_result["success"]:
            return Content(data=routing_result)
        
        request_type = routing_result["request_type"]
        confidence = routing_result.get("confidence", 0.0)
        
        print(f"🎯 ROUTING DECISION: {request_type} (confidence: {confidence:.2f})")
        
        if request_type == "search_interaction":
            # Step 2: Task breakdown for complex search operations
            return await self._handle_search_with_task_breakdown(user_input, session_state)
        
        elif request_type == "general_query":
            # Step 3: Handle general queries with LLM
            return await self._handle_general_query(user_input, session_state)
        
        else:
            return Content(data={
                "success": False,
                "error": f"Unknown routed request type: {request_type}"
            })
    
    async def _route_request(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to route the request."""
        try:
            from .prompts import RootAgentPrompts
            
            routing_prompt = RootAgentPrompts.get_routing_prompt(user_input, session_state)
            
            # Call LLM for routing decision
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=routing_prompt,
                task="routing"
            )
            
            if llm_result["success"]:
                routing_data = llm_result["parsed_response"]
                return {
                    "success": True,
                    "request_type": routing_data.get("request_type", "general_query"),
                    "confidence": routing_data.get("confidence", 0.5),
                    "reasoning": routing_data.get("reasoning", "")
                }
            else:
                # Fallback to simple keyword detection
                return self._fallback_routing(user_input)
                
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            return self._fallback_routing(user_input)
    
    def _fallback_routing(self, user_input: str) -> Dict[str, Any]:
        """Fallback routing using keyword detection."""
        search_keywords = ["search", "find", "add", "remove", "filter", "set", "modify", "candidates"]
        general_keywords = ["hi", "hello", "analyze", "explain", "what", "how", "help"]
        
        input_lower = user_input.lower()
        
        if any(keyword in input_lower for keyword in search_keywords):
            return {"success": True, "request_type": "search_interaction", "confidence": 0.7}
        elif any(keyword in input_lower for keyword in general_keywords):
            return {"success": True, "request_type": "general_query", "confidence": 0.7}
        else:
            return {"success": True, "request_type": "general_query", "confidence": 0.5}
    
    async def _handle_search_with_task_breakdown(self, user_input: str, session_state: Dict[str, Any]) -> Content:
        """NEW: Handle search requests with LLM task breakdown."""
        try:
            from .prompts import RootAgentPrompts
            
            # Step 1: Get task breakdown from LLM
            task_prompt = RootAgentPrompts.get_task_breakdown_prompt(user_input, session_state)
            
            print(f"🧠 TASK BREAKDOWN: Analyzing '{user_input}'")
            
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=task_prompt,
                task="task_breakdown"
            )
            
            if llm_result["success"]:
                task_plan = llm_result["parsed_response"]
                print(f"📋 TASK PLAN: {task_plan.get('final_goal', 'Unknown goal')}")
                
                # Step 2: Execute the task plan
                return await self._execute_task_plan(task_plan, user_input, session_state)
            else:
                # Fallback to original search interaction
                print("⚠️ Task breakdown failed, using fallback")
                return await self._fallback_to_search_interaction(user_input, session_state)
                
        except Exception as e:
            logger.error(f"Task breakdown failed: {e}")
            return await self._fallback_to_search_interaction(user_input, session_state)
    
    async def _execute_task_plan(self, task_plan: Dict[str, Any], user_input: str, session_state: Dict[str, Any]) -> Content:
        """Execute the LLM-generated task plan."""
        try:
            tasks = task_plan.get("tasks", [])
            final_goal = task_plan.get("final_goal", "Process user request")
            requires_search = task_plan.get("requires_search", False)
            
            print(f"🚀 EXECUTING {len(tasks)} tasks for: {final_goal}")
            
            all_modifications = []
            final_message = ""
            
            for task in tasks:
                step = task.get("step", 0)
                action = task.get("action", "")
                description = task.get("description", "")
                parameters = task.get("parameters", {})
                
                print(f"📍 Step {step}: {description}")
                
                if action == "filter_modification":
                    # Execute filter modification through search interaction agent
                    mod_result = await self._execute_filter_modification(parameters, session_state)
                    if mod_result["success"]:
                        all_modifications.extend(mod_result.get("modifications", []))
                
                elif action == "location_analysis":
                    # Execute location analysis
                    loc_result = await self._execute_location_analysis(parameters, session_state)
                    if loc_result["success"]:
                        # Add discovered locations to next filter step
                        for next_task in tasks:
                            if next_task.get("action") == "filter_modification" and "locations" in next_task.get("parameters", {}):
                                next_task["parameters"]["locations"] = loc_result.get("similar_locations", [])
                
                elif action == "search_execution":
                    # Execute search with current filters
                    search_result = await self._execute_search(session_state)
                    if search_result["success"]:
                        session_state.update({
                            'candidates': search_result["candidates"],
                            'total_results': search_result["total_count"],
                            'search_applied': True,
                            'page': 0
                        })
                        final_message = search_result.get("message", "Search completed")
            
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
            logger.error(f"Task plan execution failed: {e}")
            return Content(data={
                "success": False,
                "error": f"Task execution failed: {str(e)}",
                "fallback_message": "Falling back to simple processing"
            })
    
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
    
    async def _fallback_to_search_interaction(self, user_input: str, session_state: Dict[str, Any]) -> Content:
        """Fallback to original search interaction agent."""
        content = Content(data={
            "request_type": "search_interaction",
            "user_input": user_input,
            "session_state": session_state
        })
        return await self._handle_search_interaction(content)
    
    async def _handle_general_query(self, user_input: str, session_state: Dict[str, Any]) -> Content:
        """NEW: Handle general queries using LLM."""
        try:
            from .prompts import RootAgentPrompts
            
            general_prompt = RootAgentPrompts.get_general_query_prompt(user_input, session_state)
            
            print(f"💬 GENERAL QUERY: Processing '{user_input}'")
            
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=general_prompt,
                task="general_conversation"
            )
            
            if llm_result["success"]:
                response_text = llm_result.get("response_text", "I'm here to help!")
                
                return Content(data={
                    "success": True,
                    "message": response_text,
                    "type": "general_query",
                    "trigger_search": False,
                    "session_state": session_state,
                    "llm_response": True
                })
            else:
                # Simple fallback responses
                fallback_responses = {
                    "hi": "Hello! I'm your AI assistant for candidate search. How can I help you today?",
                    "hello": "Hi there! I can help you search for candidates and modify filters. What would you like to do?",
                    "help": "I can help you search for candidates, analyze results, and modify search filters. Try asking me to 'search with python' or 'add java skill'.",
                    "analyze": f"Looking at your current search results, you have {len(session_state.get('candidates', []))} candidates. Would you like me to help refine your search?",
                }
                
                fallback_message = fallback_responses.get(user_input.lower(), 
                    "I'm here to help with candidate search! You can ask me to search for candidates, modify filters, or analyze results.")
                
                return Content(data={
                    "success": True,
                    "message": fallback_message,
                    "type": "general_query",
                    "trigger_search": False,
                    "session_state": session_state,
                    "fallback_response": True
                })
                
        except Exception as e:
            logger.error(f"General query processing failed: {e}")
            return Content(data={
                "success": False,
                "error": "Failed to process general query",
                "message": "I encountered an error. Please try rephrasing your question."
            })
    
    # Keep original methods for backward compatibility
    async def _handle_search_interaction(self, content: Content) -> Content:
        """Handle search interaction requests through sub-agent (ORIGINAL)."""
        if "search_interaction" not in self.sub_agents:
            return Content(data={
                "success": False,
                "error": "Search interaction sub-agent not available"
            })
        
        result = await self.sub_agents["search_interaction"].execute(content)
        
        if result.data:
            result.data["root_agent"] = {
                "name": self.config.name,
                "version": self.config.version,
                "delegated_to": "search_interaction"
            }
        
        return result
    
    async def _handle_candidate_search(self, content: Content) -> Content:
        """Handle candidate search requests (ORIGINAL)."""
        search_filters = content.data.get("search_filters", {})
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
        """Handle health check requests (ORIGINAL)."""
        from .utils.db_manager import db_manager
        db_status = await db_manager.test_connection()
        
        sub_agent_status = {}
        for name, agent in self.sub_agents.items():
            sub_agent_status[name] = {
                "available": True,
                "name": getattr(agent, 'name', name)
            }
        
        health_data = {
            "success": True,
            "status": "healthy",
            "root_agent": {
                "name": self.config.name,
                "version": self.config.version,
                "config_valid": True,
                "enhanced_features": ["llm_routing", "task_breakdown", "general_queries"]
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