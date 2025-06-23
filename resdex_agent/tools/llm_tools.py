"""
LLM interaction tools for ResDex Agent.
"""
from typing import Dict, Any, List, Optional, Union
import logging
import json
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from openai import OpenAI
from ..config import config
from ..utils.data_processing import DataProcessor

logger = logging.getLogger(__name__)


class LLMTool(Tool):
    """Tool for LLM interactions and intent extraction using Qwen API with streaming."""
    def __init__(self, name: str = "llm_tool"):
        super().__init__(name=name, description="Process natural language using Qwen LLM with streaming")
        
        self.api_key = config.llm.api_key  
        self.base_url = config.llm.base_url 
        self.model_name = config.llm.model  
        self.temperature = config.llm.temperature  
        self.max_tokens = config.llm.max_tokens 
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        self.data_processor = DataProcessor()
        
        logger.info(f"LLM Tool initialized with OpenAI client:")
        logger.info(f"  API Base URL: {self.base_url}")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Temperature: {self.temperature}")
        logger.info(f"  Max Tokens: {self.max_tokens}")
    
    async def __call__(self, 
                      user_input: str, 
                      current_filters: Dict[str, Any],
                      task: str = "extract_intent") -> Dict[str, Any]:
        """Process user input using Qwen LLM with streaming."""
        try:
            if task == "extract_intent":
                return await self._extract_search_intent(user_input, current_filters)
            else:
                return {"success": False, "error": f"Unknown task: {task}"}
                
        except Exception as e:
            logger.error(f"Qwen LLM processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_llm_direct(self, prompt: str, task: str = "general") -> Dict[str, Any]:
        try:
            messages = [{"role": "user", "content": prompt}]
            
            logger.info(f"🚀 Direct LLM call for task: {task}")
            print(f"🚀 DIRECT LLM CALL: {task}")
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
                presence_penalty=0,
                top_p=0.6,
                n=1
            )
            
            full_response = ""
            print(f"📡 LLM RESPONSE ({task}):")
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end='', flush=True)
            
            print(f"\n✅ STREAMING COMPLETE - Length: {len(full_response)} characters")
            
            # ENHANCED: Handle JSON parsing tasks with debugging
            if task in ["routing", "routing_with_memory", "task_breakdown","multi_intent_analysis", "skill_expansion", "designation_skill_analysis"]:
                print(f"🔍 ATTEMPTING JSON PARSING for task: {task}")
                
                # Clean the response
                cleaned_response = self._clean_llm_response(full_response)
                print(f"🧹 CLEANED RESPONSE: {cleaned_response}")
                
                # Try to parse JSON
                parsed_data = self.data_processor.extract_json_from_text(cleaned_response)
                print(f"🔍 PARSED DATA: {parsed_data} (type: {type(parsed_data)})")
                
                if parsed_data:
                    print(f"✅ JSON PARSING SUCCESS for {task}")
                    return {
                        "success": True,
                        "parsed_response": parsed_data,
                        "raw_response": full_response,
                        "cleaned_response": cleaned_response,
                        "task": task
                    }
                else:
                    print(f"❌ JSON PARSING FAILED for task: {task}")
                    print(f"🔍 Raw response preview: {full_response[:300]}...")
                    print(f"🧹 Cleaned response preview: {cleaned_response[:300]}...")
                    
                    # Try manual JSON extraction as fallback
                    import json
                    import re
                    
                    # Look for JSON patterns manually
                    json_patterns = [
                        r'\{[^{}]*"request_type"[^{}]*\}',  # Simple object pattern
                        r'\{[\s\S]*?"request_type"[\s\S]*?\}',  # Multi-line object
                        r'\[[\s\S]*?\]'  # Array pattern
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, cleaned_response, re.IGNORECASE)
                        for match in matches:
                            try:
                                manual_parsed = json.loads(match)
                                print(f"✅ MANUAL JSON PARSING SUCCESS: {manual_parsed}")
                                return {
                                    "success": True,
                                    "parsed_response": manual_parsed,
                                    "raw_response": full_response,
                                    "cleaned_response": cleaned_response,
                                    "task": task,
                                    "parsing_method": "manual_regex"
                                }
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"❌ ALL JSON PARSING METHODS FAILED for {task}")
                    return {
                        "success": False,
                        "error": "Failed to parse JSON response after all attempts",
                        "raw_response": full_response,
                        "cleaned_response": cleaned_response,
                        "task": task
                    }
            
            # ENHANCED: Handle non-JSON tasks  
            else:
                cleaned_response = self._clean_llm_response(full_response)
                print(f"✅ NON-JSON TASK COMPLETED: {task}")
                return {
                    "success": True,
                    "response_text": cleaned_response,
                    "raw_response": full_response,
                    "task": task
                }
                
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}")
            print(f"❌ LLM CALL EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _extract_search_intent(self, user_input: str, current_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract search modification intent from user input using Qwen with streaming."""
        system_prompt = self._build_intent_extraction_prompt(current_filters)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User request: {user_input}"}
        ]
        
        try:
            logger.info(f"🚀 Sending streaming request to Qwen API at {self.base_url}")
            print(f"🚀 STREAMING REQUEST TO QWEN API...")
            print(f"  - Model: {self.model_name}")
            print(f"  - User Input: '{user_input}'")
            print(f"  - Streaming: Enabled")
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True, 
                presence_penalty=0,
                top_p=0.6,
                n=1
            )
            
            full_response = ""
            print(f"📡 QWEN STREAMING RESPONSE:")
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end='', flush=True)  
            
            print(f"\n✅ STREAMING COMPLETE - Total length: {len(full_response)} characters")
            cleaned_response = self._clean_llm_response(full_response)
            print(f"🧹 CLEANED RESPONSE: {cleaned_response}")
            
            logger.info(f"Qwen streaming response completed: {len(full_response)} characters")
            
            if cleaned_response.strip():
                intent_data = self.data_processor.extract_json_from_text(cleaned_response)
                
                if intent_data:
                    logger.info(f"Successfully extracted intent: {intent_data}")
                    print(f"🎯 SUCCESSFULLY PARSED INTENT: {intent_data}")
                    return {
                        "success": True,
                        "intent_data": intent_data,
                        "raw_response": full_response
                    }
                else:
                    logger.warning("Failed to parse JSON from Qwen response, using default")
                    print(f"⚠️ JSON PARSING FAILED - Using fallback intent")
                    return {
                        "success": True,
                        "intent_data": self._default_intent_response(user_input),
                        "raw_response": full_response
                    }
            else:
                logger.error("Empty response from Qwen API")
                print(f"❌ EMPTY RESPONSE FROM QWEN API")
                return {
                    "success": False,
                    "error": "Empty response from Qwen API",
                    "intent_data": self._default_intent_response(user_input)
                }
                
        except Exception as e:
            logger.error(f"Qwen API streaming call failed: {e}")
            print(f"❌ QWEN API STREAMING ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "intent_data": self._default_intent_response(user_input)
            }
    
    def _build_intent_extraction_prompt(self, current_filters: Dict[str, Any]) -> str:
        """Build system prompt for intent extraction."""
        return f"""You are a JSON extraction assistant for a job candidate search system.   

Current filters:
- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Current Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}

CRITICAL RULES:
1. Return ONLY valid JSON - no explanations, no <think> tags, no extra text
2. For single action: return one object
3. For multiple actions: return array of objects
4. **SEARCH EXECUTION**: When user says "execute search", "search now", "trigger search", etc.
SEARCH EXECUTION SPECIAL HANDLING:
If user request contains search execution keywords like:
- "execute search", "trigger search", "search now", "run search"
- "find candidates", "show results", "get candidates"

Return:
{{
    "action": "search_execution",
    "filter_type": "search",
    "operation": "execute",
    "value": "current_criteria",
    "mandatory": false,
    "response_text": "Executing search with current criteria",
    "trigger_search": true
}}

EXAMPLES:
"execute search with updated criteria" → {{"action": "search_execution", "response_text": "Executing search with current criteria", "trigger_search": true}}
"search now" → {{"action": "search_execution", "response_text": "Executing search", "trigger_search": true}}
"find candidates" → {{"action": "search_execution", "response_text": "Finding candidates with current filters", "trigger_search": true}}

ACTION TYPES:
- add_skill: Add a keyword/skill
- remove_skill: Remove a keyword/skill  
- modify_experience: Change experience range
- modify_salary: Change salary range
- add_location: Add a city location

OPERATION TYPES (USE ONLY THESE):
- For experience/salary: "set_range" (for ranges like "5-10") or "set" (for single values)
- NEVER use: "decrease_max_by", "increase_by", "reduce_by" - these don't exist!

EXPERIENCE/SALARY MODIFICATION LOGIC:
- "reduce experience by 2" → Calculate new range: current max - 2, use "set_range"
- "increase salary by 5" → Calculate new range: current max + 5, use "set_range"  
- "set experience to 8" → Use "set" with value "8"
- "experience 5-12 years" → Use "set_range" with value "5-12"

CURRENT VALUES FOR CALCULATIONS:
- Current experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Current salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs

TRIGGER_SEARCH LOGIC - SIMPLIFIED:
- If user request starts with "search with" or "find" or "show me": SET trigger_search=true for ALL actions
- If user request is just modifications without "search": SET trigger_search=false for ALL actions
- For multiple actions: ALL actions get same trigger_search value
- If the user asks "filter by" : SET trigger_search=true for ALL actions

MANDATORY vs OPTIONAL:
- mandatory=true for: "mandatory", "required", "must have", "should have", "essential", "permanent"
- mandatory=false for: "optional", "nice to have", default case

VALUE FORMATS:
- Skills: "Python", "Java" (clean skill names)
- Experience ranges: "6-15" (always min-max format)
- Salary ranges: "7-30" (always min-max format)  
- Locations: "Bangalore", "Mumbai" (clean city names)

EXAMPLES:
Input: "reduce experience by 2"
Current: 0-10 years
Calculation: 10 - 2 = 8
Output: {{"action": "modify_experience", "operation": "set_range", "value": "0-8", "response_text": "Reduced experience range to 0-8 years", "trigger_search": false}}

Input: "increase salary by 5"  
Current: 0-15 lakhs
Calculation: 15 + 5 = 20
Output: {{"action": "modify_salary", "operation": "set_range", "value": "0-20", "response_text": "Increased salary range to 0-20 lakhs", "trigger_search": false}}

Input: "set max experience to 12"
Current: 0-10 years  
Output: {{"action": "modify_experience", "operation": "set_range", "value": "0-12", "response_text": "Set experience range to 0-12 years", "trigger_search": false}}

Input: "add python as mandatory"
Output: {{"action": "add_skill", "value": "Python", "mandatory": true, "response_text": "Added Python as mandatory skill", "trigger_search": false}}

Input: "search with java"
Output: {{"action": "add_skill", "value": "Java", "mandatory": false, "response_text": "Added Java and searching", "trigger_search": true}}

Input: "search with java as mandatory, experience 6-15 years, bangalore location, salary 7-30 lakhs"
Output: [
{{"action": "add_skill", "value": "Java", "mandatory": true, "response_text": "Added Java as mandatory", "trigger_search": true}},
{{"action": "modify_experience", "operation": "set_range", "value": "6-15", "response_text": "Set experience 6-15 years", "trigger_search": true}},
{{"action": "add_location", "value": "Bangalore", "mandatory": false, "response_text": "Added Bangalore location", "trigger_search": true}},
{{"action": "modify_salary", "operation": "set_range", "value": "7-30", "response_text": "Set salary 7-30 lakhs", "trigger_search": true}}
]

Return ONLY the JSON response."""
    
    # In resdex_agent/tools/llm_tools.py
    def _clean_llm_response(self, response: str) -> str:
        import re
        import json
        
        # Remove <think> tags first
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # ENHANCED: Try multiple JSON extraction patterns
        patterns = [
            # Multi-intent specific pattern (PRIORITY 1)
            r'\{[\s\S]*?"is_multi_intent"[\s\S]*?"reasoning":\s*"[^"]*"[\s\S]*?\}',
            # Array pattern for skill expansion
            r'\[[\s\S]*?\]',
            # General object pattern
            r'\{[\s\S]*?\}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, cleaned, re.MULTILINE | re.DOTALL)
            for match in matches:
                try:
                    match_clean = match.strip()
                    # Remove trailing commas
                    match_clean = re.sub(r',(\s*[}\]])', r'\1', match_clean)
                    
                    parsed = json.loads(match_clean)
                    
                    # CRITICAL: Validate response type
                    if isinstance(parsed, dict):
                        # Multi-intent response
                        if "is_multi_intent" in parsed:
                            print(f"✅ FOUND MULTI-INTENT OBJECT: {parsed}")
                            return match_clean
                        # Other object types
                        else:
                            return match_clean
                    elif isinstance(parsed, list):
                        return match_clean
                            
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse failed for pattern: {e}")
                    continue
        
        print(f"⚠️ No valid JSON found in response: {cleaned[:200]}...")
        return cleaned
    def _default_intent_response(self, user_input: str) -> Dict[str, Any]:
        """Return default intent response when Qwen fails."""
        return {
            "action": "general_query",
            "filter_type": None,
            "operation": None,
            "value": None,
            "mandatory": False,
            "response_text": f"I understand you're asking about: '{user_input}'. Could you please rephrase your request?",
            "trigger_search": False
        }   