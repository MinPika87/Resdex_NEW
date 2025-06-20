# Replace resdx_agent/utils/data_processing.py with this fixed version

"""
Data processing utilities for ResDex Agent.
"""

from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime
import logging
import random

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
        """Extract JSON object from text response with enhanced patterns."""
        try:
            import json
            import re
            
            # Remove thinking tags and extra text
            cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            cleaned_text = cleaned_text.strip()
            
            # Enhanced JSON extraction patterns
            patterns = [
                # Multi-intent specific pattern
                r'\{[\s\S]*?"is_multi_intent"[\s\S]*?"reasoning":\s*"[^"]*"[\s\S]*?\}',
                # Routing specific pattern  
                r'\{[\s\S]*?"request_type"[\s\S]*?"memory_influenced"[\s\S]*?\}',
                # General object pattern
                r'\{[\s\S]*?\}',
                # Array pattern
                r'\[[\s\S]*?\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, cleaned_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    try:
                        # Clean the match
                        match_clean = match.strip()
                        
                        # Remove trailing commas
                        match_clean = re.sub(r',(\s*[}\]])', r'\1', match_clean)
                        
                        # Try to parse
                        parsed = json.loads(match_clean)
                        
                        # Validate it's the right type of response
                        if isinstance(parsed, dict):
                            # Check for multi-intent response
                            if "is_multi_intent" in parsed:
                                return parsed
                            # Check for routing response
                            elif "request_type" in parsed:
                                return parsed
                            # Check for task breakdown
                            elif "tasks" in parsed:
                                return parsed
                            # Generic object
                            else:
                                return parsed
                        elif isinstance(parsed, list):
                            return parsed
                            
                    except json.JSONDecodeError:
                        continue
            
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
        """Format raw candidate data into display format using working version logic."""
        try:
            candidate = {}
            
            # Basic information
            basic = raw_data.get('basic', {})
            employment = raw_data.get('employment', {})
            education = raw_data.get('education', {})
            skills = raw_data.get('skills', {})
            
            # Get real name from database or fallback to username
            user_id = basic.get('userid')
            print(f"🔍 Processing candidate with User ID: {user_id}")
            
            if real_name:
                candidate['name'] = real_name
                print(f"✅ Using real name from DB for {user_id}: {candidate['name']}")
            else:
                # Fallback to username extraction
                username = basic.get('username', '')
                if '@' in username:
                    name_part = username.split('@')[0]
                    candidate['name'] = name_part.replace('.', ' ').replace('_', ' ').title()
                else:
                    candidate['name'] = username.title() if username else "Anonymous User"
                print(f"⚠️ Using fallback name for {user_id}: {candidate['name']} (Real name not found in DB)")
            
            # Experience
            total_exp = employment.get('stotalexp', '0')
            try:
                candidate['experience'] = float(total_exp) if total_exp else 0.0
            except:
                candidate['experience'] = 0.0
            
            # Salary
            ctc_lacs = employment.get('ctc_LACS', 0)
            candidate['salary'] = float(ctc_lacs) if ctc_lacs else 0.0
            
            # Current location
            candidate['current_location'] = employment.get('scity', 'Not specified')
            
            # Preferred locations
            pref_locations = employment.get('slocapref', '')
            if pref_locations:
                candidate['preferred_locations'] = [loc.strip() for loc in pref_locations.split(',') if loc.strip()]
            else:
                candidate['preferred_locations'] = []
            
            # Current company and role
            candidate['current_company'] = employment.get('lastorgn', 'Not specified')
            candidate['current_role'] = employment.get('lastdesig', 'Not specified')
            
            # Previous company and role
            candidate['previous_company'] = employment.get('secorgn', 'Not specified')
            candidate['previous_role'] = employment.get('secdesig', 'Not specified')
            
            # Education - using pgcourse, pginst, pg_YEAR or fallback to ug fields
            ug_course = education.get('ugcourse', '')
            ug_inst = education.get('uginst', '')
            ug_year = education.get('ug_YEAR', '')
            
            pg_course = education.get('pgcourse', '')
            pg_inst = education.get('pginst', '')
            pg_year = education.get('pg_YEAR', '')
            
            # Prioritize PG education if available, fallback to UG
            if pg_course and pg_inst and pg_year:
                candidate['education_display'] = f"{pg_course}, {pg_inst}, {pg_year}"
            elif pg_course and pg_year:
                candidate['education_display'] = f"{pg_course}, {pg_year}"
            elif ug_course and ug_inst and ug_year:
                candidate['education_display'] = f"{ug_course}, {ug_inst}, {ug_year}"
            elif ug_course and ug_year:
                candidate['education_display'] = f"{ug_course}, {ug_year}"
            else:
                candidate['education_display'] = "Not specified"
            
            # Skills processing using working version logic
            display_keywords = skills.get('display_keywords', '')
            merged_keywords = skills.get('mergedkeyskill', '')
            
            # Combine and clean skills
            all_skills = []
            if display_keywords:
                all_skills.extend([skill.strip() for skill in display_keywords.split(',') if skill.strip()])
            if merged_keywords:
                merged_skills = [skill.strip() for skill in merged_keywords.split(',') if skill.strip()]
                all_skills.extend(merged_skills)
            
            # Remove duplicates and limit (using working version limits)
            unique_skills = list(dict.fromkeys(all_skills))
            candidate['skills'] = unique_skills[:15] if unique_skills else []  # Max 15 skills
            
            # May also know (can be derived from merged keywords if available)
            if len(unique_skills) > 15:
                candidate['may_also_know'] = unique_skills[15:25]  # Next 10 skills
            else:
                candidate['may_also_know'] = []
            
            # Required fields for UI (with defaults matching working version)
            candidate['last_active'] = "2025-01-01"  
            candidate['last_modified'] = "2025-01-01"  
            candidate['views'] = random.randint(50, 500)
            candidate['applications'] = random.randint(10, 50)
            candidate['has_cv'] = True  
            candidate['similar_profiles'] = random.randint(50, 200)
            
            # Store user ID for reference
            candidate['user_id'] = user_id
            
            # Notice period
            notice_period = employment.get('notice_PERIOD', 0)
            candidate['notice_period'] = notice_period
            
            print(f"✅ Successfully mapped candidate: {candidate.get('name', 'Unknown')} with {len(candidate.get('skills', []))} skills")
            
            return candidate
            
        except Exception as e:
            logger.error(f"Error formatting candidate data: {e}")
            print(f"❌ Error mapping candidate data: {e}")
            import traceback
            traceback.print_exc()
            return None