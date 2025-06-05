# Replace resdx_agent/sub_agents/search_interaction/agent.py with this fixed version

"""
Search Interaction Sub-Agent - Simple implementation without Pydantic conflicts.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SearchInteractionAgent:
    """
    Sub-agent for processing search filter modifications through natural language.
    """

    def __init__(self, config=None):
        from .config import SearchInteractionConfig
        self._config = config or SearchInteractionConfig()
        
        self.name = self._config.name
        self.description = self._config.description
        
        # Initialize tools as dictionary
        from .tools import IntentProcessor
        from ...tools.llm_tools import LLMTool
        from ...tools.validation_tools import ValidationTool
        
        self.tools = {
            "llm_tool": LLMTool("llm_tool"),
            "validation_tool": ValidationTool("validation_tool"),
            "intent_processor": IntentProcessor("intent_processor")
        }
        
        from .prompts import IntentExtractionPrompt
        self._prompt_template = IntentExtractionPrompt()

        print(f"🔍 {self.name} initialized with tools: {list(self.tools.keys())}")
        logger.info(f"Initialized {self._config.name} v{self._config.version}")

    @property
    def config(self):
        return self._config

    @property
    def prompt_template(self):
        return self._prompt_template

    async def execute(self, content) -> object:
        """Execute search interaction processing."""
        try:
            # Extract input data safely
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            # Ensure session_state is a dict
            if not isinstance(session_state, dict):
                logger.error(f"Session state is not a dict: {type(session_state)}")
                session_state = {}
            
            logger.info(f"Processing search interaction: '{user_input}'")
            print(f"🔍 SearchInteractionAgent processing: '{user_input}'")
            print(f"🔍 Session state type: {type(session_state)}")
            print(f"🔍 Tools available: {list(self.tools.keys())}")
            
            # Validate user input
            validation_result = await self.tools["validation_tool"](
                validation_type="user_input",
                data=user_input
            )
            
            if not validation_result["success"]:
                from ...agent import Content
                return Content(data={
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
                from ...agent import Content
                return Content(data={
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
                "session_state": session_state,  # Updated session state
                "intent_data": intent_data,  # For debugging
                "processing_details": {
                    "agent": self.config.name,
                    "version": self.config.version,
                    "input_validation": validation_result.get("input_analysis", {}),
                    "modification_count": len(processing_result.get("modifications", []))
                }
            }
            
            if not processing_result["success"]:
                response_data["error"] = processing_result.get("error", "Processing failed")
            
            logger.info(f"Search interaction completed: {len(processing_result.get('modifications', []))} modifications")
            
            from ...agent import Content
            return Content(data=response_data)
            
        except Exception as e:
            logger.error(f"Search interaction agent failed: {e}")
            print(f"❌ Search interaction agent error: {e}")
            import traceback
            traceback.print_exc()
            
            from ...agent import Content
            return Content(data={
                "success": False,
                "error": "An unexpected error occurred while processing your request",
                "details": str(e)
            })