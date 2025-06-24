# resdex_agent/sub_agents/expansion/agent.py - ENHANCED with Matrix Features
"""
Enhanced Expansion Agent - Matrix-based skill and title expansion with LLM fallback.
"""

from typing import Dict, Any, List, Optional
import logging

from ...base_agent import BaseResDexAgent, Content
from .config import ExpansionConfig

logger = logging.getLogger(__name__)


class ExpansionAgent(BaseResDexAgent):
    """
    Enhanced Expansion Agent with Matrix Features integration.
    
    RESPONSIBILITIES:
    1. Matrix-based skill expansion (primary method)
    2. Matrix-based title expansion (primary method)  
    3. Location expansion (LLM-based)
    4. LLM fallback for skill/title expansion when matrix fails
    5. Integration with session state for filter updates
    
    HIERARCHY:
    1. Matrix Features (high accuracy, fast)
    2. LLM Analysis (fallback, flexible)
    3. Hardcoded mappings (final fallback)
    """

    def __init__(self, config: ExpansionConfig = None):
        self._config = config or ExpansionConfig()
        
        super().__init__(
            name=self._config.name,
            description=self._config.description
        )
        
        # Initialize expansion-specific tools
        self._setup_expansion_tools()
        
        logger.info(f"Enhanced ExpansionAgent initialized with Matrix Features + LLM fallback")

    @property
    def config(self):
        return self._config
    
    def _setup_expansion_tools(self):
        """Setup expansion-specific tools with Matrix Features priority."""
        try:
            # PRIMARY: Matrix-based expansion tool
            from ...tools.matrix_expansion_tool import MatrixExpansionTool
            self.tools["matrix_expansion"] = MatrixExpansionTool("matrix_expansion_tool")
            
            # Location expansion tool (unchanged)
            from ...tools.location_tools import LocationAnalysisTool
            self.tools["location_tool"] = LocationAnalysisTool("location_expansion_tool")
            
            # Filter tool for applying expanded results
            from ...tools.filter_tools import FilterTool
            self.tools["filter_tool"] = FilterTool("expansion_filter_tool")
            
            print(f"🔧 Enhanced ExpansionAgent tools: {list(self.tools.keys())}")
            
            # Check matrix availability
            matrix_stats = self.tools["matrix_expansion"].get_matrix_stats()
            if matrix_stats.get("available", False):
                print("✅ Matrix Features system available - using as primary expansion method")
            else:
                print("⚠️ Matrix Features not available - will use LLM fallback only")
            
        except Exception as e:
            logger.error(f"Failed to setup enhanced expansion tools: {e}")
            print(f"❌ Enhanced expansion tools setup failed: {e}")
    
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Enhanced core expansion logic with Matrix Features priority.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            intent_data = content.data.get("intent_data", {})
            
            logger.info(f"Enhanced ExpansionAgent processing: '{user_input}'")
            print(f"🔧 ENHANCED EXPANSION AGENT: Processing '{user_input}'")
            
            # Determine expansion type
            expansion_type = self._determine_expansion_type(user_input, intent_data)
            
            if expansion_type == "skill_expansion":
                return await self._handle_matrix_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "title_expansion":
                return await self._handle_matrix_title_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "location_expansion":
                return await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "multi_expansion":
                return await self._handle_multi_expansion(user_input, session_state, memory_context, session_id, user_id)
            else:
                return await self._handle_auto_expansion(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            logger.error(f"Enhanced ExpansionAgent execution failed: {e}")
            return self.create_content({
                "success": False,
                "error": "Enhanced expansion failed",
                "details": str(e)
            })
    
    def _determine_expansion_type(self, user_input: str, intent_data: Dict[str, Any]) -> str:
        """Enhanced expansion type determination with better detection."""
        input_lower = user_input.lower()
        
        # Check intent data first
        if intent_data.get("expansion_type"):
            return intent_data["expansion_type"]
        
        # Enhanced skill expansion indicators
        skill_indicators = [
            "similar skills", "related skills", "skill expansion", "expand skills",
            "skills similar to", "skills like", "skills related to",
            "comparable skills", "equivalent skills", "find skills", "suggest skills", "skill suggestions"
        ]
        
        # Enhanced title expansion indicators  
        title_indicators = [
            "similar titles", "related titles", "job titles", "expand titles",
            "titles similar to", "titles like", "titles related to",
            "equivalent roles", "similar roles", "related roles", "roles similar to", "roles like",
            "equivalent positions", "similar positions", "related positions", "positions similar to", "positions like",
            "find titles", "suggest titles", "title suggestions", "find roles", "suggest roles",
            "job roles", "career roles", "professional roles"
        ]
        
        # Location expansion indicators (unchanged)
        location_indicators = [
            "nearby locations", "similar locations", "location expansion", "expand locations",
            "nearby cities", "similar cities", "around", "close to", "near", "locations near",
            "cities near", "locations similar to", "cities similar to"
        ]
        
        has_skill = any(indicator in input_lower for indicator in skill_indicators)
        has_title = any(indicator in input_lower for indicator in title_indicators)
        has_location = any(indicator in input_lower for indicator in location_indicators)
        
        # Multi-expansion check
        expansion_count = sum([has_skill, has_title, has_location])
        if expansion_count > 1:
            return "multi_expansion"
        elif has_skill:
            return "skill_expansion"
        elif has_title:
            return "title_expansion"
        elif has_location:
            return "location_expansion"
        else:
            return "auto_detection"
    

    async def _handle_matrix_skill_expansion(self, user_input: str, session_state: Dict[str, Any],
                                   memory_context: List[Dict[str, Any]], session_id: str, 
                                   user_id: str) -> Content:
        """Handle skill expansion with Matrix Features - COLLECTIVE expansion approach."""
        try:
            print(f"🎯 MATRIX SKILL EXPANSION: Analyzing '{user_input}'")
            
            # Use matrix tool's enhanced skill extraction
            base_skills = self.tools["matrix_expansion"]._extract_base_skills(user_input, session_state)
            
            print(f"📝 Base skills identified: {base_skills}")
            
            if not base_skills:
                return self.create_content({
                    "success": False,
                    "error": "No base skills found for expansion",
                    "message": "Please specify skills to expand (e.g., 'find similar skills to python')"
                })
            
            # FIXED: Use collective expansion - pass ALL skills at once
            print(f"🔧 Processing {len(base_skills)} skills collectively: {base_skills}")
            
            matrix_result = await self.tools["matrix_expansion"](
                expansion_type="skill_to_skill",
                base_items=base_skills,  # Pass ALL skills together
                top_n=5,
                normalize=True
            )
            
            print(f"🔍 Matrix expansion result: success={matrix_result.get('success', False)}")
            
            if matrix_result["success"]:
                print(f"✅ Matrix expansion successful for collective skills")
                
                # Process the collective results
                expanded_items = matrix_result.get("expanded_items", [])
                expanded_skills = [item["name"] for item in expanded_items]
                
                print(f"🎯 Found {len(expanded_skills)} skills similar to ALL input skills: {expanded_skills}")
                
                # Apply expanded skills to session state
                modifications = []
                for skill_item in expanded_items:
                    skill_name = skill_item["name"]
                    if skill_name not in session_state.get('keywords', []):
                        filter_result = await self.tools["filter_tool"](
                            "add_skill", session_state, skill=skill_name, mandatory=False
                        )
                        if filter_result["success"]:
                            modifications.extend(filter_result["modifications"])
                
                # Create UI-friendly expanded skills data
                ui_expanded_skills = []
                for item in expanded_items:
                    ui_expanded_skills.append({
                        "name": item["name"],
                        "score": item["score"],
                        "confidence": "high",  # Matrix-based = high confidence
                        "method": "matrix_analysis"
                    })
                
                base_skills_str = ", ".join(base_skills)
                expanded_skills_str = ", ".join(expanded_skills)
                
                if len(base_skills) > 1:
                    message = f"Matrix analysis found {len(expanded_skills)} skills similar to ALL of: {base_skills_str} → {expanded_skills_str}"
                else:
                    message = f"Matrix analysis expanded '{base_skills_str}' to {len(expanded_skills)} related skills: {expanded_skills_str}"
                
                return self.create_content({
                    "success": True,
                    "expansion_type": "skill_expansion",
                    "method": "matrix_features",
                    "base_skills": base_skills,
                    "expanded_skills": expanded_skills,
                    "ui_expanded_skills": ui_expanded_skills,
                    "modifications": modifications,
                    "session_state": session_state,
                    "message": message,
                    "trigger_search": False,
                    "matrix_stats": {
                        "total_found": matrix_result.get("total_found", len(expanded_skills)),
                        "top_displayed": len(ui_expanded_skills),
                        "confidence": "high",
                        "collective_expansion": True,
                        "base_skills_count": len(base_skills)
                    }
                })
            else:
                print(f"⚠️ Matrix expansion failed: {matrix_result.get('error', 'Unknown error')}")
                print(f"🔄 Falling back to LLM expansion...")
                
                # Fallback to LLM for all skills collectively
                return await self._handle_llm_skill_expansion_fallback(base_skills, session_state, memory_context)
                    
        except Exception as e:
            print(f"❌ Matrix skill expansion error: {e}")
            import traceback
            traceback.print_exc()
            # Use existing LLM fallback
            base_skills = base_skills if 'base_skills' in locals() else []
            if base_skills:
                return await self._handle_llm_skill_expansion_fallback(base_skills, session_state, memory_context)
            else:
                return self.create_content({
                    "success": False,
                    "error": f"Skill expansion failed: {str(e)}"
                })

    
    async def _handle_matrix_title_expansion(self, user_input: str, session_state: Dict[str, Any],
                                       memory_context: List[Dict[str, Any]], session_id: str, 
                                       user_id: str) -> Content:
        """Handle title expansion with Matrix Features - COLLECTIVE expansion approach."""
        try:
            print(f"💼 MATRIX TITLE EXPANSION: Analyzing '{user_input}'")
            
            # Use matrix tool's enhanced title extraction
            base_titles = self.tools["matrix_expansion"]._extract_base_titles(user_input, session_state)
            
            print(f"📝 Base titles identified: {base_titles}")
            
            if not base_titles:
                return self.create_content({
                    "success": False,
                    "error": "No base titles found for expansion",
                    "message": "Please specify titles to expand (e.g., 'find similar titles to data scientist')"
                })
            
            # FIXED: Use collective expansion - pass ALL titles at once
            print(f"🔧 Processing {len(base_titles)} titles collectively: {base_titles}")
            
            # Get similar titles
            title_result = await self.tools["matrix_expansion"](
                expansion_type="title_to_title",
                base_items=base_titles,  # Pass ALL titles together
                top_n=5,
                normalize=True
            )
            
            # Get suggested skills for these titles
            skills_result = await self.tools["matrix_expansion"](
                expansion_type="title_to_skill",
                base_items=base_titles,  # Pass ALL titles together
                top_n=5,
                normalize=True
            )
            
            print(f"🔍 Title expansion result: success={title_result.get('success', False)}")
            print(f"🔍 Skills suggestion result: success={skills_result.get('success', False)}")
            
            if title_result["success"]:
                print(f"✅ Matrix title expansion successful for collective titles")
                
                # Process the collective results
                expanded_titles = [item["name"] for item in title_result.get("expanded_items", [])]
                suggested_skills = [item["name"] for item in skills_result.get("expanded_items", [])] if skills_result.get("success") else []
                
                print(f"🎯 Found {len(expanded_titles)} titles similar to ALL input titles: {expanded_titles}")
                print(f"🎯 Found {len(suggested_skills)} skills relevant to these titles: {suggested_skills}")
                
                # Apply suggested skills to session state (limit to top 3)
                modifications = []
                for skill_item in skills_result.get("expanded_items", [])[:3]:
                    skill_name = skill_item["name"]
                    if skill_name not in session_state.get('keywords', []):
                        filter_result = await self.tools["filter_tool"](
                            "add_skill", session_state, skill=skill_name, mandatory=False
                        )
                        if filter_result["success"]:
                            modifications.extend(filter_result["modifications"])
                
                # Create UI-friendly data
                ui_expanded_titles = []
                for item in title_result["expanded_items"]:
                    ui_expanded_titles.append({
                        "name": item["name"],
                        "score": item["score"],
                        "confidence": "high",
                        "method": "matrix_analysis"
                    })
                
                ui_suggested_skills = []
                for item in skills_result.get("expanded_items", [])[:5]:
                    ui_suggested_skills.append({
                        "name": item["name"],
                        "score": item["score"],
                        "confidence": "high",
                        "method": "matrix_analysis"
                    })
                
                base_titles_str = ", ".join(base_titles)
                expanded_titles_str = ", ".join(expanded_titles)
                
                if len(base_titles) > 1:
                    message = f"Matrix analysis found {len(expanded_titles)} titles similar to ALL of: {base_titles_str} and added {len(suggested_skills[:3])} relevant skills → {expanded_titles_str}"
                else:
                    message = f"Matrix analysis expanded '{base_titles_str}' to {len(expanded_titles)} related titles and added {len(suggested_skills[:3])} relevant skills: {expanded_titles_str}"
                
                return self.create_content({
                    "success": True,
                    "expansion_type": "title_expansion",
                    "method": "matrix_features",
                    "base_titles": base_titles,
                    "expanded_titles": expanded_titles,
                    "suggested_skills": suggested_skills[:3],
                    "ui_expanded_titles": ui_expanded_titles,
                    "ui_suggested_skills": ui_suggested_skills,
                    "modifications": modifications,
                    "session_state": session_state,
                    "message": message,
                    "trigger_search": False,
                    "matrix_stats": {
                        "titles_found": title_result.get("total_found", len(expanded_titles)),
                        "skills_found": skills_result.get("total_found", 0),
                        "confidence": "high",
                        "collective_expansion": True,
                        "base_titles_count": len(base_titles)
                    }
                })
            else:
                print(f"⚠️ Matrix title expansion failed: {title_result.get('error', 'Unknown error')}")
                print(f"🔄 Falling back to LLM expansion...")
                
                # Fallback to LLM for all titles collectively
                return await self._handle_llm_title_expansion_fallback(base_titles, session_state, memory_context)
                
        except Exception as e:
            print(f"❌ Matrix title expansion error: {e}")
            import traceback
            traceback.print_exc()
            # Use existing LLM fallback
            base_titles = base_titles if 'base_titles' in locals() else []
            if base_titles:
                return await self._handle_llm_title_expansion_fallback(base_titles, session_state, memory_context)
            else:
                return self.create_content({
                    "success": False,
                    "error": f"Title expansion failed: {str(e)}"
                })
    
    async def _process_matrix_skill_results(self, matrix_result: Dict[str, Any], base_skills: List[str], 
                                      session_state: Dict[str, Any]) -> Content:
        """Process matrix skill expansion results and apply to session state."""
        try:
            print(f"🔧 Processing matrix skill results...")
            print(f"📊 Matrix result keys: {list(matrix_result.keys())}")
            print(f"📊 Matrix result type: {type(matrix_result)}")
            
            # FIX: The matrix_result already contains the processed results
            # We need to extract the ui_expanded_skills directly
            
            if "ui_expanded_skills" in matrix_result:
                # Matrix tool already processed the results
                expanded_items = matrix_result["ui_expanded_skills"]
                expanded_skills = matrix_result["expanded_skills"]
                
                print(f"🔧 Using pre-processed results: {len(expanded_items)} skills")
                
            elif "expanded_items" in matrix_result:
                # Legacy format
                expanded_items = matrix_result["expanded_items"]
                expanded_skills = [item["name"] for item in expanded_items]
                
            else:
                # Raw matrix format (skill_id -> score)
                print(f"🔧 Processing raw matrix format...")
                expanded_items = []
                
                # Check if we have raw matrix results
                raw_results = {k: v for k, v in matrix_result.items() 
                            if k not in ['success', 'expansion_type', 'method', 'base_skills', 'expanded_skills', 'ui_expanded_skills', 'modifications', 'session_state', 'message', 'trigger_search', 'matrix_stats']}
                
                if raw_results:
                    # Convert raw results to proper format
                    for skill_id, score in sorted(raw_results.items(), key=lambda x: -float(x[1])):
                        skill_name = self.tools["matrix_expansion"]._convert_id_to_skill(skill_id)
                        if skill_name and skill_name != "UNKNOWN":
                            expanded_items.append({
                                "name": skill_name,
                                "id": skill_id,
                                "score": float(score),
                                "type": "skill"
                            })
                            if len(expanded_items) >= 5:
                                break
                    
                    expanded_skills = [item["name"] for item in expanded_items]
                else:
                    print(f"❌ No valid expansion data found in matrix result")
                    return self.create_content({
                        "success": False,
                        "error": "No valid expansion data found in matrix result"
                    })
            
            if not expanded_items:
                print(f"❌ No expanded items found")
                return self.create_content({
                    "success": False,
                    "error": "No expanded skills found"
                })
            
            print(f"🔧 Processing {len(expanded_skills)} matrix-expanded skills: {expanded_skills}")
            
            # Apply expanded skills to session state
            modifications = []
            for skill_item in expanded_items:
                skill_name = skill_item["name"]
                if skill_name not in session_state.get('keywords', []):
                    filter_result = await self.tools["filter_tool"](
                        "add_skill", session_state, skill=skill_name, mandatory=False
                    )
                    if filter_result["success"]:
                        modifications.extend(filter_result["modifications"])
            
            # Create UI-friendly expanded skills data (if not already processed)
            if "ui_expanded_skills" in matrix_result:
                ui_expanded_skills = matrix_result["ui_expanded_skills"]
            else:
                ui_expanded_skills = []
                for item in expanded_items:
                    ui_expanded_skills.append({
                        "name": item["name"],
                        "score": item.get("score", 0.8),
                        "confidence": "high",  # Matrix-based = high confidence
                        "method": "matrix_analysis"
                    })
            
            base_skills_str = ", ".join(base_skills)
            expanded_skills_str = ", ".join(expanded_skills)
            message = f"Matrix analysis expanded '{base_skills_str}' to {len(expanded_skills)} related skills: {expanded_skills_str}"
            
            return self.create_content({
                "success": True,
                "expansion_type": "skill_expansion",
                "method": "matrix_features",
                "base_skills": base_skills,
                "expanded_skills": expanded_skills,
                "ui_expanded_skills": ui_expanded_skills,  # For UI display with scores
                "modifications": modifications,
                "session_state": session_state,
                "message": message,
                "trigger_search": False,
                "matrix_stats": {
                    "total_found": len(expanded_items),
                    "top_displayed": len(ui_expanded_skills),
                    "confidence": "high"
                }
            })
            
        except Exception as e:
            logger.error(f"Processing matrix skill results failed: {e}")
            print(f"❌ Processing matrix skill results failed: {e}")
            import traceback
            traceback.print_exc()
            return self.create_content({
                "success": False,
                "error": f"Processing matrix skill results failed: {str(e)}"
            })

    
    async def _process_matrix_title_results(self, title_result: Dict[str, Any], skills_result: Dict[str, Any],
                                          base_titles: List[str], session_state: Dict[str, Any]) -> Content:
        """Process matrix title expansion results and apply to session state."""
        try:
            expanded_titles = [item["name"] for item in title_result["expanded_items"]]
            suggested_skills = [item["name"] for item in skills_result.get("expanded_items", [])] if skills_result.get("success") else []
            
            print(f"🔧 Processing {len(expanded_titles)} matrix-expanded titles and {len(suggested_skills)} suggested skills")
            
            # Apply suggested skills to session state (limit to top 3)
            modifications = []
            for skill_item in skills_result.get("expanded_items", [])[:3]:
                skill_name = skill_item["name"]
                if skill_name not in session_state.get('keywords', []):
                    filter_result = await self.tools["filter_tool"](
                        "add_skill", session_state, skill=skill_name, mandatory=False
                    )
                    if filter_result["success"]:
                        modifications.extend(filter_result["modifications"])
            
            # Create UI-friendly data
            ui_expanded_titles = []
            for item in title_result["expanded_items"]:
                ui_expanded_titles.append({
                    "name": item["name"],
                    "score": item["score"],
                    "confidence": "high",
                    "method": "matrix_analysis"
                })
            
            ui_suggested_skills = []
            for item in skills_result.get("expanded_items", [])[:5]:  # Top 5 for UI
                ui_suggested_skills.append({
                    "name": item["name"],
                    "score": item["score"],
                    "confidence": "high",
                    "method": "matrix_analysis"
                })
            
            base_titles_str = ", ".join(base_titles)
            expanded_titles_str = ", ".join(expanded_titles)
            message = f"Matrix analysis expanded '{base_titles_str}' to {len(expanded_titles)} related titles and added {len(suggested_skills[:3])} relevant skills"
            
            return self.create_content({
                "success": True,
                "expansion_type": "title_expansion",
                "method": "matrix_features",
                "base_titles": base_titles,
                "expanded_titles": expanded_titles,
                "suggested_skills": suggested_skills[:3],
                "ui_expanded_titles": ui_expanded_titles,
                "ui_suggested_skills": ui_suggested_skills,
                "modifications": modifications,
                "session_state": session_state,
                "message": message,
                "trigger_search": False,
                "matrix_stats": {
                    "titles_found": title_result["total_found"],
                    "skills_found": skills_result.get("total_found", 0),
                    "confidence": "high"
                }
            })
            
        except Exception as e:
            logger.error(f"Processing matrix title results failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Processing matrix title results failed: {str(e)}"
            })
    
    def _extract_base_skills(self, user_input: str, session_state: Dict[str, Any]) -> List[str]:
        """Enhanced skill extraction from user input or session state."""
        skills = []
        input_lower = user_input.lower()
        
        # Enhanced skill extraction patterns
        skill_patterns = [
            r"skills?\s+(?:to|like|similar\s+to)\s+([a-zA-Z+#.\s,]+)",
            r"expand\s+([a-zA-Z+#.\s,]+)\s+skill",
            r"similar\s+to\s+([a-zA-Z+#.\s,]+)",
            r"like\s+([a-zA-Z+#.\s,]+)",
            r"find\s+skills\s+(?:similar\s+to|like)\s+([a-zA-Z+#.\s,]+)"
        ]
        
        import re
        for pattern in skill_patterns:
            match = re.search(pattern, input_lower)
            if match:
                skill_text = match.group(1).strip()
                # Handle multiple skills separated by commas/and
                skill_candidates = re.split(r'[,\s+and\s+]', skill_text)
                for skill in skill_candidates:
                    skill = skill.strip()
                    if len(skill) > 1 and skill.isalpha():
                        skills.append(skill.title())
                break
        
        # If no skills found in input, check session state
        if not skills:
            keywords = session_state.get('keywords', [])
            if keywords:
                # Use the last added skill as base
                last_skill = keywords[-1].replace('★ ', '')
                skills.append(last_skill)
        
        # Remove duplicates while preserving order
        unique_skills = list(dict.fromkeys(skills))
        return unique_skills
    
    def _extract_base_titles(self, user_input: str, session_state: Dict[str, Any]) -> List[str]:
        """Enhanced title extraction from user input."""
        # Use matrix tool's title extraction if available
        if hasattr(self.tools["matrix_expansion"], '_extract_base_titles'):
            return self.tools["matrix_expansion"]._extract_base_titles(user_input, session_state)
        
        # Fallback method (original logic)
        titles = []
        input_lower = user_input.lower()
        
        title_patterns = [
            r"titles?\s+(?:to|like|similar\s+to)\s+([a-zA-Z\s,]+)",
            r"roles?\s+(?:to|like|similar\s+to)\s+([a-zA-Z\s,]+)",
            r"positions?\s+(?:to|like|similar\s+to)\s+([a-zA-Z\s,]+)",
            r"expand\s+([a-zA-Z\s,]+)\s+(?:title|role|position)",
            r"find\s+titles\s+(?:similar\s+to|like)\s+([a-zA-Z\s,]+)",
            r"similar\s+to\s+([a-zA-Z\s,]+)\s+(?:role|position|title)"
        ]
        
        import re
        for pattern in title_patterns:
            match = re.search(pattern, input_lower)
            if match:
                title_text = match.group(1).strip()
                # Handle multiple titles separated by commas/and
                title_candidates = re.split(r'[,\s+and\s+]', title_text)
                for title in title_candidates:
                    title = title.strip()
                    if len(title) > 3:  # Titles are usually longer
                        titles.append(title.title())
                break
        
        # Remove duplicates while preserving order
        unique_titles = list(dict.fromkeys(titles))
        return unique_titles
    
    async def _handle_llm_skill_expansion_fallback(self, base_skills: List[str], session_state: Dict[str, Any],
                                                 memory_context: List[Dict[str, Any]]) -> Content:
        """Fallback to LLM-based skill expansion when matrix fails."""
        try:
            print(f"🔄 LLM SKILL EXPANSION FALLBACK for: {base_skills}")
            
            # Use the original LLM expansion method
            for base_skill in base_skills:
                expansion_result = await self._expand_skills_with_llm(base_skill, memory_context)
                
                if expansion_result["success"]:
                    expanded_skills = expansion_result["expanded_skills"]
                    
                    # Apply expanded skills to session state
                    modifications = []
                    for skill in expanded_skills:
                        if skill not in session_state.get('keywords', []):
                            filter_result = await self.tools["filter_tool"](
                                "add_skill", session_state, skill=skill, mandatory=False
                            )
                            if filter_result["success"]:
                                modifications.extend(filter_result["modifications"])
                    
                    # Create UI-friendly data
                    ui_expanded_skills = []
                    for skill in expanded_skills:
                        ui_expanded_skills.append({
                            "name": skill,
                            "score": 0.8,  # Default score for LLM
                            "confidence": "medium",
                            "method": "llm_analysis"
                        })
                    
                    message = f"LLM analysis expanded '{base_skill}' to {len(expanded_skills)} related skills: {', '.join(expanded_skills)}"
                    
                    return self.create_content({
                        "success": True,
                        "expansion_type": "skill_expansion",
                        "method": "llm_fallback",
                        "base_skills": [base_skill],
                        "expanded_skills": expanded_skills,
                        "ui_expanded_skills": ui_expanded_skills,
                        "modifications": modifications,
                        "session_state": session_state,
                        "message": message,
                        "trigger_search": False,
                        "fallback_used": True
                    })
            
            # If LLM also fails, use hardcoded fallback
            return await self._use_hardcoded_skill_fallback(base_skills, session_state)
            
        except Exception as e:
            logger.error(f"LLM skill expansion fallback failed: {e}")
            return await self._use_hardcoded_skill_fallback(base_skills, session_state)
    
    async def _handle_llm_title_expansion_fallback(self, base_titles: List[str], session_state: Dict[str, Any],
                                                 memory_context: List[Dict[str, Any]]) -> Content:
        """Fallback to LLM-based title expansion when matrix fails."""
        try:
            print(f"🔄 LLM TITLE EXPANSION FALLBACK for: {base_titles}")
            
            # Use the original LLM expansion method
            for base_title in base_titles:
                expansion_result = await self._expand_titles_with_llm(base_title, memory_context)
                
                if expansion_result["success"]:
                    expanded_titles = expansion_result["expanded_titles"]
                    suggested_skills = expansion_result.get("suggested_skills", [])
                    
                    # Apply suggested skills to session state
                    modifications = []
                    for skill in suggested_skills[:3]:  # Limit to 3 skills
                        if skill not in session_state.get('keywords', []):
                            filter_result = await self.tools["filter_tool"](
                                "add_skill", session_state, skill=skill, mandatory=False
                            )
                            if filter_result["success"]:
                                modifications.extend(filter_result["modifications"])
                    
                    # Create UI-friendly data
                    ui_expanded_titles = []
                    for title in expanded_titles:
                        ui_expanded_titles.append({
                            "name": title,
                            "score": 0.8,
                            "confidence": "medium",
                            "method": "llm_analysis"
                        })
                    
                    ui_suggested_skills = []
                    for skill in suggested_skills:
                        ui_suggested_skills.append({
                            "name": skill,
                            "score": 0.8,
                            "confidence": "medium",
                            "method": "llm_analysis"
                        })
                    
                    message = f"LLM analysis expanded '{base_title}' to {len(expanded_titles)} related titles and added {len(suggested_skills[:3])} relevant skills"
                    
                    return self.create_content({
                        "success": True,
                        "expansion_type": "title_expansion",
                        "method": "llm_fallback",
                        "base_titles": [base_title],
                        "expanded_titles": expanded_titles,
                        "suggested_skills": suggested_skills[:3],
                        "ui_expanded_titles": ui_expanded_titles,
                        "ui_suggested_skills": ui_suggested_skills,
                        "modifications": modifications,
                        "session_state": session_state,
                        "message": message,
                        "trigger_search": False,
                        "fallback_used": True
                    })
            
            # If LLM also fails, use hardcoded fallback
            return await self._use_hardcoded_title_fallback(base_titles, session_state)
            
        except Exception as e:
            logger.error(f"LLM title expansion fallback failed: {e}")
            return await self._use_hardcoded_title_fallback(base_titles, session_state)
    
    async def _use_hardcoded_skill_fallback(self, base_skills: List[str], session_state: Dict[str, Any]) -> Content:
        """Final fallback using hardcoded skill mappings."""
        try:
            print(f"🔧 HARDCODED SKILL FALLBACK for: {base_skills}")
            
            # Use existing fallback method
            for base_skill in base_skills:
                fallback_result = self._fallback_skill_expansion(base_skill)
                
                if fallback_result["success"]:
                    expanded_skills = fallback_result["expanded_skills"]
                    
                    # Apply expanded skills to session state
                    modifications = []
                    for skill in expanded_skills:
                        if skill not in session_state.get('keywords', []):
                            filter_result = await self.tools["filter_tool"](
                                "add_skill", session_state, skill=skill, mandatory=False
                            )
                            if filter_result["success"]:
                                modifications.extend(filter_result["modifications"])
                    
                    # Create UI-friendly data
                    ui_expanded_skills = []
                    for skill in expanded_skills:
                        ui_expanded_skills.append({
                            "name": skill,
                            "score": 0.7,
                            "confidence": "low",
                            "method": "hardcoded_mapping"
                        })
                    
                    message = f"Hardcoded mapping expanded '{base_skill}' to {len(expanded_skills)} related skills: {', '.join(expanded_skills)}"
                    
                    return self.create_content({
                        "success": True,
                        "expansion_type": "skill_expansion",
                        "method": "hardcoded_fallback",
                        "base_skills": [base_skill],
                        "expanded_skills": expanded_skills,
                        "ui_expanded_skills": ui_expanded_skills,
                        "modifications": modifications,
                        "session_state": session_state,
                        "message": message,
                        "trigger_search": False,
                        "fallback_used": True
                    })
            
            return self.create_content({
                "success": False,
                "error": "All skill expansion methods failed",
                "message": "Unable to expand skills using any available method"
            })
            
        except Exception as e:
            logger.error(f"Hardcoded skill fallback failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Hardcoded skill fallback failed: {str(e)}"
            })
    
    async def _use_hardcoded_title_fallback(self, base_titles: List[str], session_state: Dict[str, Any]) -> Content:
        """Final fallback using hardcoded title mappings."""
        try:
            print(f"🔧 HARDCODED TITLE FALLBACK for: {base_titles}")
            
            # Use existing fallback method
            for base_title in base_titles:
                fallback_result = self._fallback_title_expansion(base_title)
                
                if fallback_result["success"]:
                    expanded_titles = fallback_result["expanded_titles"]
                    suggested_skills = fallback_result.get("suggested_skills", [])
                    
                    # Apply suggested skills to session state
                    modifications = []
                    for skill in suggested_skills[:3]:  # Limit to 3 skills
                        if skill not in session_state.get('keywords', []):
                            filter_result = await self.tools["filter_tool"](
                                "add_skill", session_state, skill=skill, mandatory=False
                            )
                            if filter_result["success"]:
                                modifications.extend(filter_result["modifications"])
                    
                    # Create UI-friendly data
                    ui_expanded_titles = []
                    for title in expanded_titles:
                        ui_expanded_titles.append({
                            "name": title,
                            "score": 0.7,
                            "confidence": "low",
                            "method": "hardcoded_mapping"
                        })
                    
                    ui_suggested_skills = []
                    for skill in suggested_skills:
                        ui_suggested_skills.append({
                            "name": skill,
                            "score": 0.7,
                            "confidence": "low",
                            "method": "hardcoded_mapping"
                        })
                    
                    message = f"Hardcoded mapping expanded '{base_title}' to {len(expanded_titles)} related titles and added {len(suggested_skills[:3])} relevant skills"
                    
                    return self.create_content({
                        "success": True,
                        "expansion_type": "title_expansion",
                        "method": "hardcoded_fallback",
                        "base_titles": [base_title],
                        "expanded_titles": expanded_titles,
                        "suggested_skills": suggested_skills[:3],
                        "ui_expanded_titles": ui_expanded_titles,
                        "ui_suggested_skills": ui_suggested_skills,
                        "modifications": modifications,
                        "session_state": session_state,
                        "message": message,
                        "trigger_search": False,
                        "fallback_used": True
                    })
            
            return self.create_content({
                "success": False,
                "error": "All title expansion methods failed",
                "message": "Unable to expand titles using any available method"
            })
            
        except Exception as e:
            logger.error(f"Hardcoded title fallback failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Hardcoded title fallback failed: {str(e)}"
            })
    
    # Keep existing location expansion methods unchanged
    async def _handle_location_expansion(self, user_input: str, session_state: Dict[str, Any],
                                       memory_context: List[Dict[str, Any]], session_id: str, 
                                       user_id: str) -> Content:
        """Handle location expansion using existing location tools (unchanged)."""
        # ... existing location expansion code remains the same ...
        try:
            print(f"🗺️ LOCATION EXPANSION: Analyzing '{user_input}'")
            
            location_info = self._extract_location_info(user_input, session_state)
            
            if not location_info["base_location"]:
                return self.create_content({
                    "success": False,
                    "error": "No base location found for expansion",
                    "message": "Please specify a location to expand (e.g., 'find nearby locations to Mumbai')"
                })
            
            location_result = await self.tools["location_tool"](
                base_location=location_info["base_location"],
                analysis_type=location_info["analysis_type"],
                criteria="job market and tech industry"
            )
            
            if not location_result["success"]:
                return self.create_content({
                    "success": False,
                    "error": "Location expansion failed",
                    "details": location_result.get("error", "Unknown error")
                })
            
            # Extract discovered locations
            discovered_locations = []
            if location_info["analysis_type"] == "nearby":
                if "nearby_locations" in location_result:
                    nearby_data = location_result["nearby_locations"]
                    if isinstance(nearby_data, list) and len(nearby_data) > 0:
                        if isinstance(nearby_data[0], dict) and "city" in nearby_data[0]:
                            discovered_locations = [loc["city"] for loc in nearby_data]
                        else:
                            discovered_locations = nearby_data
            else:
                discovered_locations = location_result.get("similar_locations", [])
            
            # Apply expanded locations to session state
            modifications = []
            all_locations = [location_info["base_location"]] + discovered_locations[:self.config.max_locations_expansion]
            
            for location in all_locations:
                if location not in session_state.get('current_cities', []):
                    filter_result = await self.tools["filter_tool"](
                        "add_location", session_state, location=location, mandatory=False
                    )
                    if filter_result["success"]:
                        modifications.extend(filter_result["modifications"])
            
            message = f"Expanded '{location_info['base_location']}' to {len(all_locations)} locations: {', '.join(all_locations)}"
            
            return self.create_content({
                "success": True,
                "expansion_type": "location_expansion",
                "base_location": location_info["base_location"],
                "analysis_type": location_info["analysis_type"],
                "expanded_locations": all_locations,
                "modifications": modifications,
                "session_state": session_state,
                "message": message,
                "trigger_search": False,
                "location_analysis": location_result
            })
            
        except Exception as e:
            logger.error(f"Location expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Location expansion failed: {str(e)}"
            })
    
    async def _handle_multi_expansion(self, user_input: str, session_state: Dict[str, Any],
                                memory_context: List[Dict[str, Any]], session_id: str, 
                                user_id: str) -> Content:
        """Handle multiple expansion types in sequence with Matrix Features priority."""
        try:
            print(f"🔄 ENHANCED MULTI-EXPANSION: Processing '{user_input}'")
            
            all_modifications = []
            expansion_results = []
            
            # Determine which expansions are needed
            input_lower = user_input.lower()
            
            # Skill expansion with Matrix Features
            if any(indicator in input_lower for indicator in ["skill", "skills", "similar skills", "related skills"]):
                skill_result = await self._handle_matrix_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
                if skill_result.data.get("success"):
                    all_modifications.extend(skill_result.data.get("modifications", []))
                    method = skill_result.data.get("method", "unknown")
                    expansion_results.append(f"Skills ({method}): {skill_result.data.get('message', '')}")
            
            # Title expansion with Matrix Features
            if any(indicator in input_lower for indicator in ["title", "titles", "role", "roles", "position", "positions", "similar titles", "related titles", "similar roles", "related roles"]):
                title_result = await self._handle_matrix_title_expansion(user_input, session_state, memory_context, session_id, user_id)
                if title_result.data.get("success"):
                    all_modifications.extend(title_result.data.get("modifications", []))
                    method = title_result.data.get("method", "unknown")
                    expansion_results.append(f"Titles ({method}): {title_result.data.get('message', '')}")
            
            # Location expansion (unchanged)
            if any(indicator in input_lower for indicator in ["location", "locations", "nearby", "similar cities", "cities", "city"]):
                location_result = await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
                if location_result.data.get("success"):
                    all_modifications.extend(location_result.data.get("modifications", []))
                    expansion_results.append(f"Locations: {location_result.data.get('message', '')}")
            
            combined_message = " | ".join(expansion_results) if expansion_results else "Multi-expansion completed"
            
            return self.create_content({
                "success": True,
                "expansion_type": "multi_expansion",
                "modifications": all_modifications,
                "session_state": session_state,
                "message": combined_message,
                "trigger_search": False,
                "expansion_count": len(expansion_results),
                "enhanced_multi_expansion": True
            })
            
        except Exception as e:
            logger.error(f"Enhanced multi-expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Enhanced multi-expansion failed: {str(e)}"
            })
    
    async def _handle_auto_expansion(self, user_input: str, session_state: Dict[str, Any],
                           memory_context: List[Dict[str, Any]], session_id: str, 
                           user_id: str) -> Content:
        """Auto-detect expansion type with enhanced title detection."""
        try:
            print(f"🔍 AUTO-EXPANSION: '{user_input}'")
            
            # Enhanced detection
            input_lower = user_input.lower()
            
            # Check for skill expansion
            if any(word in input_lower for word in ["skill", "skills", "similar skills", "related skills"]):
                print(f"🎯 Detected skill expansion")
                return await self._handle_matrix_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
            
            # Check for title expansion
            elif any(word in input_lower for word in ["title", "titles", "role", "roles", "position", "positions", "similar titles", "related titles", "similar roles", "related roles"]):
                print(f"🎯 Detected title expansion")
                return await self._handle_matrix_title_expansion(user_input, session_state, memory_context, session_id, user_id)
            
            # Check for location expansion
            elif any(word in input_lower for word in ["location", "city", "nearby", "cities", "similar locations", "nearby locations"]):
                print(f"🎯 Detected location expansion")
                return await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
            
            else:
                # Default to skill expansion if uncertain
                print(f"🎯 Defaulting to skill expansion")
                return await self._handle_matrix_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            return self.create_content({
                "success": False,
                "error": f"Auto-expansion failed: {str(e)}"
            })
    
    async def _expand_skills_with_llm(self, base_skill: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to expand skills (existing method for fallback)."""
        prompt = f"""You are a skills expansion expert. Find 4-5 related/similar skills to "{base_skill}" for tech recruitment.

Base Skill: {base_skill}

CRITICAL: Return ONLY valid JSON in this EXACT format:
{{
    "base_skill": "{base_skill}",
    "expanded_skills": ["skill1", "skill2", "skill3", "skill4"],
    "reasoning": "brief explanation"
}}"""

        try:
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="skill_expansion"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result and llm_result["parsed_response"]:
                parsed = llm_result["parsed_response"]
                return {
                    "success": True,
                    "expanded_skills": parsed.get("expanded_skills", [])
                }
            else:
                return self._fallback_skill_expansion(base_skill)
                
        except Exception as e:
            logger.error(f"LLM skill expansion failed: {e}")
            return self._fallback_skill_expansion(base_skill)
    
    async def _expand_titles_with_llm(self, base_title: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to expand job titles (existing method for fallback)."""
        prompt = f"""You are a job title expansion expert. Find related job titles and suggest relevant skills for "{base_title}".

Base Title: {base_title}

Return ONLY JSON:
{{
    "base_title": "{base_title}",
    "expanded_titles": ["title1", "title2", "title3"],
    "suggested_skills": ["skill1", "skill2", "skill3", "skill4"],
    "reasoning": "brief explanation"
}}"""

        try:
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="title_expansion"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result:
                parsed = llm_result["parsed_response"]
                return {
                    "success": True,
                    "expanded_titles": parsed.get("expanded_titles", []),
                    "suggested_skills": parsed.get("suggested_skills", [])
                }
            else:
                return self._fallback_title_expansion(base_title)
                
        except Exception as e:
            logger.error(f"LLM title expansion failed: {e}")
            return self._fallback_title_expansion(base_title)
    
    def _extract_location_info(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract location and analysis type from user input."""
        input_lower = user_input.lower()
        
        # Location extraction patterns
        location_patterns = [
            r"nearby to ([a-zA-Z\s]+)",
            r"near ([a-zA-Z\s]+)",
            r"around ([a-zA-Z\s]+)",
            r"based (?:in|at|near) ([a-zA-Z\s]+)",
            r"(?:to|from) ([a-zA-Z\s]+)",
            r"locations? (?:to|like|similar to) ([a-zA-Z\s]+)"
        ]
        
        base_location = ""
        import re
        
        for pattern in location_patterns:
            match = re.search(pattern, input_lower)
            if match:
                location_candidate = match.group(1).strip().title()
                if self._is_valid_city_name(location_candidate):
                    base_location = location_candidate
                    break
        
        # Fallback to session state
        if not base_location:
            current_cities = session_state.get('current_cities', [])
            if current_cities:
                base_location = current_cities[-1]
        
        # Determine analysis type
        analysis_type = "similar"
        if "nearby" in input_lower or "close" in input_lower or "near" in input_lower:
            analysis_type = "nearby"
        elif "tech hub" in input_lower or "it hub" in input_lower:
            analysis_type = "industry_hubs"
        
        return {
            "base_location": base_location,
            "analysis_type": analysis_type
        }

    def _is_valid_city_name(self, candidate: str) -> bool:
        """Check if the candidate is a valid city name."""
        from ...utils.constants import CITIES, TECH_SKILLS
        
        # Check against known cities
        if candidate in CITIES:
            return True
        
        # Check if it's obviously a tech skill (to avoid confusion)
        if candidate in TECH_SKILLS:
            return False
        
        # Check length and format
        if len(candidate) >= 3 and candidate.replace(' ', '').isalpha():
            return True
        
        return False
    
    def _fallback_skill_expansion(self, base_skill: str) -> Dict[str, Any]:
        """Fallback skill expansion with hardcoded mappings."""
        skill_mappings = {
            "python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy"],
            "java": ["Spring", "Hibernate", "Maven", "Gradle", "JUnit"],
            "react": ["JavaScript", "TypeScript", "Redux", "Next.js", "Node.js"],
            "javascript": ["React", "Vue.js", "Angular", "Node.js", "TypeScript"],
            "sql": ["MySQL", "PostgreSQL", "Oracle", "MongoDB", "Redis"],
            "aws": ["Docker", "Kubernetes", "Terraform", "Jenkins", "DevOps"],
            "machine learning": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas"],
            "data science": ["Python", "R", "SQL", "Tableau", "Statistics"],
            "devops": ["Docker", "Kubernetes", "Jenkins", "AWS", "Terraform"],
            "frontend": ["React", "Vue.js", "Angular", "CSS", "JavaScript"],
            "backend": ["Node.js", "Express", "API", "Database", "Server"]
        }
        
        expanded = skill_mappings.get(base_skill.lower(), [base_skill])
        return {
            "success": True,
            "expanded_skills": expanded[:self.config.max_skills_expansion]
        }
    
    def _fallback_title_expansion(self, base_title: str) -> Dict[str, Any]:
        """Fallback title expansion with hardcoded mappings."""
        title_mappings = {
            "data scientist": {
                "titles": ["ML Engineer", "Data Analyst", "AI Researcher", "Business Intelligence Analyst"],
                "skills": ["Python", "SQL", "Machine Learning", "Statistics", "Pandas"]
            },
            "software engineer": {
                "titles": ["Developer", "Software Developer", "Programmer", "Full Stack Developer"],
                "skills": ["Java", "Python", "JavaScript", "React", "SQL"]
            },
            "devops engineer": {
                "titles": ["Site Reliability Engineer", "Infrastructure Engineer", "Cloud Engineer", "Platform Engineer"],
                "skills": ["AWS", "Docker", "Kubernetes", "Jenkins", "Terraform"]
            },
            "frontend developer": {
                "titles": ["UI Developer", "React Developer", "Web Developer", "JavaScript Developer"],
                "skills": ["React", "JavaScript", "CSS", "HTML", "TypeScript"]
            },
            "backend developer": {
                "titles": ["API Developer", "Server Developer", "Database Developer", "Microservices Developer"],
                "skills": ["Node.js", "Java", "Python", "SQL", "REST API"]
            },
            "full stack developer": {
                "titles": ["Software Developer", "Web Developer", "Application Developer", "Tech Lead"],
                "skills": ["React", "Node.js", "JavaScript", "SQL", "AWS"]
            },
            "product manager": {
                "titles": ["Product Owner", "Business Analyst", "Project Manager", "Strategy Manager"],
                "skills": ["Agile", "Scrum", "Analytics", "Product Strategy", "Roadmapping"]
            }
        }
        
        mapping = title_mappings.get(base_title.lower(), {
            "titles": [base_title],
            "skills": []
        })
        
        return {
            "success": True,
            "expanded_titles": mapping["titles"][:self.config.max_titles_expansion],
            "suggested_skills": mapping["skills"][:5]
        }
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - enhanced expansion agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on expansion-related terms
        expansion_keywords = ["expand", "similar", "related", "nearby", "like", "matrix", "skill", "title"]
        words = user_input.lower().split()
        
        # Extract expansion type and target
        relevant_terms = []
        for word in words:
            if word in expansion_keywords or len(word) > 3:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:4])