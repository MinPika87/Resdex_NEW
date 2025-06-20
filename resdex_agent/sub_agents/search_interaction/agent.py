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
        """Enhanced execute that handles multi-intent queries intelligently."""
        try:
            request_type = content.data.get("request_type", "search_interaction")
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            if not isinstance(session_state, dict):
                logger.error(f"Session state is not a dict: {type(session_state)}")
                session_state = {}
            
            logger.info(f"SearchInteractionAgent processing: '{user_input}'")
            print(f"🚀 SEARCH AGENT: Processing '{user_input}'")
            print(f"🔧 Request type: {request_type}")
            
            # ENHANCED: Use LLM to determine if this is a multi-intent query
            multi_intent_analysis = await self._analyze_multi_intent_query(user_input)
            print(f"🧠 MULTI-INTENT ANALYSIS: {multi_intent_analysis}")
            
            if multi_intent_analysis["is_multi_intent"]:
                print(f"🎯 MULTI-INTENT QUERY: Using coordinated processing")
                return await self._handle_multi_intent_query(user_input, session_state, multi_intent_analysis)
            
            # Check for location expansion (single intent)
            location_info = self._requires_location_expansion(user_input)
            if location_info["requires_expansion"]:
                print(f"🗺️ LOCATION EXPANSION DETECTED: {location_info}")
                return await self._handle_location_expansion_request(user_input, session_state)
            
            # Default to simple interaction
            print(f"📝 SIMPLE REQUEST: Using intent extraction approach")
            return await self._handle_simple_interaction(user_input, session_state)
                    
        except Exception as e:
            logger.error(f"Search interaction failed: {e}")
            print(f"❌ Search interaction error: {e}")
            return self._create_content({
                "success": False,
                "error": "An unexpected error occurred while processing your request",
                "details": str(e)
            })
    # =============================================================================
# SCALABLE MULTI-INTENT ORCHESTRATOR (LLM-Driven)
# =============================================================================

