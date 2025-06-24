# resdex_agent/prompts.py - ENHANCED with Memory Context Support
"""
Enhanced prompts with memory context support for better AI responses.
"""

from typing import Dict, Any, List


class RootAgentPrompts:
    """Enhanced prompts with memory context integration."""
    
    @staticmethod
    def get_routing_prompt_with_memory(user_input: str, session_state: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> str:
        """Enhanced routing prompt with memory context and expanded expansion support."""
        
        memory_summary = ""
        if memory_context and len(memory_context) > 0:
            try:
                memory_items = []
                for memory in memory_context[:3]:
                    content = memory.get("content", "")
                    if content and len(content) > 10:
                        memory_items.append(f"- {content[:100]}...")
                
                if memory_items:
                    memory_summary = f"""
    Recent conversation context:
    {chr(10).join(memory_items)}
    """
            except Exception as e:
                print(f"⚠️ Memory context processing failed: {e}")
                memory_summary = ""
        
        return f"""You are a routing assistant for a candidate search system with memory awareness and expansion capabilities. Think through the classification and respond with JSON.

    {memory_summary}

    Current context:
    - Active search filters: {session_state.get('keywords', [])}
    - Current candidates: {len(session_state.get('candidates', []))} results

    User input: "{user_input}"

    <think>
    Consider both the current user input and the conversation history:
    1. Does this relate to previous conversations or searches?
    2. Is this a new request or continuation of previous discussion?
    3. Should this be routed to expansion operations, search operations, or general conversation?

    Analyze the user input to determine if this is:
    1. EXPANSION operations (skill expansion, title expansion, location expansion)
    2. SEARCH/FILTER operations (adding skills, modifying criteria, searching) 
    3. GENERAL conversation/questions (greetings, help, analysis requests)
    4. MEMORY-related queries (asking about past conversations)
    </think>

    ENHANCED ROUTING RULES:
    1. If input involves EXPANSION operations → route to "expansion"
    - Skill expansion: "similar skills to X", "related skills", "expand skills", "skills like X"
    - Title expansion: "similar titles to X", "related titles", "expand titles", "titles like X", "similar roles", "related positions"
    - Location expansion: "nearby locations", "similar cities", "locations near X"
    
    2. If input involves SEARCH/FILTER operations → route to "search_interaction"
    - Adding/removing skills, experience, salary, location filters
    - Search commands: "search with", "find", "show me", "filter by"
    - Modifying any search criteria

    3. If input asks about PAST/PREVIOUS conversations → route to "general_query"

    4. If input is general conversation/analysis → route to "general_query"

    EXPANSION INDICATORS (route to "expansion"):
    - "similar skills to [X]", "related skills", "skills like [X]"
    - "similar titles to [X]", "related titles", "titles like [X]"  
    - "similar roles to [X]", "related roles", "roles like [X]"
    - "similar positions to [X]", "related positions", "positions like [X]"
    - "nearby locations to [X]", "similar cities", "locations near [X]"
    - "expand [X]", "find similar [X]", "related to [X]"

    SEARCH/FILTER INDICATORS (route to "search_interaction"):
    - Adding/removing skills, experience, salary, location filters
    - Search commands: "search with", "find candidates", "show me results", "filter by"
    - Modifying any search criteria without expansion

    MEMORY QUERY INDICATORS (route to "general_query"):
    - "remember", "recall", "what did we discuss", "previous", "before", "last time"

    GENERAL QUERY INDICATORS (route to "general_query"):
    - Greetings: "hi", "hello", "hey"
    - Analysis: "analyze results", "explain", "what do you think"
    - Questions: "how does this work", "what can you do"

    Response format:
    {{
        "request_type": "expansion" | "search_interaction" | "general_query",
        "expansion_subtype": "skill_expansion" | "title_expansion" | "location_expansion" | null,
        "confidence": 0.0-1.0,
        "reasoning": "brief explanation",
        "memory_influenced": true | false
    }}

    Examples:
    "similar skills to python" → {{"request_type": "expansion", "expansion_subtype": "skill_expansion", "confidence": 0.95, "reasoning": "Clear skill expansion request", "memory_influenced": false}}
    "find similar titles to data scientist" → {{"request_type": "expansion", "expansion_subtype": "title_expansion", "confidence": 0.95, "reasoning": "Clear title expansion request", "memory_influenced": false}}
    "filter by java" → {{"request_type": "search_interaction", "expansion_subtype": null, "confidence": 0.95, "reasoning": "Clear filter command", "memory_influenced": false}}
    "hello" → {{"request_type": "general_query", "expansion_subtype": null, "confidence": 0.95, "reasoning": "Greeting message", "memory_influenced": false}}"""

    @staticmethod
    def get_general_query_prompt_with_memory(user_input: str, session_state: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> str:
        """Enhanced general query prompt with intelligent memory integration."""
        total_results = session_state.get('total_results', 0)
        current_filters = session_state.get('keywords', [])
        
        # Format memory context for LLM intelligence (not hardcoded rules)
        memory_context_text = ""
        if memory_context and len(memory_context) > 0:
            try:
                memory_entries = []
                for memory in memory_context[:5]:  # Provide more context
                    content = memory.get("content", "")
                    timestamp = memory.get("timestamp", "")
                    if content and len(content) > 5:
                        memory_entries.append({
                            "content": content,
                            "timestamp": timestamp,
                            "relevance_score": memory.get("score", 0.0)
                        })
                
                if memory_entries:
                    memory_context_text = f"""

    CONVERSATION MEMORY (Use your intelligence to determine relevance):
    """
                    for i, entry in enumerate(memory_entries, 1):
                        memory_context_text += f"""
    {i}. "{entry['content']}" (Score: {entry['relevance_score']:.2f}, Time: {entry['timestamp']})"""
                    
                    memory_context_text += """

    Instructions: Use the above memory entries intelligently. If the user asks about personal information (like their name), search the memory for relevant details. If they ask about past conversations, reference the appropriate memories. Don't force memory usage - only use it when genuinely relevant."""
            except Exception as e:
                print(f"⚠️ Memory context processing failed: {e}")
                memory_context_text = ""
    
        return f"""You are a helpful AI assistant for a candidate search system with conversation memory. You have access to previous conversation history and should use it intelligently when relevant.

Current search context:
- Active filters: {current_filters}
- Total results in database: {total_results:,}

{memory_context_text}

User input: "{user_input}"
INSTRUCTIONS:
1. NO <think> tags - respond directly to the user
2. Use conversation memory intelligently:
   - If user asks about their name/identity, check memory for previous introductions
   - If user references past conversations, look for relevant context
   - If user asks about previous searches, reference search history
   - Don't mention memory explicitly unless directly asked
3. Be conversational and helpful
4. Keep responses concise but informative
5. When listing capabilities, use numbered format: "1. ...", "2. ...", "3. ..."
6. If something is not mentioned by the user then you can assume it and reply something good to the user instead of you cannot perform the task.


CAPABILITIES TO MENTION (when relevant):
1. Add/modify skills, experience ranges, locations
2. Analyze current search results and provide insights
3. Sort candidates by experience, salary, or other criteria
4. Show more candidates from database
5. Explain why certain candidates match criteria
6. Remember and reference our conversations naturally

Respond naturally and helpfully using your intelligence to leverage conversation memory when appropriate.

RESPONSE EXAMPLES:
Input: "Hi" → "Hello! Great to continue our conversation. You have {total_results:,} total results available. I can help with:

1. Modify search filters by adding skills or criteria
2. Analyze your current search results
3. Sort candidates by different parameters
4. Show more candidates from the database

What would you like to do?"

Input: "What did we discuss about Python before?" → [Reference memory context and provide relevant information]

Input: "What can you do?" → "I can assist you in several ways:

1. Filter Management: Add/remove skills, set experience ranges, modify salary criteria
2. Result Analysis: Analyze candidate skills, experience distribution, salary ranges
3. Search Optimization: Suggest related skills, recommend filter adjustments
4. Data Organization: Sort by experience/salary, group by skills
5. Insights: Identify skill gaps, market trends, candidate availability
6. Conversation Memory: Remember our past discussions and searches

You currently have {total_results:,} total results to work with. What would you like to try?"

Respond naturally and helpfully. No thinking process - just the direct response."""

    @staticmethod 
    def get_task_breakdown_prompt_with_memory(user_input: str, session_state: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> str:
        """Enhanced task breakdown prompt with memory context."""
        current_location = ""
        current_filters = {
            'keywords': session_state.get('keywords', []),
            'experience': f"{session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years",
            'salary': f"{session_state.get('min_salary', 0)}-{session_state.get('max_salary', 15)} lakhs",
            'current_cities': session_state.get('current_cities', []),
            'preferred_cities': session_state.get('preferred_cities', [])
        }
        
        memory_context_text = ""
        if memory_context:
            memory_items = []
            for memory in memory_context[:2]:
                content = memory.get("content", "")
                if content and len(content) < 150:
                    memory_items.append(f"- {content}")
            
            if memory_items:
                memory_context_text = f"""
Relevant past interactions:
{chr(10).join(memory_items)}
Consider this context when breaking down the task.
"""
        
        return f"""You are a task breakdown assistant with conversation memory. Analyze the user request and create a step-by-step execution plan.

Current context:
- User location: {current_location}
- Current filters: {current_filters}

{memory_context_text}

User input: "{user_input}"

<think>
Analyze this request carefully with memory context:
1. What is the user trying to achieve?
2. Does this relate to previous conversations or searches?
3. What tools are needed?
4. What's the optimal sequence of operations?
5. Should a search be triggered? (only if user mentions search anywhere in their message)

Break down complex requests into logical steps, considering conversation history.
</think>

AVAILABLE TOOLS:
1. "filter_tools" - Add/remove skills, modify experience/salary, add/remove locations
2. "search_tools" - Execute candidate search with current filters
3. "location_tools" - Find similar/nearby locations
4. "skill_analysis" - Find related/similar skills
5. "memory_tools" - Reference past conversations and searches

TASK BREAKDOWN FORMAT:
{{
    "tasks": [
        {{
            "step": 1,
            "action": "filter_modification|search_execution|location_analysis|skill_analysis|memory_reference",
            "description": "What this step does",
            "parameters": {{"key": "value"}},
            "reasoning": "Why this step is needed"
        }}
    ],
    "final_goal": "Overall objective",
    "requires_search": true/false,
    "memory_informed": true/false
}}

Return the JSON task breakdown."""


class IntentExtractionPrompt:
    """Enhanced intent extraction with memory awareness."""
    
    def __init__(self):
        self.system_prompt_template = """You are an AI assistant that helps interpret user requests to modify search filters for a job candidate search system with conversation memory.

Current search filters:
{current_filters}

{memory_context}

<think>
Analyze the user request carefully with memory context:
1. What action do they want to perform?
2. Does this relate to previous conversations?
3. What specific values are mentioned?
4. Is this mandatory or optional?
5. Should a search be triggered?
6. How should I respond to the user considering our conversation history?

Parse the request thoroughly to extract the correct intent, using memory context for better understanding.
</think>

Your task is to interpret the user's request and return a JSON response with the filter modifications.

IMPORTANT: If the user mentions multiple actions in one request, return an array of actions. If it's a single action, return a single object. If something is not mentioned by the user then you can assume it and reply something good to the user instead of you cannot perform the task.

Response formats and examples remain the same...

Return ONLY valid JSON response. No additional text or explanation."""
    
    def build_prompt_with_memory(self, user_input: str, current_filters: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> str:
        """Build intent extraction prompt with memory context."""
        filters_str = f"""- Keywords: {current_filters.get('keywords', [])}
- Experience: {current_filters.get('min_exp', 0)}-{current_filters.get('max_exp', 10)} years
- Salary: {current_filters.get('min_salary', 0)}-{current_filters.get('max_salary', 15)} lakhs
- Cities: {current_filters.get('current_cities', [])}
- Preferred Cities: {current_filters.get('preferred_cities', [])}"""
        
        memory_context_text = ""
        if memory_context:
            memory_items = []
            for memory in memory_context[:2]:
                content = memory.get("content", "")
                if content and len(content) < 100:
                    memory_items.append(f"- {content}")
            
            if memory_items:
                memory_context_text = f"""
Recent conversation context:
{chr(10).join(memory_items)}
"""
        
        system_prompt = self.system_prompt_template.format(
            current_filters=filters_str,
            memory_context=memory_context_text
        )
        
        return f"{system_prompt}\n\nUser request: {user_input}"
    
    def build_prompt(self, user_input: str, current_filters: Dict[str, Any]) -> str:
        """Build intent extraction prompt without memory context (fallback)."""
        return self.build_prompt_with_memory(user_input, current_filters, [])