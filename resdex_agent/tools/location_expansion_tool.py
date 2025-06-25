import os
import json
import pickle
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
logger = logging.getLogger(__name__)
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class HaversineCalculator:
    
    EARTH_RADIUS_KM = 6371.0
    KM_PER_DEGREE_LAT = 111.0
    
    @staticmethod
    def km_per_degree_lng(latitude: float) -> float:
        import math
        return HaversineCalculator.KM_PER_DEGREE_LAT * math.cos(math.radians(latitude))
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        import math
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        return HaversineCalculator.EARTH_RADIUS_KM * c
    
    @staticmethod
    def get_bounding_box(lat: float, lng: float, radius_km: float):
        lat_diff = radius_km / HaversineCalculator.KM_PER_DEGREE_LAT
        lng_diff = radius_km / HaversineCalculator.km_per_degree_lng(lat)
        
        min_lat = lat - lat_diff
        max_lat = lat + lat_diff
        min_lng = lng - lng_diff
        max_lng = lng + lng_diff
        
        return min_lat, max_lat, min_lng, max_lng
    
    @staticmethod
    def is_valid_coordinate(lat: float, lng: float) -> bool:
        return (
            isinstance(lat, (int, float)) and 
            isinstance(lng, (int, float)) and
            -90 <= lat <= 90 and 
            -180 <= lng <= 180 and
            lat != -1.0 and lng != -1.0
        )
    
    def find_nearby_locations(self, locations_data: Dict[str, List[float]], 
                            target_id: str, radius_km: float = 50.0, 
                            max_results: int = 5) -> List[Dict[str, any]]:
        if target_id not in locations_data:
            return []
        
        target_coords = locations_data[target_id]
        target_lat, target_lng = target_coords[0], target_coords[1]
        
        if not self.is_valid_coordinate(target_lat, target_lng):
            return []
        
        min_lat, max_lat, min_lng, max_lng = self.get_bounding_box(target_lat, target_lng, radius_km)
        
        nearby_locations = []
        
        for location_id, coords in locations_data.items():
            if location_id == target_id:
                continue
                
            lat, lng = coords[0], coords[1]
            
            if not self.is_valid_coordinate(lat, lng):
                continue
            
            if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                continue
            
            distance = self.haversine_distance(target_lat, target_lng, lat, lng)
            
            if distance <= radius_km:
                nearby_locations.append({
                    'location_id': location_id,
                    'coordinates': [lat, lng],
                    'distance_km': round(distance, 2)
                })
        
        nearby_locations.sort(key=lambda x: x['distance_km'])
        return nearby_locations[:max_results]


