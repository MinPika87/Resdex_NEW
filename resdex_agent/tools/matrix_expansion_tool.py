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
            
            # Step 4: Verify MatrixFeatures has the required methods
            print("🔍 Step 4: Verifying MatrixFeatures methods...")
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
            
            logger.info(f"Matrix expansion tool initialized with features: {available_features}")
            
        except Exception as e:
            logger.error(f"Matrix system initialization failed: {e}")
            print(f"❌ Matrix system initialization failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Set error for all instances
            cls._initialization_error = str(e)
            cls._skill_convertor = None
            cls._matrix_features = None
            cls._feature_matrix_loader = None
    
    def _is_available(self) -> bool:
        """Check if matrix system is available."""
        return self._matrix_features is not None and self._initialization_error is None
    
    def _convert_skill_to_id(self, skill: str):
        """Convert skill name to ID."""
        if self._skill_convertor:
            try:
                result = self._skill_convertor.convert(skill)
                print(f"🔄 SkillConvertor: '{skill}' -> {result}")
                return result
            except Exception as e:
                print(f"⚠️ SkillConvertor failed for '{skill}': {e}")
        
        # Fallback: use skill name directly
        print(f"🔄 Fallback mapping: '{skill}' -> '{skill.lower()}'")
        return skill.lower()
    
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
        """FIXED: Enhanced skill extraction from user input or session state."""
        skills = []
        input_lower = user_input.lower()
        
        print(f"🔍 SKILL EXTRACTION DEBUG:")
        print(f"  - Original input: '{user_input}'")
        print(f"  - Lowercase input: '{input_lower}'")
        
        # FIXED: Enhanced skill extraction patterns with better regex
        skill_patterns = [
            r"(?:skills?\s+(?:to|like|similar\s+to)\s+)([a-zA-Z+#.]+)(?:\s|$)",  # FIXED: Removed comma from character class
            r"(?:expand\s+)([a-zA-Z+#.]+)(?:\s+skill)",
            r"(?:similar\s+to\s+)([a-zA-Z+#.]+)(?:\s|$)",
            r"(?:like\s+)([a-zA-Z+#.]+)(?:\s|$)",
            r"(?:find\s+skills\s+(?:similar\s+to|like)\s+)([a-zA-Z+#.]+)(?:\s|$)",
            r"(?:related\s+to\s+)([a-zA-Z+#.]+)(?:\s|$)"
        ]
        
        import re
        for i, pattern in enumerate(skill_patterns):
            print(f"  - Trying pattern {i+1}: {pattern}")
            match = re.search(pattern, input_lower)
            if match:
                skill_text = match.group(1).strip()
                print(f"  ✅ Pattern {i+1} matched: '{skill_text}'")
                
                # FIXED: Don't split single words - they're already extracted correctly
                if ' ' in skill_text or ',' in skill_text:
                    # Only split if there are actually multiple skills
                    skill_candidates = re.split(r'[,\s+and\s+]', skill_text)
                    print(f"  - Split candidates: {skill_candidates}")
                else:
                    # Single skill - don't split
                    skill_candidates = [skill_text]
                    print(f"  - Single skill (no split): {skill_candidates}")
                
                for skill in skill_candidates:
                    skill = skill.strip()
                    print(f"    - Processing candidate: '{skill}'")
                    
                    # CRITICAL FIX: Better validation and cleaning
                    if len(skill) > 1 and not skill in ['to', 'and', 'or', 'the', 'a', 'an']:
                        # Clean up the skill name
                        cleaned_skill = self._clean_skill_name(skill)
                        if cleaned_skill:
                            skills.append(cleaned_skill)
                            print(f"    ✅ Added skill: '{cleaned_skill}'")
                        else:
                            print(f"    ❌ Rejected after cleaning: '{skill}'")
                    else:
                        print(f"    ❌ Rejected (too short or stop word): '{skill}'")
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
    
    def _clean_skill_name(self, skill: str) -> str:
        """Clean and normalize skill name."""
        if not skill:
            return ""
        
        # Remove common suffixes and clean
        skill = skill.strip()
        
        # Remove trailing words that might be captured by regex
        stop_suffixes = ['skill', 'skills', 'programming', 'language', 'technology']
        for suffix in stop_suffixes:
            if skill.lower().endswith(suffix):
                skill = skill[:-len(suffix)].strip()
        
        # Handle common skill name variations
        skill_mappings = {
            'pytho': 'python',
            'javascrip': 'javascript', 
            'jav': 'java',
            'reac': 'react',
            'angula': 'angular',
            'nod': 'node.js',
            'sq': 'sql',
            'htm': 'html',
            'cs': 'css'
        }
        
        skill_lower = skill.lower()
        for partial, full in skill_mappings.items():
            if skill_lower == partial:
                print(f"    🔧 Skill mapping: '{skill}' -> '{full}'")
                return full
        
        # Final cleanup and capitalization
        cleaned = skill.strip().title()
        
        # Special cases for well-known skills
        special_cases = {
            'Python': 'Python',
            'Javascript': 'JavaScript', 
            'Java': 'Java',
            'React': 'React',
            'Angular': 'Angular',
            'Node.Js': 'Node.js',
            'Sql': 'SQL',
            'Html': 'HTML',
            'Css': 'CSS',
            'Machine Learning': 'Machine Learning',
            'Data Science': 'Data Science'
        }
        
        return special_cases.get(cleaned, cleaned)
    
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
        """Expand skills to related skills."""
        try:
            print(f"🔧 SKILL-TO-SKILL EXPANSION for: {skills}")
            
            if not hasattr(self._matrix_features, 'skillToSkillFeature'):
                return {
                    "success": False,
                    "error": "skillToSkillFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert skill names to IDs
            skill_ids = []
            skill_mapping = {}
            
            for skill in skills:
                skill_id = self._convert_skill_to_id(skill)
                if skill_id:
                    skill_ids.append(skill_id)
                    skill_mapping[skill_id] = skill
                    print(f"  ✅ {skill} -> ID: {skill_id}")
                else:
                    print(f"  ❌ {skill} -> No ID found")
            
            if not skill_ids:
                return {
                    "success": False,
                    "error": "No valid skill IDs found",
                    "method": "skill_to_skill_matrix"
                }
            
            # Call the matrix feature
            print(f"🔍 Calling skillToSkillFeature.get_feature_value...")
            print(f"  - Input IDs: {skill_ids}")
            print(f"  - TopN: {top_n * 2}")
            print(f"  - Normalize: {normalize}")
            
            expansion_results = self._matrix_features.skillToSkillFeature.get_feature_value(
                skill_ids, topN=top_n * 2, normalize=normalize
            )
            
            print(f"📊 Matrix returned {len(expansion_results)} results")
            
            # Convert back to skill names and format results
            expanded_skills = []
            processed_count = 0
            
            for skill_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                # Skip if it's one of the input skills
                if skill_id in skill_mapping:
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
                "message": f"Found {len(expanded_skills)} related skills using matrix analysis"
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
        """Expand titles to related skills."""
        try:
            print(f"🔧 TITLE-TO-SKILL EXPANSION for: {titles}")
            
            if not hasattr(self._matrix_features, 'titleToSkillFeature'):
                return {
                    "success": False,
                    "error": "titleToSkillFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert title names to IDs
            title_ids = []
            for title in titles:
                title_id = self._convert_skill_to_id(title)
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
            
            # Convert skill IDs back to names
            expanded_skills = []
            processed_count = 0
            
            for skill_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
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
        """Expand titles to related titles."""
        try:
            print(f"🔧 TITLE-TO-TITLE EXPANSION for: {titles}")
            
            if not hasattr(self._matrix_features, 'titleToTitleFeature'):
                return {
                    "success": False,
                    "error": "titleToTitleFeature not available in MatrixFeatures",
                    "method": "feature_missing"
                }
            
            # Convert title names to IDs
            title_ids = []
            title_mapping = {}
            
            for title in titles:
                title_id = self._convert_skill_to_id(title)
                if title_id:
                    title_ids.append(title_id)
                    title_mapping[title_id] = title
                    print(f"  ✅ {title} -> ID: {title_id}")
            
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
            
            # Convert back to title names and format results
            expanded_titles = []
            processed_count = 0
            
            for title_id, score in sorted(expansion_results.items(), key=lambda x: -x[1]):
                # Skip if it's one of the input titles
                if title_id in title_mapping:
                    continue
                    
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
                "expansion_type": "title_to_title",
                "base_items": titles,
                "expanded_items": expanded_titles,
                "total_found": len(expansion_results),
                "method": "title_to_title_matrix",
                "message": f"Found {len(expanded_titles)} related titles using matrix analysis"
            }
            
        except Exception as e:
            logger.error(f"Title-to-title expansion failed: {e}")
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