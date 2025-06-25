# resdex_agent/agent.py - MINIMAL UPDATE (Backward Compatible)
"""
MINIMAL Root Agent Update - Adds orchestration without breaking existing code
"""

# Keep all your existing imports and add these new ones:
from typing import Dict, Any, List, Optional
import logging
import uuid
import asyncio
from datetime import datetime

# NEW: Import base functionality (only if available)
try:
    from .base_agent import MemoryMixin
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    class MemoryMixin:
        def __init__(self): pass

# Keep all your existing imports
from .utils.step_logger import step_logger

logger = logging.getLogger(__name__)


# Keep your existing Content class
class Content:
    """Simple content wrapper for agent communication."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data


# Keep your existing BaseAgent class  
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


# UPDATED: Enhanced ResDexRootAgent with minimal changes
class ResDexRootAgent(BaseAgent, MemoryMixin if MEMORY_AVAILABLE else object):
    """
    MINIMALLY UPDATED Root agent - adds orchestration while keeping existing functionality
    """

    def __init__(self, config=None):
        from .config import AgentConfig
        self._config = config or AgentConfig.from_env()

        # Initialize memory if available
        if MEMORY_AVAILABLE:
            MemoryMixin.__init__(self)

        # Initialize tools including new memory tool
        from .tools.search_tools import SearchTool
        from .tools.llm_tools import LLMTool
        from .tools.validation_tools import ValidationTool
        
        tools_list = [
            SearchTool("search_tool"),
            LLMTool("root_llm_tool"),
            ValidationTool("validation_tool")
        ]
        
        # Add memory tool if available
        if MEMORY_AVAILABLE:
            from .tools.memory_tools import MemoryTool
            tools_list.append(MemoryTool("memory_tool", self.memory_service))

        # Call parent constructor
        BaseAgent.__init__(
            self,
            name=self._config.name,
            description=self._config.description,
            tools=tools_list
        )

        # Initialize sub-agents
        self.sub_agents = {}
        self._initialize_sub_agents()
        
        logger.info(f"Updated {self._config.name} v{self._config.version} with orchestration")

    @property
    def config(self):
        """Read-only access to config."""
        return self._config
    
    def _initialize_sub_agents(self):
        """Initialize available sub-agents."""
        try:
            # SearchInteractionAgent (existing) - ✅ WORKING
            if self.config.is_sub_agent_enabled("search_interaction"):
                try:
                    from .sub_agents.search_interaction.agent import SearchInteractionAgent
                    search_agent = SearchInteractionAgent()
                    
                    if MEMORY_AVAILABLE and hasattr(self, 'memory_service'):
                        search_agent.memory_service = self.memory_service
                        search_agent.session_manager = self.session_manager
                    
                    self.sub_agents["search_interaction"] = search_agent
                    logger.info("✅ Initialized SearchInteractionAgent successfully")
                except Exception as e:
                    logger.warning(f"❌ Failed to initialize SearchInteractionAgent: {e}")
            
            # NEW: ExpansionAgent
            if self.config.is_sub_agent_enabled("expansion"):
                try:
                    from .sub_agents.expansion.agent import ExpansionAgent
                    expansion_agent = ExpansionAgent()  # No config parameter
                    
                    if MEMORY_AVAILABLE and hasattr(self, 'memory_service'):
                        expansion_agent.memory_service = self.memory_service
                        expansion_agent.session_manager = self.session_manager
                    
                    self.sub_agents["expansion"] = expansion_agent
                    logger.info("✅ Initialized ExpansionAgent successfully")
                except Exception as e:
                    logger.warning(f"❌ Failed to initialize ExpansionAgent: {e}")
                    import traceback
                    traceback.print_exc()
            
            # NEW: GeneralQueryAgent  
            if self.config.is_sub_agent_enabled("general_query"):
                try:
                    from .sub_agents.general_query.agent import GeneralQueryAgent
                    general_agent = GeneralQueryAgent()  # No config parameter
                    
                    if MEMORY_AVAILABLE and hasattr(self, 'memory_service'):
                        general_agent.memory_service = self.memory_service
                        general_agent.session_manager = self.session_manager
                    
                    self.sub_agents["general_query"] = general_agent
                    logger.info("✅ Initialized GeneralQueryAgent successfully")
                except Exception as e:
                    logger.warning(f"❌ Failed to initialize GeneralQueryAgent: {e}")
                    import traceback
                    traceback.print_exc()
            
            logger.info(f"✅ Initialized {len(self.sub_agents)} sub-agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize sub-agents: {e}")
        
    async def execute(self, content: Content) -> Content:
        """ENHANCED execute with optional orchestration + all original functionality."""
        try:
            # Extract session info
            session_id = content.data.get('session_id') or str(uuid.uuid4())
            user_id = content.data.get('user_id', 'default_user')
            
            # NEW: Try intelligent routing first (if available)
            if len(self.sub_agents) > 1 and content.data.get("user_input"):
                try:
                    return await self._try_intelligent_routing(content, session_id, user_id)
                except Exception as e:
                    logger.warning(f"Intelligent routing failed, using fallback: {e}")
            
            # FALLBACK: Use existing execute logic
            return await self._execute_original_logic(content, session_id, user_id)
                
        except Exception as e:
            logger.error(f"Root agent execution failed: {e}")
            return Content(data={
                "success": False,
                "error": "Root agent execution failed",
                "details": str(e)
            })
    
    async def _try_intelligent_routing(self, content: Content, session_id: str, user_id: str) -> Content:
        """NEW: Intelligent multi-intent orchestration with expansion support."""
        user_input = content.data.get("user_input", "")
        session_state = content.data.get("session_state", {})
        
        # STEP 1: Multi-Intent Analysis using LLM
        intent_breakdown = await self._analyze_multi_intent_breakdown(user_input, session_state)
        
        print(f"🔍 INTENT BREAKDOWN RESULT: {intent_breakdown}")
        
        # Execute orchestration when multi-intent is detected
        if intent_breakdown["success"] and intent_breakdown.get("is_multi_intent", False):
            if session_id:
                step_logger.log_step(f"🔗 Multi-intent detected: {intent_breakdown['total_intents']} intents", "orchestration")
            
            print(f"🎯 EXECUTING MULTI-INTENT ORCHESTRATION")
            
            return await self._execute_multi_intent_orchestration(
                intent_breakdown, user_input, session_state, session_id, user_id
            )
        
        # Only fall through to single-intent routing if NOT multi-intent
        print(f"🔄 SINGLE INTENT ROUTING (multi-intent not detected)")
        
        # STEP 2: Enhanced Single Intent Routing with expansion support
        input_lower = user_input.lower()
        
        # ENHANCED: Route to ExpansionAgent for all expansion types
        if "expansion" in self.sub_agents:
            expansion_indicators = [
                # Skill expansion
                "similar skills", "related skills", "skills similar to", "skills like",
                "expand skills", "find skills", "skill suggestions",
                
                # Title expansion  
                "similar titles", "related titles", "titles similar to", "titles like",
                "similar roles", "related roles", "roles similar to", "roles like",
                "similar positions", "related positions", "positions similar to", "positions like",
                "expand titles", "find titles", "title suggestions",
                
                # Location expansion
                "nearby locations", "similar locations", "locations similar to", "locations like",
                "nearby cities", "similar cities", "cities similar to", "cities like",
                "expand locations", "find locations", "around", "close to", "near"
            ]
            
            if any(indicator in input_lower for indicator in expansion_indicators):
                if session_id:
                    step_logger.log_step("🎯 Routing to ExpansionAgent", "routing")
                return await self._route_to_agent("expansion", content, session_id)
        
        # Route to GeneralQueryAgent if available  
        if "general_query" in self.sub_agents:
            general_indicators = ["hi", "hello", "help", "what can you", "explain", "how do"]
            if any(indicator in input_lower for indicator in general_indicators):
                if session_id:
                    step_logger.log_step("🎯 Routing to GeneralQueryAgent", "routing")
                return await self._route_to_agent("general_query", content, session_id)
        
        # Default to SearchInteractionAgent
        if "search_interaction" in self.sub_agents:
            if session_id:
                step_logger.log_step("🎯 Routing to SearchInteractionAgent", "routing")
            return await self._route_to_agent("search_interaction", content, session_id)
        
        # If no agents available, use original logic
        return await self._execute_original_logic(content, session_id, user_id)
    """
    async def _try_intelligent_routing(self, content: Content, session_id: str, user_id: str) -> Content:
        user_input = content.data.get("user_input", "")
        session_state = content.data.get("session_state", {})
        
        # STEP 1: Multi-Intent Analysis using LLM
        intent_breakdown = await self._analyze_multi_intent_breakdown(user_input, session_state)
        
        print(f"🔍 INTENT BREAKDOWN RESULT: {intent_breakdown}")
        
        # CRITICAL FIX: Check if we have valid intent analysis
        if intent_breakdown["success"] and intent_breakdown.get("intents"):
            intents = intent_breakdown.get("intents", [])
            
            # If we have intents from LLM analysis, use them for routing
            if len(intents) > 0:
                first_intent = intents[0]
                target_agent = first_intent.get("target_agent")
                intent_type = first_intent.get("intent_type")
                
                print(f"🎯 LLM ANALYSIS ROUTING: target_agent={target_agent}, intent_type={intent_type}")
                
                # FIXED: Route based on LLM analysis instead of fallback logic
                if target_agent == "expansion":
                    if session_id:
                        step_logger.log_step("🎯 Routing to ExpansionAgent (LLM Analysis)", "routing")
                    return await self._route_to_agent("expansion", content, session_id)
                
                elif target_agent == "search_interaction":
                    if session_id:
                        step_logger.log_step("🎯 Routing to SearchInteractionAgent (LLM Analysis)", "routing")
                    return await self._route_to_agent("search_interaction", content, session_id)
                
                elif target_agent == "general_query":
                    if session_id:
                        step_logger.log_step("🎯 Routing to GeneralQueryAgent (LLM Analysis)", "routing")
                    return await self._route_to_agent("general_query", content, session_id)
            
            # Execute orchestration when multi-intent is detected
            if intent_breakdown.get("is_multi_intent", False):
                if session_id:
                    step_logger.log_step(f"🔗 Multi-intent detected: {intent_breakdown['total_intents']} intents", "orchestration")
                
                print(f"🎯 EXECUTING MULTI-INTENT ORCHESTRATION")
                
                return await self._execute_multi_intent_orchestration(
                    intent_breakdown, user_input, session_state, session_id, user_id
                )
        
        # FALLBACK: Only use keyword-based routing if LLM analysis fails
        print(f"🔄 FALLBACK ROUTING (LLM analysis failed or no intents)")
        
        # STEP 2: Enhanced Single Intent Routing with expansion support (FALLBACK ONLY)
        input_lower = user_input.lower()
        
        # Route to ExpansionAgent for all expansion types
        if "expansion" in self.sub_agents:
            expansion_indicators = [
                # Skill expansion
                "similar skills", "related skills", "skills similar to", "skills like",
                "expand skills", "find skills", "skill suggestions",
                
                # Title expansion  
                "similar titles", "related titles", "titles similar to", "titles like",
                "similar roles", "related roles", "roles similar to", "roles like",
                "similar positions", "related positions", "positions similar to", "positions like",
                "expand titles", "find titles", "title suggestions",
                
                # Location expansion
                "nearby locations", "similar locations", "locations similar to", "locations like",
                "nearby cities", "similar cities", "cities similar to", "cities like",
                "expand locations", "find locations", "around", "close to", "near"
            ]
            
            if any(indicator in input_lower for indicator in expansion_indicators):
                if session_id:
                    step_logger.log_step("🎯 Routing to ExpansionAgent (Fallback)", "routing")
                return await self._route_to_agent("expansion", content, session_id)
        
        # Route to GeneralQueryAgent if available  
        if "general_query" in self.sub_agents:
            general_indicators = ["hi", "hello", "help", "what can you", "explain", "how do"]
            if any(indicator in input_lower for indicator in general_indicators):
                if session_id:
                    step_logger.log_step("🎯 Routing to GeneralQueryAgent (Fallback)", "routing")
                return await self._route_to_agent("general_query", content, session_id)
        
        # Default to SearchInteractionAgent
        if "search_interaction" in self.sub_agents:
            if session_id:
                step_logger.log_step("🎯 Routing to SearchInteractionAgent (Default Fallback)", "routing")
            return await self._route_to_agent("search_interaction", content, session_id)
        
        # If no agents available, use original logic
        return await self._execute_original_logic(content, session_id, user_id)
    """

    async def _analyze_multi_intent_breakdown(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if query has multiple intents and break them down - ENHANCED with intelligent extraction."""
        
        prompt = f"""You are an intent analyzer. Break down this user query into distinct, actionable intents for a recruitment system with expansion capabilities.

    User query: "{user_input}"

    Current session context:
    - Active skills: {session_state.get('keywords', [])}
    - Experience: {session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years
    - Current locations: {session_state.get('current_cities', [])}

    CRITICAL AGENT ROUTING RULES:
    1. **Skill Expansion**: If user mentions "similar skills to X" or "related skills" → target_agent: "expansion"
    2. **Title Expansion**: If user mentions "similar titles to X" or "related titles/roles/positions" → target_agent: "expansion"  
    3. **Location Expansion**: If user mentions "nearby to X" or "similar locations" → target_agent: "expansion"
    4. **Filter Operations**: Experience/salary modifications → target_agent: "search_interaction"
    5. **Search Execution**: Final search trigger → target_agent: "search_interaction"
    6. **Expansion**: If the user mentions "similar skills/titles/locations to X and Y and .... then this is a single intent query
    7. **Expansion**: If the user mentions "similar skills to X and similar titles to Y" then this is a multi intent query
    8. **Expansion**: If the user mentions "similar skills to X, similar skills to Y" then this is a multi intent query

    INTELLIGENT QUERY FORMATTING:
    When creating extracted_query for expansion agent, ALWAYS format it properly:
    - For skills: "similar skills to [SKILL_NAME]" (e.g., "similar skills to Python")
    - For titles: "similar titles to [TITLE_NAME]" (e.g., "similar titles to Data Scientist")  
    - For locations: "nearby locations to [LOCATION_NAME]" (e.g., "nearby locations to Mumbai")

    EXAMPLES OF INTELLIGENT FORMATTING:
    Input: "skills like Python and React"
    → Extract: ["Python", "React"]
    → Format: "similar skills to Python and React"

    Input: "titles for data scientist"  
    → Extract: ["Data Scientist"]
    → Format: "similar titles to Data Scientist"

    Input: "nearby Mumbai"
    → Extract: ["Mumbai"] 
    → Format: "nearby locations to Mumbai"

    Input: "expand frontend skills"
    → Extract: ["frontend"]
    → Format: "similar skills to frontend"

    Break down the query into individual intents:

    {{
        "is_multi_intent": true/false,
        "total_intents": number,
        "intents": [
            {{
                "intent_id": 1,
                "intent_type": "skill_expansion|title_expansion|location_expansion|filter_operation|search_execution",
                "target_agent": "expansion|search_interaction",
                "extracted_query": "PROPERLY FORMATTED QUERY FOR TARGET AGENT",
                "raw_entities": ["extracted", "entities", "from", "input"],
                "execution_order": 1,
                "description": "human readable description"
            }}
        ],
        "execution_strategy": "sequential",
        "confidence": 0.0-1.0,
        "reasoning": "explanation of the breakdown"
    }}

    EXAMPLES:

    Input: "skills like Python and titles like Data Scientist"
    Output: {{
        "is_multi_intent": true,
        "total_intents": 2,
        "intents": [
            {{
                "intent_id": 1,
                "intent_type": "skill_expansion",
                "target_agent": "expansion",
                "extracted_query": "similar skills to Python",
                "raw_entities": ["Python"],
                "execution_order": 1,
                "description": "Find skills similar to Python"
            }},
            {{
                "intent_id": 2,
                "intent_type": "title_expansion", 
                "target_agent": "expansion",
                "extracted_query": "similar titles to Data Scientist",
                "raw_entities": ["Data Scientist"],
                "execution_order": 2,
                "description": "Find titles similar to Data Scientist"
            }}
        ]
    }}

    Input: "similar titles for data scientist"
    Output: {{
        "is_multi_intent": false,
        "total_intents": 1,
        "intents": [
            {{
                "intent_id": 1,
                "intent_type": "title_expansion",
                "target_agent": "expansion", 
                "extracted_query": "similar titles to Data Scientist",
                "raw_entities": ["Data Scientist"],
                "execution_order": 1,
                "description": "Find titles similar to Data Scientist"
            }}
        ]
    }}

    Input: "expand Python skills"
    Output: {{
        "is_multi_intent": false,
        "total_intents": 1,
        "intents": [
            {{
                "intent_id": 1,
                "intent_type": "skill_expansion",
                "target_agent": "expansion",
                "extracted_query": "similar skills to Python", 
                "raw_entities": ["Python"],
                "execution_order": 1,
                "description": "Find skills similar to Python"
            }}
        ]
    }}

    Input: "nearby Mumbai locations"
    Output: {{
        "is_multi_intent": false,
        "total_intents": 1,
        "intents": [
            {{
                "intent_id": 1,
                "intent_type": "location_expansion",
                "target_agent": "expansion",
                "extracted_query": "nearby locations to Mumbai",
                "raw_entities": ["Mumbai"],
                "execution_order": 1,
                "description": "Find locations near Mumbai"
            }}
        ]
    }}

    Return ONLY the JSON response."""

        try:
            llm_result = await self.tools["root_llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="multi_intent_breakdown"
            )
            
            print(f"🔍 LLM RESULT: {llm_result}")
            
            if llm_result["success"]:
                if "parsed_response" in llm_result and llm_result["parsed_response"]:
                    breakdown = llm_result["parsed_response"]
                    
                    # ENHANCED: Validate and improve extracted queries
                    if "intents" in breakdown:
                        for intent in breakdown["intents"]:
                            # Ensure the extracted_query is properly formatted
                            if intent.get("target_agent") == "expansion":
                                original_query = intent.get("extracted_query", "")
                                improved_query = self._ensure_proper_expansion_format(
                                    original_query, 
                                    intent.get("intent_type", ""),
                                    intent.get("raw_entities", [])
                                )
                                intent["extracted_query"] = improved_query
                                print(f"🔧 Improved query: '{original_query}' → '{improved_query}'")
                    
                    print(f"🧠 ENHANCED MULTI-INTENT BREAKDOWN: {breakdown}")
                    return {"success": True, **breakdown}
                elif "response_text" in llm_result:
                    try:
                        import json
                        response_text = llm_result["response_text"].strip()
                        
                        if "{" in response_text:
                            json_start = response_text.find("{")
                            json_end = response_text.rfind("}") + 1
                            json_text = response_text[json_start:json_end]
                            
                            breakdown = json.loads(json_text)
                            
                            # Apply the same enhancement
                            if "intents" in breakdown:
                                for intent in breakdown["intents"]:
                                    if intent.get("target_agent") == "expansion":
                                        original_query = intent.get("extracted_query", "")
                                        improved_query = self._ensure_proper_expansion_format(
                                            original_query, 
                                            intent.get("intent_type", ""),
                                            intent.get("raw_entities", [])
                                        )
                                        intent["extracted_query"] = improved_query
                                        print(f"🔧 Improved query: '{original_query}' → '{improved_query}'")
                            
                            print(f"🧠 ENHANCED MULTI-INTENT BREAKDOWN (manual): {breakdown}")
                            return {"success": True, **breakdown}
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing failed: {e}")
            
            print(f"⚠️ LLM breakdown failed: {llm_result}")
            return {"success": False, "is_multi_intent": False}
                
        except Exception as e:
            logger.error(f"Multi-intent breakdown failed: {e}")
            print(f"❌ Multi-intent breakdown exception: {e}")
            return {"success": False, "is_multi_intent": False}

    def _ensure_proper_expansion_format(self, extracted_query: str, intent_type: str, raw_entities: List[str]) -> str:
        """
        Ensure the extracted query is in the proper format that expansion agent patterns can handle.
        """
        if not extracted_query or not intent_type:
            return extracted_query
        
        # If it's already in the right format, keep it
        proper_patterns = {
            "skill_expansion": ["similar skills to", "skills similar to", "expand", "skills like"],
            "title_expansion": ["similar titles to", "titles similar to", "expand", "titles like", "roles similar to"],
            "location_expansion": ["nearby locations to", "locations near", "similar locations to"]
        }
        
        current_patterns = proper_patterns.get(intent_type, [])
        if any(pattern in extracted_query.lower() for pattern in current_patterns):
            return extracted_query
        
        # Format according to intent type
        if intent_type == "skill_expansion":
            if raw_entities:
                entities_str = " and ".join(raw_entities)
                return f"similar skills to {entities_str}"
            else:
                # Try to extract from the query itself
                return extracted_query
        
        elif intent_type == "title_expansion":
            if raw_entities:
                entities_str = " and ".join(raw_entities)
                return f"similar titles to {entities_str}"
            else:
                return extracted_query
        
        elif intent_type == "location_expansion":
            if raw_entities:
                entities_str = " and ".join(raw_entities)
                return f"nearby locations to {entities_str}"
            else:
                return extracted_query
        
        # Default: return as-is
        return extracted_query
    
    async def _execute_multi_intent_orchestration(self, intent_breakdown: Dict[str, Any], 
                                                user_input: str, session_state: Dict[str, Any],
                                                session_id: str, user_id: str) -> Content:
        """Execute multiple intents in orchestrated sequence."""
        try:
            intents = intent_breakdown.get("intents", [])
            total_intents = intent_breakdown.get("total_intents", 0)
            
            if session_id:
                step_logger.log_step(f"🎯 Orchestrating {total_intents} intents", "orchestration")
            
            print(f"🎯 ORCHESTRATING {total_intents} INTENTS:")
            for intent in intents:
                print(f"  - Intent {intent.get('intent_id', '?')}: {intent.get('description', 'no description')}")
            
            all_modifications = []
            all_messages = []
            execution_log = []
            final_result = None
            search_executed = False
            # Sort intents by execution order
            sorted_intents = sorted(intents, key=lambda x: x.get('execution_order', 999))
            
            # Execute each intent sequentially
            for i, intent in enumerate(sorted_intents, 1):
                intent_type = intent.get("intent_type")
                target_agent = intent.get("target_agent")
                extracted_query = intent.get("extracted_query", "")
                description = intent.get("description", f"Intent {i}")
                
                if session_id:
                    step_logger.log_step(f"⚙️ Step {i}/{len(sorted_intents)}: {description}", "orchestration")
                
                print(f"\n🔧 STEP {i}/{len(sorted_intents)}: {description}")
                print(f"   Target Agent: {target_agent}")
                print(f"   Query: '{extracted_query}'")
                
                try:
                    # Route to appropriate agent
                    intent_content = Content(data={
                        "user_input": extracted_query,
                        "session_state": session_state,
                        "intent_context": {
                            "original_query": user_input,
                            "intent_id": intent.get("intent_id"),
                            "intent_type": intent_type,
                            "is_orchestrated": True
                        }
                    })
                    
                    result = await self._route_to_agent(target_agent, intent_content, session_id)
                    
                    if result.data.get("success", False):
                        modifications = result.data.get("modifications", [])
                        all_modifications.extend(modifications)
                        if "search_executed" in modifications:
                            search_executed = True  
                            final_result = result.data.get("search_results", {})
                        message = result.data.get("message", "")
                        if message:
                            all_messages.append(message)
                        
                        execution_log.append(f"✅ {description}: {len(modifications)} modifications")
                        print(f"✅ Intent {i} completed: {len(modifications)} modifications")
                        
                        # Update session state for next intent
                        session_state.update(result.data.get("session_state", {}))
                    else:
                        execution_log.append(f"❌ {description}: {result.data.get('error', 'Failed')}")
                        print(f"❌ Intent {i} failed: {result.data.get('error', 'Unknown error')}")
                        # Continue with other intents even if one fails
                        
                except Exception as e:
                    execution_log.append(f"❌ {description}: Exception {str(e)}")
                    print(f"❌ Intent {i} exception: {e}")
                    continue
            
            # Generate comprehensive response
            combined_message = " | ".join(all_messages) if all_messages else f"Orchestrated {len(sorted_intents)} intents"
            
            if session_id:
                step_logger.log_step(f"🎯 Orchestration complete: {len(all_modifications)} total modifications", "orchestration")
            
            response_data = {
                "success": True,
                "message": combined_message,
                "modifications": all_modifications,
                "trigger_search": search_executed,
                "session_state": session_state,
                "orchestration_summary": {
                    "total_intents": total_intents,
                    "successful_intents": len([log for log in execution_log if "✅" in log]),
                    "failed_intents": len([log for log in execution_log if "❌" in log]),
                    "execution_log": execution_log,
                    "original_query": user_input,
                    "search_executed":search_executed
                },
                "type": "multi_intent_orchestrated"
            }
            if final_result:
                response_data["search_results"] = final_result
        
            return Content(data=response_data)
        
        except Exception as e:
            logger.error(f"Multi-intent orchestration failed: {e}")
            return Content(data={
                "success": False,
                "error": "Multi-intent orchestration failed",
                "details": str(e)
            })
    async def _route_to_agent(self, agent_name: str, content: Content, session_id: str) -> Content:
        """Route request to specific sub-agent."""
        try:
            agent = self.sub_agents[agent_name]
            
            # Add session info
            content.data.update({
                "session_id": session_id,
                "routed_from": "root_agent"
            })
            
            # Execute agent
            if hasattr(agent, 'execute_with_memory_context') and MEMORY_AVAILABLE:
                # Use memory-enhanced execution if available
                user_id = content.data.get('user_id', 'default_user')
                result = await agent.execute_with_memory_context(content, session_id, user_id)
            else:
                # Use standard execution
                result = await agent.execute(content)
            
            # Add routing metadata
            if result.data:
                result.data["routed_to"] = agent_name
                result.data["root_agent"] = {
                    "name": self.config.name,
                    "version": self.config.version
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to route to {agent_name}: {e}")
            return Content(data={
                "success": False,
                "error": f"Routing to {agent_name} failed",
                "details": str(e)
            })
    
    async def _execute_original_logic(self, content: Content, session_id: str, user_id: str) -> Content:
        """FALLBACK: Execute using your original logic (keep all existing functionality)."""
        
        # Check if this is a direct API call (has explicit request_type)
        if "request_type" in content.data and content.data["request_type"] != "auto_route":
            return await self._handle_direct_request_original(content, session_id, user_id)
        
        # Enhanced LLM-driven routing for user inputs
        user_input = content.data.get("user_input", "")
        session_state = content.data.get("session_state", {})
        
        if user_input:
            # Try memory-enhanced processing if available
            if MEMORY_AVAILABLE and hasattr(self, 'get_memory_context_mixin'):
                try:
                    memory_context = await self.get_memory_context_mixin(user_input, user_id)
                    return await self._handle_intelligent_routing_with_memory_original(
                        user_input, session_state, memory_context, session_id, user_id
                    )
                except Exception as e:
                    logger.warning(f"Memory-enhanced processing failed: {e}")
            
            # Fallback to original processing
            return await self._handle_intelligent_routing_original(
                user_input, session_state, session_id, user_id
            )
        
        # Fallback to search interaction
        return await self._handle_search_interaction_original(content, session_id)
    
    
    async def _handle_direct_request_original(self, content: Content, session_id: str, user_id: str) -> Content:
        """Handle direct requests using original logic."""
        request_type = content.data.get("request_type")
        
        if request_type == "candidate_search":
            # Use search tool directly
            search_filters = content.data.get("search_filters", {})
            search_result = await self.tools["search_tool"](search_filters=search_filters)
            return Content(data=search_result)
        
        elif request_type == "health_check":
            return Content(data={
                "success": True,
                "status": "healthy",
                "root_agent": {
                    "name": self.config.name,
                    "version": self.config.version,
                    "sub_agents": list(self.sub_agents.keys()),
                    "memory_enabled": MEMORY_AVAILABLE
                }
            })
        
        else:
            return Content(data={
                "success": False,
                "error": f"Unknown request type: {request_type}"
            })
    
    async def _handle_intelligent_routing_with_memory_original(self, user_input: str, session_state: Dict[str, Any],
                                                             memory_context: List[Dict[str, Any]], session_id: str, 
                                                             user_id: str) -> Content:
        """Handle routing with memory context."""
        # Simplified memory-aware routing
        if any(mem.get('content', '').lower().find('skill') >= 0 for mem in memory_context):
            # Previous skill-related conversations
            if "search_interaction" in self.sub_agents:
                content = Content(data={
                    "user_input": user_input,
                    "session_state": session_state,
                    "memory_context": memory_context
                })
                return await self._route_to_agent("search_interaction", content, session_id)
        
        # Default routing
        return await self._handle_intelligent_routing_original(user_input, session_state, session_id, user_id)
    
    async def _handle_intelligent_routing_original(self, user_input: str, session_state: Dict[str, Any],
                                                  session_id: str, user_id: str) -> Content:
        """Handle routing without memory (original logic)."""
        # Route to SearchInteractionAgent if available
        if "search_interaction" in self.sub_agents:
            content = Content(data={
                "user_input": user_input,
                "session_state": session_state
            })
            return await self._route_to_agent("search_interaction", content, session_id)
        
        # Fallback response
        return Content(data={
            "success": True,
            "message": f"Processed: '{user_input}'. Please use the search interface for detailed operations.",
            "modifications": [],
            "trigger_search": False,
            "session_state": session_state
        })
    
    async def _handle_search_interaction_original(self, content: Content, session_id: str) -> Content:
        """Handle search interaction using original logic."""
        if "search_interaction" in self.sub_agents:
            return await self._route_to_agent("search_interaction", content, session_id)
        
        # Fallback
        return Content(data={
            "success": False,
            "error": "Search interaction not available"
        })
    async def save_session_to_memory(self, user_id: str, session_id: str):
        """Save the current session to long-term memory."""
        try:
            if MEMORY_AVAILABLE and hasattr(self, 'session_manager') and self.session_manager:
                await self.session_manager.save_session_to_memory(user_id, session_id)
                logger.info(f"Saved session {session_id} to memory for user {user_id}")
            else:
                logger.warning("Session manager not available for memory save")
        except Exception as e:
            logger.error(f"Failed to save session to memory: {e}")