class MatrixLocationExpansionTool(Tool):
    
    def __init__(self, name: str = "matrix_location_expansion_tool"):
        super().__init__(name=name, description="Matrix-based location expansion using coordinates")
        
        self.calculator = HaversineCalculator()
        self.coordinates_data = {}
        self.id_to_name_mapping = {}
        self.name_to_id_mapping = {}
        
        # Initialize data
        self._load_location_data()
        
        print(f"🗺️ MatrixLocationExpansionTool initialized:")
        print(f"   📍 {len(self.coordinates_data):,} coordinate entries")
        print(f"   🏷️ {len(self.id_to_name_mapping):,} ID mappings")
    
    def _load_location_data(self):
        try:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # Go up to project root
            sample_location_dir = project_root / "sample_location"
            
            coordinates_file = sample_location_dir / "coordinates.json"
            if coordinates_file.exists():
                self._load_coordinates(str(coordinates_file))
            else:
                logger.warning(f"Coordinates file not found: {coordinates_file}")
            
            mapping_file = sample_location_dir / "city_dict.pickle"
            if mapping_file.exists():
                self._load_id_mapping(str(mapping_file))
            else:
                logger.warning(f"Mapping file not found: {mapping_file}")
                
        except Exception as e:
            logger.error(f"Failed to load location data: {e}")
    
    def _load_coordinates(self, json_path: str):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            valid_locations = {}
            for location_id, coords in data.items():
                if isinstance(coords, list) and len(coords) == 2:
                    lat, lng = coords[0], coords[1]
                    if self.calculator.is_valid_coordinate(lat, lng):
                        valid_locations[str(location_id)] = coords
            
            self.coordinates_data = valid_locations
            logger.info(f"Loaded {len(valid_locations):,} valid coordinates")
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            self.coordinates_data = {}
    
    def _load_id_mapping(self, pickle_path: str):
        try:
            with open(pickle_path, 'rb') as f:
                mapping_data = pickle.load(f)
            
            if isinstance(mapping_data, dict):
                self.id_to_name_mapping = {str(k): str(v) for k, v in mapping_data.items()}
            else:
                logger.warning(f"Unexpected pickle format: {type(mapping_data)}")
                self.id_to_name_mapping = {}
            
            # Create reverse mapping (name to ID)
            self.name_to_id_mapping = {
                name.lower(): location_id 
                for location_id, name in self.id_to_name_mapping.items()
            }
            
            logger.info(f"Loaded {len(self.id_to_name_mapping):,} ID mappings")
            
        except Exception as e:
            logger.error(f"Error loading ID mapping: {e}")
            self.id_to_name_mapping = {}
            self.name_to_id_mapping = {}
    
    def get_matrix_stats(self) -> Dict[str, Any]:
        return {
            "available": len(self.coordinates_data) > 0,
            "total_coordinates": len(self.coordinates_data),
            "total_mappings": len(self.id_to_name_mapping),
            "coverage_percentage": (len(self.id_to_name_mapping) / len(self.coordinates_data) * 100) if self.coordinates_data else 0
        }
    
    async def __call__(self, 
                      base_location: str, 
                      radius_km: float = 50.0, 
                      max_results: int = 5) -> Dict[str, Any]:
        try:
            print(f"🗺️ MATRIX LOCATION EXPANSION: '{base_location}' within {radius_km}km")
            
            if not self.coordinates_data:
                return {
                    "success": False,
                    "error": "No coordinate data available",
                    "method": "matrix_unavailable"
                }
            
            # Find location ID
            location_id = self._find_location_id(base_location)
            
            if not location_id:
                return {
                    "success": False,
                    "error": f"Location '{base_location}' not found in matrix data",
                    "method": "matrix_location_not_found",
                    "suggestions": self._get_location_suggestions(base_location)
                }
            
            # Get nearby locations using Haversine
            nearby_locations = self.calculator.find_nearby_locations(
                self.coordinates_data,
                location_id,
                radius_km,
                max_results
            )
            
            if not nearby_locations:
                return {
                    "success": False,
                    "error": f"No locations found within {radius_km}km of {base_location}",
                    "method": "matrix_no_results"
                }
            
            # Format results
            expanded_locations = []
            for location in nearby_locations:
                location_name = self._get_location_name(location["location_id"])
                expanded_locations.append({
                    "name": location_name,
                    "location_id": location["location_id"],
                    "distance_km": location["distance_km"],
                    "coordinates": location["coordinates"]
                })
            
            base_name = self._get_location_name(location_id)
            location_names = [loc["name"] for loc in expanded_locations]
            
            print(f"✅ Matrix found {len(expanded_locations)} locations near {base_name}")
            
            return {
                "success": True,
                "method": "matrix_coordinates",
                "base_location": base_name,
                "base_location_id": location_id,
                "expanded_locations": location_names,
                "detailed_locations": expanded_locations,
                "search_params": {
                    "radius_km": radius_km,
                    "max_results": max_results
                },
                "total_found": len(expanded_locations)
            }
            
        except Exception as e:
            logger.error(f"Matrix location expansion failed: {e}")
            return {
                "success": False,
                "error": f"Matrix expansion failed: {str(e)}",
                "method": "matrix_error"
            }
    
    def _find_location_id(self, location_name: str) -> Optional[str]:
        name_lower = location_name.lower().strip()
        
        if name_lower in self.name_to_id_mapping:
            return self.name_to_id_mapping[name_lower]

        if location_name in self.coordinates_data:
            return location_name

        for name, location_id in self.name_to_id_mapping.items():
            if name_lower in name or name in name_lower:
                return location_id

        for coord_id in self.coordinates_data.keys():
            coord_name = self._get_location_name(coord_id).lower()
            if name_lower in coord_name or coord_name in name_lower:
                return coord_id
        
        return None
    
    def _get_location_name(self, location_id: str) -> str:
        """Get location name from ID."""
        return self.id_to_name_mapping.get(str(location_id), f"Location_{location_id}")
    
    def _get_location_suggestions(self, location_name: str) -> List[str]:
        """Get location name suggestions for failed matches."""
        name_lower = location_name.lower()
        suggestions = []
        
        # Find similar names
        for name in self.name_to_id_mapping.keys():
            if name_lower in name or name in name_lower:
                suggestions.append(self._get_location_name(self.name_to_id_mapping[name]))
                if len(suggestions) >= 5:
                    break
        
        return suggestions