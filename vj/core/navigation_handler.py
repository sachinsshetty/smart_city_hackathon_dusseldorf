"""
Navigation Handler Module for Dwani AI
Manages geocoding and routing for emergency evacuation
"""

import requests
from typing import Tuple, Optional, Dict, Any, List
from .config import DwaniConfig

class NavigationHandler:
    """Handles navigation and routing operations"""
    
    def __init__(self):
        """Initialize navigation handler"""
        self.api_key = DwaniConfig.OPENROUTE_SERVICE_API_KEY
        self.safe_places = {
            'hospital': {
                'name': 'University Hospital Düsseldorf',
                'address': 'Moorenstraße 5, 40225 Düsseldorf',
                'type': 'hospital',
                'capacity': 'large',
                'services': ['emergency', 'trauma', 'burn_unit']
            },
            'fire_station': {
                'name': 'Fire Station Düsseldorf Central',
                'address': 'Berger Allee 25, 40213 Düsseldorf',
                'type': 'fire_station',
                'capacity': 'medium',
                'services': ['fire_emergency', 'rescue']
            },
            'police_station': {
                'name': 'Police Station Düsseldorf',
                'address': 'Jürgensplatz 1, 40219 Düsseldorf',
                'type': 'police',
                'capacity': 'medium',
                'services': ['security', 'emergency_response']
            },
            'shelter': {
                'name': 'Emergency Shelter Düsseldorf',
                'address': 'Königsallee 92, 40212 Düsseldorf',
                'type': 'shelter',
                'capacity': 'large',
                'services': ['temporary_housing', 'basic_needs']
            },
            'train_station': {
                'name': 'Düsseldorf Hauptbahnhof',
                'address': 'Konrad-Adenauer-Platz 14, 40210 Düsseldorf',
                'type': 'transportation',
                'capacity': 'large',
                'services': ['evacuation', 'transport']
            },
            'park': {
                'name': 'Hofgarten Park',
                'address': 'Hofgarten, 40213 Düsseldorf',
                'type': 'open_space',
                'capacity': 'very_large',
                'services': ['safe_assembly', 'fresh_air']
            }
        }
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to coordinates
        
        Args:
            address: Address to geocode
            
        Returns:
            Tuple[float, float]: (longitude, latitude) or None if failed
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            headers = {
                "User-Agent": "Dwani.AI-Guard/1.0 (emergency_navigation@dwani.ai)"
            }
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                print(f"Could not geocode address: {address}")
                return None
                
            return float(data[0]['lon']), float(data[0]['lat'])
            
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None
    
    def get_directions(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                      profile: str = "foot-walking") -> Optional[Dict[str, Any]]:
        """
        Get directions using OpenRouteService
        
        Args:
            origin: (longitude, latitude) of starting point
            destination: (longitude, latitude) of destination
            profile: Routing profile (foot-walking, driving-car, etc.)
            
        Returns:
            Dict: Route data or None if failed
        """
        try:
            if not self.api_key:
                print("OpenRouteService API key not configured")
                return None
            
            url = f"https://api.openrouteservice.org/v2/directions/{profile}"
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "coordinates": [origin, destination]
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Routing error: {e}")
            return None
    
    def parse_route_steps(self, route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse route steps into structured format
        
        Args:
            route_data: Raw route data from OpenRouteService
            
        Returns:
            List[Dict]: Parsed route steps
        """
        try:
            steps = route_data["routes"][0]["segments"][0]["steps"]
            parsed_steps = []
            
            for i, step in enumerate(steps, 1):
                distance = round(step["distance"])
                duration = round(step["duration"] / 60, 1)  # convert to minutes
                
                parsed_steps.append({
                    'step_number': i,
                    'instruction': step['instruction'],
                    'distance_meters': distance,
                    'duration_minutes': duration,
                    'maneuver': step.get('maneuver', {}),
                    'way_points': step.get('way_points', [])
                })
            
            return parsed_steps
            
        except (KeyError, IndexError) as e:
            print(f"Error parsing route data: {e}")
            return []
    
    def get_nearest_safe_place(self, current_location: str, emergency_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Get the nearest safe place based on emergency type
        
        Args:
            current_location: Current location address
            emergency_type: Type of emergency (fire, medical, etc.)
            
        Returns:
            Dict: Safe place information or None
        """
        # Prioritize safe places based on emergency type
        priority_map = {
            'fire': ['fire_station', 'park', 'shelter'],
            'medical': ['hospital', 'fire_station', 'shelter'],
            'structural': ['park', 'shelter', 'train_station'],
            'chemical': ['hospital', 'fire_station', 'park'],
            'general': ['shelter', 'park', 'train_station']
        }
        
        priority_list = priority_map.get(emergency_type, priority_map['general'])
        
        # Return the first available safe place in priority order
        for place_key in priority_list:
            if place_key in self.safe_places:
                return self.safe_places[place_key]
        
        return None
    
    def generate_evacuation_route(self, current_location: str, emergency_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Generate evacuation route to nearest safe place
        
        Args:
            current_location: Current location address
            emergency_type: Type of emergency
            
        Returns:
            Dict: Evacuation route information
        """
        try:
            # Get nearest safe place
            safe_place = self.get_nearest_safe_place(current_location, emergency_type)
            if not safe_place:
                print("No safe place found")
                return None
            
            # Geocode current location and destination
            origin_coords = self.geocode_address(current_location)
            dest_coords = self.geocode_address(safe_place['address'])
            
            if not origin_coords or not dest_coords:
                print("Could not geocode locations")
                return None
            
            # Get route
            route_data = self.get_directions(origin_coords, dest_coords)
            if not route_data:
                print("Could not get route")
                return None
            
            # Parse steps
            steps = self.parse_route_steps(route_data)
            
            # Get route summary
            route_summary = route_data["routes"][0]["summary"]
            total_distance = round(route_summary["distance"])
            total_duration = round(route_summary["duration"] / 60, 1)
            
            return {
                'safe_place': safe_place,
                'origin': current_location,
                'destination': safe_place['address'],
                'total_distance_meters': total_distance,
                'total_duration_minutes': total_duration,
                'steps': steps,
                'emergency_type': emergency_type,
                'route_data': route_data
            }
            
        except Exception as e:
            print(f"Error generating evacuation route: {e}")
            return None
    
    def format_route_instructions(self, route_info: Dict[str, Any]) -> str:
        """
        Format route instructions for voice output
        
        Args:
            route_info: Route information from generate_evacuation_route
            
        Returns:
            str: Formatted instructions
        """
        try:
            safe_place = route_info['safe_place']
            steps = route_info['steps']
            total_distance = route_info['total_distance_meters']
            total_duration = route_info['total_duration_minutes']
            
            instructions = f"🚨 EMERGENCY EVACUATION ROUTE 🚨\n\n"
            instructions += f"Destination: {safe_place['name']}\n"
            instructions += f"Address: {safe_place['address']}\n"
            instructions += f"Type: {safe_place['type'].replace('_', ' ').title()}\n"
            instructions += f"Total Distance: {total_distance} meters\n"
            instructions += f"Estimated Time: {total_duration} minutes\n\n"
            
            instructions += "Step-by-step instructions:\n"
            for step in steps[:10]:  # Limit to first 10 steps for voice
                instructions += f"{step['step_number']}. {step['instruction']} "
                instructions += f"({step['distance_meters']} m, ~{step['duration_minutes']} min)\n"
            
            if len(steps) > 10:
                instructions += f"... and {len(steps) - 10} more steps\n"
            
            instructions += f"\n⚠️ Follow these directions carefully and stay calm."
            
            return instructions
            
        except Exception as e:
            print(f"Error formatting route instructions: {e}")
            return "Error generating route instructions"
    
    def get_all_safe_places(self) -> Dict[str, Dict[str, Any]]:
        """Get all available safe places"""
        return self.safe_places.copy() 