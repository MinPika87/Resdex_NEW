# resdex_agent/sub_agents/refinement/agent.py
"""
Refinement Sub-Agent for handling facet generation and query relaxation.
"""

from typing import Dict, Any, List, Optional
import logging

from ...base_agent import BaseResDexAgent, Content
from .config import RefinementConfig

logger = logging.getLogger(__name__)


class RefinementAgent(BaseResDexAgent):
    """
    Refinement Agent for facet generation and query relaxation.
    
    RESPONSIBILITIES:
    1. Facet generation from search results and current filters
    2. Query relaxation when search results are insufficient
    3. Integration with external facet generation API
    4. User-friendly response formatting
    """

    def __init__(self, config: RefinementConfig = None):
        self._config = config or RefinementConfig()
        
        super().__init__(
            name=self._config.name,
            description=self._config.description
        )
        
        # Initialize refinement-specific tools
        self._setup_refinement_tools()
        
        logger.info(f"RefinementAgent initialized with facet generation capabilities")

    @property
    def config(self):
        return self._config
    
    def _setup_refinement_tools(self):
        """Setup refinement-specific tools."""
        try:
            # Facet generation tool
            from ...tools.facet_generation import FacetGenerationTool
            self.tools["facet_generation"] = FacetGenerationTool("facet_generation_tool")
            
            # Query relaxation tool (placeholder for future implementation)
            # from ...tools.query_relaxation import QueryRelaxationTool
            # self.tools["query_relaxation"] = QueryRelaxationTool("query_relaxation_tool")
            
            # Filter tool for applying relaxation suggestions
            from ...tools.filter_tools import FilterTool
            self.tools["filter_tool"] = FilterTool("refinement_filter_tool")
            
            print(f"🔧 RefinementAgent tools: {list(self.tools.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to setup refinement tools: {e}")
            print(f"❌ Refinement tools setup failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Core refinement logic.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            intent_data = content.data.get("intent_data", {})
            
            logger.info(f"RefinementAgent processing: '{user_input}'")
            print(f"🔧 REFINEMENT AGENT: Processing '{user_input}'")
            
            # Determine refinement type
            refinement_type = self._determine_refinement_type(user_input, intent_data)
            
            if refinement_type == "facet_generation":
                return await self._handle_facet_generation(user_input, session_state, memory_context, session_id, user_id)
            elif refinement_type == "query_relaxation":
                return await self._handle_query_relaxation(user_input, session_state, memory_context, session_id, user_id)
            else:
                return await self._handle_auto_refinement(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            logger.error(f"RefinementAgent execution failed: {e}")
            return self.create_content({
                "success": False,
                "error": "Refinement failed",
                "details": str(e)
            })
    
    def _determine_refinement_type(self, user_input: str, intent_data: Dict[str, Any]) -> str:
        """Determine the type of refinement needed."""
        input_lower = user_input.lower()
        
        # Check intent data first
        if intent_data.get("refinement_type"):
            return intent_data["refinement_type"]
        
        # Facet generation indicators
        facet_indicators = [
            "facets", "categories", "drill down", "refine", "breakdown",
            "show categories", "categorize", "group by", "segment",
            "facet generation", "generate facets", "show facets"
        ]
        
        # Query relaxation indicators
        relaxation_indicators = [
            "relax", "broaden", "more results", "expand search",
            "fewer filters", "less strict", "widen", "loosen"
        ]
        
        has_facet = any(indicator in input_lower for indicator in facet_indicators)
        has_relaxation = any(indicator in input_lower for indicator in relaxation_indicators)
        
        if has_facet:
            return "facet_generation"
        elif has_relaxation:
            return "query_relaxation"
        else:
            return "auto_detection"
    
    async def _handle_facet_generation(self, user_input: str, session_state: Dict[str, Any],
                                 memory_context: List[Dict[str, Any]], session_id: str, 
                                 user_id: str) -> Content:
        """Handle facet generation requests."""
        try:
            print(f"🎯 FACET GENERATION: Analyzing '{user_input}'")
            
            # Check if we have the facet generation tool
            if "facet_generation" not in self.tools:
                return self.create_content({
                    "success": False,
                    "error": "Facet generation tool not available",
                    "message": "Facet generation is currently unavailable. Please try again later.",
                    "type": "refinement_response",  # FIXED: Add response type
                    "refinement_type": "facet_generation"
                })
            
            # Call the facet generation tool
            facet_result = await self.tools["facet_generation"](
                session_state=session_state,
                user_input=user_input,
                memory_context=memory_context
            )
            
            print(f"🔍 Facet generation result: success={facet_result.get('success', False)}")
            
            if facet_result["success"]:
                print(f"✅ Facet generation successful")
                
                facets_data = facet_result.get("facets_data", {})
                
                # Format user-friendly response
                message = self._format_facets_response(facets_data, user_input)
                
                return self.create_content({
                    "success": True,
                    "type": "refinement_response",  # FIXED: Add response type
                    "refinement_type": "facet_generation",
                    "method": "api_integration",
                    "facets_data": facets_data,
                    "message": message,
                    "session_state": session_state,
                    "trigger_search": False,
                    "user_friendly_display": self._create_user_friendly_facets(facets_data),
                    # REMOVED: modifications array to prevent search triggering
                    "modifications": []  # Empty modifications
                })
            else:
                print(f"⚠️ Facet generation failed: {facet_result.get('error', 'Unknown error')}")
                
                return self.create_content({
                    "success": False,
                    "type": "refinement_response",  # FIXED: Add response type
                    "refinement_type": "facet_generation",
                    "error": facet_result.get("error", "Facet generation failed"),
                    "message": "I couldn't generate facets for your current search. This might be due to insufficient data or API issues. Please try with different search criteria.",
                    "modifications": []  # Empty modifications
                })
                    
        except Exception as e:
            print(f"❌ Facet generation error: {e}")
            import traceback
            traceback.print_exc()
            return self.create_content({
                "success": False,
                "type": "refinement_response",  # FIXED: Add response type
                "refinement_type": "facet_generation",
                "error": f"Facet generation failed: {str(e)}",
                "modifications": []  # Empty modifications
            })

    async def _handle_query_relaxation(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Handle query relaxation requests."""
        try:
            print(f"🔄 QUERY RELAXATION: Analyzing '{user_input}'")
            
            relaxation_suggestions = self._generate_relaxation_suggestions(session_state)
            
            return self.create_content({
                "success": True,
                "type": "refinement_response",  # FIXED: Add response type
                "refinement_type": "query_relaxation",
                "method": "rule_based",
                "relaxation_suggestions": relaxation_suggestions,
                "message": f"Here are some suggestions to get more results: {', '.join(relaxation_suggestions)}",
                "session_state": session_state,
                "trigger_search": False,
                "modifications": []  # Empty modifications
            })
                
        except Exception as e:
            print(f"❌ Query relaxation error: {e}")
            return self.create_content({
                "success": False,
                "type": "refinement_response",  # FIXED: Add response type
                "refinement_type": "query_relaxation", 
                "error": f"Query relaxation failed: {str(e)}",
                "modifications": []  # Empty modifications
            })

    
    async def _handle_auto_refinement(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Auto-detect refinement type based on context."""
        try:
            print(f"🔍 AUTO-REFINEMENT: '{user_input}'")
            
            # Default to facet generation if we have search results
            return await self._handle_facet_generation(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            return self.create_content({
                "success": False,
                "error": f"Auto-refinement failed: {str(e)}"
            })
    
    def _format_facets_response(self, facets_data: Dict[str, Any], user_input: str) -> str:
        """Format facets data into user-friendly message - SIMPLIFIED."""
        try:
            if not facets_data:
                return "No facet categories could be generated for your current search criteria."
            
            # Count categories
            primary_categories = len(facets_data.get("result_1", {}))
            secondary_categories = len(facets_data.get("result_2", {}))
            total_categories = primary_categories + secondary_categories
            
            if total_categories > 0:
                category_text = f"{total_categories} facet categories"
                if primary_categories > 0 and secondary_categories > 0:
                    category_text = f"{primary_categories} primary and {secondary_categories} additional facet categories"
                
                return f"🔍 Generated {category_text} for your search. Browse the category titles below to explore available facets."
            else:
                return "Facet categories have been generated for your search criteria."
                
        except Exception as e:
            logger.error(f"Error formatting facets response: {e}")
            return "Facet categories have been generated for your search."
    
    def _create_user_friendly_facets(self, facets_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user-friendly facet display data."""
        try:
            user_friendly = {
                "primary_facets": {},
                "secondary_facets": {},
                "total_categories": 0
            }
            
            # Process result_1 (primary facets)
            result_1 = facets_data.get("result_1", {})
            if result_1:
                user_friendly["primary_facets"] = result_1
                user_friendly["total_categories"] += len(result_1)
            
            # Process result_2 (secondary facets)
            result_2 = facets_data.get("result_2", {})
            if result_2:
                user_friendly["secondary_facets"] = result_2
                user_friendly["total_categories"] += len(result_2)
            
            return user_friendly
            
        except Exception as e:
            logger.error(f"Error creating user-friendly facets: {e}")
            return {"primary_facets": {}, "secondary_facets": {}, "total_categories": 0}
    
    def _generate_relaxation_suggestions(self, session_state: Dict[str, Any]) -> List[str]:
        """Generate query relaxation suggestions (placeholder)."""
        suggestions = []
        
        # Check current filters and suggest relaxations
        if session_state.get("min_exp", 0) > 0:
            suggestions.append("reduce minimum experience requirement")
        
        if session_state.get("max_exp", 50) < 20:
            suggestions.append("increase maximum experience range")
        
        if len(session_state.get("keywords", [])) > 3:
            suggestions.append("reduce number of required skills")
        
        if session_state.get("preferred_cities"):
            suggestions.append("consider candidates from additional locations")
        
        if not suggestions:
            suggestions = ["broaden location criteria", "reduce skill requirements", "expand experience range"]
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - refinement agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on refinement-related terms
        refinement_keywords = ["facet", "category", "refine", "drill", "relax", "broaden"]
        words = user_input.lower().split()
        
        # Extract refinement type and target
        relevant_terms = []
        for word in words:
            if word in refinement_keywords or len(word) > 3:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:4])