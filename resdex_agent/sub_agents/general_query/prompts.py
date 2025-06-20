# resdex_agent/sub_agents/general_query/prompts.py
"""
General Query Agent Specific Prompts
"""

from typing import Dict, Any, List


class GeneralQueryPrompts:
    """Prompts specific to GeneralQueryAgent."""
    
    @staticmethod
    def get_conversation_prompt_with_memory(user_input: str, session_state: Dict[str, Any],
                                          memory_context: List[Dict[str, Any]], user_name: str = None) -> str:
        """Conversational prompt with full memory context."""
        
        name_part = f"User's name: {user_name}\n" if user_name else ""
        
        memory_summary = ""
        if memory_context:
            memory_summary = "Previous conversation history:\n"
            for i, mem in enumerate(memory_context[:3], 1):
                content = mem.get('content', '')[:80]
                memory_summary += f"{i}. {content}...\n"
            memory_summary += "\n"
        
        current_context = f"""Current search context:
- Skills: {session_state.get('keywords', [])}
- Experience: {session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years  
- Locations: {session_state.get('current_cities', [])}
- Available candidates: {session_state.get('total_results', 0):,}
- Loaded results: {len(session_state.get('candidates', []))}
"""
        
        return f"""You are a friendly, knowledgeable AI assistant for candidate search with conversation memory.

{name_part}{current_context}

{memory_summary}User message: "{user_input}"

Respond naturally as a helpful assistant. Use conversation history when relevant. Keep responses conversational and under 250 words.

Key capabilities to mention when relevant:
1. Search filter management (skills, experience, salary, locations)
2. Smart expansion (related skills, nearby locations) 
3. Result analysis (sorting, filtering, insights)
4. Conversation continuity across sessions

Provide specific, actionable suggestions based on their current state and history.

Response:"""
    
    @staticmethod
    def get_explanation_prompt(topic: str, context: Dict[str, Any]) -> str:
        """Generate explanation prompt for specific topics."""
        return f"""You are an expert at explaining candidate search concepts clearly and simply.

Topic to explain: "{topic}"
Context: {context}

Provide a clear, helpful explanation that:
1. Uses simple language and avoids jargon
2. Includes practical examples
3. Offers actionable next steps
4. Stays focused on the topic
5. Keeps response under 300 words

Make it conversational and engaging.

Explanation:"""
    
    @staticmethod
    def get_help_prompt_with_context(user_input: str, current_state: Dict[str, Any]) -> str:
        """Generate contextual help prompt."""
        return f"""You are providing help for a candidate search system.

User's help request: "{user_input}"
Current state: {current_state}

Provide targeted help that:
1. Addresses their specific question
2. Considers their current search state  
3. Offers 3-4 specific examples they can try
4. Includes next steps
5. Is organized and easy to scan

Format with clear sections and examples.

Help response:"""