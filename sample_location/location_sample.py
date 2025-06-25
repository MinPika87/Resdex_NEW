import pickle
import json
import argparse
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time

from haversine import HaversineCalculator, load_locations_from_json


class LocationExpansionMatrix:
    def __init__(self, coordinates_json_path: str, mapping_pickle_path: str):
        self.calculator = HaversineCalculator()
        self.coordinates_data = {}
        self.id_to_name_mapping = {}
        self.name_to_id_mapping = {}
        
        # Load data
        self.load_coordinates(coordinates_json_path)
        self.load_id_mapping(mapping_pickle_path)
        
        print(f"🎯 LocationExpansionMatrix initialized with:")
        print(f"   📍 {len(self.coordinates_data):,} coordinate entries")
        print(f"   🏷️  {len(self.id_to_name_mapping):,} ID mappings")
    
    def load_coordinates(self, json_path: str):
        try:
            print(f"📂 Loading coordinates from {json_path}...")
            self.coordinates_data = load_locations_from_json(json_path)
            print(f"✅ Loaded {len(self.coordinates_data):,} valid coordinates")
        except Exception as e:
            print(f"❌ Error loading coordinates: {e}")
            sys.exit(1)
    
    def load_id_mapping(self, pickle_path: str):
        try:
            print(f"📂 Loading ID mapping from {pickle_path}...")
            
            with open(pickle_path, 'rb') as f:
                mapping_data = pickle.load(f)
            
            # Handle different possible formats of the pickle file
            if isinstance(mapping_data, dict):
                self.id_to_name_mapping = {str(k): str(v) for k, v in mapping_data.items()}
            else:
                print(f"⚠️  Unexpected pickle format: {type(mapping_data)}")
                self.id_to_name_mapping = {}
            
            # Create reverse mapping (name to ID)
            self.name_to_id_mapping = {
                name.lower(): location_id 
                for location_id, name in self.id_to_name_mapping.items()
            }
            
            print(f"✅ Loaded {len(self.id_to_name_mapping):,} ID mappings")
            
            # Show sample mappings
            sample_items = list(self.id_to_name_mapping.items())[:5]
            print(f"📋 Sample mappings:")
            for location_id, name in sample_items:
                print(f"   {location_id} -> {name}")
                
        except Exception as e:
            print(f"❌ Error loading ID mapping: {e}")
            print(f"💡 Creating empty mapping - will use IDs as names")
            self.id_to_name_mapping = {}
            self.name_to_id_mapping = {}
    
    def get_location_name(self, location_id: str) -> str:
        return self.id_to_name_mapping.get(str(location_id), f"Location_{location_id}")
    
    def find_location_id_by_name(self, location_name: str) -> Optional[str]:
        name_lower = location_name.lower()
        
        if name_lower in self.name_to_id_mapping:
            return self.name_to_id_mapping[name_lower]
        
        for name, location_id in self.name_to_id_mapping.items():
            if name_lower in name or name in name_lower:
                return location_id
        
        return None
    
    def expand_location_by_id(
        self, 
        location_id: str, 
        radius_km: float = 5.0, 
        max_results: int = 5
    ) -> Dict[str, any]:
        if str(location_id) not in self.coordinates_data:
            available_ids = list(self.coordinates_data.keys())[:10]
            return {
                "success": False,
                "error": f"Location ID {location_id} not found in coordinates",
                "available_samples": available_ids
            }
        
        base_name = self.get_location_name(location_id)
        base_coords = self.coordinates_data[str(location_id)]
        
        print(f"\n🎯 EXPANDING LOCATION: {base_name} (ID: {location_id})")
        print(f"📍 Coordinates: {base_coords[0]:.4f}, {base_coords[1]:.4f}")
        print(f"🔍 Searching within {radius_km}km radius for max {max_results} locations")
        
        nearby_locations = self.calculator.find_nearby_locations(
            self.coordinates_data,
            str(location_id),
            radius_km,
            max_results
        )
        
        enhanced_results = []
        for location in nearby_locations:
            enhanced_results.append({
                "location_id": location["location_id"],
                "location_name": self.get_location_name(location["location_id"]),
                "coordinates": location["coordinates"],
                "distance_km": location["distance_km"]
            })
        
        return {
            "success": True,
            "base_location": {
                "id": str(location_id),
                "name": base_name,
                "coordinates": base_coords
            },
            "search_params": {
                "radius_km": radius_km,
                "max_results": max_results
            },
            "nearby_locations": enhanced_results,
            "total_found": len(enhanced_results)
        }
    
    def expand_location_by_name(
        self, 
        location_name: str, 
        radius_km: float = 5.0, 
        max_results: int = 5
    ) -> Dict[str, any]:
        location_id = self.find_location_id_by_name(location_name)
        
        if not location_id:
            similar_names = [
                name for name in self.name_to_id_mapping.keys() 
                if location_name.lower() in name or name in location_name.lower()
            ][:10]
            
            return {
                "success": False,
                "error": f"Location '{location_name}' not found",
                "suggestions": similar_names
            }
        
        print(f"🔍 Found location: '{location_name}' -> ID: {location_id}")
        
        return self.expand_location_by_id(location_id, radius_km, max_results)
    
    def batch_expand_locations(
        self, 
        location_identifiers: List[str], 
        radius_km: float = 5.0, 
        max_results: int = 5
    ) -> Dict[str, Dict[str, any]]:
        print(f"\n🚀 BATCH EXPANSION: {len(location_identifiers)} locations")
        print(f"📏 Radius: {radius_km}km, Max results: {max_results}")
        
        batch_results = {}
        start_time = time.time()
        
        for i, identifier in enumerate(location_identifiers, 1):
            print(f"\n📍 [{i}/{len(location_identifiers)}] Processing: {identifier}")
            
            # Try as ID first, then as name
            if identifier in self.coordinates_data:
                result = self.expand_location_by_id(identifier, radius_km, max_results)
            else:
                result = self.expand_location_by_name(identifier, radius_km, max_results)
            
            batch_results[identifier] = result
            
            if result["success"]:
                nearby_count = result["total_found"]
                base_name = result["base_location"]["name"]
                print(f"✅ {base_name}: Found {nearby_count} nearby locations")
            else:
                print(f"❌ Failed: {result['error']}")
        
        total_time = time.time() - start_time
        print(f"\n⚡ Batch processing completed in {total_time:.2f} seconds")
        
        return batch_results
    
    def get_location_statistics(self) -> Dict[str, any]:
        """Get statistics about the location dataset."""
        valid_coords = len(self.coordinates_data)
        total_mappings = len(self.id_to_name_mapping)
        
        # Calculate coordinate bounds
        if self.coordinates_data:
            lats = [coords[0] for coords in self.coordinates_data.values()]
            lngs = [coords[1] for coords in self.coordinates_data.values()]
            
            bounds = {
                "lat_min": min(lats),
                "lat_max": max(lats),
                "lng_min": min(lngs),
                "lng_max": max(lngs)
            }
        else:
            bounds = {}
        
        return {
            "total_coordinates": valid_coords,
            "total_mappings": total_mappings,
            "coverage_percentage": (total_mappings / valid_coords * 100) if valid_coords > 0 else 0,
            "coordinate_bounds": bounds
        }
    
    def display_expansion_results(self, results: Dict[str, any]):
        """Display expansion results in a formatted way."""
        if not results["success"]:
            print(f"❌ Expansion failed: {results['error']}")
            if "suggestions" in results:
                print(f"💡 Suggestions: {', '.join(results['suggestions'][:5])}")
            return
        
        base = results["base_location"]
        nearby = results["nearby_locations"]
        
        print(f"\n🎯 EXPANSION RESULTS")
        print(f"=" * 60)
        print(f"📍 Base Location: {base['name']} (ID: {base['id']})")
        print(f"📐 Coordinates: {base['coordinates'][0]:.4f}, {base['coordinates'][1]:.4f}")
        print(f"🔍 Search Radius: {results['search_params']['radius_km']}km")
        print(f"✅ Found: {results['total_found']} nearby locations")
        
        if nearby:
            print(f"\n📋 NEARBY LOCATIONS:")
            print(f"{'Rank':<4} {'Distance':<8} {'ID':<8} {'Name'}")
            print(f"{'-'*4} {'-'*8} {'-'*8} {'-'*20}")
            
            for i, location in enumerate(nearby, 1):
                print(f"{i:<4} {location['distance_km']:<8.1f} {location['location_id']:<8} {location['location_name']}")
        else:
            print(f"\n💭 No locations found within {results['search_params']['radius_km']}km radius")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Location Matrix Expansion Tool")
    parser.add_argument("--coordinates", default="/data/analytics/rohit.agarwal/Resdex/sample_location/coordinates.json", 
                       help="Path to JSON file with coordinates")
    parser.add_argument("--mapping", default="city_dict.pickle",
                       help="Path to pickle file with ID mappings")
    parser.add_argument("--location", help="Location name to expand")
    parser.add_argument("--location-id", help="Location ID to expand")
    parser.add_argument("--radius", type=float, default=50.0,
                       help="Search radius in kilometers (default: 5)")
    parser.add_argument("--max-results", type=int, default=100,
                       help="Maximum number of results (default: 5)")
    parser.add_argument("--batch", nargs="+", help="Batch process multiple locations")
    parser.add_argument("--stats", action="store_true", help="Show dataset statistics")
    
    args = parser.parse_args()
    
    # Initialize the location expansion system
    try:
        expansion_system = LocationExpansionMatrix(args.coordinates, args.mapping)
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        sys.exit(1)
    
    # Show statistics if requested
    if args.stats:
        stats = expansion_system.get_location_statistics()
        print(f"\n📊 DATASET STATISTICS")
        print(f"=" * 40)
        print(f"📍 Total coordinates: {stats['total_coordinates']:,}")
        print(f"🏷️  Total mappings: {stats['total_mappings']:,}")
        print(f"📈 Coverage: {stats['coverage_percentage']:.1f}%")
        if stats['coordinate_bounds']:
            bounds = stats['coordinate_bounds']
            print(f"🗺️  Coordinate bounds:")
            print(f"   Latitude: {bounds['lat_min']:.2f} to {bounds['lat_max']:.2f}")
            print(f"   Longitude: {bounds['lng_min']:.2f} to {bounds['lng_max']:.2f}")
    
    # Process expansion requests
    if args.batch:
        # Batch processing
        results = expansion_system.batch_expand_locations(
            args.batch, args.radius, args.max_results
        )
        
        for identifier, result in results.items():
            print(f"\n{'='*60}")
            print(f"🎯 RESULTS FOR: {identifier}")
            expansion_system.display_expansion_results(result)
    
    elif args.location_id:
        # Expand by location ID
        results = expansion_system.expand_location_by_id(
            args.location_id, args.radius, args.max_results
        )
        expansion_system.display_expansion_results(results)
    
    elif args.location:
        # Expand by location name
        results = expansion_system.expand_location_by_name(
            args.location, args.radius, args.max_results
        )
        expansion_system.display_expansion_results(results)
    
    else:
        # Interactive mode or demo
        print(f"\n🎮 INTERACTIVE MODE")
        print(f"Available sample IDs: {list(expansion_system.coordinates_data.keys())[:10]}")
        
        # Demo with a sample location
        sample_ids = list(expansion_system.coordinates_data.keys())
        if sample_ids:
            sample_id = sample_ids[0]
            print(f"\n🧪 Demo: Expanding sample location ID: {sample_id}")
            
            results = expansion_system.expand_location_by_id(
                sample_id, args.radius, args.max_results
            )
            expansion_system.display_expansion_results(results)


if __name__ == "__main__":
    main()