# Replace the content of resdex_agent/tools/search_tools.py

"""
Search-related tools for ResDex Agent.
"""

from typing import Dict, Any, List, Optional
import logging

# Since Google ADK doesn't have a separate Tool class in the same way,
# we'll create our own tool class that works with ADK
class Tool:
    """Base tool class for ResDex Agent tools."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from ..utils.api_client import api_client
from ..utils.data_processing import DataProcessor
from ..utils.db_manager import db_manager

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    """Tool for performing candidate searches."""
    
    def __init__(self, name: str = "search_tool"):
        super().__init__(name=name, description="Search for candidates based on filters")
        self.api_client = api_client
        self.db_manager = db_manager
        self.data_processor = DataProcessor()
    
    async def __call__(self, search_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute candidate search."""
        try:
            logger.info(f"Executing search with filters: {search_filters}")
            
            # Build search request
            request_payload = self.api_client.build_search_request(search_filters)
            
            # Execute search
            search_response = await self.api_client.search_candidates(request_payload)
            
            if not search_response["success"]:
                return {
                    "success": False,
                    "error": search_response["error"],
                    "candidates": [],
                    "total_count": 0
                }
            
            # Extract user IDs
            user_ids = self._extract_user_ids(search_response["data"])
            
            if not user_ids:
                return {
                    "success": True,
                    "candidates": [],
                    "total_count": search_response["total_count"],
                    "message": "No candidates found matching the criteria"
                }
            
            # Get detailed user information
            user_details = await self.api_client.get_user_details(user_ids[:20])
            
            # Get real names from database
            real_names = await self.db_manager.get_real_names(user_ids[:20])
            
            # Format candidate data
            candidates = []
            for user_data in user_details:
                user_id = user_data.get('basic', {}).get('userid')
                real_name = real_names.get(user_id) if user_id else None
                
                candidate = self.data_processor.format_candidate_data(user_data, real_name)
                if candidate:
                    candidates.append(candidate)
            
            return {
                "success": True,
                "candidates": candidates,
                "total_count": search_response["total_count"],
                "message": f"Found {len(candidates)} detailed profiles from {search_response['total_count']:,} total matches"
            }
            
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "candidates": [],
                "total_count": 0
            }
    
    def _extract_user_ids(self, search_data: Dict[str, Any]) -> List[str]:
        """Extract user IDs from search response."""
        user_ids = []
        
        try:
            if 'results' in search_data and isinstance(search_data['results'], list):
                for result in search_data['results']:
                    if isinstance(result, dict):
                        # Check for different possible user ID field names
                        for field in ['USERID', 'userid', 'userId', 'user_id']:
                            if field in result:
                                user_ids.append(str(result[field]))
                                break
        except Exception as e:
            logger.error(f"Error extracting user IDs: {e}")
        
        return user_ids