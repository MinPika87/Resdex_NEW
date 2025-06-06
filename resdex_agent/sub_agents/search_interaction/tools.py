# Replace resdx_agent/sub_agents/search_interaction/tools.py with this fixed version

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
            # CRITICAL FIX: Ensure session_state is a dict
            if not isinstance(session_state, dict):
                logger.error(f"Session state is not a dict: {type(session_state)}")
                session_state = {}
            
            print(f"🔍 IntentProcessor: Processing intent_data: {intent_data}")
            print(f"🔍 IntentProcessor: Session state type: {type(session_state)}")
            
            if isinstance(intent_data, list):
                return await self._process_multiple_intents(intent_data, session_state)
            else:
                return await self._process_single_intent(intent_data, session_state)
                
        except Exception as e:
            logger.error(f"Intent processing failed: {e}")
            print(f"❌ Intent processing error: {e}")
            import traceback
            traceback.print_exc()
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
        
        print(f"🔍 Processing single intent: action={action}, trigger_search={trigger_search}")
        
        # Import filter tool here to avoid circular imports
        from ...tools.filter_tools import FilterTool
        filter_tool = FilterTool()
        
        # Apply the modification
        if action in ["add_skill", "remove_skill", "modify_experience", "modify_salary", "add_location", "remove_location"]:
            # CRITICAL FIX: Extract parameters properly to avoid argument conflicts
            
            # Prepare parameters for FilterTool
            filter_params = {}
            
            if action in ["add_skill", "remove_skill"]:
                filter_params["skill"] = intent_data.get("value", "")
                if "mandatory" in intent_data:
                    filter_params["mandatory"] = intent_data.get("mandatory", False)
            
            elif action in ["modify_experience", "modify_salary"]:
                filter_params["operation"] = intent_data.get("operation", "set")
                value = intent_data.get("value", "")
                
                # CRITICAL FIX: Handle dictionary values for range operations
                if isinstance(value, dict):
                    if "min" in value and "max" in value:
                        # Convert dict to range string format "min-max"
                        filter_params["value"] = f"{value['min']}-{value['max']}"
                    elif "min" in value:
                        filter_params["value"] = str(value["min"])
                    elif "max" in value:
                        filter_params["value"] = str(value["max"])
                    else:
                        filter_params["value"] = str(value)
                else:
                    filter_params["value"] = str(value) if value else ""
            
            elif action in ["add_location", "remove_location"]:
                filter_params["location"] = intent_data.get("value", "")
                if "mandatory" in intent_data:
                    filter_params["mandatory"] = intent_data.get("mandatory", False)
            
            print(f"🔍 Calling FilterTool with action='{action}' and params: {filter_params}")
            
            # FIXED: Call filter_tool correctly without argument conflicts
            result = await filter_tool(action, session_state, **filter_params)
            
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
            # Handle general queries or non-filter actions
            if action == "general_query":
                # Handle sorting and other candidate operations
                candidates = session_state.get('candidates', [])
                
                if "sort" in response_text.lower() and candidates:
                    if "experience" in response_text.lower():
                        # Sort by experience
                        sorted_candidates = sorted(candidates, key=lambda x: x.get("experience", 0), reverse=True)
                        session_state['candidates'] = sorted_candidates
                        session_state['page'] = 0  # Reset to first page
                        return {
                            "success": True,
                            "message": "Sorted candidates by experience level (highest first)",
                            "modifications": ["sort_by_experience"],
                            "trigger_search": False
                        }
                    elif "salary" in response_text.lower():
                        # Sort by salary
                        sorted_candidates = sorted(candidates, key=lambda x: x.get("salary", 0), reverse=True)
                        session_state['candidates'] = sorted_candidates
                        session_state['page'] = 0  # Reset to first page
                        return {
                            "success": True,
                            "message": "Sorted candidates by salary expectations (highest first)",
                            "modifications": ["sort_by_salary"],
                            "trigger_search": False
                        }
            
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
        
        print(f"🔍 Processing {len(intent_list)} multiple intents")
        
        # Check if any intent wants to trigger search
        for intent_data in intent_list:
            if intent_data.get("trigger_search", False):
                any_trigger_search = True
                break
        
        # Process each intent
        for i, intent_data in enumerate(intent_list):
            print(f"🔍 Processing intent {i+1}: {intent_data}")
            # Prevent individual search triggers for multiple intents
            intent_copy = intent_data.copy()
            intent_copy["trigger_search"] = False
            
            result = await self._process_single_intent(intent_copy, session_state)
            
            if result["success"]:
                all_modifications.extend(result["modifications"])
                if result["message"]:
                    all_messages.append(result["message"])
            else:
                # If any intent fails, return the error
                return result
        
        # Combine messages
        combined_message = " | ".join(all_messages) if all_messages else f"Applied {len(intent_list)} modifications"
        
        return {
            "success": True,
            "message": combined_message,
            "modifications": all_modifications,
            "trigger_search": any_trigger_search
        }