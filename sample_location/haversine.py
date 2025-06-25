import math
import json
from typing import List, Dict, Tuple, Optional
import time


class HaversineCalculator:
    EARTH_RADIUS_KM = 6371.0
    KM_PER_DEGREE_LAT = 111.0 
    
    @staticmethod
    def km_per_degree_lng(latitude: float) -> float:
        return HaversineCalculator.KM_PER_DEGREE_LAT * math.cos(math.radians(latitude))
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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
    def get_bounding_box(lat: float, lng: float, radius_km: float) -> Tuple[float, float, float, float]:
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
    
    def find_nearby_locations(
        self, 
        locations_data: Dict[str, List[float]], 
        target_id: str, 
        radius_km: float = 5.0, 
        max_results: int = 5
    ) -> List[Dict[str, any]]:
        if target_id not in locations_data:
            print(f"❌ Target location {target_id} not found in data")
            return []
        
        target_coords = locations_data[target_id]
        target_lat, target_lng = target_coords[0], target_coords[1]
        
        if not self.is_valid_coordinate(target_lat, target_lng):
            print(f"❌ Invalid coordinates for {target_id}: {target_coords}")
            return []
        
        print(f"Finding locations within {radius_km}km of {target_id} at ({target_lat:.4f}, {target_lng:.4f})")
        
        min_lat, max_lat, min_lng, max_lng = self.get_bounding_box(target_lat, target_lng, radius_km)
        
        nearby_locations = []
        processed_count = 0
        filtered_count = 0
        
        start_time = time.time()
        
        for location_id, coords in locations_data.items():
            if location_id == target_id:
                continue
                
            processed_count += 1
            lat, lng = coords[0], coords[1]
            
            if not self.is_valid_coordinate(lat, lng):
                continue
            
            if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                continue
                
            filtered_count += 1
            
            distance = self.haversine_distance(target_lat, target_lng, lat, lng)
            
            if distance <= radius_km:
                nearby_locations.append({
                    'location_id': location_id,
                    'coordinates': [lat, lng],
                    'distance_km': round(distance, 2)
                })
        
        nearby_locations.sort(key=lambda x: x['distance_km'])
        limited_results = nearby_locations[:max_results]
        
        calculation_time = time.time() - start_time
        
        print(f"📊 Processed {processed_count:,} locations")
        print(f"🔍 Bounding box filtered to {filtered_count} candidates")
        print(f"✅ Found {len(nearby_locations)} locations within {radius_km}km")
        print(f"⚡ Calculation time: {calculation_time:.3f} seconds")
        
        return limited_results
    
    def find_multiple_radius_locations(
        self,
        locations_data: Dict[str, List[float]],
        target_id: str,
        radius_configs: List[Dict[str, any]] = None
    ) -> Dict[str, List[Dict[str, any]]]:
        if radius_configs is None:
            radius_configs = [
                {"label": "very_close", "radius_km": 5, "max_results": 5},
                {"label": "close", "radius_km": 15, "max_results": 8},
                {"label": "nearby", "radius_km": 30, "max_results": 10},
                {"label": "regional", "radius_km": 50, "max_results": 12}
            ]
        
        results = {}
        
        for config in radius_configs:
            label = config["label"]
            radius_km = config["radius_km"]
            max_results = config.get("max_results", 5)
            
            print(f"\n🔍 Finding {label} locations (within {radius_km}km)...")
            
            nearby = self.find_nearby_locations(
                locations_data, target_id, radius_km, max_results
            )
            
            results[label] = nearby
            
            if nearby:
                distances = [loc['distance_km'] for loc in nearby]
                print(f"📏 Distance range: {min(distances):.1f}km - {max(distances):.1f}km")
            else:
                print(f"❌ No locations found within {radius_km}km")
        
        return results


def load_locations_from_json(file_path: str) -> Dict[str, List[float]]:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data):,} locations from {file_path}")
        
        # Validate data format
        valid_locations = {}
        invalid_count = 0
        
        for location_id, coords in data.items():
            if isinstance(coords, list) and len(coords) == 2:
                lat, lng = coords[0], coords[1]
                if HaversineCalculator.is_valid_coordinate(lat, lng):
                    valid_locations[location_id] = coords
                else:
                    invalid_count += 1
            else:
                invalid_count += 1
        
        print(f"📊 Valid locations: {len(valid_locations):,}")
        print(f"⚠️  Invalid/skipped locations: {invalid_count:,}")
        
        return valid_locations
        
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return {}


def test_haversine_calculator():
    print("🧪 Testing Haversine Calculator")
    print("=" * 50)
    
    test_locations = {
        "mumbai": [19.0760, 72.8777],
        "delhi": [28.6139, 77.2090],
        "bangalore": [12.9716, 77.5946],
        "pune": [18.5204, 73.8567],
        "thane": [19.2183, 72.9781],  # Close to Mumbai
        "navi_mumbai": [19.0330, 73.0297],  # Close to Mumbai
        "noida": [28.5355, 77.3910],  # Close to Delhi
        "gurgaon": [28.4595, 77.0266],  # Close to Delhi
        "invalid": [-1.0, -1.0]  # Invalid coordinates
    }
    
    calculator = HaversineCalculator()    
    print("\n🎯 Testing: Locations near Mumbai")
    nearby_mumbai = calculator.find_nearby_locations(
        test_locations, "mumbai", radius_km=50, max_results=5
    )
    
    for location in nearby_mumbai:
        print(f"  📍 {location['location_id']}: {location['distance_km']}km away")
    
    print("\n🎯 Testing: Locations near Delhi")
    nearby_delhi = calculator.find_nearby_locations(
        test_locations, "delhi", radius_km=50, max_results=5
    )
    
    for location in nearby_delhi:
        print(f"  📍 {location['location_id']}: {location['distance_km']}km away")
    
    print("\n🎯 Testing: Multiple radius ranges for Mumbai")
    multi_radius = calculator.find_multiple_radius_locations(
        test_locations, "mumbai"
    )
    
    for radius_label, locations in multi_radius.items():
        print(f"\n📏 {radius_label.upper()}:")
        for loc in locations:
            print(f"  📍 {loc['location_id']}: {loc['distance_km']}km")


if __name__ == "__main__":
    test_haversine_calculator()