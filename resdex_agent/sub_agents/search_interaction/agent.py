# Replace resdex_agent/sub_agents/search_interaction/agent.py with this:

"""
Search Interaction Sub-Agent following Google ADK patterns.
"""

from typing import Dict, Any, List, Optional
import logging
from google.adk.agents import Agent

# FIX: Import Content from the root agent instead of google.adk.core.content
from ...agent import Content

from .config import SearchInteractionConfig
from .tools import IntentProcessor
from .prompts import IntentExtractionPrompt
from ...tools.llm_tools import LLMTool
from ...tools.validation_tools import ValidationTool

logger = logging.getLogger(__name__)


class SearchInteractionAgent(Agent):
    """
    Sub-agent for processing search filter modifications through natural language.
    """

    def __init__(self, config: Optional[SearchInteractionConfig] = None):
        _config = config or SearchInteractionConfig()

        super().__init__(
            name=_config.name,
            description=_config.description,
            model="gemini-2.0-flash",
            tools=[
                LLMTool("llm_tool"),
                ValidationTool("validation_tool"),
                IntentProcessor("intent_processor")
            ]
        )

        self._config = _config
        self._prompt_template = IntentExtractionPrompt()  # ✅ Use private variable

        logger.info(f"Initialized {_config.name} v{_config.version}")

    @property
    def config(self) -> SearchInteractionConfig:
        return self._config

    @property
    def prompt_template(self) -> IntentExtractionPrompt:
        return self._prompt_template


    
    async def execute(self, content: Content) -> Content:
        """Execute search interaction processing."""
        try:
            # Extract input data
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            logger.info(f"Processing search interaction: '{user_input}'")
            
            # Validate user input
            validation_result = await self.tools["validation_tool"](
                validation_type="user_input",
                data=user_input
            )
            
            if not validation_result["success"]:
                return Content(data={
                    "success": False,
                    "error": validation_result["error"],
                    "suggestions": validation_result.get("suggestions", [])
                })
            
            # Extract current filters for context
            current_filters = {
                "keywords": session_state.get('keywords', []),
                "min_exp": session_state.get('min_exp', 0),
                "max_exp": session_state.get('max_exp', 10),
                "min_salary": session_state.get('min_salary', 0),
                "max_salary": session_state.get('max_salary', 15),
                "current_cities": session_state.get('current_cities', []),
                "preferred_cities": session_state.get('preferred_cities', [])
            }
            
            # Extract intent using LLM
            llm_result = await self.tools["llm_tool"](
                user_input=user_input,
                current_filters=current_filters,
                task="extract_intent"
            )
            
            if not llm_result["success"]:
                return Content(data={
                    "success": False,
                    "error": "Failed to process your request",
                    "details": llm_result["error"]
                })
            
            intent_data = llm_result["intent_data"]
            
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
                    "input_validation": validation_result["input_analysis"],
                    "modification_count": len(processing_result.get("modifications", []))
                }
            }
            
            if not processing_result["success"]:
                response_data["error"] = processing_result.get("error", "Processing failed")
            
            logger.info(f"Search interaction completed: {len(processing_result.get('modifications', []))} modifications")
            
            return Content(data=response_data)
            
        except Exception as e:
            logger.error(f"Search interaction agent failed: {e}")
            return Content(data={
                "success": False,
                "error": "An unexpected error occurred while processing your request",
                "details": str(e)
            })