# File: resdx_agent/sub_agents/search_interaction/agent.py
# Replace the _analyze_multi_intent_query method:

    async def _analyze_multi_intent_query(self, user_input: str) -> Dict[str, Any]:
        """Use LLM to intelligently detect and break down complex multi-intent queries."""
        
        prompt = f"""You are an intelligent query analyzer. Break down this user query into distinct, actionable intents.

    User query: "{user_input}"

    <think>
    Analyze this query step by step:

    1. INTENT IDENTIFICATION:
    - Look for distinct actions: add, remove, set, increase, decrease, search, find
    - Identify what each action targets: skills, experience, salary, locations, search execution
    - Determine the order and dependencies between actions

    2. INTENT CATEGORIZATION:
    Each intent should be one of:
    - skill_addition: Adding skills/keywords
    - skill_removal: Removing skills/keywords  
    - skill_modification: Making skills mandatory/optional
    - experience_modification: Setting/changing experience ranges
    - salary_modification: Setting/changing salary ranges
    - location_addition: Adding specific locations
    - location_expansion: Finding and adding nearby/similar locations
    - search_execution: Triggering a candidate search

    3. DEPENDENCY ANALYSIS:
    - Do any intents depend on others completing first?
    - Should location expansion happen before or after other modifications?
    - When should search be triggered (usually last)?

    4. COMPLEXITY ASSESSMENT:
    - How many distinct intents are there?
    - Do any require special tool coordination?
    - What's the optimal execution sequence?
    </think>

    Break down the query into individual intents with execution details:

    {{
        "is_multi_intent": true/false,
        "total_intents": number,
        "intents": [
            {{
                "id": 1,
                "type": "skill_addition|skill_removal|experience_modification|salary_modification|location_addition|location_expansion|search_execution",
                "action": "add_skill|remove_skill|modify_experience|modify_salary|add_location|location_expansion|search",
                "details": {{
                    "value": "extracted_value",
                    "operation": "set|set_range|increase|decrease",
                    "mandatory": true/false,
                    "base_location": "city_name",
                    "analysis_type": "nearby|similar|tech_hubs"
                }},
                "execution_order": 1,
                "depends_on": [],
                "description": "human readable description"
            }}
        ],
        "execution_plan": {{
            "sequential": true/false,
            "total_steps": number,
            "requires_coordination": true/false,
            "complexity_score": 0.0-1.0
        }},
        "confidence": 0.0-1.0,
        "reasoning": "detailed explanation of the breakdown"
    }}

    Examples:

    Query: "add python and java"
    → 2 intents: skill_addition(python), skill_addition(java)

    Query: "add python, set experience to 5-10 years, and search"  
    → 3 intents: skill_addition(python), experience_modification(5-10), search_execution

    Query: "add nearby locations to bangalore and increase salary by 5"
    → 2 intents: location_expansion(bangalore, nearby), salary_modification(increase, 5)

    Respond with JSON only."""

        try:
            llm_result = await self.tools["llm_tool"]._call_llm_direct(prompt, task="multi_intent_analysis")
            
            if llm_result["success"] and "parsed_response" in llm_result:
                analysis = llm_result["parsed_response"]
                print(f"🧠 LLM INTENT BREAKDOWN: {analysis.get('total_intents', 0)} intents detected")
                return analysis
            else:
                # Enhanced fallback for complex queries
                return self._fallback_multi_intent_analysis(user_input)
                
        except Exception as e:
            print(f"❌ Multi-intent analysis failed: {e}")
            return self._fallback_multi_intent_analysis(user_input)

    def _fallback_multi_intent_analysis(self, user_input: str) -> Dict[str, Any]:
        """Fallback analysis when LLM fails."""
        input_lower = user_input.lower()
        
        # Count potential intents
        intent_indicators = [
            ("add", "skill_addition"),
            ("remove", "skill_removal"), 
            ("set", "modification"),
            ("increase", "salary_modification"),
            ("decrease", "salary_modification"),
            ("nearby", "location_expansion"),
            ("search", "search_execution"),
            ("find", "search_execution")
        ]
        
        detected_intents = []
        for indicator, intent_type in intent_indicators:
            if indicator in input_lower:
                detected_intents.append(intent_type)
        
        return {
            "is_multi_intent": len(detected_intents) > 1,
            "total_intents": len(detected_intents),
            "intents": [],  # Simplified fallback
            "execution_plan": {"sequential": True, "total_steps": len(detected_intents)},
            "confidence": 0.6,
            "reasoning": "Fallback analysis - LLM parsing failed"
        }

    # =============================================================================
    # ENHANCED MULTI-INTENT HANDLER (Scalable)
    # =============================================================================

    async def _handle_multi_intent_query(self, user_input: str, session_state: Dict[str, Any], analysis: Dict[str, Any]) -> object:
        """Handle queries with multiple coordinated intents using intelligent orchestration."""
        try:
            intents = analysis.get("intents", [])
            total_intents = analysis.get("total_intents", 0)
            
            print(f"🎯 ORCHESTRATING {total_intents} INTENTS:")
            for intent in intents:
                print(f"  - Intent {intent.get('id', '?')}: {intent.get('type', 'unknown')} - {intent.get('description', 'no description')}")
            
            all_modifications = []
            execution_log = []
            
            # Sort intents by execution order
            sorted_intents = sorted(intents, key=lambda x: x.get('execution_order', 999))
            
            # Execute each intent in order
            for i, intent in enumerate(sorted_intents, 1):
                intent_type = intent.get("type", "unknown")
                intent_details = intent.get("details", {})
                description = intent.get("description", f"Intent {i}")
                
                print(f"\n🔧 STEP {i}/{len(sorted_intents)}: {description}")
                
                try:
                    result = await self._execute_single_intent(intent_type, intent_details, session_state, user_input)
                    
                    if result["success"]:
                        modifications = result.get("modifications", [])
                        all_modifications.extend(modifications)
                        execution_log.append(f"✅ {description}: {len(modifications)} modifications")
                        print(f"✅ Intent {i} completed: {len(modifications)} modifications")
                    else:
                        execution_log.append(f"❌ {description}: {result.get('error', 'Failed')}")
                        print(f"❌ Intent {i} failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    execution_log.append(f"❌ {description}: Exception {str(e)}")
                    print(f"❌ Intent {i} exception: {e}")
                    continue
            
            # Generate comprehensive response
            if all_modifications:
                action_descriptions = self._format_action_descriptions(all_modifications)
                
                # Check if search should be triggered
                has_search_intent = any(intent.get("type") == "search_execution" for intent in intents)
                trigger_search = has_search_intent or any(mod.get("type") == "search_triggered" for mod in all_modifications)
                
                success_message = f"Executed {len(sorted_intents)} intents: {'; '.join(action_descriptions)}"
                
                return self._create_content({
                    "success": True,
                    "message": success_message,
                    "modifications": all_modifications,
                    "trigger_search": trigger_search,
                    "session_state": session_state,
                    "type": "multi_intent_orchestrated",
                    "execution_summary": {
                        "total_intents": total_intents,
                        "successful_intents": len([log for log in execution_log if "✅" in log]),
                        "failed_intents": len([log for log in execution_log if "❌" in log]),
                        "execution_log": execution_log
                    }
                })
            else:
                return self._create_content({
                    "success": False,
                    "error": "No intents could be executed successfully",
                    "execution_log": execution_log
                })
                
        except Exception as e:
            print(f"❌ Multi-intent orchestration failed: {e}")
            return await self._handle_simple_interaction(user_input, session_state)

    # =============================================================================
    # SINGLE INTENT EXECUTOR (Router to Specific Handlers)
    # =============================================================================

    async def _execute_single_intent(self, intent_type: str, intent_details: Dict[str, Any], session_state: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Execute a single intent based on its type."""
        
        try:
            if intent_type == "skill_addition":
                return await self._execute_skill_addition_intent(intent_details, session_state)
                
            elif intent_type == "skill_removal":
                return await self._execute_skill_removal_intent(intent_details, session_state)
                
            elif intent_type == "experience_modification":
                return await self._execute_experience_modification_intent(intent_details, session_state)
                
            elif intent_type == "salary_modification":
                return await self._execute_salary_modification_intent(intent_details, session_state)
                
            elif intent_type == "location_addition":
                return await self._execute_location_addition_intent(intent_details, session_state)
                
            elif intent_type == "location_expansion":
                return await self._execute_location_expansion_intent(intent_details, session_state)
                
            elif intent_type == "search_execution":
                return await self._execute_search_intent(intent_details, session_state)
                
            else:
                return {"success": False, "error": f"Unknown intent type: {intent_type}", "modifications": []}
                
        except Exception as e:
            return {"success": False, "error": f"Intent execution failed: {str(e)}", "modifications": []}

    # =============================================================================
    # SPECIFIC INTENT EXECUTORS
    # =============================================================================

    async def _execute_skill_addition_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill addition intent."""
        skill = details.get("value", "")
        mandatory = details.get("mandatory", False)
        
        if not skill:
            return {"success": False, "error": "No skill specified", "modifications": []}
        
        return await self.tools["filter_tool"]("add_skill", session_state, skill=skill, mandatory=mandatory)

    async def _execute_skill_removal_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill removal intent."""
        skill = details.get("value", "")
        
        if not skill:
            return {"success": False, "error": "No skill specified for removal", "modifications": []}
        
        return await self.tools["filter_tool"]("remove_skill", session_state, skill=skill)

    async def _execute_experience_modification_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute experience modification intent."""
        operation = details.get("operation", "set")
        value = details.get("value", "")
        
        if not value:
            return {"success": False, "error": "No experience value specified", "modifications": []}
        
        return await self.tools["filter_tool"]("modify_experience", session_state, operation=operation, value=value)

    async def _execute_salary_modification_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute salary modification intent."""
        operation = details.get("operation", "set")
        value = details.get("value", "")
        
        if not value:
            return {"success": False, "error": "No salary value specified", "modifications": []}
        
        # Handle relative increases/decreases
        if operation in ["increase", "decrease"]:
            current_max = session_state.get("max_salary", 15)
            current_min = session_state.get("min_salary", 0)
            
            try:
                change_amount = float(value)
                if operation == "increase":
                    new_max = current_max + change_amount
                    new_range = f"{current_min}-{new_max}"
                else:  # decrease
                    new_max = max(current_min, current_max - change_amount)
                    new_range = f"{current_min}-{new_max}"
                
                return await self.tools["filter_tool"]("modify_salary", session_state, operation="set_range", value=new_range)
            except ValueError:
                return {"success": False, "error": f"Invalid salary change amount: {value}", "modifications": []}
        
        return await self.tools["filter_tool"]("modify_salary", session_state, operation=operation, value=value)

    async def _execute_location_addition_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute location addition intent."""
        location = details.get("value", "")
        mandatory = details.get("mandatory", False)
        
        if not location:
            return {"success": False, "error": "No location specified", "modifications": []}
        
        return await self.tools["filter_tool"]("add_location", session_state, location=location, mandatory=mandatory)

    async def _execute_location_expansion_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute location expansion intent using location tool."""
        base_location = details.get("base_location", "")
        analysis_type = details.get("analysis_type", "nearby")
        
        if not base_location:
            return {"success": False, "error": "No base location specified for expansion", "modifications": []}
        
        try:
            # Use location tool to find related locations
            if self.tools["location_tool"]:
                location_result = await self.tools["location_tool"](
                    base_location=base_location,
                    analysis_type=analysis_type,
                    criteria="job market and tech industry"
                )
                
                if location_result["success"]:
                    # Get discovered locations
                    if analysis_type == "nearby":
                        discovered_locations = location_result.get("nearby_locations", [])
                    else:
                        discovered_locations = location_result.get("similar_locations", [])
                    
                    # Add base location and discovered locations
                    all_modifications = []
                    
                    # Add base location if not already present
                    if base_location not in session_state.get('current_cities', []):
                        base_result = await self.tools["filter_tool"]("add_location", session_state, location=base_location, mandatory=False)
                        if base_result["success"]:
                            all_modifications.extend(base_result["modifications"])
                    
                    # Add discovered locations (limit to 5)
                    for location in discovered_locations[:5]:
                        if location != base_location and location not in session_state.get('current_cities', []):
                            loc_result = await self.tools["filter_tool"]("add_location", session_state, location=location, mandatory=False)
                            if loc_result["success"]:
                                all_modifications.extend(loc_result["modifications"])
                    
                    return {"success": True, "modifications": all_modifications}
                else:
                    return {"success": False, "error": "Location tool failed", "modifications": []}
            else:
                return {"success": False, "error": "Location tool not available", "modifications": []}
                
        except Exception as e:
            return {"success": False, "error": f"Location expansion failed: {str(e)}", "modifications": []}

    async def _execute_search_intent(self, details: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search intent."""
        return {
            "success": True,
            "modifications": [{"type": "search_triggered", "value": "search_executed"}]
        }

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def _format_action_descriptions(self, modifications: List[Dict[str, Any]]) -> List[str]:
        """Format modifications into human-readable action descriptions."""
        action_descriptions = []
        
        for mod in modifications:
            mod_type = mod.get("type", "")
            value = mod.get("value", "")
            mandatory = mod.get("mandatory", False)
            
            if mod_type == "skill_added":
                action_descriptions.append(f"Skill added: {value}{'*' if mandatory else ''}")
            elif mod_type == "skill_removed":
                action_descriptions.append(f"Skill removed: {value}")
            elif mod_type == "experience_modified":
                action_descriptions.append(f"Experience set: {value} years")
            elif mod_type == "salary_modified":
                action_descriptions.append(f"Salary range set: {value} LPA")
            elif mod_type == "location_added":
                if mandatory:
                    action_descriptions.append(f"Location added (mandatory): {value}")
                else:
                    action_descriptions.append(f"Location added: {value}")
            elif mod_type == "search_triggered":
                action_descriptions.append("Search executed")
            else:
                action_descriptions.append(f"Action: {mod_type}")
        
        return action_descriptions
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
        
        # ENHANCED Complex indicators
        complex_patterns = [
            "similar location", "nearby", "tech hubs", "metro area",
            "find candidates from", "filter by", "within", "radius",
            "like", "comparable to", "industry hubs",
            "near", "based near", "from nearby", "in nearby", "around", "close to",
            "areas near", "vicinity", "proximity", "adjacent", "neighboring",
            "engineers from", "developers from", "candidates from"
        ]
        
        multi_step_indicators = [
            " and ", " then ", " after ", "first", "next", "also",
            " with ", " who are ", " that are ", " based in ", " from "
        ]
        
        input_lower = user_input.lower()
        
        is_complex = any(pattern in input_lower for pattern in complex_patterns)
        is_multi_step = any(indicator in input_lower for indicator in multi_step_indicators)
        
        has_skill_and_location = (
            any(skill in input_lower for skill in ["python", "java", "react", "node", "django", "postgres", "android", "devops", "spark", "angular"]) and
            any(loc in input_lower for loc in ["hyderabad", "bangalore", "delhi", "mumbai", "chennai", "pune", "noida", "gurgaon", "blr", "hyd", "ncr"])
        )
        
        has_memory_reference = any(mem in input_lower for mem in [
            "same", "previous", "earlier", "last", "before", "keep", "resume", "repeat"
        ])
        complexity_score = 0
        if is_complex: complexity_score += 0.6
        if is_multi_step: complexity_score += 0.4
        if len(user_input.split()) > 8: complexity_score += 0.2
        if has_skill_and_location: complexity_score += 0.3
        if has_memory_reference: complexity_score += 0.3
        
        return {
            "is_complex": complexity_score > 0.5,
            "complexity_score": complexity_score,
            "requires_location_analysis": is_complex and any(loc in input_lower for loc in ["location", "nearby", "similar", "tech hub", "near", "from"]),
            "requires_multi_step": is_multi_step,
            "has_skill_and_location": has_skill_and_location,
            "has_memory_reference": has_memory_reference,
            "analysis_factors": {
                "complex_patterns": is_complex,
                "multi_step": is_multi_step,
                "word_count": len(user_input.split()),
                "skill_location_combo": has_skill_and_location,
                "memory_reference": has_memory_reference
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
    def _requires_location_expansion(self, user_input: str) -> Dict[str, Any]:
        """Detect if user input requires location expansion using location tools."""
        location_expansion_patterns = [
            "nearby locations", "nearby cities", "similar locations", "similar cities",
            "tech hubs", "tech cities", "technology hubs", "IT hubs", "IT cities",
            "metro area", "metropolitan", "surrounding", "around", "close to",
            "big cities", "major cities", "industrial cities", "commercial hubs",
            "near", "based near", "from nearby", "in nearby", "areas near",
            "vicinity of", "proximity to", "adjacent to", "neighboring",
            "in the region of", "in and around", "around the area",
            "or nearby", "and nearby", "nearby areas", "nearby regions"
        ]
        
        base_location_keywords = [
            "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata",
            "Noida", "Gurgaon", "Ahmedabad", "Jaipur", "Kochi", "Indore",
            "BLR", "NCR", "Hyd", "Blr"
        ]
        
        input_lower = user_input.lower()
        has_expansion_pattern = any(pattern in input_lower for pattern in location_expansion_patterns)        
        implicit_nearby_patterns = [
            "engineers from", "developers from", "candidates from", "people from",
            "folks from", "professionals from", "talent from"
        ]
        has_implicit_nearby = any(pattern in input_lower for pattern in implicit_nearby_patterns)
        base_location = None
        for location in base_location_keywords:
            if location.lower() in input_lower:
                base_location = location
                break
        
        if not base_location:
            location_mapping = {
                "hyd": "Hyderabad", "blr": "Bangalore", "del": "Delhi",
                "mum": "Mumbai", "chen": "Chennai", "ban": "Bangalore"
            }
            for abbrev, full_name in location_mapping.items():
                if abbrev in input_lower:
                    base_location = full_name
                    break
        
        analysis_type = "similar"
        if "nearby" in input_lower or "close to" in input_lower or "surrounding" in input_lower:
            analysis_type = "nearby"
        elif "tech hub" in input_lower or "it hub" in input_lower or "technology" in input_lower:
            analysis_type = "industry_hubs"
        elif "metro" in input_lower or "metropolitan" in input_lower:
            analysis_type = "metro_area"
        
        force_expansion = (
            base_location and 
            (has_expansion_pattern or has_implicit_nearby or "from" in input_lower)
        )
        
        return {
            "requires_expansion": has_expansion_pattern or force_expansion,
            "base_location": base_location,
            "analysis_type": analysis_type,
            "patterns_found": [p for p in location_expansion_patterns if p in input_lower],
            "implicit_nearby": has_implicit_nearby
        }
    async def _handle_location_expansion_request(self, user_input: str, session_state: Dict[str, Any]) -> object:
        try:
            location_info = self._requires_location_expansion(user_input)
            
            print(f"🗺️ LOCATION EXPANSION INFO: {location_info}")
            
            if not location_info["requires_expansion"]:
                print("🔄 No expansion required, using simple interaction")
                return await self._handle_simple_interaction(user_input, session_state)
            
            base_location = location_info["base_location"]
            analysis_type = location_info["analysis_type"]
            
            print(f"🗺️ AGENTIC LOCATION EXPANSION: {analysis_type} for {base_location}")
            
            if not base_location:
                current_cities = session_state.get('current_cities', [])
                preferred_cities = session_state.get('preferred_cities', [])
                if current_cities:
                    base_location = current_cities[-1] 
                    print(f"🔍 Using recent city from session: {base_location}")
                elif preferred_cities:
                    base_location = preferred_cities[-1]
                    print(f"🔍 Using preferred city from session: {base_location}")
                else:
                    return self._create_content({
                        "success": False,
                        "error": "Please specify a base location for expansion",
                        "message": "I need a base city to find nearby locations. For example: 'add nearby locations to Mumbai'"
                    })
            
            print(f"🔧 STEP 1: Using LocationTool to find {analysis_type} cities for {base_location}")
            
            if self.tools["location_tool"]:
                location_result = await self.tools["location_tool"](
                    base_location=base_location,
                    analysis_type=analysis_type,
                    criteria="job market and tech industry"
                )
                
                print(f"🔍 LOCATION TOOL RESULT: {location_result}")
                
                if location_result["success"]:
                    discovered_locations = []
                    
                    if analysis_type == "nearby":
                        if "nearby_locations" in location_result:
                            nearby_data = location_result["nearby_locations"]
                            if isinstance(nearby_data, list) and len(nearby_data) > 0:
                                if isinstance(nearby_data[0], dict) and "city" in nearby_data[0]:
                                    discovered_locations = [loc["city"] for loc in nearby_data]
                                else:
                                    discovered_locations = nearby_data
                    
                    elif analysis_type == "similar":
                        discovered_locations = location_result.get("similar_locations", [])
                    elif analysis_type == "industry_hubs":
                        discovered_locations = location_result.get("industry_hubs", [])
                    elif analysis_type == "metro_area":
                        discovered_locations = location_result.get("metro_area_locations", [])
                    
                    print(f"🎯 STEP 1 RESULT: Discovered {len(discovered_locations)} locations: {discovered_locations}")
                    print(f"🔧 STEP 2: Using FilterTool to add {len(discovered_locations)} locations")
                    
                    all_modifications = []
                    if base_location not in session_state.get('current_cities', []):
                        print(f"🔧 STEP 2.1: Adding base location: {base_location}")
                        filter_result = await self.tools["filter_tool"](
                            "add_location", 
                            session_state, 
                            location=base_location,
                            mandatory=False
                        )
                        if filter_result["success"]:
                            all_modifications.extend(filter_result["modifications"])
                            print(f"✅ Added base location: {base_location}")
                        else:
                            print(f"❌ Failed to add base location: {filter_result.get('error')}")
                    
                    max_locations = min(5, len(discovered_locations))  # Limit to 5
                    for i, location in enumerate(discovered_locations[:max_locations], 1): 
                        if location != base_location and location not in session_state.get('current_cities', []):
                            print(f"🔧 STEP 2.{i+1}: Adding nearby location: {location}")
                            
                            filter_result = await self.tools["filter_tool"](
                                "add_location", 
                                session_state, 
                                location=location,
                                mandatory=False
                            )
                            
                            if filter_result["success"]:
                                all_modifications.extend(filter_result["modifications"])
                                print(f"✅ Added location {i}: {location}")
                            else:
                                print(f"❌ Failed to add location {i}: {location} - {filter_result.get('error')}")
                    

                    print(f"🔧 STEP 3: Generating response with {len(all_modifications)} total modifications")
                    
                    if all_modifications:
                        location_names = [mod["value"] for mod in all_modifications]
                        reasoning = location_result.get("reasoning", {})
                        
                        message_parts = [f"Added {len(all_modifications)} locations for {base_location}:"]
                        for name in location_names:
                            message_parts.append(f"• {name}")
                        
                        if reasoning and len(reasoning) > 0:
                            message_parts.append(f"\nWhy these locations:")
                            for loc, reason in list(reasoning.items())[:max_locations]:
                                if loc in location_names:
                                    message_parts.append(f"• {loc}: {reason}")
                        
                        return self._create_content({
                            "success": True,
                            "message": "\n".join(message_parts),
                            "modifications": all_modifications,
                            "trigger_search": False,
                            "session_state": session_state,
                            "agentic_tools_used": ["location_tool", "filter_tool"],
                            "location_analysis": location_result
                        })
                    else:
                        return self._create_content({
                            "success": False,
                            "message": f"Found {len(discovered_locations)} locations but failed to add them to filters",
                            "error": "Filter tool failed to apply location modifications"
                        })
                else:
                    print(f"⚠️ Location tool failed, using fallback")
                    return await self._handle_simple_fallback_location_expansion(base_location, analysis_type, session_state)
            else:
                print(f"⚠️ No location tool available, using fallback")
                return await self._handle_simple_fallback_location_expansion(base_location, analysis_type, session_state)
                
        except Exception as e:
            print(f"❌ Agentic location expansion failed: {e}")
            import traceback
            traceback.print_exc()
            return await self._handle_simple_interaction(user_input, session_state)
    
    async def _handle_simple_fallback_location_expansion(self, base_location: str, analysis_type: str, session_state: Dict[str, Any]) -> object:
        """Simple fallback for location expansion when location tool fails."""
        try:
            location_mappings = {
                "Noida": ["Delhi", "Gurgaon", "Ghaziabad", "Greater Noida"],
                "Delhi": ["Noida", "Gurgaon", "Faridabad", "Ghaziabad"],
                "Mumbai": ["Pune", "Thane", "Navi Mumbai", "Nashik"],
                "Bangalore": ["Mysore", "Chennai", "Hyderabad", "Coimbatore"],
                "Chennai": ["Bangalore", "Coimbatore", "Madurai", "Pondicherry"],
                "Hyderabad": ["Bangalore", "Chennai", "Vijayawada", "Warangal"],
                "Pune": ["Mumbai", "Nashik", "Aurangabad", "Satara"]
            }
            
            if analysis_type == "industry_hubs":
                tech_hubs = ["Bangalore", "Hyderabad", "Chennai", "Pune", "Mumbai", "Delhi", "Noida", "Gurgaon"]
                discovered_locations = [loc for loc in tech_hubs if loc != base_location][:4]
            else:
                discovered_locations = location_mappings.get(base_location, [base_location])[:4]
            
            # Add to session state
            modifications = []
            for location in discovered_locations:
                if location not in session_state.get('current_cities', []):
                    session_state.setdefault('current_cities', []).append(location)
                    modifications.append({
                        "type": "location_added",
                        "field": "location", 
                        "value": location,
                        "mandatory": False
                    })
            
            message = f"Added {len(modifications)} locations near {base_location}: {', '.join([m['value'] for m in modifications])}"
            
            return self._create_content({
                "success": True,
                "message": message,
                "modifications": modifications,
                "trigger_search": True,
                "session_state": session_state,
                "method": "fallback_mapping"
            })
            
        except Exception as e:
            return self._create_content({
                "success": False,
                "error": f"Location expansion failed: {str(e)}"
            })
    
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