"""
Location analysis tools using Qwen LLM for intelligent location matching.
"""

from typing import Dict, Any, List, Optional
import logging

# Simple Tool base class
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

logger = logging.getLogger(__name__)


class LocationAnalysisTool(Tool):
    """Tool for intelligent location analysis using Qwen LLM."""
    
    def __init__(self, name: str = "location_analysis_tool"):
        super().__init__(name=name, description="Analyze and find similar locations using AI")
        
        # Initialize LLM tool for location analysis
        from ..tools.llm_tools import LLMTool
        self.llm_tool = LLMTool("location_llm_tool")
    
    async def __call__(self, 
                      base_location: str, 
                      analysis_type: str = "similar",
                      radius_km: Optional[int] = None,
                      criteria: Optional[str] = None) -> Dict[str, Any]:
        """Execute location analysis using Qwen LLM."""
        try:
            logger.info(f"Location analysis: {analysis_type} locations for {base_location}")
            print(f"🗺️ LOCATION ANALYSIS: Finding {analysis_type} locations for {base_location}")
            
            if analysis_type == "similar":
                return await self._find_similar_locations(base_location, criteria)
            elif analysis_type == "nearby":
                return await self._find_nearby_locations(base_location, radius_km)
            elif analysis_type == "metro_area":
                return await self._find_metro_area_locations(base_location)
            elif analysis_type == "industry_hubs":
                return await self._find_industry_hubs(base_location, criteria)
            else:
                return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}
                
        except Exception as e:
            logger.error(f"Location analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Replace the _find_similar_locations method in LocationAnalysisTool:

    async def _find_similar_locations(self, base_location: str, criteria: Optional[str] = None) -> Dict[str, Any]:
        """Find locations similar to the base location using enhanced LLM analysis."""
        
        # Enhanced prompt with better context and examples
        prompt = f"""You are a location analysis expert for Indian job markets. Find cities similar to {base_location} for candidate search.

    Base Location: {base_location}
    Analysis Criteria: {criteria or "economic similarity, job market, tech industry presence, cost of living"}

    CONTEXT: This is for a job recruitment platform. Users want to expand their candidate search to similar cities that would have comparable talent pools.

    Consider these factors in priority order:
    1. Tech industry presence and job market size
    2. Economic development level and opportunities  
    3. Educational institutions (IITs, NITs, tech colleges)
    4. Transportation connectivity and accessibility
    5. Cost of living and salary expectations
    6. Infrastructure quality for businesses

    COMPREHENSIVE INDIAN CITIES DATABASE:
    **Tier 1 (Major Tech Hubs):** Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Pune
    **Tier 1.5 (Emerging Tech):** Ahmedabad, Kochi, Coimbatore, Indore, Jaipur
    **Tier 2 (Growing Markets):** Surat, Lucknow, Kanpur, Nagpur, Bhopal, Visakhapatnam, Vadodara
    **Tier 3 (Developing):** Agra, Nashik, Faridabad, Meerut, Rajkot, Varanasi, Amritsar
    **Satellite Cities:** Gurgaon, Noida, Thane, Navi Mumbai, Greater Noida, Ghaziabad
    **South Tech Corridor:** Bangalore, Chennai, Hyderabad, Kochi, Coimbatore, Mysore
    **West Corridor:** Mumbai, Pune, Ahmedabad, Surat, Nashik, Vadodara
    **North Corridor:** Delhi, Noida, Gurgaon, Jaipur, Chandigarh, Lucknow

    EXAMPLES OF GOOD MATCHES:
    - Noida → Delhi, Gurgaon, Greater Noida (NCR region, similar tech focus)
    - Bangalore → Hyderabad, Chennai, Pune (major tech hubs with similar talent)
    - Mumbai → Pune, Thane, Ahmedabad (western corridor, financial/tech centers)

    Task: Find 4-6 cities most similar to {base_location} that would have comparable candidate pools for tech recruitment.

    CRITICAL: Return ONLY valid JSON. No explanations, no extra text.

    Response format:
    {{
        "base_location": "{base_location}",
        "similar_locations": ["City1", "City2", "City3", "City4"],
        "reasoning": {{
            "City1": "specific reason why similar (max 20 words)",
            "City2": "specific reason why similar (max 20 words)",
            "City3": "specific reason why similar (max 20 words)",
            "City4": "specific reason why similar (max 20 words)"
        }},
        "similarity_score": 0.85,
        "analysis_factors": ["tech_industry", "job_market_size", "educational_institutions", "economic_level"]
    }}"""

        try:
            llm_result = await self.llm_tool._call_llm_direct(prompt, task="location_analysis")
            
            if llm_result["success"]:
                location_data = llm_result.get("parsed_response")
                
                if location_data and "similar_locations" in location_data:
                    similar_locations = location_data["similar_locations"]
                    reasoning = location_data.get("reasoning", {})
                    
                    print(f"🎯 LLM FOUND SIMILAR LOCATIONS: {similar_locations}")
                    for loc, reason in reasoning.items():
                        print(f"   • {loc}: {reason}")
                    
                    return {
                        "success": True,
                        "base_location": base_location,
                        "similar_locations": similar_locations,
                        "reasoning": reasoning,
                        "similarity_score": location_data.get("similarity_score", 0.8),
                        "analysis_factors": location_data.get("analysis_factors", []),
                        "method": "enhanced_llm_analysis",
                        "message": f"Found {len(similar_locations)} similar locations using AI analysis"
                    }
                else:
                    print("⚠️ LLM returned invalid location data, using fallback")
                    return await self._fallback_location_mapping(base_location)
            else:
                print("⚠️ LLM analysis failed, using fallback")
                return await self._fallback_location_mapping(base_location)
                
        except Exception as e:
            logger.error(f"Enhanced LLM location analysis failed: {e}")
            return await self._fallback_location_mapping(base_location)
    
    # In LocationAnalysisTool._find_nearby_locations method, fix the LLM call:

    async def _find_nearby_locations(self, base_location: str, radius_km: Optional[int] = None) -> Dict[str, Any]:    
        radius = radius_km or 200  # Default 200km radius
        
        prompt = f"""You are a geography expert for India. Find cities within approximately {radius} km of {base_location}.

    Base Location: {base_location}
    Search Radius: {radius} km

    Consider:
    1. Actual geographical distance
    2. Transportation connectivity (road/rail)
    3. Economic connectivity
    4. Commute feasibility for professionals

    Task: Find cities within {radius} km radius that are relevant for job search.

    CRITICAL: Return ONLY valid JSON. No explanations, no extra text, no <think> tags.

    Response format (JSON only):
    {{
        "base_location": "{base_location}",
        "radius_km": {radius},
        "nearby_locations": [
            {{"city": "City1", "distance_km": 50, "connectivity": "excellent"}},
            {{"city": "City2", "distance_km": 120, "connectivity": "good"}},
            {{"city": "City3", "distance_km": 180, "connectivity": "moderate"}}
        ],
        "total_found": 3
    }}"""

        try:
            llm_result = await self.llm_tool._call_llm_direct(prompt, task="location_analysis")
            
            print(f"🔍 LLM RESULT: {llm_result}")
            
            if llm_result["success"]:
                location_data = llm_result.get("parsed_response")
                
                # ✅ FIX 1: Try multiple parsing methods
                if not location_data and "response_text" in llm_result:
                    try:
                        import json
                        response_text = llm_result["response_text"].strip()
                        
                        # Handle case where response_text contains just the array part
                        if response_text.startswith('[') and response_text.endswith(']'):
                            # LLM returned just the nearby_locations array
                            nearby_array = json.loads(response_text)
                            location_data = {
                                "base_location": base_location,
                                "nearby_locations": nearby_array,
                                "total_found": len(nearby_array)
                            }
                            print(f"🔧 PARSED ARRAY FORMAT: {len(nearby_array)} cities")
                        else:
                            # Try parsing as full object
                            location_data = json.loads(response_text)
                            print(f"🔧 PARSED OBJECT FORMAT: {location_data}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Manual JSON parse failed: {e}")
                        location_data = None
                
                # ✅ FIX 2: Enhanced validation logic
                nearby_locations = []
                
                if location_data:
                    print(f"🔍 VALIDATING LOCATION DATA: {location_data}")
                    
                    # Check for nearby_locations field
                    if "nearby_locations" in location_data and isinstance(location_data["nearby_locations"], list):
                        nearby_data = location_data["nearby_locations"]
                        
                        for loc in nearby_data:
                            if isinstance(loc, dict) and "city" in loc:
                                nearby_locations.append(loc["city"])
                            elif isinstance(loc, str):
                                nearby_locations.append(loc)
                        
                        print(f"🎯 EXTRACTED {len(nearby_locations)} CITIES: {nearby_locations}")
                    
                    # ✅ FIX 3: Check if we got valid cities
                    if len(nearby_locations) > 0:
                        print(f"✅ VALIDATION SUCCESS: Found {len(nearby_locations)} cities")
                        
                        return {
                            "success": True,
                            "base_location": base_location,
                            "nearby_locations": nearby_locations,
                            "detailed_locations": location_data.get("nearby_locations", []),
                            "radius_km": radius,
                            "method": "enhanced_llm_geographical_analysis",
                            "message": f"Found {len(nearby_locations)} locations within {radius}km",
                            "raw_data": location_data  # For debugging
                        }
                    else:
                        print(f"❌ VALIDATION FAILED: No valid cities extracted from {location_data}")
                else:
                    print("❌ No valid location_data after all parsing attempts")
            else:
                print(f"❌ LLM call failed: {llm_result}")
            
            # Fallback
            print("⚠️ Using fallback mapping")
            return await self._fallback_nearby_mapping(base_location, radius)
                        
        except Exception as e:
            logger.error(f"Nearby location analysis failed: {e}")
            print(f"❌ Location analysis exception: {e}")
            import traceback
            traceback.print_exc()
            return await self._fallback_nearby_mapping(base_location, radius)
    
    async def _find_metro_area_locations(self, base_location: str) -> Dict[str, Any]:
        """Find metropolitan area locations using Qwen LLM."""
        
        prompt = f"""You are an urban planning expert for India. Find all cities/areas that are part of the {base_location} metropolitan region.

Base Location: {base_location}

Consider:
1. Official metropolitan area boundaries
2. Satellite cities and suburbs
3. Industrial corridors and townships  
4. Areas with economic integration
5. Daily commute feasibility

Task: Find all cities/areas in the greater {base_location} metropolitan region.

Response format (JSON only):
{{
    "base_location": "{base_location}",
    "metro_area_locations": ["Area1", "Area2", "Area3"],
    "metro_type": "major_metro|metro|urban_agglomeration",
    "total_population_millions": 12.5
}}

Return ONLY the JSON response."""

        try:
            llm_result = await self.llm_tool._call_llm_direct(prompt, task="metro_area_analysis")
            
            if llm_result["success"]:
                location_data = llm_result.get("parsed_response")
                
                if location_data and "metro_area_locations" in location_data:
                    metro_locations = location_data["metro_area_locations"]
                    
                    print(f"🏙️ LLM FOUND METRO AREA: {metro_locations}")
                    
                    return {
                        "success": True,
                        "base_location": base_location,
                        "metro_area_locations": metro_locations,
                        "metro_type": location_data.get("metro_type", "metro"),
                        "method": "llm_metro_analysis",
                        "message": f"Found {len(metro_locations)} areas in {base_location} metro region"
                    }
                    
        except Exception as e:
            logger.error(f"Metro area analysis failed: {e}")
        
        # Fallback for metro areas
        return await self._fallback_metro_mapping(base_location)
    
    async def _find_industry_hubs(self, base_location: str, industry: Optional[str] = None) -> Dict[str, Any]:
        """Find industry-specific hub locations using Qwen LLM."""
        
        industry_focus = industry or "technology and software"
        
        prompt = f"""You are an industry analysis expert for India. Find cities with similar {industry_focus} industry presence as {base_location}.

Base Location: {base_location}
Industry Focus: {industry_focus}

Consider:
1. Number of tech companies/startups
2. IT parks and special economic zones
3. Educational institutions (IITs, NITs, tech colleges)
4. Government tech initiatives
5. Talent pool availability
6. Industry ecosystem maturity

Task: Find cities with strong {industry_focus} industry similar to {base_location}.

Response format (JSON only):
{{
    "base_location": "{base_location}",
    "industry_focus": "{industry_focus}",
    "industry_hubs": [
        {{"city": "City1", "industry_strength": "excellent", "major_companies": ["Company1", "Company2"]}},
        {{"city": "City2", "industry_strength": "good", "major_companies": ["Company3", "Company4"]}}
    ],
    "hub_ranking": ["City1", "City2", "City3"]
}}

Return ONLY the JSON response."""

        try:
            llm_result = await self.llm_tool._call_llm_direct(prompt, task="industry_hub_analysis")
            
            if llm_result["success"]:
                location_data = llm_result.get("parsed_response")
                
                if location_data and "industry_hubs" in location_data:
                    hub_cities = [hub["city"] for hub in location_data["industry_hubs"]]
                    
                    print(f"🏭 LLM FOUND INDUSTRY HUBS: {hub_cities}")
                    
                    return {
                        "success": True,
                        "base_location": base_location,
                        "industry_hubs": hub_cities,
                        "detailed_hubs": location_data["industry_hubs"],
                        "industry_focus": industry_focus,
                        "method": "llm_industry_analysis",
                        "message": f"Found {len(hub_cities)} {industry_focus} hubs similar to {base_location}"
                    }
                    
        except Exception as e:
            logger.error(f"Industry hub analysis failed: {e}")
        
        # Fallback for industry hubs
        return await self._fallback_industry_mapping(base_location, industry_focus)
    
    async def _fallback_location_mapping(self, base_location: str) -> Dict[str, Any]:
        """Enhanced fallback with curated location mappings."""
        
        # More comprehensive location mappings
        location_mapping = {
            # Tier 1 Cities
            "Mumbai": {
                "similar": ["Pune", "Thane", "Navi Mumbai", "Nashik", "Aurangabad"],
                "reasoning": {"Pune": "Major tech hub in Maharashtra", "Thane": "Part of Mumbai metro", "Navi Mumbai": "Planned satellite city", "Nashik": "Growing IT sector"}
            },
            "Bangalore": {
                "similar": ["Hyderabad", "Chennai", "Mysore", "Coimbatore", "Hubli"],
                "reasoning": {"Hyderabad": "Major tech hub", "Chennai": "South India IT center", "Mysore": "Emerging tech city", "Coimbatore": "Industrial center"}
            },
            "Delhi": {
                "similar": ["Gurgaon", "Noida", "Faridabad", "Ghaziabad", "Chandigarh"],
                "reasoning": {"Gurgaon": "Financial and tech hub", "Noida": "IT and media center", "Chandigarh": "Planned city"}
            },
            "Hyderabad": {
                "similar": ["Bangalore", "Chennai", "Vijayawada", "Visakhapatnam", "Warangal"],
                "reasoning": {"Bangalore": "Silicon Valley of India", "Chennai": "Detroit of India", "Vijayawada": "Commercial center"}
            },
            "Chennai": {
                "similar": ["Bangalore", "Hyderabad", "Coimbatore", "Madurai", "Trichy"],
                "reasoning": {"Bangalore": "Tech ecosystem", "Coimbatore": "Textile and IT hub", "Madurai": "Educational center"}
            },
            "Pune": {
                "similar": ["Mumbai", "Nashik", "Aurangabad", "Kolhapur", "Satara"],
                "reasoning": {"Mumbai": "Financial capital", "Nashik": "Wine country and IT", "Aurangabad": "Industrial center"}
            },
            
            # Tier 2 Cities
            "Jaipur": {
                "similar": ["Indore", "Bhopal", "Udaipur", "Kota", "Ajmer"],
                "reasoning": {"Indore": "Commercial center of MP", "Bhopal": "State capital", "Kota": "Educational hub"}
            },
            "Indore": {
                "similar": ["Jaipur", "Bhopal", "Nagpur", "Surat", "Vadodara"],
                "reasoning": {"Jaipur": "Pink city with IT growth", "Bhopal": "State capital", "Nagpur": "Geographical center"}
            },
            "Kochi": {
                "similar": ["Thiruvananthapuram", "Kozhikode", "Coimbatore", "Mangalore", "Mysore"],
                "reasoning": {"Thiruvananthapuram": "IT hub of Kerala", "Coimbatore": "Industrial city", "Mangalore": "Port city"}
            }
        }
        
        location_data = location_mapping.get(base_location, {
            "similar": [base_location],
            "reasoning": {base_location: "Base location"}
        })
        
        return {
            "success": True,
            "base_location": base_location,
            "similar_locations": location_data["similar"],
            "reasoning": location_data["reasoning"],
            "method": "curated_mapping",
            "message": f"Found {len(location_data['similar'])} similar locations using curated data"
        }
    
    async def _fallback_nearby_mapping(self, base_location: str, radius_km: int) -> Dict[str, Any]:
        """Fallback for nearby location mapping."""
        # Simplified nearby mapping
        nearby_mapping = {
            "Mumbai": ["Thane", "Navi Mumbai", "Kalyan", "Vasai"],
            "Delhi": ["Gurgaon", "Noida", "Faridabad", "Ghaziabad"],
            "Bangalore": ["Mysore", "Tumkur", "Mandya", "Hassan"],
            "Chennai": ["Kanchipuram", "Vellore", "Pondicherry", "Tiruvallur"],
            "Pune": ["Mumbai", "Nashik", "Satara", "Ahmednagar"],
            "Hyderabad": ["Secunderabad", "Warangal", "Nizamabad", "Karimnagar"]
        }
        
        nearby_locations = nearby_mapping.get(base_location, [base_location])
        return {
            "success": True,
            "base_location": base_location,
            "nearby_locations": nearby_locations,
            "radius_km": radius_km,
            "method": "curated_nearby_mapping",
            "message": f"Found {len(nearby_locations)} nearby locations"
        }
    
    async def _fallback_metro_mapping(self, base_location: str) -> Dict[str, Any]:
        """Fallback for metro area mapping."""
        metro_mapping = {
            "Mumbai": ["Thane", "Navi Mumbai", "Kalyan-Dombivali", "Vasai-Virar", "Panvel"],
            "Delhi": ["New Delhi", "Gurgaon", "Noida", "Faridabad", "Ghaziabad"],
            "Bangalore": ["Bangalore Urban", "Whitefield", "Electronic City", "Yelahanka"],
            "Chennai": ["Chennai Metropolitan", "Tambaram", "Avadi", "Ambattur"],
            "Hyderabad": ["Secunderabad", "Cyberabad", "Hitech City", "Madhapur"],
            "Pune": ["Pimpri-Chinchwad", "Hinjewadi", "Magarpatta", "Kharadi"]
        }
        
        metro_locations = metro_mapping.get(base_location, [base_location])
        
        return {
            "success": True,
            "base_location": base_location,
            "metro_area_locations": metro_locations,
            "method": "curated_metro_mapping",
            "message": f"Found {len(metro_locations)} metro area locations"
        }
    
    async def _fallback_industry_mapping(self, base_location: str, industry: str) -> Dict[str, Any]:
        """Fallback for industry hub mapping."""
        tech_hubs = {
            "Mumbai": ["Pune", "Bangalore", "Chennai", "Hyderabad"],
            "Bangalore": ["Hyderabad", "Chennai", "Pune", "Mumbai"],
            "Hyderabad": ["Bangalore", "Chennai", "Pune", "Mumbai"],
            "Chennai": ["Bangalore", "Hyderabad", "Coimbatore", "Mumbai"],
            "Pune": ["Mumbai", "Bangalore", "Hyderabad", "Nashik"],
            "Delhi": ["Gurgaon", "Noida", "Bangalore", "Pune"]
        }
        
        industry_hubs = tech_hubs.get(base_location, [base_location])
        
        return {
            "success": True,
            "base_location": base_location,
            "industry_hubs": industry_hubs,
            "industry_focus": industry,
            "method": "curated_industry_mapping",
            "message": f"Found {len(industry_hubs)} {industry} hubs"
        }