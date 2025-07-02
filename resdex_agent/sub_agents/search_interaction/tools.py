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
        """Process a single intent - IMPROVED VERSION."""
        try:
            action = intent_data.get("action", "general_query")
            response_text = intent_data.get("response_text", "")
            trigger_search = intent_data.get("trigger_search", False)
            
            print(f"🔍 Processing single intent: action={action}, trigger_search={trigger_search}")
            
            if action == "search_execution":
                print(f"🚀 SEARCH EXECUTION DETECTED")
                return {
                    "success": True,
                    "message": "Search execution triggered",
                    "modifications": ["search_executed"],
                    "trigger_search": True
                }
            
            # Import filter tool here to avoid circular imports
            from ...tools.filter_tools import FilterTool
            filter_tool = FilterTool()
            
            # Apply the modification
            if action in ["add_skill", "remove_skill", "modify_experience", "modify_salary", "add_location", "remove_location"]:
                # Prepare parameters for FilterTool
                filter_params = {}
                
                if action in ["add_skill", "remove_skill"]:
                    skill_value = intent_data.get("value", "")
                    if not skill_value or skill_value.strip() == "":
                        return {
                            "success": False,
                            "error": f"No skill specified for {action}",
                            "modifications": [],
                            "trigger_search": False
                        }
                    filter_params["skill"] = skill_value.strip()
                    if "mandatory" in intent_data:
                        filter_params["mandatory"] = intent_data.get("mandatory", False)
                
                elif action in ["modify_experience", "modify_salary"]:
                    filter_params["operation"] = intent_data.get("operation", "set")
                    value = intent_data.get("value", "")
                    
                    # Handle dictionary values for range operations
                    if isinstance(value, dict):
                        if "min" in value and "max" in value:
                            filter_params["value"] = f"{value['min']}-{value['max']}"
                        elif "min" in value:
                            filter_params["value"] = str(value["min"])
                        elif "max" in value:
                            filter_params["value"] = str(value["max"])
                        else:
                            filter_params["value"] = str(value)
                    else:
                        if not value or str(value).strip() == "":
                            return {
                                "success": False,
                                "error": f"No value specified for {action}",
                                "modifications": [],
                                "trigger_search": False
                            }
                        filter_params["value"] = str(value).strip()
                
                elif action in ["add_location", "remove_location"]:
                    location_value = intent_data.get("value", "")
                    if not location_value or location_value.strip() == "":
                        return {
                            "success": False,
                            "error": f"No location specified for {action}",
                            "modifications": [],
                            "trigger_search": False
                        }
                    filter_params["location"] = location_value.strip()
                    if "mandatory" in intent_data:
                        filter_params["mandatory"] = intent_data.get("mandatory", False)
                
                print(f"🔍 Calling FilterTool with action='{action}' and params: {filter_params}")
                
                # Call filter_tool correctly
                result = await filter_tool(action, session_state, **filter_params)
                
                if result["success"]:
                    return {
                        "success": True,
                        "message": response_text or result.get("message", f"{action} completed"),
                        "modifications": result.get("modifications", []),
                        "trigger_search": trigger_search
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", f"Filter modification failed for {action}"),
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
                            sorted_candidates = sorted(candidates, key=lambda x: x.get("experience", 0), reverse=True)
                            session_state['candidates'] = sorted_candidates
                            session_state['page'] = 0
                            return {
                                "success": True,
                                "message": "Sorted candidates by experience level (highest first)",
                                "modifications": ["sort_by_experience"],
                                "trigger_search": False
                            }
                        elif "salary" in response_text.lower():
                            sorted_candidates = sorted(candidates, key=lambda x: x.get("salary", 0), reverse=True)
                            session_state['candidates'] = sorted_candidates
                            session_state['page'] = 0
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
                
        except Exception as e:
            logger.error(f"Single intent processing failed: {e}")
            print(f"❌ Single intent processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Intent processing failed: {str(e)}",
                "modifications": [],
                "trigger_search": False
            }
    
    async def _process_multiple_intents(self, intent_list: List[Dict[str, Any]], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple intents in sequence - FIXED VERSION."""
        all_modifications = []
        all_messages = []
        any_trigger_search = False
        successful_intents = 0
        
        print(f"🔍 Processing {len(intent_list)} multiple intents")
        
        # Check if any intent wants to trigger search
        for intent_data in intent_list:
            if intent_data.get("trigger_search", False):
                any_trigger_search = True
                break
        
        # Process each intent
        for i, intent_data in enumerate(intent_list, 1):
            print(f"🔍 Processing intent {i}/{len(intent_list)}: {intent_data.get('action', 'unknown')}")
            
            try:
                # FIXED: Don't modify the original intent_data, create a copy
                intent_copy = intent_data.copy()
                # Prevent individual search triggers for multiple intents - we'll handle at the end
                intent_copy["trigger_search"] = False
                
                result = await self._process_single_intent(intent_copy, session_state)
                
                if result["success"]:
                    all_modifications.extend(result.get("modifications", []))
                    if result.get("message"):
                        all_messages.append(result["message"])
                    successful_intents += 1
                    print(f"✅ Intent {i} processed successfully")
                else:
                    # FIXED: Don't fail everything if one intent fails, just log and continue
                    error_msg = result.get("error", "Unknown error")
                    print(f"⚠️ Intent {i} failed: {error_msg}")
                    all_messages.append(f"⚠️ {intent_data.get('action', 'Unknown action')}: {error_msg}")
                    # Continue processing other intents instead of returning early
                    
            except Exception as e:
                print(f"❌ Intent {i} exception: {e}")
                all_messages.append(f"❌ {intent_data.get('action', 'Unknown action')}: Failed")
                continue
        
        # FIXED: Create a more informative combined message
        if successful_intents > 0:
            if len(all_messages) > 0:
                # Show first few messages and summarize
                if len(all_messages) <= 3:
                    combined_message = " | ".join(all_messages)
                else:
                    first_three = " | ".join(all_messages[:3])
                    remaining = len(all_messages) - 3
                    combined_message = f"{first_three} ... and {remaining} more modifications"
            else:
                combined_message = f"Successfully applied {successful_intents} of {len(intent_list)} filter modifications"
            
            return {
                "success": True,
                "message": combined_message,
                "modifications": all_modifications,
                "trigger_search": any_trigger_search,
                "processed_count": successful_intents,
                "total_count": len(intent_list)
            }
        else:
            # FIXED: All intents failed
            return {
                "success": False,
                "error": f"Failed to process all {len(intent_list)} intents",
                "message": "No modifications could be applied",
                "modifications": [],
                "trigger_search": False,
                "processed_count": 0,
                "total_count": len(intent_list)
            }