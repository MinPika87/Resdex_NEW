# resdex_agent/tools/facet_generation.py
"""
Facet Generation Tool for integrating with external facet generation API.
"""
#Credits : Akshat Jain( IIT Jodhpur, Co-Intern( Rahul Mittal Team, Infoedge, Noida))
from typing import Dict, Any, List, Optional
import logging
import requests
import asyncio

# Base tool class
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

logger = logging.getLogger(__name__)


class FacetGenerationTool(Tool):
    """Tool for generating facets using external API."""
    
    def __init__(self, name: str = "facet_generation_tool"):
        super().__init__(name=name, description="Generate facets from search results using external API")
        
        # API configuration
        self.api_url = "http://10.10.112.238:8004/generate"
        self.timeout = 90
        
        # Mapping for city names to IDs (from app.py)
        self.city_mapping = self._load_city_mapping()
        
        # Segment mapping
        self.segment_list = [
            "Finance", "BPO", "IT", "HR/Admin", "Sales & Marketing",
            "Misc", "Core Engineering", "Strategic & Top Management",
            "Health", "Purchase & Logistics", "BFSI Sales"
        ]
        
        # Notice period mapping
        self.notice_period_mapping = {
            "Any": 0,
            "0-15 days": 1,
            "1 months": 2,
            "2 months": 3,
            "3 months": 4,
            "more than 3 months": 5,
            "currently serving notice period": 6
        }
        
        # Days old mapping (fixed to use working values)
        self.daysold_mapping = {
            "1 day": 3650,
            "15 days": 3650,
            "1 month": 3650,
            "2 months": 3650,
            "3 months": 3650,
            "6 months": 3650,
            "1 year": 3650
        }
        
        print(f"🔧 FacetGenerationTool initialized with API: {self.api_url}")
    
    def _load_city_mapping(self) -> Dict[str, int]:
        """Load city mapping - simplified version for common cities."""
        # Simplified city mapping based on common cities
        return {
            "Bangalore": 1,
            "Mumbai": 2,
            "Delhi": 3,
            "Hyderabad": 4,
            "Chennai": 5,
            "Pune": 6,
            "Kolkata": 7,
            "Ahmedabad": 8,
            "Gurgaon": 9,
            "Noida": 10,
            "Bengaluru": 1,  # Alias for Bangalore
            "New Delhi": 3,  # Alias for Delhi
            # Add more mappings as needed
        }
    
    async def __call__(self, 
                      session_state: Dict[str, Any],
                      user_input: str = "",
                      memory_context: List[Dict[str, Any]] = None,
                      **kwargs) -> Dict[str, Any]:
        """Execute facet generation."""
        try:
            logger.info(f"Executing facet generation for session state: {session_state}")
            print(f"🔍 FACET GENERATION TOOL: Processing request")
            
            # Map session state to API payload
            payload = self._map_session_to_api_payload(session_state)
            
            print(f"📤 API Payload: {payload}")
            
            # Call the external API
            api_response = await self._call_facet_api(payload)
            
            if api_response["success"]:
                print(f"✅ Facet API call successful")
                
                # Process and clean the response
                processed_facets = self._process_api_response(api_response["data"])
                
                return {
                    "success": True,
                    "facets_data": processed_facets,
                    "api_response": api_response["data"],
                    "payload_used": payload,
                    "message": "Facets generated successfully"
                }
            else:
                print(f"❌ Facet API call failed: {api_response.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": api_response.get("error", "API call failed"),
                    "details": api_response.get("details", "No additional details")
                }
                
        except Exception as e:
            logger.error(f"Facet generation failed: {e}")
            print(f"❌ Facet generation error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred during facet generation"
            }
    
    def _map_session_to_api_payload(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Map ResDex session state to facet generation API payload."""
        try:
            print(f"🔄 MAPPING SESSION STATE TO API PAYLOAD")
            print(f"  - Input session state: {session_state}")
            
            # Extract and map cities
            city_names = session_state.get('current_cities', []) + session_state.get('preferred_cities', [])
            city_ids = []
            for city in city_names:
                city_id = self.city_mapping.get(city)
                if city_id:
                    city_ids.append(str(city_id))
                else:
                    # Use city name directly if no mapping found
                    city_ids.append(city)
            
            # Extract and process keywords
            keywords = session_state.get('keywords', [])
            # Remove mandatory markers (★) and clean keywords
            clean_keywords = []
            for keyword in keywords:
                clean_keyword = keyword.replace('★ ', '').strip()
                if clean_keyword:
                    clean_keywords.append(clean_keyword)
            
            # Determine query segment (default to IT for tech skills)
            query_segment = self._determine_query_segment(clean_keywords)
            
            # Extract experience and salary ranges
            min_exp = session_state.get('min_exp', 0)
            max_exp = session_state.get('max_exp', 10)
            min_ctc = session_state.get('min_salary', 0)
            max_ctc = session_state.get('max_salary', 15)
            
            # Get company ID (use default if not available)
            company_id = session_state.get('recruiter_company_id', 27117)  # Default to Accenture
            
            # Build the API payload matching the expected format
            api_payload = {
                "MINEXP": float(min_exp),
                "MAXEXP": float(max_exp),
                "MINCTC": float(min_ctc),
                "MAXCTC": float(max_ctc),
                "CITY": "~".join(city_ids),
                "PREF_LOC": "~".join(city_ids),  # Use same cities for preferred locations
                "NOTICE_PERIOD": "",  # Default empty
                "DAYSOLD": 3650,  # Use working value from constants
                "CID": int(company_id),
                "query_segment": query_segment,
                "combined": clean_keywords
            }
            
            print(f"  - Mapped payload: {api_payload}")
            
            return api_payload
            
        except Exception as e:
            logger.error(f"Error mapping session state to API payload: {e}")
            print(f"❌ Mapping error: {e}")
            # Return default payload
            return {
                "MINEXP": 0.0,
                "MAXEXP": 10.0,
                "MINCTC": 0.0,
                "MAXCTC": 15.0,
                "CITY": "",
                "PREF_LOC": "",
                "NOTICE_PERIOD": "",
                "DAYSOLD": 3650,
                "CID": 27117,
                "query_segment": "IT",
                "combined": []
            }
    
    def _determine_query_segment(self, keywords: List[str]) -> str:
        """Determine query segment based on keywords."""
        try:
            # Define keyword patterns for each segment
            segment_patterns = {
                "IT": ["python", "java", "javascript", "react", "angular", "node", "sql", 
                       "aws", "docker", "kubernetes", "devops", "software", "developer", 
                       "engineer", "programming", "coding", "tech", "technical"],
                "Finance": ["finance", "accounting", "audit", "risk", "investment", 
                           "banking", "financial", "analyst", "treasury", "compliance"],
                "BPO": ["bpo", "call center", "customer service", "support", "helpdesk"],
                "HR/Admin": ["hr", "human resources", "admin", "recruitment", "hiring"],
                "Sales & Marketing": ["sales", "marketing", "business development", "account"],
                "Core Engineering": ["mechanical", "civil", "electrical", "chemical", "manufacturing"]
            }
            
            # Check keywords against patterns
            keywords_lower = [k.lower() for k in keywords]
            
            for segment, patterns in segment_patterns.items():
                if any(pattern in " ".join(keywords_lower) for pattern in patterns):
                    return segment
            
            # Default to IT if no match
            return "IT"
            
        except Exception as e:
            logger.error(f"Error determining query segment: {e}")
            return "IT"
    
    async def _call_facet_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call the external facet generation API - FIXED to match working version."""
        try:
            print(f"📡 CALLING FACET API: {self.api_url}")
            
            request_body = {
                "data": payload,
                "num_results": 5,
                "prefiltering": False,
                "llm_clean": False
            }
            
            print(f"  - Request body: {request_body}")
            
            def make_request():
                return requests.post(
                    self.api_url,
                    json=request_body,  # Use json parameter instead of data + headers
                    timeout=self.timeout
                )
            
            # Make async HTTP request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, make_request)
            
            print(f"  - Response status: {response.status_code}")
            
            try:
                response.raise_for_status()
                
                data = response.json()
                print(f"  - Response data keys: {list(data.keys())}")
                
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status_code
                }
                
            except requests.exceptions.HTTPError as http_err:
                print(f"  - HTTP Error: {http_err}")
                print(f"  - Response text: {response.text[:500]}")
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {str(http_err)}",
                    "details": response.text[:500],
                    "status_code": response.status_code,
                    "user_message": f"Facet generation failed (HTTP {response.status_code}). Please try again."
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ API TIMEOUT after {self.timeout} seconds")
            return {
                "success": False,
                "error": "Facet generation API timeout",
                "details": f"Server did not respond within {self.timeout} seconds",
                "user_message": "Facet generation is taking too long. Please try again later."
            }
        except requests.exceptions.ConnectionError:
            print(f"🔌 CONNECTION ERROR to {self.api_url}")
            return {
                "success": False,
                "error": "Failed to connect to facet generation API",
                "details": f"Could not connect to {self.api_url}",
                "user_message": "Facet generation service is currently unavailable."
            }
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred during API call",
                "user_message": "An unexpected error occurred while generating facets."
            }

    
    def _process_api_response(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean the API response."""
        try:
            print(f"🔧 PROCESSING API RESPONSE")
            print(f"  - Raw data keys: {list(api_data.keys())}")
            
            # Extract result_1 and result_2 from the API response
            processed_data = {}
            
            # Primary facets (result_1)
            if "result_1" in api_data:
                processed_data["result_1"] = api_data["result_1"]
                print(f"  - result_1 categories: {len(api_data['result_1'])}")
            
            # Secondary facets (result_2)
            if "result_2" in api_data:
                processed_data["result_2"] = api_data["result_2"]
                print(f"  - result_2 categories: {len(api_data['result_2'])}")
            
            # Clean and format the facets
            cleaned_data = self._clean_facets_data(processed_data)
            
            print(f"  - Processed data keys: {list(cleaned_data.keys())}")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error processing API response: {e}")
            print(f"❌ Processing error: {e}")
            return {"result_1": {}, "result_2": {}}
    
    def _clean_facets_data(self, facets_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and format facets data for better presentation."""
        try:
            cleaned = {}
            
            for result_key, result_data in facets_data.items():
                if isinstance(result_data, dict):
                    cleaned[result_key] = {}
                    
                    for category, items in result_data.items():
                        if isinstance(items, dict):
                            # Clean category name
                            clean_category = category.replace("_", " ").title()
                            cleaned[result_key][clean_category] = items
                        else:
                            cleaned[result_key][category] = items
                else:
                    cleaned[result_key] = result_data
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning facets data: {e}")
            return facets_data
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check the status of the facet generation API."""
        try:
            response = requests.get(f"{self.api_url.replace('/generate', '')}/", timeout=5)
            
            if response.status_code == 200:
                return {
                    "available": True,
                    "status": "healthy",
                    "api_url": self.api_url
                }
            else:
                return {
                    "available": False,
                    "status": f"unhealthy (status {response.status_code})",
                    "api_url": self.api_url
                }
                
        except Exception as e:
            return {
                "available": False,
                "status": f"error: {str(e)}",
                "api_url": self.api_url
            }