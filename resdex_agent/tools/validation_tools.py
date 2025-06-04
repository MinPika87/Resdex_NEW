# Replace the content of resdex_agent/tools/validation_tools.py

"""
Validation tools for ResDex Agent.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

# Create a simple Tool base class
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from ..utils.data_processing import DataProcessor
from ..utils.constants import TECH_SKILLS, CITIES

logger = logging.getLogger(__name__)


class ValidationTool(Tool):
    """Tool for validating inputs and filters."""
    
    def __init__(self, name: str = "validation_tool"):
        super().__init__(name=name, description="Validate user inputs and filter values")
        self.data_processor = DataProcessor()
    
    async def __call__(self, 
                      validation_type: str, 
                      data: Any, 
                      **kwargs) -> Dict[str, Any]:
        """Perform validation based on type."""
        try:
            if validation_type == "search_filters":
                return await self._validate_search_filters(data)
            elif validation_type == "user_input":
                return await self._validate_user_input(data)
            elif validation_type == "skill":
                return await self._validate_skill(data)
            elif validation_type == "location":
                return await self._validate_location(data)
            else:
                return {"success": False, "error": f"Unknown validation type: {validation_type}"}
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_search_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search filter values."""
        errors = []
        warnings = []
        
        # Validate company name
        if not filters.get('recruiter_company', '').strip():
            errors.append("Company name is required")
        
        # Validate keywords
        keywords = filters.get('keywords', [])
        if not keywords:
            errors.append("At least one keyword/skill is required")
        
        # Validate experience range
        min_exp = filters.get('min_exp', 0)
        max_exp = filters.get('max_exp', 10)
        if not self.data_processor.validate_experience_range(min_exp, max_exp):
            errors.append("Invalid experience range")
        
        # Validate salary range
        min_salary = filters.get('min_salary', 0)
        max_salary = filters.get('max_salary', 15)
        if not self.data_processor.validate_salary_range(min_salary, max_salary):
            errors.append("Invalid salary range")
        
        # Check for too many filters (performance warning)
        if len(keywords) > 10:
            warnings.append("Large number of skills may slow down search")
        
        total_locations = len(filters.get('current_cities', [])) + len(filters.get('preferred_cities', []))
        if total_locations > 5:
            warnings.append("Large number of locations may limit results")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "filter_count": {
                "keywords": len(keywords),
                "locations": total_locations,
                "has_experience_filter": min_exp > 0 or max_exp < 50,
                "has_salary_filter": min_salary > 0 or max_salary < 100
            }
        }
    
    async def _validate_user_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for chat interface."""
        if not user_input or not user_input.strip():
            return {
                "success": False,
                "error": "User input cannot be empty",
                "suggestions": ["Try asking 'add python skill'", "Try 'search with java'"]
            }
        
        if len(user_input.strip()) < 3:
            return {
                "success": False,
                "error": "User input is too short",
                "suggestions": ["Please provide more detail about what you want to do"]
            }
        
        if len(user_input) > 500:
            return {
                "success": False,
                "error": "User input is too long",
                "suggestions": ["Please keep your request under 500 characters"]
            }
        
        return {
            "success": True,
            "input_analysis": {
                "length": len(user_input),
                "word_count": len(user_input.split()),
                "has_skill_keywords": any(skill.lower() in user_input.lower() for skill in TECH_SKILLS[:20]),
                "has_location_keywords": any(city.lower() in user_input.lower() for city in CITIES[:10]),
                "has_action_keywords": any(action in user_input.lower() for action in ["add", "remove", "search", "find", "filter"])
            }
        }
    
    async def _validate_skill(self, skill: str) -> Dict[str, Any]:
        """Validate a skill name."""
        if not skill or not skill.strip():
            return {"success": False, "error": "Skill name cannot be empty"}
        
        normalized_skill = self.data_processor.normalize_skill(skill)
        
        # Check if it's a known tech skill
        is_known_skill = normalized_skill in TECH_SKILLS
        
        # Check for common misspellings or variations
        suggestions = []
        if not is_known_skill:
            for tech_skill in TECH_SKILLS:
                if skill.lower() in tech_skill.lower() or tech_skill.lower() in skill.lower():
                    suggestions.append(tech_skill)
                    if len(suggestions) >= 3:
                        break
        
        return {
            "success": True,
            "normalized_skill": normalized_skill,
            "is_known_skill": is_known_skill,
            "suggestions": suggestions,
            "validation_notes": {
                "original": skill,
                "normalized": normalized_skill,
                "length": len(skill),
                "has_special_chars": any(c in skill for c in "!@#$%^&*()[]{}|\\:;\"'<>?,./")
            }
        }
    
    async def _validate_location(self, location: str) -> Dict[str, Any]:
        """Validate a location name."""
        if not location or not location.strip():
            return {"success": False, "error": "Location name cannot be empty"}
        
        normalized_location = self.data_processor.normalize_location(location)
        
        # Check if it's a known city
        is_known_city = normalized_location in CITIES
        
        # Check for common variations
        suggestions = []
        if not is_known_city:
            for city in CITIES:
                if location.lower() in city.lower() or city.lower() in location.lower():
                    suggestions.append(city)
                    if len(suggestions) >= 3:
                        break
        
        return {
            "success": True,
            "normalized_location": normalized_location,
            "is_known_city": is_known_city,
            "suggestions": suggestions,
            "validation_notes": {
                "original": location,
                "normalized": normalized_location,
                "length": len(location)
            }
        }