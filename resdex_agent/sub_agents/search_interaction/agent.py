# resdex_agent/sub_agents/search_interaction/agent.py - SIMPLIFIED
"""
Simplified Search Interaction Agent - Filter Operations Only
"""

from typing import Dict, Any, List, Optional
import logging

from ...base_agent import BaseResDexAgent, Content
from .config import SearchInteractionConfig

logger = logging.getLogger(__name__)


class SearchInteractionAgent(BaseResDexAgent):
    """
    Simplified Search Interaction Agent
    
    RESPONSIBILITIES (FOCUSED):
    1. Filter operations (add/remove skills, modify experience/salary/location)
    2. Candidate search execution
    3. Result sorting and filtering
    4. Session state management
    
    REMOVED (moved to other agents):
    - Multi-intent detection and handling
    - Location expansion logic
    - Complex task breakdown
    - Orchestration logic
    """

    def __init__(self, config: SearchInteractionConfig = None):
        self._config = config or SearchInteractionConfig()
        
        super().__init__(
            name=self._config.name,
            description=self._config.description,
            #config=self._config
        )
        
        # Initialize search-specific tools
        self._setup_search_tools()
        
        logger.info(f"Simplified SearchInteractionAgent initialized")

    @property
    def config(self):
        return self._config
    
    def _setup_search_tools(self):
        """Setup search and filter tools."""
        try:
            # Core search tools
            from ...tools.search_tools import SearchTool
            from ...tools.filter_tools import FilterTool
            from .tools import IntentProcessor
            
            self.tools.update({
                "search_tool": SearchTool("search_tool"),
                "filter_tool": FilterTool("filter_tool"),
                "intent_processor": IntentProcessor("intent_processor")
            })
            
            print(f"🔍 SearchInteractionAgent tools: {list(self.tools.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to setup search tools: {e}")
    
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Core search interaction logic - simplified to handle single intents only.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            request_type = content.data.get("request_type", "search_interaction")
            
            # Ensure session_state is a dict
            if not isinstance(session_state, dict):
                logger.error(f"Session state is not a dict: {type(session_state)}")
                session_state = {}
            
            logger.info(f"SearchInteractionAgent processing: '{user_input}'")
            print(f"🔍 SEARCH AGENT: Processing '{user_input}'")
            
            # Handle direct search requests
            if request_type == "candidate_search":
                return await self._handle_direct_search(content, session_id)
            
            # Handle filter operations and searches
            return await self._handle_filter_operation(user_input, session_state, memory_context, session_id, user_id)
                    
        except Exception as e:
            logger.error(f"SearchInteractionAgent execution failed: {e}")
            return self.create_content({
                "success": False,
                "error": "Search interaction failed",
                "details": str(e)
            })
    
    async def _handle_direct_search(self, content: Content, session_id: str) -> Content:
        """Handle direct candidate search requests."""
        try:
            search_filters = content.data.get("search_filters", {})
            
            print(f"🔍 DIRECT SEARCH: {search_filters}")
            
            # Execute search using search tool
            search_result = await self.tools["search_tool"](search_filters=search_filters)
            
            # Prepare response
            response_data = {
                "success": search_result["success"],
                "candidates": search_result.get("candidates", []),
                "total_count": search_result.get("total_count", 0),
                "message": search_result.get("message", ""),
                "agent_info": {
                    "name": self.config.name,
                    "version": self.config.version,
                    "tool_used": "search_tool"
                }
            }
            
            if not search_result["success"]:
                response_data["error"] = search_result.get("error", "Search failed")
            
            return self.create_content(response_data)
            
        except Exception as e:
            logger.error(f"Direct search failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Direct search failed: {str(e)}",
                "candidates": [],
                "total_count": 0
            })
    
    async def _handle_filter_operation(self, user_input: str, session_state: Dict[str, Any],
                                     memory_context: List[Dict[str, Any]], session_id: str, 
                                     user_id: str) -> Content:
        """Handle filter operations with simplified intent processing."""
        try:
            print(f"🔧 FILTER OPERATION: Processing '{user_input}'")
            
            # Validate user input
            validation_result = await self.tools["validation_tool"](
                validation_type="user_input",
                data=user_input
            )
            
            if not validation_result["success"]:
                return self.create_content({
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
            
            print(f"🔍 Current filters: {current_filters}")
            
            # Extract intent using LLM (SIMPLIFIED - single call)
            llm_result = await self.tools["llm_tool"](
                user_input=user_input,
                current_filters=current_filters,
                task="extract_intent"
            )
            
            if not llm_result["success"]:
                return self.create_content({
                    "success": False,
                    "error": "Failed to process your request",
                    "details": llm_result.get("error", "Unknown error")
                })
            
            intent_data = llm_result["intent_data"]
            print(f"🎯 Intent extracted: {intent_data}")
            
            # Process the intent using intent processor
            processing_result = await self.tools["intent_processor"](
                intent_data=intent_data,
                session_state=session_state
            )
            
            # Handle candidate operations if no filters were modified
            if processing_result["success"] and not processing_result.get("modifications"):
                candidate_operation_result = await self._handle_candidate_operations(
                    user_input, session_state, intent_data
                )
                if candidate_operation_result:
                    return candidate_operation_result
            
            # Prepare final response
            response_data = {
                "success": processing_result["success"],
                "message": processing_result.get("message", ""),
                "modifications": processing_result.get("modifications", []),
                "trigger_search": processing_result.get("trigger_search", False),
                "session_state": session_state,
                "intent_data": intent_data,
                "agent_info": {
                    "name": self.config.name,
                    "version": self.config.version,
                    "type": "simplified_search_interaction"
                }
            }
            
            if not processing_result["success"]:
                response_data["error"] = processing_result.get("error", "Processing failed")
            
            return self.create_content(response_data)
            
        except Exception as e:
            logger.error(f"Filter operation failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Filter operation failed: {str(e)}",
                "modifications": [],
                "session_state": session_state,
                "trigger_search": False
            })
    
    async def _handle_candidate_operations(self, user_input: str, session_state: Dict[str, Any],
                                         intent_data: Dict[str, Any]) -> Optional[Content]:
        """Handle operations on existing candidates (sorting, filtering, etc.)."""
        try:
            candidates = session_state.get('candidates', [])
            
            if not candidates:
                return None  # No candidates to operate on
            
            input_lower = user_input.lower()
            
            # Handle sorting operations
            if "sort" in input_lower:
                return await self._handle_candidate_sorting(input_lower, candidates, session_state)
            
            # Handle filtering operations on existing results
            elif "filter" in input_lower and "by" in input_lower:
                return await self._handle_candidate_filtering(input_lower, candidates, session_state)
            
            # Handle pagination operations
            elif any(keyword in input_lower for keyword in ["more", "next", "show more", "additional"]):
                return await self._handle_pagination(candidates, session_state)
            
            return None
            
        except Exception as e:
            logger.error(f"Candidate operations failed: {e}")
            return None
    
    async def _handle_candidate_sorting(self, input_lower: str, candidates: List[Dict[str, Any]], 
                                      session_state: Dict[str, Any]) -> Content:
        """Handle sorting of existing candidates."""
        try:
            sort_field = None
            sort_order = "desc"  # Default to descending
            
            if "experience" in input_lower:
                sort_field = "experience"
                if "low" in input_lower or "asc" in input_lower:
                    sort_order = "asc"
            elif "salary" in input_lower:
                sort_field = "salary"
                if "low" in input_lower or "asc" in input_lower:
                    sort_order = "asc"
            elif "name" in input_lower:
                sort_field = "name"
                sort_order = "asc"  # Names typically sorted ascending
            
            if not sort_field:
                return self.create_content({
                    "success": False,
                    "error": "Could not determine sort criteria",
                    "suggestions": ["Sort by experience", "Sort by salary", "Sort by name"]
                })
            
            # Perform sorting
            if sort_field == "experience":
                sorted_candidates = sorted(
                    candidates, 
                    key=lambda x: x.get("experience", 0), 
                    reverse=(sort_order == "desc")
                )
                message = f"Sorted {len(candidates)} candidates by experience ({sort_order}ending)"
            elif sort_field == "salary":
                sorted_candidates = sorted(
                    candidates, 
                    key=lambda x: x.get("salary", 0), 
                    reverse=(sort_order == "desc")
                )
                message = f"Sorted {len(candidates)} candidates by salary ({sort_order}ending)"
            elif sort_field == "name":
                sorted_candidates = sorted(
                    candidates, 
                    key=lambda x: x.get("name", "").lower(), 
                    reverse=(sort_order == "desc")
                )
                message = f"Sorted {len(candidates)} candidates by name ({sort_order}ending)"
            
            # Update session state
            session_state['candidates'] = sorted_candidates
            session_state['page'] = 0  # Reset to first page
            
            return self.create_content({
                "success": True,
                "message": message,
                "modifications": [f"sort_by_{sort_field}_{sort_order}"],
                "session_state": session_state,
                "trigger_search": False,
                "operation": "candidate_sorting"
            })
            
        except Exception as e:
            logger.error(f"Candidate sorting failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Sorting failed: {str(e)}"
            })
    
    async def _handle_candidate_filtering(self, input_lower: str, candidates: List[Dict[str, Any]], 
                                        session_state: Dict[str, Any]) -> Content:
        """Handle filtering of existing candidates."""
        try:
            # Simple filtering operations on existing results
            filtered_candidates = candidates.copy()
            filter_message = ""
            
            # Filter by experience threshold
            if "experience" in input_lower and "more than" in input_lower:
                import re
                exp_match = re.search(r'more than (\d+)', input_lower)
                if exp_match:
                    threshold = int(exp_match.group(1))
                    filtered_candidates = [c for c in candidates if c.get("experience", 0) > threshold]
                    filter_message = f"Filtered to candidates with more than {threshold} years experience"
            
            # Filter by salary threshold
            elif "salary" in input_lower and "more than" in input_lower:
                import re
                sal_match = re.search(r'more than (\d+)', input_lower)
                if sal_match:
                    threshold = int(sal_match.group(1))
                    filtered_candidates = [c for c in candidates if c.get("salary", 0) > threshold]
                    filter_message = f"Filtered to candidates with salary more than {threshold} lakhs"
            
            if not filter_message:
                return self.create_content({
                    "success": False,
                    "error": "Could not determine filter criteria",
                    "suggestions": ["Filter by experience more than X", "Filter by salary more than X"]
                })
            
            # Update session state
            session_state['candidates'] = filtered_candidates
            session_state['page'] = 0
            
            return self.create_content({
                "success": True,
                "message": f"{filter_message}. Showing {len(filtered_candidates)} candidates.",
                "modifications": ["candidate_filtering"],
                "session_state": session_state,
                "trigger_search": False,
                "operation": "candidate_filtering"
            })
            
        except Exception as e:
            logger.error(f"Candidate filtering failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Filtering failed: {str(e)}"
            })
    
    async def _handle_pagination(self, candidates: List[Dict[str, Any]], 
                               session_state: Dict[str, Any]) -> Content:
        """Handle pagination of existing candidates."""
        try:
            current_page = session_state.get('page', 0)
            page_size = getattr(self.config, 'ui_pagination_size', 5)
            total_candidates = len(candidates)
            
            # Calculate next page
            next_page = current_page + 1
            start_idx = next_page * page_size
            
            if start_idx >= total_candidates:
                return self.create_content({
                    "success": True,
                    "message": f"No more candidates. Showing all {total_candidates} candidates.",
                    "modifications": [],
                    "session_state": session_state,
                    "trigger_search": False,
                    "operation": "pagination_end"
                })
            
            # Update page
            session_state['page'] = next_page
            end_idx = min(start_idx + page_size, total_candidates)
            
            return self.create_content({
                "success": True,
                "message": f"Showing candidates {start_idx + 1}-{end_idx} of {total_candidates}",
                "modifications": ["pagination_next"],
                "session_state": session_state,
                "trigger_search": False,
                "operation": "pagination"
            })
            
        except Exception as e:
            logger.error(f"Pagination failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Pagination failed: {str(e)}"
            })
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - search agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on search and filter related terms
        search_keywords = ["search", "filter", "add", "remove", "skill", "location", "experience", "salary"]
        words = user_input.lower().split()
        
        relevant_terms = []
        for word in words:
            if word in search_keywords or len(word) > 3:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:5])


