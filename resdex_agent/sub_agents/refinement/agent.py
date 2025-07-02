# resdex_agent/sub_agents/refinement/agent.py - UPDATED with Query Relaxation
"""
Refinement Sub-Agent for handling facet generation and query relaxation.
UPDATED VERSION with complete query relaxation integration.
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
    3. Integration with external APIs for both features
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
        
        logger.info(f"RefinementAgent initialized with facet generation and query relaxation")

    @property
    def config(self):
        return self._config
    
    def _setup_refinement_tools(self):
        """Setup refinement-specific tools."""
        try:
            # Facet generation tool
            from ...tools.facet_generation import FacetGenerationTool
            self.tools["facet_generation"] = FacetGenerationTool("facet_generation_tool")
            
            # NEW: Query relaxation tool
            from ...tools.query_relaxation_tool import QueryRelaxationTool
            self.tools["query_relaxation"] = QueryRelaxationTool("query_relaxation_tool")
            
            # Filter tool for applying suggestions
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
        Core refinement logic with both facet generation and query relaxation.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            intent_context = content.data.get("intent_context", {})
            
            logger.info(f"RefinementAgent processing: '{user_input}'")
            print(f"🔧 REFINEMENT AGENT: Processing '{user_input}'")
            
            # Determine refinement type
            refinement_type = self._determine_refinement_type(user_input, intent_context)
            
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
    
    def _determine_refinement_type(self, user_input: str, intent_context: Dict[str, Any]) -> str:
        """Determine the type of refinement needed."""
        input_lower = user_input.lower()
        
        # Check intent context first
        if intent_context.get("intent_type") == "query_relaxation":
            return "query_relaxation"
        elif intent_context.get("intent_type") == "facet_generation":
            return "facet_generation"
        
        # Facet generation indicators
        facet_indicators = [
            "facets", "categories", "drill down", "refine", "breakdown",
            "show categories", "categorize", "group by", "segment",
            "facet generation", "generate facets", "show facets"
        ]
        
        # Query relaxation indicators
        relaxation_indicators = [
            "relax", "broaden", "more results", "expand search",
            "fewer filters", "less strict", "widen", "loosen",
            "relax search", "broaden search", "get more candidates",
            "not enough results", "too few candidates", "increase results"
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
                    "type": "refinement_response",
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
                    "type": "refinement_response",
                    "refinement_type": "facet_generation",
                    "method": "api_integration",
                    "facets_data": facets_data,
                    "message": message,
                    "session_state": session_state,
                    "trigger_search": False,
                    "user_friendly_display": self._create_user_friendly_facets(facets_data),
                    "modifications": []  # Empty modifications
                })
            else:
                print(f"⚠️ Facet generation failed: {facet_result.get('error', 'Unknown error')}")
                
                return self.create_content({
                    "success": False,
                    "type": "refinement_response",
                    "refinement_type": "facet_generation",
                    "error": facet_result.get("error", "Facet generation failed"),
                    "message": "I couldn't generate facets for your current search. This might be due to insufficient data or API issues. Please try with different search criteria.",
                    "modifications": []
                })
                    
        except Exception as e:
            print(f"❌ Facet generation error: {e}")
            import traceback
            traceback.print_exc()
            return self.create_content({
                "success": False,
                "type": "refinement_response",
                "refinement_type": "facet_generation",
                "error": f"Facet generation failed: {str(e)}",
                "modifications": []
            })

    async def _handle_query_relaxation(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Handle query relaxation requests - UPDATED with full implementation."""
        try:
            print(f"🔄 QUERY RELAXATION: Analyzing '{user_input}'")
            
            # Check if we have the query relaxation tool
            if "query_relaxation" not in self.tools:
                print(f"⚠️ Query relaxation tool not available, using fallback")
                fallback_suggestions = self._generate_fallback_relaxation_suggestions(session_state)
                
                return self.create_content({
                    "success": True,
                    "type": "refinement_response",
                    "refinement_type": "query_relaxation",
                    "method": "rule_based_fallback",
                    "relaxation_suggestions": fallback_suggestions,
                    "message": f"Here are some suggestions to get more results: {', '.join([s['title'] for s in fallback_suggestions[:3]])}",
                    "session_state": session_state,
                    "trigger_search": False,
                    "modifications": []
                })
            
            # Call the query relaxation tool
            relaxation_result = await self.tools["query_relaxation"](
                session_state=session_state,
                user_input=user_input,
                memory_context=memory_context
            )
            
            print(f"🔍 Query relaxation result: success={relaxation_result.get('success', False)}")
            
            if relaxation_result["success"]:
                print(f"✅ Query relaxation successful")
                
                suggestions = relaxation_result.get("suggestions", [])
                current_count = relaxation_result.get("current_count", 0)
                estimated_new_count = relaxation_result.get("estimated_new_count", 0)
                
                # Format comprehensive response
                message = relaxation_result.get("message", "Query relaxation suggestions generated")
                
                return self.create_content({
                    "success": True,
                    "type": "refinement_response",
                    "refinement_type": "query_relaxation",
                    "method": "api_integration",
                    "relaxation_suggestions": suggestions,
                    "relaxation_data": relaxation_result.get("relaxation_data", {}),
                    "current_count": current_count,
                    "estimated_new_count": estimated_new_count,
                    "message": message,
                    "session_state": session_state,
                    "trigger_search": False,
                    "user_friendly_display": self._create_user_friendly_relaxation(suggestions, current_count, estimated_new_count),
                    "modifications": []  # Empty modifications to prevent search triggering
                })
            else:
                print(f"⚠️ Query relaxation failed: {relaxation_result.get('error', 'Unknown error')}")
                
                # Use fallback suggestions
                fallback_suggestions = self._generate_fallback_relaxation_suggestions(session_state)
                
                return self.create_content({
                    "success": True,  # Still successful with fallback
                    "type": "refinement_response",
                    "refinement_type": "query_relaxation",
                    "method": "rule_based_fallback",
                    "relaxation_suggestions": fallback_suggestions,
                    "error": relaxation_result.get("error", "API unavailable"),
                    "message": "I generated some general relaxation suggestions based on your current filters. API-based suggestions are currently unavailable.",
                    "session_state": session_state,
                    "trigger_search": False,
                    "modifications": []
                })
                    
        except Exception as e:
            print(f"❌ Query relaxation error: {e}")
            import traceback
            traceback.print_exc()
            
            # Generate fallback suggestions even on exception
            try:
                fallback_suggestions = self._generate_fallback_relaxation_suggestions(session_state)
                return self.create_content({
                    "success": True,
                    "type": "refinement_response",
                    "refinement_type": "query_relaxation",
                    "method": "rule_based_fallback",
                    "relaxation_suggestions": fallback_suggestions,
                    "error": f"Query relaxation failed: {str(e)}",
                    "message": "I generated some basic suggestions to help broaden your search.",
                    "modifications": []
                })
            except:
                return self.create_content({
                    "success": False,
                    "type": "refinement_response",
                    "refinement_type": "query_relaxation",
                    "error": f"Query relaxation failed: {str(e)}",
                    "modifications": []
                })

    async def _handle_auto_refinement(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Auto-detect refinement type based on context."""
        try:
            print(f"🔍 AUTO-REFINEMENT: '{user_input}'")
            
            # Check current results to determine best refinement type
            current_results = session_state.get('total_results', 0)
            
            # If few results, suggest relaxation
            if current_results < 50:
                print(f"🔄 Auto-routing to query relaxation (low results: {current_results})")
                return await self._handle_query_relaxation(user_input, session_state, memory_context, session_id, user_id)
            else:
                # If sufficient results, offer facets for exploration
                print(f"🔍 Auto-routing to facet generation (sufficient results: {current_results})")
                return await self._handle_facet_generation(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            return self.create_content({
                "success": False,
                "error": f"Auto-refinement failed: {str(e)}"
            })
    
    def _generate_fallback_relaxation_suggestions(self, session_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fallback relaxation suggestions when API is unavailable."""
        suggestions = []
        
        # Check current filters and suggest relaxations
        keywords = session_state.get('keywords', [])
        min_exp = session_state.get('min_exp', 0)
        max_exp = session_state.get('max_exp', 10)
        min_salary = session_state.get('min_salary', 0)
        max_salary = session_state.get('max_salary', 15)
        current_cities = session_state.get('current_cities', [])
        preferred_cities = session_state.get('preferred_cities', [])
        
        # Skill relaxation
        if len(keywords) > 3:
            suggestions.append({
                'type': 'skill_relaxation',
                'title': 'Reduce Required Skills',
                'description': f'You have {len(keywords)} skills. Consider making some optional.',
                'impact': 'Could significantly increase results',
                'action': 'Make 2-3 skills optional instead of mandatory',
                'confidence': 0.8
            })
        
        # Experience relaxation
        if min_exp > 0:
            new_min = max(0, min_exp - 2)
            suggestions.append({
                'type': 'experience_relaxation',
                'title': 'Lower Minimum Experience',
                'description': f'Consider candidates with {new_min}+ years experience',
                'impact': 'Could increase junior talent pool',
                'action': f'Reduce minimum from {min_exp} to {new_min} years',
                'confidence': 0.85
            })
        
        if max_exp < 15:
            new_max = min(20, max_exp + 3)
            suggestions.append({
                'type': 'experience_expansion',
                'title': 'Expand Maximum Experience',
                'description': f'Consider senior candidates up to {new_max} years',
                'impact': 'Could include senior professionals',
                'action': f'Increase maximum from {max_exp} to {new_max} years',
                'confidence': 0.75
            })
        
        # Salary relaxation
        if max_salary < 25:
            new_max_salary = min(30, max_salary + 5)
            suggestions.append({
                'type': 'salary_relaxation',
                'title': 'Increase Salary Range',
                'description': f'Consider expanding salary up to {new_max_salary} lakhs',
                'impact': 'Could attract premium candidates',
                'action': f'Increase from {max_salary} to {new_max_salary} lakhs',
                'confidence': 0.7
            })
        
        # Location relaxation
        total_cities = len(current_cities) + len(preferred_cities)
        if total_cities > 0 and total_cities < 5:
            suggestions.append({
                'type': 'location_relaxation',
                'title': 'Add More Locations',
                'description': 'Consider candidates from additional cities',
                'impact': 'Could expand geographical talent pool',
                'action': 'Add 2-3 more metro cities or enable remote work',
                'confidence': 0.75
            })
        
        # Remote work suggestion
        suggestions.append({
            'type': 'remote_work',
            'title': 'Enable Remote Work',
            'description': 'Consider candidates open to remote work',
            'impact': 'Could significantly expand talent pool',
            'action': 'Add remote work as location option',
            'confidence': 0.9
        })
        
        return suggestions[:4]  # Return top 4 suggestions
    
    def _create_user_friendly_relaxation(self, suggestions: List[Dict[str, Any]], 
                                       current_count: int, estimated_new_count: int) -> Dict[str, Any]:
        """Create user-friendly relaxation display data."""
        try:
            user_friendly = {
                "total_suggestions": len(suggestions),
                "current_candidate_count": current_count,
                "estimated_increase": estimated_new_count,
                "suggestions_by_type": {},
                "top_impact_suggestions": [],
                "summary": {}
            }
            
            # Group suggestions by type
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'general')
                if suggestion_type not in user_friendly["suggestions_by_type"]:
                    user_friendly["suggestions_by_type"][suggestion_type] = []
                user_friendly["suggestions_by_type"][suggestion_type].append(suggestion)
            
            # Find high-impact suggestions
            for suggestion in suggestions:
                confidence = suggestion.get('confidence', 0.5)
                if confidence >= 0.8:
                    user_friendly["top_impact_suggestions"].append(suggestion)
            
            # Create summary
            if estimated_new_count > 0:
                user_friendly["summary"] = {
                    "potential_increase": f"+{estimated_new_count:,} candidates",
                    "total_after_relaxation": f"~{current_count + estimated_new_count:,} candidates",
                    "improvement_percentage": f"{int((estimated_new_count / max(current_count, 1)) * 100)}% increase"
                }
            else:
                user_friendly["summary"] = {
                    "potential_increase": "Significant increase expected",
                    "total_after_relaxation": "Substantially more candidates",
                    "improvement_percentage": "Notable improvement"
                }
            
            return user_friendly
            
        except Exception as e:
            logger.error(f"Error creating user-friendly relaxation display: {e}")
            return {"total_suggestions": len(suggestions), "current_candidate_count": current_count}
    
    def _format_facets_response(self, facets_data: Dict[str, Any], user_input: str) -> str:
        """Format facets data into user-friendly message."""
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
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - refinement agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on refinement-related terms
        refinement_keywords = ["facet", "category", "refine", "drill", "relax", "broaden", "more results"]
        words = user_input.lower().split()
        
        # Extract refinement type and target
        relevant_terms = []
        for word in words:
            if word in refinement_keywords or len(word) > 3:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:4])