
# resdex_agent/sub_agents/expansion/agent.py
"""
Expansion Agent - Handles skill, location, and title expansion.
"""

from typing import Dict, Any, List, Optional
import logging

from ...base_agent import BaseResDexAgent, Content
from .config import ExpansionConfig

logger = logging.getLogger(__name__)


class ExpansionAgent(BaseResDexAgent):
    """
    Expansion Agent specializing in enriching search queries.
    
    RESPONSIBILITIES:
    1. Skill expansion (find related/similar skills)
    2. Location expansion (find nearby/similar locations) 
    3. Title expansion (find related job titles)
    4. Integration with session state for filter updates
    """

    def __init__(self, config: ExpansionConfig = None):
        self._config = config or ExpansionConfig()
        
        super().__init__(
            name=self._config.name,
            description=self._config.description
        )
        
        # Initialize expansion-specific tools
        self._setup_expansion_tools()
        
        logger.info(f"ExpansionAgent initialized with {len(self.tools)} tools")

    @property
    def config(self):
        return self._config
    
    def _setup_expansion_tools(self):
        """Setup expansion-specific tools."""
        try:
            # Add location expansion tool (move from SearchInteractionAgent)
            from ...tools.location_tools import LocationAnalysisTool
            self.tools["location_tool"] = LocationAnalysisTool("location_expansion_tool")
            
            # Filter tool for applying expanded results
            from ...tools.filter_tools import FilterTool
            self.tools["filter_tool"] = FilterTool("expansion_filter_tool")
            
            print(f"🔧 ExpansionAgent tools: {list(self.tools.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to setup expansion tools: {e}")
    
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Core expansion logic - determines expansion type and executes.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            intent_data = content.data.get("intent_data", {})
            
            logger.info(f"ExpansionAgent processing: '{user_input}'")
            print(f"🔧 EXPANSION AGENT: Processing '{user_input}'")
            
            # Determine expansion type
            expansion_type = self._determine_expansion_type(user_input, intent_data)
            
            if expansion_type == "skill_expansion":
                return await self._handle_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "location_expansion":
                return await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "title_expansion":
                return await self._handle_title_expansion(user_input, session_state, memory_context, session_id, user_id)
            elif expansion_type == "multi_expansion":
                return await self._handle_multi_expansion(user_input, session_state, memory_context, session_id, user_id)
            else:
                # Fallback to auto-detection
                return await self._handle_auto_expansion(user_input, session_state, memory_context, session_id, user_id)
                
        except Exception as e:
            logger.error(f"ExpansionAgent execution failed: {e}")
            return self.create_content({
                "success": False,
                "error": "Expansion failed",
                "details": str(e)
            })
    
    def _determine_expansion_type(self, user_input: str, intent_data: Dict[str, Any]) -> str:
        """Determine what type of expansion is needed."""
        input_lower = user_input.lower()
        
        # Check intent data first
        if intent_data.get("expansion_type"):
            return intent_data["expansion_type"]
        
        # Skill expansion indicators
        skill_indicators = [
            "similar skills", "related skills", "skill expansion", "expand skills",
            "like", "comparable skills", "equivalent skills"
        ]
        
        # Location expansion indicators
        location_indicators = [
            "nearby locations", "similar locations", "location expansion", "expand locations",
            "nearby cities", "similar cities", "around", "close to", "near"
        ]
        
        # Title expansion indicators
        title_indicators = [
            "similar titles", "related titles", "job titles", "expand titles",
            "equivalent roles", "similar roles", "related roles"
        ]
        
        has_skill = any(indicator in input_lower for indicator in skill_indicators)
        has_location = any(indicator in input_lower for indicator in location_indicators)
        has_title = any(indicator in input_lower for indicator in title_indicators)
        
        # Multi-expansion check
        expansion_count = sum([has_skill, has_location, has_title])
        if expansion_count > 1:
            return "multi_expansion"
        elif has_skill:
            return "skill_expansion"
        elif has_location:
            return "location_expansion"
        elif has_title:
            return "title_expansion"
        else:
            return "auto_detection"
    
    async def _handle_skill_expansion(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Handle skill expansion using LLM."""
        try:
            print(f"🎯 SKILL EXPANSION: Analyzing '{user_input}'")
            
            # Extract base skill from input or session state
            base_skill = self._extract_base_skill(user_input, session_state)
            
            if not base_skill:
                return self.create_content({
                    "success": False,
                    "error": "No base skill found for expansion",
                    "message": "Please specify a skill to expand (e.g., 'find similar skills to python')"
                })
            
            # Use LLM for skill expansion
            expansion_result = await self._expand_skills_with_llm(base_skill, memory_context)
            
            if not expansion_result["success"]:
                return self.create_content(expansion_result)
            
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
            
            message = f"Expanded '{base_skill}' to {len(expanded_skills)} related skills: {', '.join(expanded_skills)}"
            
            return self.create_content({
                "success": True,
                "expansion_type": "skill_expansion",
                "base_skill": base_skill,
                "expanded_skills": expanded_skills,
                "modifications": modifications,
                "session_state": session_state,
                "message": message,
                "trigger_search": False
            })
            
        except Exception as e:
            logger.error(f"Skill expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Skill expansion failed: {str(e)}"
            })
    
    async def _handle_location_expansion(self, user_input: str, session_state: Dict[str, Any],
                                       memory_context: List[Dict[str, Any]], session_id: str, 
                                       user_id: str) -> Content:
        """Handle location expansion using existing location tools."""
        try:
            print(f"🗺️ LOCATION EXPANSION: Analyzing '{user_input}'")
            
            # Extract base location and analysis type
            location_info = self._extract_location_info(user_input, session_state)
            
            if not location_info["base_location"]:
                return self.create_content({
                    "success": False,
                    "error": "No base location found for expansion",
                    "message": "Please specify a location to expand (e.g., 'find nearby locations to Mumbai')"
                })
            
            # Use location tool for expansion
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
    
    async def _handle_title_expansion(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Handle title/designation expansion using LLM."""
        try:
            print(f"💼 TITLE EXPANSION: Analyzing '{user_input}'")
            
            # Extract base title from input
            base_title = self._extract_base_title(user_input, session_state)
            
            if not base_title:
                return self.create_content({
                    "success": False,
                    "error": "No base title found for expansion",
                    "message": "Please specify a job title to expand (e.g., 'find similar titles to data scientist')"
                })
            
            # Use LLM for title expansion
            expansion_result = await self._expand_titles_with_llm(base_title, memory_context)
            
            if not expansion_result["success"]:
                return self.create_content(expansion_result)
            
            expanded_titles = expansion_result["expanded_titles"]
            suggested_skills = expansion_result.get("suggested_skills", [])
            
            # Apply suggested skills from title expansion
            modifications = []
            for skill in suggested_skills[:3]:  # Limit to 3 skills
                if skill not in session_state.get('keywords', []):
                    filter_result = await self.tools["filter_tool"](
                        "add_skill", session_state, skill=skill, mandatory=False
                    )
                    if filter_result["success"]:
                        modifications.extend(filter_result["modifications"])
            
            message = f"Expanded '{base_title}' to {len(expanded_titles)} related titles and added {len(suggested_skills)} relevant skills"
            
            return self.create_content({
                "success": True,
                "expansion_type": "title_expansion",
                "base_title": base_title,
                "expanded_titles": expanded_titles,
                "suggested_skills": suggested_skills,
                "modifications": modifications,
                "session_state": session_state,
                "message": message,
                "trigger_search": False
            })
            
        except Exception as e:
            logger.error(f"Title expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Title expansion failed: {str(e)}"
            })
    
    async def _handle_multi_expansion(self, user_input: str, session_state: Dict[str, Any],
                                    memory_context: List[Dict[str, Any]], session_id: str, 
                                    user_id: str) -> Content:
        """Handle multiple expansion types in sequence."""
        try:
            print(f"🔄 MULTI-EXPANSION: Processing '{user_input}'")
            
            all_modifications = []
            expansion_results = []
            
            # Determine which expansions are needed
            input_lower = user_input.lower()
            
            # Skill expansion
            if any(indicator in input_lower for indicator in ["skill", "similar skills", "related skills"]):
                skill_result = await self._handle_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
                if skill_result.data.get("success"):
                    all_modifications.extend(skill_result.data.get("modifications", []))
                    expansion_results.append(f"Skills: {skill_result.data.get('message', '')}")
            
            # Location expansion
            if any(indicator in input_lower for indicator in ["location", "nearby", "similar cities"]):
                location_result = await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
                if location_result.data.get("success"):
                    all_modifications.extend(location_result.data.get("modifications", []))
                    expansion_results.append(f"Locations: {location_result.data.get('message', '')}")
            
            # Title expansion
            if any(indicator in input_lower for indicator in ["title", "role", "designation"]):
                title_result = await self._handle_title_expansion(user_input, session_state, memory_context, session_id, user_id)
                if title_result.data.get("success"):
                    all_modifications.extend(title_result.data.get("modifications", []))
                    expansion_results.append(f"Titles: {title_result.data.get('message', '')}")
            
            combined_message = " | ".join(expansion_results) if expansion_results else "Multi-expansion completed"
            
            return self.create_content({
                "success": True,
                "expansion_type": "multi_expansion",
                "modifications": all_modifications,
                "session_state": session_state,
                "message": combined_message,
                "trigger_search": False,
                "expansion_count": len(expansion_results)
            })
            
        except Exception as e:
            logger.error(f"Multi-expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Multi-expansion failed: {str(e)}"
            })
    
    async def _handle_auto_expansion(self, user_input: str, session_state: Dict[str, Any],
                                   memory_context: List[Dict[str, Any]], session_id: str, 
                                   user_id: str) -> Content:
        """Auto-detect and handle appropriate expansion type."""
        try:
            print(f"🔍 AUTO-EXPANSION: Detecting type for '{user_input}'")
            
            # Use LLM to auto-detect expansion type
            detection_result = await self._auto_detect_expansion_type(user_input, memory_context)
            
            if detection_result["success"]:
                detected_type = detection_result["expansion_type"]
                
                if detected_type == "skill_expansion":
                    return await self._handle_skill_expansion(user_input, session_state, memory_context, session_id, user_id)
                elif detected_type == "location_expansion":
                    return await self._handle_location_expansion(user_input, session_state, memory_context, session_id, user_id)
                elif detected_type == "title_expansion":
                    return await self._handle_title_expansion(user_input, session_state, memory_context, session_id, user_id)
            
            # If auto-detection fails, return helpful message
            return self.create_content({
                "success": True,
                "expansion_type": "none_detected",
                "message": "I can help expand skills, locations, or job titles. Try: 'find similar skills to python' or 'add nearby locations to Mumbai'",
                "suggestions": [
                    "Find similar skills to [skill name]",
                    "Add nearby locations to [city name]", 
                    "Expand titles related to [job title]"
                ],
                "modifications": [],
                "session_state": session_state,
                "trigger_search": False
            })
            
        except Exception as e:
            logger.error(f"Auto-expansion failed: {e}")
            return self.create_content({
                "success": False,
                "error": f"Auto-expansion failed: {str(e)}"
            })
    
    # Helper methods for extraction and LLM calls
    
    def _extract_base_skill(self, user_input: str, session_state: Dict[str, Any]) -> str:
        """Extract base skill from user input or session state."""
        input_lower = user_input.lower()
        
        # Look for skill patterns in input
        skill_patterns = [
            r"skills? (?:to|like|similar to) ([a-zA-Z+#.]+)",
            r"expand ([a-zA-Z+#.]+)",
            r"similar to ([a-zA-Z+#.]+)",
            r"like ([a-zA-Z+#.]+)"
        ]
        
        import re
        for pattern in skill_patterns:
            match = re.search(pattern, input_lower)
            if match:
                return match.group(1).title()
        
        # Fallback to last skill in session state
        keywords = session_state.get('keywords', [])
        if keywords:
            return keywords[-1].replace('★ ', '')
        
        return ""
    
    def _extract_location_info(self, user_input: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract location and analysis type from user input."""
        input_lower = user_input.lower()
        
        # Extract base location
        location_patterns = [
            r"(?:to|near|around) ([a-zA-Z\s]+)",
            r"locations? (?:to|like|similar to) ([a-zA-Z\s]+)",
            r"cities? (?:to|like|similar to) ([a-zA-Z\s]+)"
        ]
        
        base_location = ""
        import re
        for pattern in location_patterns:
            match = re.search(pattern, input_lower)
            if match:
                base_location = match.group(1).strip().title()
                break
        
        # Fallback to session state
        if not base_location:
            current_cities = session_state.get('current_cities', [])
            if current_cities:
                base_location = current_cities[-1]
        
        # Determine analysis type
        analysis_type = "similar"
        if "nearby" in input_lower or "close" in input_lower:
            analysis_type = "nearby"
        elif "tech hub" in input_lower or "it hub" in input_lower:
            analysis_type = "industry_hubs"
        elif "metro" in input_lower:
            analysis_type = "metro_area"
        
        return {
            "base_location": base_location,
            "analysis_type": analysis_type
        }
    
    def _extract_base_title(self, user_input: str, session_state: Dict[str, Any]) -> str:
        """Extract base job title from user input."""
        input_lower = user_input.lower()
        
        # Look for title patterns
        title_patterns = [
            r"titles? (?:to|like|similar to) ([a-zA-Z\s]+)",
            r"roles? (?:to|like|similar to) ([a-zA-Z\s]+)",
            r"designations? (?:to|like|similar to) ([a-zA-Z\s]+)",
            r"expand ([a-zA-Z\s]+) (?:title|role|designation)"
        ]
        
        import re
        for pattern in title_patterns:
            match = re.search(pattern, input_lower)
            if match:
                return match.group(1).strip().title()
        
        return ""
    
    async def _expand_skills_with_llm(self, base_skill: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to expand skills."""
        prompt = f"""You are a skills expansion expert. Find 4-5 related/similar skills to "{base_skill}" for tech recruitment.

Base Skill: {base_skill}

Consider:
1. Technical skills in the same domain
2. Complementary technologies  
3. Skills commonly found together
4. Both specific and general variations

Return ONLY JSON:
{{
    "base_skill": "{base_skill}",
    "expanded_skills": ["skill1", "skill2", "skill3", "skill4"],
    "reasoning": "brief explanation"
}}

Examples:
Python → ["Django", "Flask", "FastAPI", "Pandas", "NumPy"]
React → ["JavaScript", "TypeScript", "Redux", "Next.js", "Node.js"]"""

        try:
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="skill_expansion"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result:
                return {
                    "success": True,
                    "expanded_skills": llm_result["parsed_response"].get("expanded_skills", [])
                }
            else:
                # Fallback to simple mapping
                return self._fallback_skill_expansion(base_skill)
                
        except Exception as e:
            logger.error(f"LLM skill expansion failed: {e}")
            return self._fallback_skill_expansion(base_skill)
    
    async def _expand_titles_with_llm(self, base_title: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to expand job titles."""
        prompt = f"""You are a job title expansion expert. Find related job titles and suggest relevant skills for "{base_title}".

Base Title: {base_title}

Return ONLY JSON:
{{
    "base_title": "{base_title}",
    "expanded_titles": ["title1", "title2", "title3"],
    "suggested_skills": ["skill1", "skill2", "skill3", "skill4"],
    "reasoning": "brief explanation"
}}

Examples:
Data Scientist → titles: ["ML Engineer", "Data Analyst", "AI Researcher"], skills: ["Python", "SQL", "Machine Learning", "Statistics"]"""

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
    
    async def _auto_detect_expansion_type(self, user_input: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to auto-detect expansion type."""
        prompt = f"""Detect what type of expansion the user wants: skill, location, or title.

User input: "{user_input}"

Return ONLY JSON:
{{
    "expansion_type": "skill_expansion|location_expansion|title_expansion|none",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        try:
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="expansion_detection"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result:
                return {
                    "success": True,
                    "expansion_type": llm_result["parsed_response"].get("expansion_type", "none")
                }
            else:
                return {"success": False, "expansion_type": "none"}
                
        except Exception as e:
            logger.error(f"Auto-detection failed: {e}")
            return {"success": False, "expansion_type": "none"}
    
    def _fallback_skill_expansion(self, base_skill: str) -> Dict[str, Any]:
        """Fallback skill expansion with hardcoded mappings."""
        skill_mappings = {
            "python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy"],
            "java": ["Spring", "Hibernate", "Maven", "Gradle", "JUnit"],
            "react": ["JavaScript", "TypeScript", "Redux", "Next.js", "Node.js"],
            "javascript": ["React", "Vue.js", "Angular", "Node.js", "TypeScript"],
            "sql": ["MySQL", "PostgreSQL", "Oracle", "MongoDB", "Redis"],
            "aws": ["Docker", "Kubernetes", "Terraform", "Jenkins", "DevOps"]
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
                "titles": ["ML Engineer", "Data Analyst", "AI Researcher"],
                "skills": ["Python", "SQL", "Machine Learning", "Statistics"]
            },
            "software engineer": {
                "titles": ["Developer", "Software Developer", "Programmer"],
                "skills": ["Java", "Python", "JavaScript", "React"]
            },
            "devops engineer": {
                "titles": ["Site Reliability Engineer", "Infrastructure Engineer", "Cloud Engineer"],
                "skills": ["AWS", "Docker", "Kubernetes", "Jenkins"]
            }
        }
        
        mapping = title_mappings.get(base_title.lower(), {
            "titles": [base_title],
            "skills": []
        })
        
        return {
            "success": True,
            "expanded_titles": mapping["titles"],
            "suggested_skills": mapping["skills"]
        }
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - expansion agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on expansion-related terms
        expansion_keywords = ["expand", "similar", "related", "nearby", "like"]
        words = user_input.lower().split()
        
        # Extract expansion type and target
        relevant_terms = []
        for word in words:
            if word in expansion_keywords or len(word) > 3:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:4])
