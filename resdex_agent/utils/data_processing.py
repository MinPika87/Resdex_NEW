"""
Data processing utilities for ResDex Agent.
"""

from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Utilities for processing and transforming data."""
    
    @staticmethod
    def normalize_skill(skill: str) -> str:
        """Normalize skill name for consistent matching."""
        from .constants import TECH_SKILLS
        
        # Check against known tech skills for exact matches
        for tech_skill in TECH_SKILLS:
            if skill.lower() == tech_skill.lower():
                return tech_skill
        
        # Return title case version
        return skill.title()
    
    @staticmethod
    def normalize_location(location: str) -> str:
        """Normalize location name for consistent matching."""
        from .constants import CITIES
        
        # Check against known cities for exact matches
        for city in CITIES:
            if location.lower() == city.lower():
                return city
        
        # Return title case version
        return location.title()
    
    @staticmethod
    def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text response."""
        try:
            # Remove thinking tags and extra text
            cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            cleaned_text = cleaned_text.strip()
            
            # Try to find JSON array first
            array_match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
            if array_match:
                json_content = array_match.group(0).strip()
                try:
                    return json.loads(json_content)
                except:
                    pass
            
            # Try to find JSON object
            object_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if object_match:
                json_content = object_match.group(0).strip()
                return json.loads(json_content)
            
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            return None
    
    @staticmethod
    def validate_experience_range(min_exp: float, max_exp: float) -> bool:
        """Validate experience range values."""
        return (0 <= min_exp <= 50 and 
                0 <= max_exp <= 50 and 
                min_exp <= max_exp)
    
    @staticmethod
    def validate_salary_range(min_salary: float, max_salary: float) -> bool:
        """Validate salary range values."""
        return (0 <= min_salary <= 100 and 
                0 <= max_salary <= 100 and 
                min_salary <= max_salary)
    
    @staticmethod
    def format_candidate_data(raw_data: Dict[str, Any], real_name: Optional[str] = None) -> Dict[str, Any]:
        """Format raw candidate data into display format."""
        try:
            candidate = {}
            
            # Basic information
            basic = raw_data.get('basic', {})
            employment = raw_data.get('employment', {})
            education = raw_data.get('education', {})
            skills = raw_data.get('skills', {})
            
            # Name processing
            if real_name:
                candidate['name'] = real_name
            else:
                username = basic.get('username', '')
                if '@' in username:
                    name_part = username.split('@')[0]
                    candidate['name'] = name_part.replace('.', ' ').replace('_', ' ').title()
                else:
                    candidate['name'] = username.title() if username else "Anonymous User"
            
            # Experience and salary
            candidate['experience'] = float(employment.get('stotalexp', 0))
            candidate['salary'] = float(employment.get('ctc_LACS', 0))
            
            # Locations
            candidate['current_location'] = employment.get('scity', 'Not specified')
            pref_locations = employment.get('slocapref', '')
            candidate['preferred_locations'] = [loc.strip() for loc in pref_locations.split(',') if loc.strip()] if pref_locations else []
            
            # Company and role information
            candidate['current_company'] = employment.get('lastorgn', 'Not specified')
            candidate['current_role'] = employment.get('lastdesig', 'Not specified')
            candidate['previous_company'] = employment.get('secorgn', 'Not specified')
            candidate['previous_role'] = employment.get('secdesig', 'Not specified')
            
            # Education
            ug_course = education.get('ugcourse', '')
            ug_inst = education.get('uginst', '')
            ug_year = education.get('ug_YEAR', '')
            pg_course = education.get('pgcourse', '')
            pg_inst = education.get('pginst', '')
            pg_year = education.get('pg_YEAR', '')
            
            if pg_course and pg_inst and pg_year:
                candidate['education_display'] = f"{pg_course}, {pg_inst}, {pg_year}"
            elif ug_course and ug_inst and ug_year:
                candidate['education_display'] = f"{ug_course}, {ug_inst}, {ug_year}"
            else:
                candidate['education_display'] = "Not specified"
            
            # Skills processing
            display_keywords = skills.get('display_keywords', '')
            merged_keywords = skills.get('mergedkeyskill', '')
            
            all_skills = []
            if display_keywords:
                all_skills.extend([skill.strip() for skill in display_keywords.split(',') if skill.strip()])
            if merged_keywords:
                merged_skills = [skill.strip() for skill in merged_keywords.split(',') if skill.strip()]
                all_skills.extend(merged_skills)
            
            # Remove duplicates and limit
            unique_skills = list(dict.fromkeys(all_skills))
            candidate['skills'] = unique_skills[:15] if unique_skills else []
            candidate['may_also_know'] = unique_skills[15:25] if len(unique_skills) > 15 else []
            
            # Additional metadata
            candidate['user_id'] = basic.get('userid')
            candidate['notice_period'] = employment.get('notice_PERIOD', 0)
            candidate['last_active'] = datetime.now().isoformat()
            candidate['last_modified'] = datetime.now().isoformat()
            
            # Mock UI data
            import random
            candidate['views'] = random.randint(50, 500)
            candidate['applications'] = random.randint(10, 50)
            candidate['similar_profiles'] = random.randint(50, 200)
            
            return candidate
            
        except Exception as e:
            logger.error(f"Error formatting candidate data: {e}")
            return {}
