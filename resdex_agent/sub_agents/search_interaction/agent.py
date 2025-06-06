# Replace resdx_agent/sub_agents/search_interaction/agent.py with this FIXED version

"""
FIXED Search Interaction Agent - Handles ALL complex search logic.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SearchInteractionAgent:
    """
    FIXED Search Interaction Agent - The workhorse that handles:
    
    RESPONSIBILITIES:
    1. Natural language intent extraction
    2. Complex task breakdown and orchestration  
    3. Filter modifications (skills, experience, salary, location)
    4. Location analysis and intelligence
    5. Multi-step task execution
    6. Search trigger decisions
    7. Session state management
    """

    def __init__(self, config=None):
        from .config import SearchInteractionConfig
        self._config = config or SearchInteractionConfig()
        
        self.name = self._config.name
        self.description = self._config.description
        
        # Initialize core tools that definitely exist
        from .tools import IntentProcessor
        from ...tools.llm_tools import LLMTool
        from ...tools.validation_tools import ValidationTool
        from ...tools.filter_tools import FilterTool
        from ...tools.search_tools import SearchTool
        
        self.tools = {
            # Core tools (these definitely work)
            "llm_tool": LLMTool("search_llm_tool"),
            "validation_tool": ValidationTool("validation_tool"),
            "intent_processor": IntentProcessor("intent_processor"),
            "filter_tool": FilterTool("filter_tool"),
            "search_tool": SearchTool("search_tool")
        }
        
        # Try to add location tool if available
        try:
            from ...tools.location_tools import LocationAnalysisTool
            self.tools["location_tool"] = LocationAnalysisTool("location_tool")
            print("✅ Location tool loaded successfully")
        except ImportError as e:
            print(f"⚠️ Location tool not available: {e}")
            self.tools["location_tool"] = None
        
        from .prompts import IntentExtractionPrompt
        self._prompt_template = IntentExtractionPrompt()

        print(f"🔍 {self.name} initialized with tools: {list(self.tools.keys())}")
        logger.info(f"Enhanced {self._config.name} v{self._config.version}")

    @property
    def config(self):
        return self._config

    @property 
    def prompt_template(self):
        return self._prompt_template

    async def execute(self, content) -> object:
        """FIXED execute - handles both simple and complex search operations."""
        try:
            request_type = content.data.get("request_type", "search_interaction")
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            # Ensure session_state is a dict
            if not isinstance(session_state, dict):
                logger.error(f"Session state is not a dict: {type(session_state)}")
                session_state = {}
            
            logger.info(f"SearchInteractionAgent processing: '{user_input}'")
            print(f"🚀 SEARCH AGENT: Processing '{user_input}'")
            print(f"🔧 Request type: {request_type}")
            
            if request_type == "enhanced_search_interaction":
                # NEW: Handle complex task breakdown and orchestration
                return await self._handle_enhanced_interaction(user_input, session_state, content.data)
            else:
                # ORIGINAL: Handle simple intent extraction  
                return await self._handle_simple_interaction(user_input, session_state)
                
        except Exception as e:
            logger.error(f"Search interaction failed: {e}")
            print(f"❌ Search interaction error: {e}")
            import traceback
            traceback.print_exc()
            
            # FIXED: Create Content properly
            return self._create_content({
                "success": False,
                "error": "An unexpected error occurred while processing your request",
                "details": str(e)
            })
    
    def _create_content(self, data: Dict[str, Any]):
        """Helper to create Content objects."""
        try:
            from ...agent import Content
            return Content(data=data)
        except ImportError:
            # Fallback - create simple object
            class SimpleContent:
                def __init__(self, data):
                    self.data = data
            return SimpleContent(data)
    
    async def _handle_enhanced_interaction(self, user_input: str, session_state: Dict[str, Any], request_data: Dict[str, Any]) -> object:
        """NEW: Handle complex interactions with task breakdown."""
        
        print(f"🧠 ENHANCED MODE: Analyzing complex request")
        
        # Step 1: Determine if this needs task breakdown
        complexity_analysis = await self._analyze_request_complexity(user_input, session_state)
        
        if complexity_analysis["is_complex"]:
            print(f"🎯 COMPLEX REQUEST: Using task breakdown approach")
            return await self._handle_complex_task_breakdown(user_input, session_state, complexity_analysis)
        else:
            print(f"📝 SIMPLE REQUEST: Using intent extraction approach")
            return await self._handle_simple_interaction(user_input, session_state)
    
    async def _analyze_request_complexity(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if request needs complex task breakdown."""
        
        # Complex indicators
        complex_patterns = [
            "similar location", "nearby", "tech hubs", "metro area",
            "find candidates from", "filter by", "within", "radius",
            "like", "comparable to", "industry hubs"
        ]
        
        # Multi-step indicators  
        multi_step_indicators = [
            " and ", " then ", " after ", "first", "next", "also"
        ]
        
        input_lower = user_input.lower()
        
        is_complex = any(pattern in input_lower for pattern in complex_patterns)
        is_multi_step = any(indicator in input_lower for indicator in multi_step_indicators)
        
        complexity_score = 0
        if is_complex: complexity_score += 0.6
        if is_multi_step: complexity_score += 0.4
        if len(user_input.split()) > 8: complexity_score += 0.2
        
        return {
            "is_complex": complexity_score > 0.5,
            "complexity_score": complexity_score,
            "requires_location_analysis": is_complex and any(loc in input_lower for loc in ["location", "nearby", "similar", "tech hub"]),
            "requires_multi_step": is_multi_step,
            "analysis_factors": {
                "complex_patterns": is_complex,
                "multi_step": is_multi_step,
                "word_count": len(user_input.split())
            }
        }
    
    async def _handle_complex_task_breakdown(self, user_input: str, session_state: Dict[str, Any], complexity_analysis: Dict[str, Any]) -> object:
        """Handle complex requests with intelligent task breakdown."""
        
        try:
            # Step 1: Get task breakdown from LLM
            task_breakdown = await self._get_intelligent_task_breakdown(user_input, session_state)
            
            if not task_breakdown["success"]:
                # Fallback to simple processing
                return await self._handle_simple_interaction(user_input, session_state)
            
            # Step 2: Execute the task plan
            execution_result = await self._execute_intelligent_task_plan(
                task_breakdown["task_plan"], 
                user_input, 
                session_state
            )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Complex task breakdown failed: {e}")
            # Fallback to simple processing
            return await self._handle_simple_interaction(user_input, session_state)
    
    async def _get_intelligent_task_breakdown(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get intelligent task breakdown using LLM."""
        
        # FIXED: Check if prompts module exists
        try:
            from ...prompts import RootAgentPrompts
            task_prompt = RootAgentPrompts.get_task_breakdown_prompt(user_input, session_state)
        except ImportError:
            print("⚠️ RootAgentPrompts not available, using simple breakdown")
            return {"success": False, "error": "Task breakdown prompts not available"}
        
        print(f"🧠 TASK BREAKDOWN: Analyzing '{user_input}'")
        
        llm_result = await self.tools["llm_tool"]._call_llm_direct(
            prompt=task_prompt,
            task="task_breakdown"
        )
        
        if llm_result["success"]:
            task_plan = llm_result["parsed_response"]
            print(f"📋 TASK PLAN: {task_plan.get('final_goal', 'Unknown goal')}")
            print(f"📝 TASKS: {len(task_plan.get('tasks', []))} steps")
            
            return {
                "success": True,
                "task_plan": task_plan
            }
        else:
            return {"success": False, "error": "Task breakdown failed"}
    
    async def _execute_intelligent_task_plan(self, task_plan: Dict[str, Any], user_input: str, session_state: Dict[str, Any]) -> object:
        """Execute the intelligent task plan step by step."""
        
        try:
            tasks = task_plan.get("tasks", [])
            final_goal = task_plan.get("final_goal", "Process user request")
            requires_search = task_plan.get("requires_search", False)
            
            print(f"🚀 EXECUTING {len(tasks)} tasks for: {final_goal}")
            
            all_modifications = []
            execution_messages = []
            
            for task in tasks:
                step = task.get("step", 0)
                action = task.get("action", "")
                description = task.get("description", "")
                parameters = task.get("parameters", {})
                
                print(f"📍 Step {step}: {description}")
                
                if action == "filter_modification":
                    result = await self._execute_filter_modification_step(parameters, session_state)
                    
                elif action == "location_analysis":
                    result = await self._execute_location_analysis_step(parameters, session_state, tasks)
                    
                elif action == "search_execution":
                    result = await self._execute_search_step(session_state)
                    if result["success"]:
                        # Update session state with search results
                        session_state.update({
                            'candidates': result["candidates"],
                            'total_results': result["total_count"],
                            'search_applied': True,
                            'page': 0
                        })
                
                else:
                    print(f"⚠️ Unknown action: {action}")
                    continue
                
                if result["success"]:
                    all_modifications.extend(result.get("modifications", []))
                    if result.get("message"):
                        execution_messages.append(result["message"])
                else:
                    # If any step fails, return error
                    return self._create_content({
                        "success": False,
                        "error": f"Step {step} failed: {result.get('error', 'Unknown error')}",
                        "completed_steps": step - 1
                    })
            
            # Prepare final response
            final_message = " | ".join(execution_messages) if execution_messages else f"Completed {len(tasks)} tasks: {final_goal}"
            
            return self._create_content({
                "success": True,
                "message": final_message,
                "modifications": all_modifications,
                "trigger_search": False,  # Search already executed if needed
                "session_state": session_state,
                "task_breakdown": {
                    "tasks_executed": len(tasks),
                    "final_goal": final_goal,
                    "intelligent_execution": True
                },
                "type": "enhanced_search_interaction"
            })
            
        except Exception as e:
            logger.error(f"Task plan execution failed: {e}")
            return self._create_content({
                "success": False,
                "error": f"Task execution failed: {str(e)}"
            })
    
    async def _execute_filter_modification_step(self, parameters: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute filter modification step."""
        
        try:
            if "skill" in parameters:
                return await self.tools["filter_tool"]("add_skill", session_state, **parameters)
            elif "experience_range" in parameters:
                return await self.tools["filter_tool"]("modify_experience", session_state, **parameters)
            elif "salary_range" in parameters:
                return await self.tools["filter_tool"]("modify_salary", session_state, **parameters)
            elif "locations" in parameters:
                # Add multiple locations
                all_mods = []
                for location in parameters["locations"]:
                    result = await self.tools["filter_tool"]("add_location", session_state, location=location)
                    if result["success"]:
                        all_mods.extend(result["modifications"])
                return {"success": True, "modifications": all_mods, "message": f"Added {len(parameters['locations'])} locations"}
            else:
                return {"success": False, "error": "Unknown filter modification parameters"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_location_analysis_step(self, parameters: Dict[str, Any], session_state: Dict[str, Any], all_tasks: List[Dict]) -> Dict[str, Any]:
        """Execute location analysis step."""
        
        try:
            # Check if location tool is available
            if self.tools["location_tool"] is None:
                # Fallback to simple location mapping
                return await self._simple_location_fallback(parameters)
            
            result = await self.tools["location_tool"](**parameters)
            
            if result["success"]:
                # Update subsequent filter_modification tasks with discovered locations
                discovered_locations = result.get("similar_locations", [])
                
                # Find next filter_modification task and update its locations
                for task in all_tasks:
                    if (task.get("action") == "filter_modification" and 
                        "locations" in task.get("parameters", {}) and 
                        task["parameters"]["locations"] == ["to_be_determined"]):
                        task["parameters"]["locations"] = discovered_locations
                        break
                
                return {
                    "success": True,
                    "modifications": [{"type": "location_analysis", "locations_found": len(discovered_locations)}],
                    "message": result.get("message", f"Found {len(discovered_locations)} locations")
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _simple_location_fallback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simple fallback for location analysis."""
        base_location = parameters.get("base_location", "Mumbai")
        
        # Simple hardcoded mapping
        location_mapping = {
            "Mumbai": ["Pune", "Thane", "Navi Mumbai"],
            "Bangalore": ["Mysore", "Hubli", "Mangalore"],
            "Delhi": ["Gurgaon", "Noida", "Faridabad"],
            "Chennai": ["Coimbatore", "Madurai", "Trichy"],
            "Hyderabad": ["Vijayawada", "Visakhapatnam", "Warangal"],
            "Pune": ["Mumbai", "Nashik", "Aurangabad"]
        }
        
        similar_locations = location_mapping.get(base_location, [base_location])
        
        return {
            "success": True,
            "similar_locations": similar_locations,
            "message": f"Found {len(similar_locations)} similar locations (simple mapping)"
        }
    
    async def _execute_search_step(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search step."""
        
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
    
    async def _handle_simple_interaction(self, user_input: str, session_state: Dict[str, Any]) -> object:
        """ORIGINAL: Handle simple interactions with intent extraction."""
        
        print(f"📝 SIMPLE INTERACTION: Processing '{user_input}'")
        
        # Validate user input
        validation_result = await self.tools["validation_tool"](
            validation_type="user_input",
            data=user_input
        )
        
        if not validation_result["success"]:
            return self._create_content({
                "success": False,
                "error": validation_result["error"],
                "suggestions": validation_result.get("suggestions", [])
            })
        
        # Extract current filters safely with defaults
        current_filters = {
            "keywords": session_state.get('keywords', []),
            "min_exp": session_state.get('min_exp', 0),
            "max_exp": session_state.get('max_exp', 10),
            "min_salary": session_state.get('min_salary', 0),
            "max_salary": session_state.get('max_salary', 15),
            "current_cities": session_state.get('current_cities', []),
            "preferred_cities": session_state.get('preferred_cities', [])
        }
        
        print(f"🔍 Current filters extracted: {current_filters}")
        
        # Extract intent using LLM
        llm_result = await self.tools["llm_tool"](
            user_input=user_input,
            current_filters=current_filters,
            task="extract_intent"
        )
        
        if not llm_result["success"]:
            return self._create_content({
                "success": False,
                "error": "Failed to process your request",
                "details": llm_result["error"]
            })
        
        intent_data = llm_result["intent_data"]
        print(f"🔍 Intent data: {intent_data}")
        
        # Process the extracted intent(s)
        processing_result = await self.tools["intent_processor"](
            intent_data=intent_data,
            session_state=session_state
        )
        
        # Prepare response
        response_data = {
            "success": processing_result["success"],
            "message": processing_result.get("message", ""),
            "modifications": processing_result.get("modifications", []),
            "trigger_search": processing_result.get("trigger_search", False),
            "session_state": session_state,
            "intent_data": intent_data,
            "type": "simple_search_interaction",
            "processing_details": {
                "agent": self.config.name,
                "version": self.config.version,
                "input_validation": validation_result.get("input_analysis", {}),
                "modification_count": len(processing_result.get("modifications", []))
            }
        }
        
        if not processing_result["success"]:
            response_data["error"] = processing_result.get("error", "Processing failed")
        
        logger.info(f"Simple search interaction completed: {len(processing_result.get('modifications', []))} modifications")
        
        return self._create_content(response_data)