
"""
Filter management tools for ResDex Agent.
"""
from typing import Dict, Any, List, Optional
import logging

# Create a simple Tool base class since we're not using google.adk.tools
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from ..utils.data_processing import DataProcessor
from ..utils.constants import ModificationType

logger = logging.getLogger(__name__)


class FilterTool(Tool):
    """Tool for managing search filters."""
    
    def __init__(self, name: str = "filter_tool"):
        super().__init__(name=name, description="Manage search filters and modifications")
        self.data_processor = DataProcessor()
    
    async def __call__(self, 
                      action: str, 
                      session_state: Dict[str, Any], 
                      **kwargs) -> Dict[str, Any]:
        """Execute filter modification."""
        try:
            logger.info(f"Executing filter action: {action}")
            print(f"🔧 FilterTool: Action={action}, kwargs={kwargs}")
            
            if action == "add_skill":
                return await self._add_skill(session_state, **kwargs)
            elif action == "remove_skill":
                return await self._remove_skill(session_state, **kwargs)
            elif action == "modify_experience":
                return await self._modify_experience(session_state, **kwargs)
            elif action == "modify_salary":
                return await self._modify_salary(session_state, **kwargs)
            elif action == "add_location":
                return await self._add_location(session_state, **kwargs)
            elif action == "remove_location":
                return await self._remove_location(session_state, **kwargs)
            elif action == "add_target_company":
                return await self._add_target_company(session_state, **kwargs)
            elif action == "remove_target_company":  
                return await self._remove_target_company(session_state, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown filter action: {action}",
                    "modifications": []
                }
                
        except Exception as e:
            logger.error(f"Filter modification failed: {e}")
            print(f"❌ FilterTool error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "modifications": []
            }
    
    async def _add_skill(self, session_state: Dict[str, Any], skill: str, mandatory: bool = False, **kwargs) -> Dict[str, Any]:
        """Add a skill to search filters."""
        normalized_skill = self.data_processor.normalize_skill(skill)
        keywords = session_state.get('keywords', [])
        
        # Check if skill already exists
        existing_index = -1
        for i, kw in enumerate(keywords):
            clean_kw = kw.replace('★ ', '')
            if normalized_skill.lower() == clean_kw.lower():
                existing_index = i
                break
        
        if existing_index != -1:
            # Update existing skill status
            old_keyword = keywords[existing_index]
            if mandatory and not old_keyword.startswith('★ '):
                keywords[existing_index] = f"★ {normalized_skill}"
                modification_type = ModificationType.SKILL_MADE_MANDATORY
            elif not mandatory and old_keyword.startswith('★ '):
                keywords[existing_index] = normalized_skill
                modification_type = ModificationType.SKILL_MADE_OPTIONAL
            else:
                return {
                    "success": True,
                    "message": f"'{normalized_skill}' is already in filters with the requested status",
                    "modifications": []
                }
        else:
            # Add new skill
            new_keyword = f"★ {normalized_skill}" if mandatory else normalized_skill
            keywords.append(new_keyword)
            modification_type = ModificationType.SKILL_ADDED
        
        session_state['keywords'] = keywords
        
        return {
            "success": True,
            "message": f"{'Added' if existing_index == -1 else 'Updated'} '{normalized_skill}' {'as mandatory' if mandatory else 'as optional'}",
            "modifications": [{
                "type": modification_type.value,
                "field": "keywords",
                "value": normalized_skill,
                "mandatory": mandatory
            }]
        }
    
    async def _remove_skill(self, session_state: Dict[str, Any], skill: str, **kwargs) -> Dict[str, Any]:
        """Remove a skill from search filters."""
        normalized_skill = self.data_processor.normalize_skill(skill)
        keywords = session_state.get('keywords', [])
        
        # Find and remove matching skill
        removed_skill = None
        for kw in keywords[:]:
            if normalized_skill.lower() in kw.replace('★ ', '').lower():
                keywords.remove(kw)
                removed_skill = kw
                break
        
        if removed_skill:
            session_state['keywords'] = keywords
            return {
                "success": True,
                "message": f"Removed '{normalized_skill}' from search filters",
                "modifications": [{
                    "type": ModificationType.SKILL_REMOVED.value,
                    "field": "keywords",
                    "value": normalized_skill
                }]
            }
        else:
            return {
                "success": False,
                "message": f"'{normalized_skill}' was not found in search filters",
                "modifications": []
            }
    
    async def _modify_experience(self, session_state: Dict[str, Any], operation: str, value: Any, **kwargs) -> Dict[str, Any]:
        """Modify experience filters."""
        try:
            print(f"🔧 Experience modification: operation={operation}, value={value} (type: {type(value)})")
            
            if operation == "set_range":
                if isinstance(value, str) and "-" in value:
                    try:
                        min_val, max_val = map(float, value.split('-'))
                        if self.data_processor.validate_experience_range(min_val, max_val):
                            session_state['min_exp'] = min_val
                            session_state['max_exp'] = max_val
                            message = f"Set experience range to {min_val}-{max_val} years"
                        else:
                            return {"success": False, "message": "Invalid experience range", "modifications": []}
                    except ValueError as e:
                        print(f"❌ Error parsing range string '{value}': {e}")
                        return {"success": False, "message": f"Invalid experience range format: {value}", "modifications": []}
                else:
                    try:
                        years = float(value)
                        session_state['min_exp'] = years
                        message = f"Set minimum experience to {years} years"
                    except (ValueError, TypeError) as e:
                        print(f"❌ Error parsing experience value '{value}': {e}")
                        return {"success": False, "message": f"Invalid experience value: {value}", "modifications": []}
            elif operation == "set":
                try:
                    years = float(value)
                    session_state['min_exp'] = years
                    message = f"Set minimum experience to {years} years"
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid experience value: {value}", "modifications": []}
            else:
                return {"success": False, "message": f"Unknown operation: {operation}", "modifications": []}
            
            return {
                "success": True,
                "message": message,
                "modifications": [{
                    "type": ModificationType.EXPERIENCE_MODIFIED.value,
                    "field": "experience",
                    "operation": operation,
                    "value": value
                }]
            }
            
        except Exception as e:
            print(f"❌ Experience modification error: {e}")
            return {"success": False, "message": f"Experience modification failed: {e}", "modifications": []}
    
    async def _modify_salary(self, session_state: Dict[str, Any], operation: str, value: Any, **kwargs) -> Dict[str, Any]:
        """Modify salary filters."""
        try:
            print(f"🔧 Salary modification: operation={operation}, value={value} (type: {type(value)})")
            
            if operation == "set_range":
                if isinstance(value, str) and "-" in value:
                    try:
                        min_val, max_val = map(float, value.split('-'))
                        if self.data_processor.validate_salary_range(min_val, max_val):
                            session_state['min_salary'] = min_val
                            session_state['max_salary'] = max_val
                            message = f"Set salary range to {min_val}-{max_val} lakhs"
                        else:
                            return {"success": False, "message": "Invalid salary range", "modifications": []}
                    except ValueError as e:
                        print(f"❌ Error parsing salary range string '{value}': {e}")
                        return {"success": False, "message": f"Invalid salary range format: {value}", "modifications": []}
                else:
                    try:
                        amount = float(value)
                        session_state['min_salary'] = amount
                        message = f"Set minimum salary to {amount} lakhs"
                    except (ValueError, TypeError) as e:
                        print(f"❌ Error parsing salary value '{value}': {e}")
                        return {"success": False, "message": f"Invalid salary value: {value}", "modifications": []}
            elif operation == "set":
                try:
                    amount = float(value)
                    session_state['min_salary'] = amount
                    message = f"Set minimum salary to {amount} lakhs"
                except (ValueError, TypeError):
                    return {"success": False, "message": f"Invalid salary value: {value}", "modifications": []}
            else:
                return {"success": False, "message": f"Unknown operation: {operation}", "modifications": []}
            
            return {
                "success": True,
                "message": message,
                "modifications": [{
                    "type": ModificationType.SALARY_MODIFIED.value,
                    "field": "salary",
                    "operation": operation,
                    "value": value
                }]
            }
            
        except Exception as e:
            print(f"❌ Salary modification error: {e}")
            return {"success": False, "message": f"Salary modification failed: {e}", "modifications": []}
    
    async def _add_location(self, session_state: Dict[str, Any], location: str, mandatory: bool = False, **kwargs) -> Dict[str, Any]:
        """Add a location to search filters."""
        normalized_location = self.data_processor.normalize_location(location)
        
        if mandatory:
            preferred_cities = session_state.get('preferred_cities', [])
            if normalized_location not in preferred_cities:
                preferred_cities.append(normalized_location)
                session_state['preferred_cities'] = preferred_cities
                message = f"Added '{normalized_location}' as mandatory location"
            else:
                message = f"'{normalized_location}' is already a mandatory location"
        else:
            current_cities = session_state.get('current_cities', [])
            if normalized_location not in current_cities:
                current_cities.append(normalized_location)
                session_state['current_cities'] = current_cities
                message = f"Added '{normalized_location}' as optional location"
            else:
                message = f"'{normalized_location}' is already an optional location"
        
        return {
            "success": True,
            "message": message,
            "modifications": [{
                "type": ModificationType.LOCATION_ADDED.value,
                "field": "location",
                "value": normalized_location,
                "mandatory": mandatory
            }]
        }
    
    async def _remove_location(self, session_state: Dict[str, Any], location: str, **kwargs) -> Dict[str, Any]:
        """Remove a location from search filters."""
        normalized_location = self.data_processor.normalize_location(location)
        
        removed_from = []
        
        # Check current cities
        current_cities = session_state.get('current_cities', [])
        if normalized_location in current_cities:
            current_cities.remove(normalized_location)
            session_state['current_cities'] = current_cities
            removed_from.append("optional")
        
        # Check preferred cities
        preferred_cities = session_state.get('preferred_cities', [])
        if normalized_location in preferred_cities:
            preferred_cities.remove(normalized_location)
            session_state['preferred_cities'] = preferred_cities
            removed_from.append("mandatory")
        
        if removed_from:
            message = f"Removed '{normalized_location}' from {' and '.join(removed_from)} location filters"
            return {
                "success": True,
                "message": message,
                "modifications": [{
                    "type": ModificationType.LOCATION_REMOVED.value,
                    "field": "location",
                    "value": normalized_location
                }]
            }
        else:
            return {
                "success": False,
                "message": f"'{normalized_location}' was not found in location filters",
                "modifications": []
            }  

    async def _add_target_company(self, session_state: Dict[str, Any], company: str, **kwargs) -> Dict[str, Any]:
        """Add a target company to search filters."""
        target_companies = session_state.get('target_companies', [])
        
        if company not in target_companies:
            target_companies.append(company)
            session_state['target_companies'] = target_companies
            
            return {
                "success": True,
                "message": f"Added '{company}' to target companies",
                "modifications": [{
                    "type": "target_company_added",
                    "field": "target_companies",
                    "value": company
                }]
            }
        else:
            return {
                "success": True,
                "message": f"'{company}' is already in target companies",
                "modifications": []
            }
    async def _remove_target_company(self, session_state: Dict[str, Any], company: str, **kwargs) -> Dict[str, Any]:
        """Remove a target company from search filters."""
        target_companies = session_state.get('target_companies', [])
        
        # Find and remove matching company (case-insensitive)
        removed_company = None
        for comp in target_companies[:]:
            if company.lower() == comp.lower():
                target_companies.remove(comp)
                removed_company = comp
                break
        
        if removed_company:
            session_state['target_companies'] = target_companies
            return {
                "success": True,
                "message": f"Removed '{removed_company}' from target companies",
                "modifications": [{
                    "type": ModificationType.TARGET_COMPANY_REMOVED.value,
                    "field": "target_companies",
                    "value": removed_company
                }]
            }
        else:
            return {
                "success": False,
                "message": f"'{company}' was not found in target companies",
                "modifications": []
        }