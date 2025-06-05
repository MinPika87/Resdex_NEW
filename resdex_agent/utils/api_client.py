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
    
    def build_search_request(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Build the API request object based on current session state"""
        print(f"🔧 Building search request with session state...")
        print(f"🔹 Keywords: {session_state.get('keywords', [])}")
        print(f"🔹 Experience: {session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)}")
        print(f"🔹 Salary: {session_state.get('min_salary', 0)}-{session_state.get('max_salary', 15)}")
        print(f"🔹 Current Cities: {session_state.get('current_cities', [])}")
        print(f"🔹 Preferred Cities: {session_state.get('preferred_cities', [])}")
        print(f"🔹 Company: {session_state.get('recruiter_company', '')}")
        
        # Get city IDs using working version logic
        city_ids = []
        for city in session_state.get('current_cities', []):
            city_id = self.get_normalized_location_id(city)
            if city_id:
                city_ids.append(city_id)
            else:
                # Fallback: add city name directly
                city_ids.append(city)
        
        # Get preferred city IDs
        pref_city_ids = []
        for city in session_state.get('preferred_cities', []):
            city_id = self.get_normalized_location_id(city)
            if city_id:
                pref_city_ids.append(city_id)
            else:
                # Fallback: add city name directly
                pref_city_ids.append(city)
        
        # Process keywords using working version logic
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
                    "type": None,
                    "globalName": None
                })
                all_keyword_tags.append(clean_keyword)
            else:
                any_keywords.append({
                    "key": None,
                    "value": keyword,
                    "type": None,
                    "globalName": None
                })
                any_keyword_tags.append(keyword)
        
        # Create base request copy
        request_object = BASE_API_REQUEST.copy()
        
        # Update with session state values using working version logic
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
            "max_exp": str(int(session_state.get('max_exp', 0))) if session_state.get('max_exp', 0) > 0 else "-1",
            "min_ctc": str(session_state.get('min_salary', 0)) if session_state.get('min_salary', 0) > 0 else "0",
            "max_ctc": str(session_state.get('max_salary', 0)) if session_state.get('max_salary', 0) > 0 else "15.0",
            "days_old": self.get_days_old_mapping(session_state.get('active_days', '1 month')),
            "recruiter_company": session_state.get('recruiter_company', '')
        })
        
        print(f"Built search request with {len(any_keyword_tags)} optional and {len(all_keyword_tags)} mandatory keywords")
        
        # Print the final request object for debugging
        print(f"📤 SEARCH REQUEST PAYLOAD: {json.dumps(request_object, indent=2)}")
        
        return request_object


# Global API client instance
api_client = APIClient()