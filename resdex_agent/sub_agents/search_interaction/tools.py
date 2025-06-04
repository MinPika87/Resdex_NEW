"""
Tools specific to Search Interaction Sub-Agent.
"""

from typing import Dict, Any, List, Optional
import logging
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

logger = logging.getLogger(__name__)


class IntentProcessor(Tool):
    """Tool for processing search modification intents."""
    
    def __init__(self, name: str = "intent_processor"):
        super().__init__(name=name, description="Process extracted search intents")
    
    async def __call__(self, intent_data: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent data and apply modifications."""
        try:
            if isinstance(intent_data, list):
                return await self._process_multiple_intents(intent_data, session_state)
            else:
                return await self._process_single_intent(intent_data, session_state)
                
        except Exception as e:
            logger.error(f"Intent processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "modifications": [],
                "trigger_search": False
            }
    
    async def _process_single_intent(self, intent_data: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single intent."""
        action = intent_data.get("action", "general_query")
        response_text = intent_data.get("response_text", "")
        trigger_search = intent_data.get("trigger_search", False)
        
        # Import filter tool here to avoid circular imports
        from ...tools.filter_tools import FilterTool
        filter_tool = FilterTool()
        
        # Apply the modification
        if action in ["add_skill", "remove_skill", "modify_experience", "modify_salary", "add_location", "remove_location"]:
            result = await filter_tool(action, session_state, **intent_data)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": response_text or result["message"],
                    "modifications": result["modifications"],
                    "trigger_search": trigger_search
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Filter modification failed"),
                    "modifications": [],
                    "trigger_search": False
                }
        else:
            return {
                "success": True,
                "message": response_text or "Request processed",
                "modifications": [],
                "trigger_search": trigger_search
            }
    
    async def _process_multiple_intents(self, intent_list: List[Dict[str, Any]], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple intents in sequence."""
        all_modifications = []
        all_messages = []
        any_trigger_search = False
        
        # Check if any intent wants to trigger search
        for intent_data in intent_list:
            if intent_data.get("trigger_search", False):
                any_trigger_search = True
                break
        
        # Process each intent
        for intent_data in intent_list:
            # Prevent individual search triggers for multiple intents
            intent_copy = intent_data.copy()
            intent_copy["trigger_search"] = False
            
            result = await self._process_single_intent(intent_copy, session_state)
            
            if result["success"]:
                all_modifications.extend(result["modifications"])
                if result["message"]:
                    all_messages.append(result["message"])
        
        # Combine messages
        combined_message = " | ".join(all_messages) if all_messages else f"Applied {len(intent_list)} modifications"
        
        return {
            "success": True,
            "message": combined_message,
            "modifications": all_modifications,
            "trigger_search": any_trigger_search
        }