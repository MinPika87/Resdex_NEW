# resdex_agent/tools/matrix_expansion_tool.py - FIXED: Singleton + Skill Extraction
"""
Matrix-based skill and title expansion tool with singleton pattern and fixed skill extraction.
"""

import time
import os
import sys
import threading
from typing import Dict, Any, List, Optional, Tuple
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


class MatrixExpansionTool(Tool):
    """
    Matrix-based expansion tool with singleton pattern to prevent reloading.
    """
    
    # Class-level variables for singleton pattern
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    # Shared matrix system instances
    _skill_convertor = None
    _title_convertor = None
    _matrix_features = None
    _feature_matrix_loader = None
    _initialization_error = None
    
    def __new__(cls, name: str = "matrix_expansion_tool"):
        """Singleton pattern to ensure only one instance with loaded matrices."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MatrixExpansionTool, cls).__new__(cls)
            return cls._instance
    
    def __init__(self, name: str = "matrix_expansion_tool"):
        # Only initialize once
        if self._initialized:
            print(f"🔄 MatrixExpansionTool: Reusing existing matrix system (no reload)")
            super().__init__(name=name, description="Matrix-based skill and title expansion")
            return
        
        super().__init__(name=name, description="Matrix-based skill and title expansion")
        
        # Initialize matrix system only once
        self._initialize_matrix_system_once()
        self._initialized = True
    
    @classmethod
    def _initialize_matrix_system_once(cls):
        """Initialize matrix system only once for all instances."""
        if cls._initialized:
            return
            
        try:
            print("🔧 MatrixExpansionTool: First-time initialization (loading matrices...)")
            start_time = time.time()
            
            # Get the current tools directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"📁 Tools directory: {current_dir}")
            
            # Add current directory to Python path for local imports
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                print(f"✅ Added tools directory to Python path")
            
            # Step 1: Import MatrixFeatures from tools/MatrixFeatures.py
            try:
                print("📦 Step 1: Importing MatrixFeatures from tools/MatrixFeatures.py...")
                from MatrixFeatures import MatrixFeatures
                cls._matrix_features = MatrixFeatures()
                print("✅ MatrixFeatures imported and initialized successfully")
            except ImportError as e:
                print(f"❌ MatrixFeatures import failed: {e}")
                raise ImportError(f"Could not import MatrixFeatures from tools: {e}")
            
            # Step 2: Import FeatureMatrixLoader from tools/FeatureMatrixLoader.py
            try:
                print("📦 Step 2: Importing FeatureMatrixLoader from tools/FeatureMatrixLoader.py...")
                from FeatureMatrixLoader import FeatureMatrixLoader
                cls._feature_matrix_loader = FeatureMatrixLoader()
                print("✅ FeatureMatrixLoader imported and initialized successfully")
            except ImportError as e:
                print(f"⚠️ FeatureMatrixLoader import failed: {e}")
                cls._feature_matrix_loader = None
            
            # Step 3: Try to import SkillConvertor from taxonomy
            try:
                print("📦 Step 3: Importing SkillConvertor from taxonomy...")
                from taxonomy.common_functions import SkillConvertor
                cls._skill_convertor = SkillConvertor()
                print("✅ SkillConvertor imported from installed taxonomy package")
            except ImportError as e:
                print(f"⚠️ SkillConvertor import failed: {e}")
                cls._skill_convertor = None
            
            # Step 4: NEW - Import TitleConvertor from taxonomy
            try:
                print("📦 Step 4: Importing TitleConvertor from taxonomy...")
                from taxonomy.common_functions import TitleConvertor
                cls._title_convertor = TitleConvertor()
                print("✅ TitleConvertor imported from installed taxonomy package")
            except ImportError as e:
                print(f"⚠️ TitleConvertor import failed: {e}")
                cls._title_convertor = None
            
            # Step 5: Verify MatrixFeatures has the required methods
            print("🔍 Step 5: Verifying MatrixFeatures methods...")
            available_features = []
            
            if hasattr(cls._matrix_features, 'skillToSkillFeature'):
                available_features.append("skill_to_skill")
                print("✅ skillToSkillFeature available")
            
            if hasattr(cls._matrix_features, 'skillToTitleFeature'):
                available_features.append("skill_to_title")
                print("✅ skillToTitleFeature available")
            
            if hasattr(cls._matrix_features, 'titleToSkillFeature'):
                available_features.append("title_to_skill")
                print("✅ titleToSkillFeature available")
            
            if hasattr(cls._matrix_features, 'titleToTitleFeature'):
                available_features.append("title_to_title")
                print("✅ titleToTitleFeature available")
            
            if not available_features:
                raise AttributeError("MatrixFeatures object has no recognizable feature methods")
            
            total_time = time.time() - start_time
            print(f"🎉 Matrix system initialization complete in {total_time:.2f} seconds!")
            print(f"📊 Available features: {available_features}")
            print(f"🔧 MatrixFeatures: ✅")
            print(f"🔧 FeatureMatrixLoader: {'✅' if cls._feature_matrix_loader else '❌'}")
            print(f"🔧 SkillConvertor: {'✅' if cls._skill_convertor else '❌ (will use fallback)'}")
            print(f"🔧 TitleConvertor: {'✅' if cls._title_convertor else '❌ (will use fallback)'}")
            
            logger.info(f"Matrix expansion tool initialized with features: {available_features}")
            
        except Exception as e:
            logger.error(f"Matrix system initialization failed: {e}")
            print(f"❌ Matrix system initialization failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Set error for all instances
            cls._initialization_error = str(e)
            cls._skill_convertor = None
            cls._title_convertor = None
            cls._matrix_features = None
            cls._feature_matrix_loader = None

    
    def _is_available(self) -> bool:
        """Check if matrix system is available."""
        return self._matrix_features is not None and self._initialization_error is None
    
    def _convert_skill_to_id(self, skill: str):
        """Convert skill name to ID using SkillConvertor (for skills only)."""
        if self._skill_convertor:
            try:
                # Try multiple skill name variations
                skill_variations = [
                    skill,
                    skill.lower(),
                    skill.upper(),
                    skill.title(),
                    skill.replace(' ', '_'),
                    skill.replace('_', ' ')
                ]
                
                for variation in skill_variations:
                    try:
                        result = self._skill_convertor.convert(variation)
                        if result and result != "UNKNOWN" and result is not None:
                            print(f"🔄 SkillConvertor: '{skill}' (via '{variation}') -> {result}")
                            return result
                    except Exception as e:
                        continue
                
                print(f"⚠️ SkillConvertor failed for all variations of '{skill}'")
            except Exception as e:
                print(f"⚠️ SkillConvertor error for '{skill}': {e}")
        
        # Fallback: use skill normalization
        normalized_skill = self._normalize_skill_for_matrix(skill)
        print(f"🔄 Skill fallback mapping: '{skill}' -> '{normalized_skill}'")
        return normalized_skill

    def _normalize_skill_for_matrix(self, skill: str) -> str:
        """Normalize skill name for matrix lookup."""
        if not skill:
            return ""
        
        # Common skill normalizations for matrix system
        skill_normalizations = {
            'python': 'python',
            'java': 'java',
            'javascript': 'javascript', 
            'react': 'reactjs',
            'angular': 'angularjs',
            'node.js': 'nodejs',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'machine learning': 'machine_learning',
            'data science': 'data_science',
            'artificial intelligence': 'ai',
            'deep learning': 'deep_learning',
            'tensorflow': 'tensorflow',
            'pytorch': 'pytorch',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'scikit-learn': 'sklearn',
            'django': 'django',
            'flask': 'flask',
            'fastapi': 'fastapi',
            'spring': 'spring',
            'hibernate': 'hibernate',
            'aws': 'aws',
            'docker': 'docker',
            'kubernetes': 'kubernetes',
            'jenkins': 'jenkins',
            'git': 'git',
            'mysql': 'mysql',
            'postgresql': 'postgresql',
            'mongodb': 'mongodb',
            'redis': 'redis'
        }
        
        skill_lower = skill.lower().strip()
        
        # Direct mapping
        if skill_lower in skill_normalizations:
            return skill_normalizations[skill_lower]
        
        # Fallback: clean the skill name
        normalized = skill_lower.replace(' ', '_').replace('-', '_').replace('.', '')
        return normalized
    def _convert_id_to_skill(self, skill_id):
        """Convert skill ID back to name."""
        if self._skill_convertor:
            try:
                result = self._skill_convertor.convert(skill_id)
                if result and result != "UNKNOWN":
                    return result
            except Exception as e:
                print(f"⚠️ SkillConvertor reverse failed for '{skill_id}': {e}")
        
        # Fallback: use ID as name
        return str(skill_id).replace('_', ' ').title()
    
    def _extract_base_skills(self, user_input: str, session_state: Dict[str, Any]) -> List[str]:
        """FIXED: Enhanced skill extraction that properly captures multiple skills."""
        skills = []
        input_lower = user_input.lower()
        
        print(f"🔍 SKILL EXTRACTION DEBUG:")
        print(f"  - Original input: '{user_input}'")
        print(f"  - Lowercase input: '{input_lower}'")
        
        skill_patterns = [
            # Pattern 1: "skills to X" - capture everything after "to"
            r"(?:skills?\s+(?:to|like|similar\s+to)\s+)(.+?)(?:\s*$)",
            # Pattern 2: "similar skills to X" - capture everything after "to"
            r"(?:similar\s+skills?\s+to\s+)(.+?)(?:\s*$)",
            # Pattern 3: "find skills similar to X" - capture everything after "to"
            r"(?:find\s+skills?\s+(?:similar\s+to|like)\s+)(.+?)(?:\s*$)",
            # Pattern 4: "expand X skills" - capture everything before "skills"
            r"(?:expand\s+)(.+?)(?:\s+skills?)",
            # Pattern 5: "like X" - capture everything after "like"
            r"(?:like\s+)(.+?)(?:\s+(?:skill|programming|language|$))",
            # Pattern 6: "related to X" - capture everything after "to"
            r"(?:related\s+to\s+)(.+?)(?:\s+(?:skill|programming|language|$))"
        ]
        
        import re
        for i, pattern in enumerate(skill_patterns):
            print(f"  - Trying pattern {i+1}: {pattern}")
            match = re.search(pattern, input_lower, re.IGNORECASE)
            if match:
                skill_text = match.group(1).strip()
                print(f"  ✅ Pattern {i+1} matched: '{skill_text}'")
                
                # FIXED: Parse multiple skills from the matched text
                skills = self._parse_multiple_skills(skill_text)
                print(f"  📝 Parsed skills: {skills}")
                
                # Break after first successful match
                if skills:
                    break
        
        # If no skills found in input, check session state
        if not skills:
            print(f"  - No skills found in input, checking session state...")
            keywords = session_state.get('keywords', [])
            if keywords:
                # Use the last added skill as base
                last_skill = keywords[-1].replace('★ ', '')
                cleaned_skill = self._clean_skill_name(last_skill)
                if cleaned_skill:
                    skills.append(cleaned_skill)
                    print(f"  ✅ Using session skill: '{cleaned_skill}'")
        
        # Remove duplicates while preserving order
        unique_skills = list(dict.fromkeys(skills))
        print(f"  📊 Final extracted skills: {unique_skills}")
        return unique_skills

    def _parse_multiple_skills(self, skill_text: str) -> List[str]:
        """Parse multiple skills from text like 'figma and CAD' or 'python, java, react'."""
        import re
        
        print(f"    🔍 Parsing multiple skills from: '{skill_text}'")
        
        # Clean up the input text first
        skill_text = skill_text.strip()
        
        # Split on multiple separators while preserving multi-word skills
        separators_pattern = r'\s+(?:and|or|,|\&)\s+'
        
        # Split the text using the pattern
        potential_skills = re.split(separators_pattern, skill_text, flags=re.IGNORECASE)
        
        print(f"    🔧 Split candidates: {potential_skills}")
        
        # Clean and validate each skill
        cleaned_skills = []
        for skill in potential_skills:
            skill = skill.strip()
            
            # Remove any trailing punctuation or words
            skill = re.sub(r'\s+(?:skill|skills|programming|language|technology)$', '', skill, flags=re.IGNORECASE)
            skill = skill.strip(' .,;')
            
            if skill and len(skill) > 1:
                cleaned_skill = self._clean_skill_name(skill)
                if cleaned_skill and len(cleaned_skill) > 1:
                    # Additional validation: not common words
                    if cleaned_skill.lower() not in ['and', 'or', 'the', 'a', 'an', 'to', 'for', 'with', 'in', 'on', 'at']:
                        cleaned_skills.append(cleaned_skill)
                        print(f"    ✅ Valid skill: '{cleaned_skill}'")
                    else:
                        print(f"    ❌ Rejected common word: '{cleaned_skill}'")
                else:
                    print(f"    ❌ Rejected after cleaning: '{skill}'")
            else:
                print(f"    ❌ Rejected too short: '{skill}'")
        
        return cleaned_skills

    def _clean_skill_name(self, skill: str) -> str:
        """Clean and normalize skill name - ENHANCED."""
        if not skill:
            return ""
        
        # Remove common suffixes and clean
        skill = skill.strip()
        
        # Remove trailing words that might be captured by regex
        stop_suffixes = ['skill', 'skills', 'programming', 'language', 'technology', 'tool', 'tools']
        for suffix in stop_suffixes:
            if skill.lower().endswith(f' {suffix}'):
                skill = skill[:-len(suffix)-1].strip()
        
        # Handle common skill name variations and normalizations
        skill_mappings = {
            # Programming languages
            'pytho': 'python', 'python': 'Python',
            'javascrip': 'javascript', 'javascript': 'JavaScript', 'js': 'JavaScript',
            'jav': 'java', 'java': 'Java',
            'c++': 'C++', 'cpp': 'C++', 'c plus plus': 'C++',
            'c#': 'C#', 'csharp': 'C#', 'c sharp': 'C#',
            
            # Design tools
            'figma': 'Figma',
            'sketch': 'Sketch', 
            'adobe xd': 'Adobe XD', 'xd': 'Adobe XD',
            'photoshop': 'Photoshop',
            'illustrator': 'Illustrator',
            'cad': 'CAD', 'autocad': 'AutoCAD',
            
            # Web technologies
            'reac': 'react', 'react': 'React',
            'angula': 'angular', 'angular': 'Angular',
            'nod': 'node.js', 'node': 'Node.js', 'nodejs': 'Node.js',
            'sql': 'SQL', 'mysql': 'MySQL', 'postgresql': 'PostgreSQL',
            'htm': 'html', 'html': 'HTML',
            'cs': 'css', 'css': 'CSS',
            
            # Other technologies
            'aws': 'AWS', 'amazon web services': 'AWS',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
            'jenkins': 'Jenkins',
            'git': 'Git',
            'mongodb': 'MongoDB', 'mongo': 'MongoDB',
            'redis': 'Redis'
        }
        
        skill_lower = skill.lower().strip()
        
        # Direct mapping
        if skill_lower in skill_mappings:
            return skill_mappings[skill_lower]
        
        # Fallback: proper case the skill name
        # Handle special cases for acronyms and camelCase
        if skill_lower.isupper() or len(skill_lower) <= 3:
            # Likely an acronym, keep uppercase
            cleaned = skill.upper()
        elif skill_lower.islower() and ' ' not in skill_lower:
            # Single word, title case
            cleaned = skill.title()
        else:
            # Multi-word, title case each word
            cleaned = ' '.join(word.title() for word in skill.split())
        
        return cleaned
    def _convert_title_to_id(self, title: str):
        """Convert title name to ID using TitleConvertor."""
        if self._title_convertor:
            try:
                # Try multiple title name variations
                title_variations = [
                    title,
                    title.lower(),
                    title.title(),
                    title.replace(' ', '_'),
                    title.replace('_', ' '),
                    # Try common title variations
                    title.replace(' Engineer', '').strip(),
                    title.replace(' Developer', '').strip(),
                    title.replace(' Manager', '').strip(),
                    title.replace(' Scientist', '').strip(),
                    title.replace(' Analyst', '').strip()
                ]
                
                for variation in title_variations:
                    try:
                        result = self._title_convertor.convert(variation)
                        if result and result != "UNKNOWN" and result is not None:
                            print(f"🔄 TitleConvertor: '{title}' (via '{variation}') -> {result}")
                            return result
                    except Exception as e:
                        continue
                
                print(f"⚠️ TitleConvertor failed for all variations of '{title}'")
            except Exception as e:
                print(f"⚠️ TitleConvertor error for '{title}': {e}")
        
        # Fallback: use title normalization
        normalized_title = self._normalize_title_for_matrix(title)
        print(f"🔄 Title fallback mapping: '{title}' -> '{normalized_title}'")
        return normalized_title

    def _convert_id_to_title(self, title_id):
        """Convert title ID back to name using TitleConvertor."""
        if self._title_convertor:
            try:
                result = self._title_convertor.convert(title_id)
                if result and result != "UNKNOWN":
                    return result
            except Exception as e:
                print(f"⚠️ TitleConvertor reverse failed for '{title_id}': {e}")
        
        # Fallback: use ID as name
        return str(title_id).replace('_', ' ').title()

    def _normalize_title_for_matrix(self, title: str) -> str:
        """Normalize title name for matrix lookup."""
        if not title:
            return ""
        
        # Common title normalizations for matrix system
        title_normalizations = {
            'data scientist': 'data_scientist',
            'software engineer': 'software_engineer', 
            'software developer': 'software_developer',
            'full stack developer': 'fullstack_developer',
            'frontend developer': 'frontend_developer',
            'backend developer': 'backend_developer',
            'devops engineer': 'devops_engineer',
            'ml engineer': 'ml_engineer',
            'machine learning engineer': 'machine_learning_engineer',
            'product manager': 'product_manager',
            'project manager': 'project_manager',
            'business analyst': 'business_analyst',
            'data analyst': 'data_analyst',
            'data engineer': 'data_engineer',
            'ui designer': 'ui_designer',
            'ux designer': 'ux_designer',
            'product designer': 'product_designer',
            'qa engineer': 'qa_engineer',
            'test engineer': 'test_engineer',
            'tech lead': 'tech_lead',
            'team lead': 'team_lead',
            'automation engineer': 'automation_engineer'
        }
        
        title_lower = title.lower().strip()
        
        # Direct mapping
        if title_lower in title_normalizations:
            return title_normalizations[title_lower]
        
        # Fallback: clean the title name
        normalized = title_lower.replace(' ', '_').replace('-', '_').replace('.', '')
        return normalized
    def _extract_base_titles(self, user_input: str, session_state: Dict[str, Any]) -> List[str]:
        """FIXED: Enhanced title extraction that properly captures multiple titles."""
        titles = []
        input_lower = user_input.lower()
        
        print(f"🔍 TITLE EXTRACTION DEBUG:")
        print(f"  - Original input: '{user_input}'")
        print(f"  - Lowercase input: '{input_lower}'")
        
        # FIXED: Enhanced patterns that capture multiple titles
        title_patterns = [
            # Pattern 1: "titles to X" - capture everything after "to"
            r"(?:titles?\s+(?:to|like|similar\s+to)\s+)(.+?)(?:\s*$)",
            # Pattern 2: "similar titles to X" - capture everything after "to"
            r"(?:similar\s+titles?\s+to\s+)(.+?)(?:\s*$)",
            # Pattern 3: "find titles similar to X" - capture everything after "to"
            r"(?:find\s+titles?\s+(?:similar\s+to|like)\s+)(.+?)(?:\s*$)",
            # Pattern 4: "expand X titles" - capture everything before "titles"
            r"(?:expand\s+)(.+?)(?:\s+titles?)",
            # Pattern 5: "roles like X" - capture everything after "like"
            r"(?:roles?\s+(?:like|similar\s+to)\s+)(.+?)(?:\s*$)",
            # Pattern 6: "positions similar to X" - capture everything after "to"
            r"(?:positions?\s+(?:similar\s+to|like)\s+)(.+?)(?:\s*$)"
        ]
        
        import re
        for i, pattern in enumerate(title_patterns):
            print(f"  - Trying pattern {i+1}: {pattern}")
            match = re.search(pattern, input_lower, re.IGNORECASE)
            if match:
                title_text = match.group(1).strip()
                print(f"  ✅ Pattern {i+1} matched: '{title_text}'")
                
                # Parse multiple titles from the matched text
                titles = self._parse_multiple_titles(title_text)
                print(f"  📝 Parsed titles: {titles}")
                
                # Break after first successful match
                if titles:
                    break
        
        # If no titles found in input, check session state
        if not titles:
            print(f"  - No titles found in input, checking session state...")
            # Could check for current job titles in session if we track them
            # For now, return empty
        
        # Remove duplicates while preserving order
        unique_titles = list(dict.fromkeys(titles))
        print(f"  📊 Final extracted titles: {unique_titles}")
        return unique_titles

    def _parse_multiple_titles(self, title_text: str) -> List[str]:
        """Parse multiple titles from text like 'data scientist and software engineer'."""
        import re
        
        print(f"    🔍 Parsing multiple titles from: '{title_text}'")
        
        # Clean up the input text first
        title_text = title_text.strip()
        
        # Split on multiple separators while preserving multi-word titles
        separators_pattern = r'\s+(?:and|or|,|\&)\s+'
        
        # Split the text using the pattern
        potential_titles = re.split(separators_pattern, title_text, flags=re.IGNORECASE)
        
        print(f"    🔧 Split candidates: {potential_titles}")
        
        # Clean and validate each title
        cleaned_titles = []
        for title in potential_titles:
            title = title.strip()
            
            # Remove any trailing punctuation or words
            title = re.sub(r'\s+(?:role|roles|position|positions|job|jobs)$', '', title, flags=re.IGNORECASE)
            title = title.strip(' .,;')
            
            if title and len(title) > 2:  # Titles are usually longer than skills
                cleaned_title = self._clean_title_name(title)
                if cleaned_title and len(cleaned_title) > 2:
                    # Additional validation: not common words
                    if cleaned_title.lower() not in ['and', 'or', 'the', 'a', 'an', 'to', 'for', 'with', 'in', 'on', 'at', 'role', 'position']:
                        cleaned_titles.append(cleaned_title)
                        print(f"    ✅ Valid title: '{cleaned_title}'")
                    else:
                        print(f"    ❌ Rejected common word: '{cleaned_title}'")
                else:
                    print(f"    ❌ Rejected after cleaning: '{title}'")
            else:
                print(f"    ❌ Rejected too short: '{title}'")
        
        return cleaned_titles

    def _clean_title_name(self, title: str) -> str:
        """Clean and normalize title name."""
        if not title:
            return ""
        
        # Remove common suffixes and clean
        title = title.strip()
        
        # Remove trailing words that might be captured by regex
        stop_suffixes = ['role', 'roles', 'position', 'positions', 'job', 'jobs']
        for suffix in stop_suffixes:
            if title.lower().endswith(f' {suffix}'):
                title = title[:-len(suffix)-1].strip()
        
        # Handle common title name variations and normalizations
        title_mappings = {
            # Tech roles
            'data scientist': 'Data Scientist',
            'software engineer': 'Software Engineer', 
            'software developer': 'Software Developer',
            'full stack developer': 'Full Stack Developer',
            'frontend developer': 'Frontend Developer',
            'backend developer': 'Backend Developer',
            'devops engineer': 'DevOps Engineer',
            'ml engineer': 'ML Engineer',
            'machine learning engineer': 'Machine Learning Engineer',
            
            # Design roles
            'ui designer': 'UI Designer',
            'ux designer': 'UX Designer',
            'product designer': 'Product Designer',
            'graphic designer': 'Graphic Designer',
            
            # Management roles
            'product manager': 'Product Manager',
            'project manager': 'Project Manager',
            'tech lead': 'Tech Lead',
            'team lead': 'Team Lead',
            
            # Data roles
            'data analyst': 'Data Analyst',
            'business analyst': 'Business Analyst',
            'data engineer': 'Data Engineer',
            
            # QA roles
            'qa engineer': 'QA Engineer',
            'test engineer': 'Test Engineer',
            'automation engineer': 'Automation Engineer'
        }
        
        title_lower = title.lower().strip()
        
        # Direct mapping
        if title_lower in title_mappings:
            return title_mappings[title_lower]
        
        # Fallback: proper case the title name
        # Title case each word for professional titles
        cleaned = ' '.join(word.title() for word in title.split())
        
        return cleaned
    async def __call__(self, 
                      expansion_type: str,
                      base_items: List[str],
                      top_n: int = 5,
                      normalize: bool = True) -> Dict[str, Any]:
        """
        Perform matrix-based expansion using singleton instance.
        """
        try:
            if not self._is_available():
                error_msg = self._initialization_error or "Matrix expansion system not available"
                return {
                    "success": False,
                    "error": f"Matrix expansion system not available: {error_msg}",
                    "method": "matrix_unavailable"
                }
            
            print(f"🎯 MATRIX EXPANSION: {expansion_type}")
            print(f"📝 Base items: {base_items}")
            print(f"🔢 Requesting top {top_n} results")
            
            start_time = time.time()
            
            if expansion_type == "skill_to_skill":
                return await self._expand_skill_to_skill(base_items, top_n, normalize)
            elif expansion_type == "skill_to_title":
                return await self._expand_skill_to_title(base_items, top_n, normalize)
            elif expansion_type == "title_to_skill":
                return await self._expand_title_to_skill(base_items, top_n, normalize)
            elif expansion_type == "title_to_title":
                return await self._expand_title_to_title(base_items, top_n, normalize)
            else:
                return {
                    "success": False,
                    "error": f"Unknown expansion type: {expansion_type}",
                    "method": "invalid_type"
                }
                
        except Exception as e:
            logger.error(f"Matrix expansion failed: {e}")
            print(f"❌ Matrix expansion error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "method": "matrix_error"
            }
    
    async def _expand_skill_to_skill(self, skills: List[str], top_n: int, normalize: bool) -> Dict[str, Any]:
        """Expand skills to related skills - FIXED to use multiple skills collectively."""
        try:
            print(f"🔧 SKILL-TO-SKILL EXPANSION for: {skills}")
            
            if not hasattr(self._matrix_features, 'skillToSkillFeature'):
                return {
                    "success": False,
                    "error": "skillToSkillFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert ALL skill names to IDs first
            skill_ids = []
            skill_mapping = {}
            
            for skill in skills:
                skill_id = self._convert_skill_to_id(skill)
                if skill_id and skill_id != "":
                    skill_ids.append(skill_id)
                    skill_mapping[skill_id] = skill
                    print(f"  ✅ {skill} -> ID: {skill_id}")
                else:
                    print(f"  ❌ {skill} -> No valid ID found")
            
            if not skill_ids:
                print(f"❌ No valid skill IDs found, falling back to LLM")
                return {
                    "success": False,
                    "error": "No valid skill IDs found",
                    "method": "skill_to_skill_matrix"
                }
            
            # CRITICAL FIX: Pass ALL skill IDs to matrix at once
            # This finds skills similar to the COMBINATION of input skills
            print(f"🔍 Calling skillToSkillFeature.get_feature_value...")
            print(f"  - Input IDs: {skill_ids}")
            print(f"  - TopN: {top_n * 2}")
            print(f"  - Normalize: {normalize}")
            
            # This is the correct usage - multiple skills as input
            expansion_results = self._matrix_features.skillToSkillFeature.get_feature_value(
                skill_ids, topN=top_n * 2, normalize=normalize
            )
            
            print(f"📊 Matrix returned {len(expansion_results)} results")
            print(f"🎯 Finding skills similar to ALL input skills: {[skill_mapping.get(sid, sid) for sid in skill_ids]}")
            
            # Convert back to skill names and format results
            expanded_skills = []
            processed_count = 0
            
            for skill_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                # Skip if it's one of the input skills
                if skill_id in skill_mapping:
                    print(f"  ⏭️  Skipping input skill: {skill_mapping[skill_id]} (ID: {skill_id})")
                    continue
                    
                skill_name = self._convert_id_to_skill(skill_id)
                if skill_name and skill_name != "UNKNOWN" and processed_count < top_n:
                    expanded_skills.append({
                        "name": skill_name,
                        "id": skill_id,
                        "score": float(score),
                        "type": "skill"
                    })
                    processed_count += 1
                    print(f"  🎯 {skill_name} (ID: {skill_id}, Score: {score:.4f})")
            
            return {
                "success": True,
                "expansion_type": "skill_to_skill",
                "base_items": skills,
                "expanded_items": expanded_skills,
                "total_found": len(expansion_results),
                "method": "skill_to_skill_matrix",
                "message": f"Found {len(expanded_skills)} skills similar to ALL input skills: {', '.join(skills)}"
            }
            
        except Exception as e:
            logger.error(f"Skill-to-skill expansion failed: {e}")
            print(f"❌ Skill-to-skill expansion error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "method": "skill_to_skill_matrix"
            }
    
    async def _expand_skill_to_title(self, skills: List[str], top_n: int, normalize: bool) -> Dict[str, Any]:
        """Expand skills to related titles."""
        try:
            print(f"🔧 SKILL-TO-TITLE EXPANSION for: {skills}")
            
            if not hasattr(self._matrix_features, 'skillToTitleFeature'):
                return {
                    "success": False,
                    "error": "skillToTitleFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert skill names to IDs
            skill_ids = []
            for skill in skills:
                skill_id = self._convert_skill_to_id(skill)
                if skill_id:
                    skill_ids.append(skill_id)
                    print(f"  ✅ {skill} -> ID: {skill_id}")
            
            if not skill_ids:
                return {
                    "success": False,
                    "error": "No valid skill IDs found",
                    "method": "skill_to_title_matrix"
                }
            
            # Call the matrix feature
            print(f"🔍 Calling skillToTitleFeature.get_feature_value...")
            expansion_results = self._matrix_features.skillToTitleFeature.get_feature_value(
                skill_ids, topN=top_n * 2, normalize=normalize
            )
            
            print(f"📊 Matrix returned {len(expansion_results)} results")
            
            # Convert title IDs back to names
            expanded_titles = []
            processed_count = 0
            
            for title_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                title_name = self._convert_id_to_skill(title_id)
                if title_name and title_name != "UNKNOWN" and processed_count < top_n:
                    expanded_titles.append({
                        "name": title_name,
                        "id": title_id,
                        "score": float(score),
                        "type": "title"
                    })
                    processed_count += 1
                    print(f"  🎯 {title_name} (ID: {title_id}, Score: {score:.4f})")
            
            return {
                "success": True,
                "expansion_type": "skill_to_title",
                "base_items": skills,
                "expanded_items": expanded_titles,
                "total_found": len(expansion_results),
                "method": "skill_to_title_matrix",
                "message": f"Found {len(expanded_titles)} related titles for skills using matrix analysis"
            }
            
        except Exception as e:
            logger.error(f"Skill-to-title expansion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "skill_to_title_matrix"
            }
    
    async def _expand_title_to_skill(self, titles: List[str], top_n: int, normalize: bool) -> Dict[str, Any]:
        """Expand titles to related skills using TitleConvertor."""
        try:
            print(f"🔧 TITLE-TO-SKILL EXPANSION for: {titles}")
            
            if not hasattr(self._matrix_features, 'titleToSkillFeature'):
                return {
                    "success": False,
                    "error": "titleToSkillFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert title names to IDs using TitleConvertor
            title_ids = []
            for title in titles:
                title_id = self._convert_title_to_id(title)  # Use TitleConvertor
                if title_id:
                    title_ids.append(title_id)
                    print(f"  ✅ {title} -> ID: {title_id}")
            
            if not title_ids:
                return {
                    "success": False,
                    "error": "No valid title IDs found",
                    "method": "title_to_skill_matrix"
                }
            
            # Call the matrix feature
            print(f"🔍 Calling titleToSkillFeature.get_feature_value...")
            expansion_results = self._matrix_features.titleToSkillFeature.get_feature_value(
                title_ids, topN=top_n * 2, normalize=normalize
            )
            
            print(f"📊 Matrix returned {len(expansion_results)} results")
            
            # Validate that we actually got meaningful results
            if not expansion_results or len(expansion_results) == 0:
                print(f"❌ Matrix returned empty results - titles may not exist in matrix")
                return {
                    "success": False,
                    "error": "No skills found in matrix database for the given titles",
                    "method": "title_to_skill_matrix",
                    "details": f"Title IDs {title_ids} not found in matrix"
                }
            
            # Convert skill IDs back to names using SkillConvertor
            expanded_skills = []
            processed_count = 0
            
            for skill_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                skill_name = self._convert_id_to_skill(skill_id)  # Use SkillConvertor for skills
                if skill_name and skill_name != "UNKNOWN" and processed_count < top_n:
                    expanded_skills.append({
                        "name": skill_name,
                        "id": skill_id,
                        "score": float(score),
                        "type": "skill"
                    })
                    processed_count += 1
                    print(f"  🎯 {skill_name} (ID: {skill_id}, Score: {score:.4f})")
            
            # Validate that we got actual expanded skills
            if not expanded_skills:
                print(f"❌ No valid expanded skills after processing")
                return {
                    "success": False,
                    "error": "No valid skills found after processing matrix results",
                    "method": "title_to_skill_matrix"
                }
            
            return {
                "success": True,
                "expansion_type": "title_to_skill",
                "base_items": titles,
                "expanded_items": expanded_skills,
                "total_found": len(expansion_results),
                "method": "title_to_skill_matrix",
                "message": f"Found {len(expanded_skills)} related skills for titles using matrix analysis"
            }
            
        except Exception as e:
            logger.error(f"Title-to-skill expansion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "title_to_skill_matrix"
            }
    async def _expand_title_to_title(self, titles: List[str], top_n: int, normalize: bool) -> Dict[str, Any]:
        """Expand titles to related titles using TitleConvertor."""
        try:
            print(f"🔧 TITLE-TO-TITLE EXPANSION for: {titles}")
            
            if not hasattr(self._matrix_features, 'titleToTitleFeature'):
                return {
                    "success": False,
                    "error": "titleToTitleFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert title names to IDs using TitleConvertor
            title_ids = []
            title_mapping = {}
            
            for title in titles:
                title_id = self._convert_title_to_id(title)  # Use TitleConvertor
                if title_id:
                    title_ids.append(title_id)
                    title_mapping[title_id] = title
                    print(f"  ✅ {title} -> ID: {title_id}")
                else:
                    print(f"  ❌ {title} -> No valid ID found")
            
            if not title_ids:
                return {
                    "success": False,
                    "error": "No valid title IDs found",
                    "method": "title_to_title_matrix"
                }
            
            # Call the matrix feature
            print(f"🔍 Calling titleToTitleFeature.get_feature_value...")
            expansion_results = self._matrix_features.titleToTitleFeature.get_feature_value(
                title_ids, topN=top_n * 2, normalize=normalize
            )
            
            print(f"📊 Matrix returned {len(expansion_results)} results")
            
            # Validate that we actually got meaningful results
            if not expansion_results or len(expansion_results) == 0:
                print(f"❌ Matrix returned empty results - titles may not exist in matrix")
                return {
                    "success": False,
                    "error": "No titles found in matrix database for the given inputs",
                    "method": "title_to_title_matrix",
                    "details": f"Title IDs {title_ids} not found in matrix"
                }
            
            # Convert back to title names and format results
            expanded_titles = []
            processed_count = 0
            
            for title_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                # Skip if it's one of the input titles
                if title_id in title_mapping:
                    print(f"  ⏭️  Skipping input title: {title_mapping[title_id]} (ID: {title_id})")
                    continue
                    
                title_name = self._convert_id_to_title(title_id)  # Use TitleConvertor
                if title_name and title_name != "UNKNOWN" and processed_count < top_n:
                    expanded_titles.append({
                        "name": title_name,
                        "id": title_id,
                        "score": float(score),
                        "type": "title"
                    })
                    processed_count += 1
                    print(f"  🎯 {title_name} (ID: {title_id}, Score: {score:.4f})")
            
            # Validate that we got actual expanded titles
            if not expanded_titles:
                print(f"❌ No valid expanded titles after processing")
                return {
                    "success": False,
                    "error": "No valid expanded titles found after processing matrix results",
                    "method": "title_to_title_matrix"
                }
            
            return {
                "success": True,
                "expansion_type": "title_to_title",
                "base_items": titles,
                "expanded_items": expanded_titles,
                "total_found": len(expansion_results),
                "method": "title_to_title_matrix",
                "message": f"Found {len(expanded_titles)} related titles using matrix analysis"
            }
            
        except Exception as e:
            logger.error(f"Title-to-title expansion failed: {e}")
            print(f"❌ Title-to-title expansion error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "title_to_title_matrix"
            }

    
    
    def get_matrix_stats(self) -> Dict[str, Any]:
        """Get statistics about the matrix system."""
        try:
            if not self._is_available():
                return {
                    "available": False,
                    "error": self._initialization_error or "Matrix system not initialized"
                }
            
            return {
                "available": True,
                "features": {
                    "skill_to_skill": hasattr(self._matrix_features, 'skillToSkillFeature'),
                    "skill_to_title": hasattr(self._matrix_features, 'skillToTitleFeature'),
                    "title_to_skill": hasattr(self._matrix_features, 'titleToSkillFeature'),
                    "title_to_title": hasattr(self._matrix_features, 'titleToTitleFeature')
                },
                "feature_matrix_loader_available": self._feature_matrix_loader is not None,
                "skill_convertor_available": self._skill_convertor is not None,
                "title_convertor_available": self._title_convertor is not None,  # NEW
                "singleton_initialized": self._initialized
            }
            
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

# Test function 
async def test_matrix_expansion():
    """Test function for matrix expansion."""
    print("🧪 Testing Matrix Expansion with singleton pattern...")
    
    # Test multiple instances - should reuse matrix system
    tool1 = MatrixExpansionTool()
    tool2 = MatrixExpansionTool() 
    
    print(f"🔍 Are both tools the same instance? {tool1 is tool2}")
    print(f"📊 Matrix Stats: {tool1.get_matrix_stats()}")
    
    if not tool1._is_available():
        print("❌ Matrix system not available for testing")
        return
    
    # Test skill extraction fix
    print("\n🧪 Testing Skill Extraction Fix:")
    test_inputs = [
        "find similar skills to python",
        "similar skills to javascript", 
        "expand java skills",
        "skills like react"
    ]
    
    for test_input in test_inputs:
        skills = tool1._extract_base_skills(test_input, {})
        print(f"  '{test_input}' -> {skills}")
    
    # Test actual expansion
    print("\n🧪 Testing Skill-to-Skill Expansion:")
    result = await tool1(
        expansion_type="skill_to_skill",
        base_items=["python"],
        top_n=5
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_matrix_expansion())