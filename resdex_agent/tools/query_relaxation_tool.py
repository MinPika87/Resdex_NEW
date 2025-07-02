# resdex_agent/tools/query_relaxation_tool.py
"""
Query Relaxation Tool for ResDex Agent - Integration with external relaxation API.
"""

import requests
import json
import logging
from typing import Dict, Any, List, Optional
from ..config import config

logger = logging.getLogger(__name__)


class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class QueryRelaxationTool(Tool):
    """
    Tool for generating query relaxation suggestions using external API.
    
    FEATURES:
    1. Convert current session filters to API request format
    2. Call external relaxation API
    3. Parse and format relaxation suggestions
    4. Provide user-friendly recommendations
    """

    def __init__(self, name: str = "query_relaxation_tool"):
        super().__init__(
            name=name,
            description="Generate query relaxation suggestions to get more candidates"
        )
        
        # API Configuration
        self.api_url = "http://10.10.112.202:8125/get_relaxed_query_optimized"
        self.headers = {
            'Content-Type': 'application/json',
            'X-TRANSACTION-ID': '3113ea131'
        }
        
        # Default company/recruiter info (can be made configurable)
        self.default_company_info = {
            'company_id': 3812074,
            'comnotGroupId': 4634055,
            'recruiter_id': 124271564,
            'preference_key': 'e7d47e8e-4728-4a9f-9bfe-d9e8e9586a2b'
        }
        
        logger.info(f"QueryRelaxationTool initialized with API: {self.api_url}")
        print(f"🔄 QueryRelaxationTool ready for relaxation suggestions")

    async def __call__(self, 
                  session_state: Dict[str, Any],
                  user_input: str = "",
                  memory_context: List[Dict[str, Any]] = None,
                  **kwargs) -> Dict[str, Any]:
        """Generate query relaxation suggestions."""
        try:
            print(f"🔄 QUERY RELAXATION: Processing request")
            logger.info(f"Query relaxation requested: '{user_input}'")
            
            # Step 1: Convert session state to API request format
            api_request = self._convert_session_to_api_request(session_state)
            
            # Step 2: Get current candidate count (estimate)
            current_count = session_state.get('total_results', 0)
            if current_count == 0:
                current_count = self._estimate_current_count(session_state)
            
            print(f"🔍 Current candidate count: {current_count}")
            
            # Step 3: Call relaxation API
            api_response = await self._call_relaxation_api(api_request, current_count)
            
            if not api_response["success"]:
                print(f"⚠️ API call failed: {api_response.get('error', 'Unknown error')}")
                # Use fallback suggestions
                fallback_suggestions = self._generate_fallback_suggestions(session_state)
                
                return {
                    "success": True,  # Still return success with fallback
                    "suggestions": fallback_suggestions,
                    "current_count": current_count,
                    "estimated_new_count": 0,
                    "message": "I generated some general relaxation suggestions based on your current filters. API-based suggestions are currently unavailable.",
                    "method": "fallback_suggestions",
                    "error": api_response.get("error", "API unavailable")
                }
            
            # Step 4: Parse and format suggestions
            relaxation_data = api_response["data"]
            
            # DEBUG: Log what we received
            print(f"🔍 Received relaxation_data type: {type(relaxation_data)}")
            if relaxation_data:
                print(f"🔍 relaxation_data keys: {list(relaxation_data.keys()) if isinstance(relaxation_data, dict) else 'Not a dict'}")
            
            formatted_suggestions = self._format_relaxation_suggestions(
                relaxation_data, session_state, user_input
            )
            
            print(f"✅ Generated {len(formatted_suggestions)} relaxation suggestions")
            
            # FIX: Safe extraction of estimated count
            estimated_new_count = 0
            if relaxation_data and isinstance(relaxation_data, dict):
                estimated_new_count = relaxation_data.get("approx_new_count", 0)
                if estimated_new_count is None:
                    estimated_new_count = 0
            
            return {
                "success": True,
                "relaxation_data": relaxation_data,
                "suggestions": formatted_suggestions,
                "current_count": current_count,
                "estimated_new_count": estimated_new_count,
                "api_response": api_response["raw_response"],
                "message": self._create_relaxation_message(formatted_suggestions, relaxation_data),
                "method": "api_integration"
            }
            
        except Exception as e:
            logger.error(f"Query relaxation failed: {e}")
            print(f"❌ Query relaxation error: {e}")
            import traceback
            traceback.print_exc()
            
            # FIX: Always provide fallback on any error
            try:
                fallback_suggestions = self._generate_fallback_suggestions(session_state)
                return {
                    "success": True,  # Return success with fallback
                    "suggestions": fallback_suggestions,
                    "current_count": session_state.get('total_results', 0),
                    "estimated_new_count": 0,
                    "message": "I generated some basic suggestions to help broaden your search.",
                    "method": "fallback_suggestions",
                    "error": str(e)
                }
            except:
                return {
                    "success": False,
                    "error": f"Query relaxation failed: {str(e)}",
                    "message": "Sorry, I couldn't generate relaxation suggestions. Please try again.",
                    "suggestions": []
                }
    def _convert_session_to_api_request(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert session state to API request format."""
        try:
            print(f"🔧 Converting session state to API format")
            
            # Extract current filters
            keywords = session_state.get('keywords', [])
            min_exp = session_state.get('min_exp', 0)
            max_exp = session_state.get('max_exp', 10)
            min_salary = session_state.get('min_salary', 0)
            max_salary = session_state.get('max_salary', 15)
            current_cities = session_state.get('current_cities', [])
            preferred_cities = session_state.get('preferred_cities', [])
            
            # Convert keywords to API format
            ez_keyword_any = []
            for i, keyword in enumerate(keywords):
                ez_keyword_any.append({
                    'key': str(i + 1),  # Use index as key
                    'value': keyword,
                    'type': 'skill',
                    'globalName': keyword.lower()
                })
            
            # Convert cities to API format (using mock IDs)
            city_ids = []
            pref_loc_ids = []
            
            # Mock city mapping (in real implementation, you'd have proper city ID mapping)
            city_mapping = {
                'bangalore': '9501', 'mumbai': '6', 'delhi': '17', 
                'pune': '139', 'hyderabad': '220', 'chennai': '4',
                'kolkata': '11', 'gurgaon': '122', 'noida': '123'
            }
            
            for city in current_cities:
                city_key = city_mapping.get(city.lower(), '9501')  # Default to Bangalore
                city_ids.append(city_key)
            
            for city in preferred_cities:
                city_key = city_mapping.get(city.lower(), '6')  # Default to Mumbai
                pref_loc_ids.append(city_key)
            
            # Build API request
            api_request = {
                'sid': None,
                'ctc_Type': 'rs',
                **self.default_company_info,
                'user_ids': None,
                'search_flag': 'adv',
                'unique_id': None,
                
                # Keywords (any keywords - less restrictive)
                'ez_keyword_any': ez_keyword_any,
                'anyKeywords': ez_keyword_any,
                'ez_keyword_all': [],  # No mandatory keywords for relaxation
                'allKeywords': [],
                'ez_keyword_exclude': [],
                'excludeKeywords': [],
                
                # Experience
                'min_exp': str(min_exp),
                'max_exp': str(max_exp) if max_exp < 50 else '-1',
                
                # Salary (convert lakhs to lakh format for API)
                'min_ctc': f"{float(min_salary):.2f}",
                'max_ctc': f"{float(max_salary):.2f}",
                'ctc_type': 'rs',
                'CTC_Type': 'rs',
                'dollarRate': 60,
                'dollar_rate': 60,
                'zero_ctc_search': False,
                
                # Location
                'city': city_ids,
                'currentStateId': [],
                'OCity': '',
                'pref_loc': pref_loc_ids,
                'preferredStateId': [],
                'loc_city_only': 0,
                'location_op': 'and',
                
                # Other standard parameters
                'farea_roles': [],
                'indtype': [],
                'excludeIndtype': [],
                'noticePeriodArr': [1],
                'notice_period': [1],
                'ugcourse': [],
                'ug_year_range': [-1, -1],
                'pgcourse': [],
                'pg_year_range': [-1, -1],
                'ppgcourse': [],
                'ppg_year_range': [-1, -1],
                'caste_id': [],
                'gender': 'n',
                'dis_type': False,
                'candidate_age_range': [-1, -1],
                'wstatus_usa': [-1],
                'work_auth_others': [-1],
                'all_new': 'ALL',
                'search_on_verified_numbers': False,
                'verified_email': False,
                'uploaded_cv': False,
                'premium': False,
                'featured_search': False,
                'PAGE_LIMIT': 40,
                'sort_by': 'RELEVANCE',
                'isMakeSenseSrch': 1,
                'days_old': '3650',
                'SEARCH_OFFSET': 0,
                'SEARCH_COUNT': 80,
                'freeSearch': False,
                'expActive': True,
                'rerankEnabled': False,
                'excludeTestProfiles': True,
                'segmentEnabled': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                'anyKeywordTags': ','.join(keywords),
                'allKeywordTags': '',
                'daysold': '3650'
            }
            
            print(f"✅ API request prepared with {len(keywords)} skills, exp: {min_exp}-{max_exp}")
            return api_request
            
        except Exception as e:
            logger.error(f"Failed to convert session to API request: {e}")
            raise Exception(f"Session conversion failed: {str(e)}")

    async def _call_relaxation_api(self, api_request: Dict[str, Any], current_count: int) -> Dict[str, Any]:
        """Call the external relaxation API."""
        try:
            print(f"📡 Calling relaxation API...")
            
            payload = {
                'request_object': api_request,
                'totalcount': current_count
            }
            
            # DEBUG: Print the actual payload being sent
            print("🔍 DEBUG: API PAYLOAD BEING SENT:")
            print("=" * 50)
            print(json.dumps(payload, indent=2, default=str))
            print("=" * 50)
            
            logger.info(f"Calling relaxation API with current count: {current_count}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload, default=str),
                timeout=30
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # DEBUG: Print the actual API response
                print("🔍 DEBUG: API RESPONSE RECEIVED:")
                print("=" * 50)
                print(json.dumps(response_data, indent=2, default=str))
                print("=" * 50)
                
                print(f"✅ API call successful")
                logger.info("Relaxation API call successful")
                
                return {
                    "success": True,
                    "data": response_data,
                    "raw_response": response_data
                }
            else:
                error_msg = f"API returned status {response.status_code}"
                print(f"❌ API Error Response: {response.text}")
                logger.error(f"Relaxation API failed: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "raw_response": None
                }
                
        except requests.exceptions.Timeout:
            error_msg = "API request timed out"
            logger.error(f"Relaxation API timeout")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"API call failed: {str(e)}"
            logger.error(f"Relaxation API exception: {e}")
            return {"success": False, "error": error_msg}

    def _estimate_current_count(self, session_state: Dict[str, Any]) -> int:
        """Estimate current candidate count based on filters."""
        # Simple estimation logic based on filter complexity
        base_count = 1000
        
        keywords = session_state.get('keywords', [])
        if len(keywords) > 5:
            base_count = 500
        elif len(keywords) > 3:
            base_count = 750
        
        # Adjust for experience range
        exp_range = session_state.get('max_exp', 10) - session_state.get('min_exp', 0)
        if exp_range < 3:
            base_count = int(base_count * 0.6)
        
        # Adjust for location restrictions
        cities = len(session_state.get('current_cities', [])) + len(session_state.get('preferred_cities', []))
        if cities > 0:
            base_count = int(base_count * 0.8)
        
        return max(base_count, 50)  # Minimum 50

    def _format_relaxation_suggestions(self, relaxation_data: Dict[str, Any], 
                                 session_state: Dict[str, Any], 
                                 user_input: str) -> List[Dict[str, Any]]:
        """Format relaxation suggestions for UI display."""
        try:
            suggestions = []
            
            # FIX: Better None checking
            if not relaxation_data or not isinstance(relaxation_data, dict):
                print(f"⚠️ Invalid relaxation_data: {type(relaxation_data)}")
                return self._generate_fallback_suggestions(session_state)
            
            if 'relaxed_query' not in relaxation_data:
                print(f"⚠️ No relaxed_query in API response. Keys available: {list(relaxation_data.keys())}")
                return self._generate_fallback_suggestions(session_state)
            
            relaxed_query = relaxation_data['relaxed_query']
            
            # FIX: Handle None estimated_count properly
            estimated_count = relaxation_data.get('approx_new_count')
            if estimated_count is None:
                print(f"⚠️ approx_new_count is None in API response")
                estimated_count = 0
            else:
                print(f"✅ API returned estimated_count: {estimated_count}")
            
            print(f"🔧 Formatting suggestions from API response")
            
            # Analyze differences between original and relaxed query
            original_keywords = session_state.get('keywords', [])
            original_min_exp = session_state.get('min_exp', 0)
            original_max_exp = session_state.get('max_exp', 10)
            
            # Extract relaxed keywords - with None checking
            relaxed_any_keywords = relaxed_query.get('ez_keyword_any', []) if relaxed_query else []
            relaxed_all_keywords = relaxed_query.get('ez_keyword_all', []) if relaxed_query else []
            
            # FIX: Only add suggestions if we have valid data
            if relaxed_query:
                # Suggestion 1: Skill relaxation
                if len(relaxed_any_keywords) != len(original_keywords):
                    impact_value = int(estimated_count * 0.3) if estimated_count > 0 else "significant"
                    suggestions.append({
                        'type': 'skill_relaxation',
                        'title': 'Reduce Required Skills',
                        'description': f'API suggests using {len(relaxed_any_keywords)} skills instead of {len(original_keywords)}',
                        'impact': f'Could increase results by ~{impact_value}' if isinstance(impact_value, int) else 'Could significantly increase results',
                        'action': 'Move some skills from mandatory to optional',
                        'confidence': 0.85
                    })
                
                # Suggestion 2: Experience range relaxation
                try:
                    relaxed_min_exp = int(relaxed_query.get('min_exp', 0)) if relaxed_query.get('min_exp') else 0
                    relaxed_max_exp = relaxed_query.get('max_exp', '-1')
                    relaxed_max_exp = 50 if relaxed_max_exp == '-1' else int(relaxed_max_exp) if relaxed_max_exp else original_max_exp
                    
                    if relaxed_min_exp != original_min_exp or relaxed_max_exp != original_max_exp:
                        impact_value = int(estimated_count * 0.4) if estimated_count > 0 else "significant"
                        suggestions.append({
                            'type': 'experience_relaxation',
                            'title': 'Expand Experience Range',
                            'description': f'API suggests {relaxed_min_exp}-{relaxed_max_exp} years instead of {original_min_exp}-{original_max_exp}',
                            'impact': f'Could increase results by ~{impact_value}' if isinstance(impact_value, int) else 'Could significantly increase results',
                            'action': f'Expand from {original_min_exp}-{original_max_exp} to {relaxed_min_exp}-{relaxed_max_exp} years',
                            'confidence': 0.9
                        })
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Error processing experience data: {e}")
                
                # Suggestion 3: Location relaxation (always suggest if user has current cities)
                original_cities = session_state.get('current_cities', []) + session_state.get('preferred_cities', [])
                if original_cities:
                    impact_value = int(estimated_count * 0.25) if estimated_count > 0 else "moderate"
                    suggestions.append({
                        'type': 'location_relaxation',
                        'title': 'Consider Additional Locations',
                        'description': 'Include candidates from nearby cities or remote workers',
                        'impact': f'Could increase results by ~{impact_value}' if isinstance(impact_value, int) else 'Could moderately increase results',
                        'action': 'Add more location options or enable remote work',
                        'confidence': 0.75
                    })
            
            # If no API suggestions, use fallback
            if not suggestions:
                print(f"⚠️ No suggestions from API analysis, using fallback")
                suggestions = self._generate_fallback_suggestions(session_state)
            
            print(f"✅ Generated {len(suggestions)} formatted suggestions")
            return suggestions[:4]  # Return top 4 suggestions
            
        except Exception as e:
            logger.error(f"Failed to format relaxation suggestions: {e}")
            print(f"❌ Suggestion formatting error: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_suggestions(session_state)

    def _generate_fallback_suggestions(self, session_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fallback suggestions when API fails."""
        suggestions = []
        
        keywords = session_state.get('keywords', [])
        if len(keywords) > 3:
            suggestions.append({
                'type': 'skill_relaxation',
                'title': 'Reduce Required Skills',
                'description': f'You have {len(keywords)} skills. Consider making some optional.',
                'impact': 'Could significantly increase results',
                'action': 'Make 2-3 skills optional instead of mandatory',
                'confidence': 0.8
            })
        
        min_exp = session_state.get('min_exp', 0)
        if min_exp > 0:
            suggestions.append({
                'type': 'experience_relaxation',
                'title': 'Lower Minimum Experience',
                'description': f'Consider candidates with {max(0, min_exp-2)}+ years experience',
                'impact': 'Could increase junior talent pool',
                'action': f'Reduce minimum from {min_exp} to {max(0, min_exp-2)} years',
                'confidence': 0.85
            })
        
        return suggestions

    def _create_relaxation_message(self, suggestions: List[Dict[str, Any]], 
                             relaxation_data: Dict[str, Any]) -> str:
        """Create user-friendly relaxation message."""
        if not suggestions:
            return "I analyzed your search criteria but couldn't generate specific relaxation suggestions at this time."
        
        # FIX: Proper None handling
        estimated_count = None
        if relaxation_data and isinstance(relaxation_data, dict):
            estimated_count = relaxation_data.get('approx_new_count')
        
        # Convert None to 0 for comparison
        if estimated_count is None:
            estimated_count = 0
            print(f"⚠️ estimated_count was None, set to 0")
        
        suggestion_count = len(suggestions)
        
        if estimated_count > 0:
            return f"""🔄 **Query Relaxation Analysis Complete**

    I found {suggestion_count} ways to potentially increase your candidate pool by ~{estimated_count:,} additional candidates.

    💡 **Top Recommendations:**
    {chr(10).join([f"• **{sugg['title']}**: {sugg['description']}" for sugg in suggestions[:3]])}

    🎯 **Next Steps:** Review the suggestions below and let me know which relaxation approach you'd like to try first!"""
        else:
            return f"""🔄 **Query Relaxation Analysis Complete**

    I've generated {suggestion_count} suggestions to help broaden your search and find more candidates.

    💡 **Recommendations:** Review the suggestions below to see which approach might work best for your hiring needs."""
