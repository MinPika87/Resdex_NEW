# Replace resdex_agent/tools/search_tools.py with this fixed version

"""
Search-related tools for ResDex Agent.
"""

from typing import Dict, Any, List, Optional
import logging

# Create a simple Tool base class
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
            print(f"🔍 SEARCH TOOL DEBUG: Starting search with filters: {search_filters}")
            
            # Build search request using the API client
            request_payload = self.api_client.build_search_request(search_filters)
            
            # Execute search
            search_response = await self.api_client.search_candidates(request_payload)
            
            print(f"📥 SEARCH API RESPONSE: Success={search_response['success']}")
            
            if not search_response["success"]:
                return {
                    "success": False,
                    "error": search_response["error"],
                    "candidates": [],
                    "total_count": 0
                }
            
            # Process the search response data
            search_data = search_response["data"]
            total_count = search_response["total_count"]
            
            print(f"📊 RAW API DATA STRUCTURE:")
            print(f"  - Type: {type(search_data)}")
            print(f"  - Keys: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dict'}")
            if isinstance(search_data, dict) and 'results' in search_data:
                print(f"  - Results type: {type(search_data['results'])}")
                print(f"  - Results count: {len(search_data['results'])}")
            print(f"  - Total count: {total_count}")
            
            # Extract user IDs
            user_ids = self._extract_user_ids_from_search_response(search_data)
            
            print(f"👥 EXTRACTED USER IDS: {len(user_ids)} users")
            
            if not user_ids:
                return {
                    "success": True,
                    "candidates": [],
                    "total_count": total_count,
                    "message": "No candidates found matching the criteria"
                }
            
            # Limit to first 20 for detailed processing
            user_ids = user_ids[:20]
            print(f"🔍 Processing first {len(user_ids)} user IDs for detailed profiles")
            
            # Get detailed user information
            user_details = await self.api_client.get_user_details(user_ids)
            
            if not user_details:
                return {
                    "success": True,
                    "candidates": [],
                    "total_count": total_count,
                    "message": f"Found {total_count:,} matches but failed to fetch candidate details"
                }
            
            # Get real names from database
            real_names = await self.db_manager.get_real_names(user_ids)
            
            # Format candidate data
            candidates = []
            for user_data in user_details:
                user_id = None
                if 'basic' in user_data and 'userid' in user_data['basic']:
                    user_id = user_data['basic']['userid']
                
                real_name = real_names.get(user_id) if user_id else None
                
                candidate = self.data_processor.format_candidate_data(user_data, real_name)
                if candidate:
                    candidates.append(candidate)
            
            print(f"Search completed: {len(candidates) > 0}, candidates: {len(candidates)}")
            
            return {
                "success": True,
                "candidates": candidates,
                "total_count": total_count,
                "message": f"Found {len(candidates)} detailed profiles from {total_count:,} total matches"
            }
            
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "candidates": [],
                "total_count": 0
            }
    
    def _extract_user_ids_from_search_response(self, search_data: Dict[str, Any]) -> List[str]:
        """Extract user IDs from the search API response using working version logic"""
        user_ids = []
        
        try:
            print(f"🔍 EXTRACTING USER IDS from search data...")
            print(f"  - Search data type: {type(search_data)}")
            print(f"  - Search data keys: {list(search_data.keys()) if isinstance(search_data, dict) else 'Not a dict'}")
            
            if 'results' in search_data and isinstance(search_data['results'], list):
                results = search_data['results']
                print(f"  - Results type: {type(results)}")
                print(f"  - Results length: {len(results)}")
                
                for idx, result in enumerate(results):
                    if isinstance(result, dict):
                        # Check for different possible user ID field names
                        user_id = None
                        for field in ['USERID', 'userid', 'userId', 'user_id']:
                            if field in result:
                                user_id = str(result[field])
                                user_ids.append(user_id)
                                if idx < 3:  # Debug first few
                                    print(f"  - Found {field}: {user_id}")
                                break
                        
                        if not user_id and idx < 3:
                            print(f"  - No user ID field found in result {idx}: {list(result.keys())}")
                    else:
                        print(f"  - Result {idx} is not a dict: {type(result)}")
            else:
                print(f"  - No 'results' key found or results is not a list")
                if isinstance(search_data, dict):
                    print(f"  - Available keys: {list(search_data.keys())}")
        
        except Exception as e:
            logger.error(f"Error extracting user IDs: {e}")
            print(f"❌ Error extracting user IDs: {e}")
        
        print(f"🎯 EXTRACTION COMPLETE: Found {len(user_ids)} user IDs")
        return user_ids