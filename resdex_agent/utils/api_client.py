# Replace resdex_agent/utils/api_client.py with this fixed version

"""
API client utilities for external service integration.
"""

import requests
import json
from typing import Dict, Any, List, Optional
import logging
from .constants import API_HEADERS, BASE_API_REQUEST, API_COOKIES, ACTIVE_PERIOD_MAPPING
from ..config import config

logger = logging.getLogger(__name__)


class APIClient:
    """Client for external API interactions."""
    
    def __init__(self):
        self.search_api_url = config.api.search_api_url
        self.user_details_api_url = config.api.user_details_api_url
        self.location_api_url = config.api.location_api_url
    
    def get_normalized_location_id(self, city):
        """Get normalized location ID for a city"""
        payload = json.dumps({
            "location": [
                {
                    "city": city
                }
            ]
        })
        
        try:
            response = requests.request("POST", self.location_api_url, headers=API_HEADERS["location"], data=payload)
            loc_id = eval(response.text)[0]['city']['globalId']
            return str(loc_id)
        except Exception as e:
            print(f"Error getting location ID for {city}: {e}")
            return None
    
    def get_days_old_mapping(self, active_period):
        """Convert active period to days_old value"""
        return ACTIVE_PERIOD_MAPPING.get(active_period, "3650")
    
    async def search_candidates(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Search for candidates using the search API."""
        try:
            print(f"🔍 CALLING SEARCH API...")
            print(f"  - URL: {self.search_api_url}")
            print(f"  - Headers: {API_HEADERS['search']}")
            print(f"  - Cookies: {API_COOKIES['search']}")
            print(f"  - Payload size: {len(str(request_payload))} characters")
            
            emp_key = request_payload.get('emp_key', '')
            emp_key_globalid = request_payload.get('emp_key_globalid', {})
            print(f"🏢 emp_key: '{emp_key}'")
            print(f"🏢 emp_key_globalid: {emp_key_globalid}")
            
            response = requests.post(
                self.search_api_url,
                headers=API_HEADERS["search"],
                cookies=API_COOKIES["search"],
                json=request_payload,
                timeout=30
            )           
            print(f"📡 SEARCH API RESPONSE:")
            print(f"  - Status Code: {response.status_code}")
            print(f"  - Response size: {len(response.text)} characters")
            print(f"  - Content type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 PARSED JSON RESPONSE:")
                print(f"  - Type: {type(data)}")
                print(f"  - Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                print(f"  - Total count: {data.get('totalcount', 0)}")
                print(f"  - Results type: {type(data.get('results', []))}")
                print(f"  - Results length: {len(data.get('results', []))}")
                
                return {
                    "success": True,
                    "data": data,
                    "total_count": data.get('totalcount', 0)
                }
            else:
                logger.error(f"Search API failed with status {response.status_code}")
                print(f"❌ Error response: {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "data": None
                }
                
        except Exception as e:
            logger.error(f"Search API request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def get_user_details(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed user information."""
        print(f"🔍 Calling user details API with IDs: {user_ids}")
        
        try:
            json_data = {
                'identifier': 'userId',
                'ids': user_ids,
                'sectionNames': ["employment", "education", "skills", "basic"],
                'visibilityFlag': ['a', 'b']
            }
            
            response = requests.post(
                self.user_details_api_url,
                headers=API_HEADERS["user_details"],
                cookies=API_COOKIES["user_details"],
                json=json_data,
                timeout=30
            )
            
            print(f"🔍 User details API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ User details API success: Got {len(result) if isinstance(result, list) else 'non-list'} results")
                return result
            else:
                logger.error(f"User details API failed with status {response.status_code}")
                print(f"🔍 Response content: {response.text[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"User details API request failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def normalize_location(self, city: str) -> Optional[str]:
        """Get normalized location ID for a city."""
        return self.get_normalized_location_id(city)
    # Update the build_search_request method in api_client.py

    def build_search_request(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Build the API request object using company normalization API."""
        print(f"🔧 Building search request with session state...")
        print(f"🔹 Keywords: {session_state.get('keywords', [])}")
        print(f"🔹 Experience: {session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)}")
        print(f"🔹 Salary: {session_state.get('min_salary', 0)}-{session_state.get('max_salary', 15)}")
        print(f"🔹 Current Cities: {session_state.get('current_cities', [])}")
        print(f"🔹 Preferred Cities: {session_state.get('preferred_cities', [])}")
        print(f"🔹 Recruiter Company: {session_state.get('recruiter_company', '')}")
        print(f"🔹 Target Companies: {session_state.get('target_companies', [])}")
        
        # Get city IDs (existing working logic)
        city_ids = []
        for city in session_state.get('current_cities', []):
            city_id = self.get_normalized_location_id(city)
            if city_id:
                city_ids.append(city_id)
            else:
                city_ids.append(city)
        
        pref_city_ids = []
        for city in session_state.get('preferred_cities', []):
            city_id = self.get_normalized_location_id(city)
            if city_id:
                pref_city_ids.append(city_id)
            else:
                pref_city_ids.append(city)
        
        # NEW: Get company IDs using normalization API
        target_companies = session_state.get('target_companies', [])
        emp_key_globalid = {}
        
        if target_companies:
            from ..tools.company_tools import CompanyNormalizationTool
            company_tool = CompanyNormalizationTool()
            
            print(f"🏢 Getting company IDs for: {target_companies}")
            emp_key_globalid = company_tool.get_company_mapping(target_companies)
        
        print(f"🏢 COMPANY FILTER:")
        print(f"  - emp_key_globalid: {emp_key_globalid}")
        
        # Process keywords (existing working logic)
        any_keywords = []
        all_keywords = []
        any_keyword_tags = []
        all_keyword_tags = []
        
        for keyword in session_state.get('keywords', []):
            if keyword.startswith('★ '):
                clean_keyword = keyword.replace('★ ', '')
                all_keywords.append({
                    "key": None,
                    "value": clean_keyword,
                    "type": "skill",
                    "globalName": clean_keyword
                })
                all_keyword_tags.append(clean_keyword)
            else:
                any_keywords.append({
                    "key": None,
                    "value": keyword,
                    "type": "skill",
                    "globalName": keyword
                })
                any_keyword_tags.append(keyword)
        
        # Create base request copy
        request_object = BASE_API_REQUEST.copy()
        
        # Calculate search count
        max_candidates = session_state.get('max_candidates', 100)
        api_search_count = max(80, max_candidates)
        
        # Update with session state values
        request_object.update({
            "city": city_ids,
            "pref_loc": pref_city_ids,
            "anyKeywords": any_keywords,
            "allKeywords": all_keywords,
            "ez_keyword_any": any_keywords,
            "ez_keyword_all": all_keywords,
            "anyKeywordTags": ",".join(any_keyword_tags) if any_keyword_tags else "",
            "allKeywordTags": ",".join(all_keyword_tags) if all_keyword_tags else "",
            "min_exp": str(int(session_state.get('min_exp', 0))) if session_state.get('min_exp', 0) > 0 else "-1",
            "max_exp": str(int(session_state.get('max_exp', 10))) if session_state.get('max_exp', 10) < 50 else "-1",
            "min_ctc": str(session_state.get('min_salary', 0)) if session_state.get('min_salary', 0) > 0 else "0",
            "max_ctc": str(session_state.get('max_salary', 15)) if session_state.get('max_salary', 15) < 100 else "100",
            
            # Company filter using API results
            "emp_key_globalid": emp_key_globalid,
            
            # Search counts
            "SEARCH_COUNT": api_search_count,
            "PAGE_LIMIT": api_search_count
        })
        
        print(f"🔧 FINAL API REQUEST:")
        print(f"  - SEARCH_COUNT: {request_object['SEARCH_COUNT']}")
        print(f"  - emp_key_globalid: {request_object['emp_key_globalid']}")
        print(f"  - anyKeywordTags: '{request_object['anyKeywordTags']}'")
        print(f"  - allKeywordTags: '{request_object['allKeywordTags']}'")
        
        return request_object


# Global API client instance
api_client = APIClient()