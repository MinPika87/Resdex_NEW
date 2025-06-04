"""
API client utilities for external service integration.
"""

import requests
import json
from typing import Dict, Any, List, Optional
import logging
from .constants import API_HEADERS, BASE_API_REQUEST, API_COOKIES
from ..config import config

logger = logging.getLogger(__name__)


class APIClient:
    """Client for external API interactions."""
    
    def __init__(self):
        self.search_api_url = config.api.search_api_url
        self.user_details_api_url = config.api.user_details_api_url
        self.location_api_url = config.api.location_api_url
    
    async def search_candidates(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Search for candidates using the search API."""
        try:
            response = requests.post(
                self.search_api_url,
                headers=API_HEADERS["search"],
                cookies=API_COOKIES["search"],
                json=request_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "total_count": data.get('totalcount', 0)
                }
            else:
                logger.error(f"Search API failed with status {response.status_code}")
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
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"User details API failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"User details API request failed: {e}")
            return []
    
    async def normalize_location(self, city: str) -> Optional[str]:
        """Get normalized location ID for a city."""
        try:
            payload = json.dumps({
                "location": [{"city": city}]
            })
            
            response = requests.post(
                self.location_api_url,
                headers=API_HEADERS["location"],
                data=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = eval(response.text)
                return str(result[0]['city']['globalId'])
            else:
                logger.warning(f"Location normalization failed for {city}")
                return None
                
        except Exception as e:
            logger.error(f"Location normalization error for {city}: {e}")
            return None
    
    def build_search_request(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Build search request from session state."""
        request_object = BASE_API_REQUEST.copy()
        
        # Process keywords
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
        
        # Update request object
        request_object.update({
            "anyKeywords": any_keywords,
            "allKeywords": all_keywords,
            "anyKeywordTags": ",".join(any_keyword_tags) if any_keyword_tags else "",
            "allKeywordTags": ",".join(all_keyword_tags) if all_keyword_tags else "",
            "min_exp": str(int(session_state.get('min_exp', 0))) if session_state.get('min_exp', 0) > 0 else "-1",
            "max_exp": str(int(session_state.get('max_exp', 0))) if session_state.get('max_exp', 0) > 0 else "-1",
            "min_ctc": str(session_state.get('min_salary', 0)) if session_state.get('min_salary', 0) > 0 else "0",
            "max_ctc": str(session_state.get('max_salary', 0)) if session_state.get('max_salary', 0) > 0 else "100"
        })
        
        return request_object


# Global API client instance
api_client = APIClient()