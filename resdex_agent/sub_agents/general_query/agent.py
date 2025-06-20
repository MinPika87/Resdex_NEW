# resdex_agent/sub_agents/general_query/agent.py
"""
General Query Agent - Pure conversational responses with memory.
"""

from typing import Dict, Any, List, Optional
import logging

from ...base_agent import BaseResDexAgent, Content
from .config import GeneralQueryConfig

logger = logging.getLogger(__name__)


class GeneralQueryAgent(BaseResDexAgent):
    """
    General Query Agent for conversational interactions.
    
    RESPONSIBILITIES:
    1. Conversational responses (greetings, help, explanations)
    2. System capability explanations
    3. Memory-aware contextual responses
    4. Pure LLM streaming (no search/filter tools)
    """

    def __init__(self, config: GeneralQueryConfig = None):
        self._config = config or GeneralQueryConfig()
        
        super().__init__(
            name=self._config.name,
            description=self._config.description,
        )
        
        logger.info(f"GeneralQueryAgent initialized for conversational responses")

    @property
    def config(self):
        return self._config
    
    async def execute_core(self, content: Content, memory_context: List[Dict[str, Any]], 
                          session_id: str, user_id: str) -> Content:
        """
        Core conversational logic with memory awareness.
        """
        try:
            user_input = content.data.get("user_input", "")
            session_state = content.data.get("session_state", {})
            
            logger.info(f"GeneralQueryAgent processing: '{user_input}'")
            print(f"💬 GENERAL QUERY: Processing '{user_input}'")
            
            # Determine query type
            query_type = self._classify_query_type(user_input)
            
            # Handle different query types
            if query_type == "greeting":
                return await self._handle_greeting(user_input, session_state, memory_context, user_id)
            elif query_type == "help_request":
                return await self._handle_help_request(user_input, session_state, memory_context)
            elif query_type == "capability_question":
                return await self._handle_capability_question(user_input, session_state, memory_context)
            elif query_type == "explanation":
                return await self._handle_explanation_request(user_input, session_state, memory_context)
            elif query_type == "memory_query":
                return await self._handle_memory_query(user_input, memory_context, user_id)
            else:
                return await self._handle_general_conversation(user_input, session_state, memory_context, user_id)
                
        except Exception as e:
            logger.error(f"GeneralQueryAgent execution failed: {e}")
            return self.create_content({
                "success": False,
                "error": "Conversational response failed",
                "details": str(e)
            })
    
    def _classify_query_type(self, user_input: str) -> str:
        """Classify the type of general query."""
        input_lower = user_input.lower()
        
        # Greeting patterns
        greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if any(pattern in input_lower for pattern in greeting_patterns):
            return "greeting"
        
        # Help patterns
        help_patterns = ["help", "how do i", "how can i", "what can you do", "how to"]
        if any(pattern in input_lower for pattern in help_patterns):
            return "help_request"
        
        # Capability patterns
        capability_patterns = ["what can you", "what do you do", "what are your capabilities", "features"]
        if any(pattern in input_lower for pattern in capability_patterns):
            return "capability_question"
        
        # Explanation patterns
        explanation_patterns = ["explain", "what is", "how does", "why", "tell me about"]
        if any(pattern in input_lower for pattern in explanation_patterns):
            return "explanation"
        
        # Memory patterns
        memory_patterns = ["remember", "recall", "what did we", "previous", "last time", "before"]
        if any(pattern in input_lower for pattern in memory_patterns):
            return "memory_query"
        
        return "general_conversation"
    
    async def _handle_greeting(self, user_input: str, session_state: Dict[str, Any],
                             memory_context: List[Dict[str, Any]], user_id: str) -> Content:
        """Handle greeting messages with memory awareness."""
        try:
            # Check if we have conversation history with this user
            user_name = self._extract_user_name_from_memory(memory_context)
            total_results = session_state.get('total_results', 0)
            
            # Build personalized greeting
            if user_name:
                greeting = f"Hello {user_name}! Great to continue our conversation."
            else:
                greeting = "Hello! I'm your AI assistant for candidate search."
            
            if total_results > 0:
                greeting += f" You have {total_results:,} candidates available in your current search."
            
            greeting += "\n\nI can help you with:\n"
            greeting += "1. **Filter Management**: Add/modify skills, experience, salary, locations\n"
            greeting += "2. **Search Operations**: Find candidates, execute searches\n"
            greeting += "3. **Result Analysis**: Sort, filter, and analyze candidate data\n"
            greeting += "4. **Smart Expansion**: Find related skills, nearby locations\n"
            
            if memory_context:
                greeting += "5. **Continue Previous Work**: I remember our past conversations\n"
            
            greeting += "\nWhat would you like to do today?"
            
            return self.create_content({
                "success": True,
                "message": greeting,
                "type": "greeting",
                "trigger_search": False,
                "session_state": session_state,
                "suggestions": [
                    "Add Python skill",
                    "Find candidates with 5+ years experience",
                    "Show nearby locations to Mumbai",
                    "Sort candidates by experience"
                ]
            })
            
        except Exception as e:
            logger.error(f"Greeting handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "Hello! I'm here to help with candidate search. What can I do for you?",
                "type": "greeting",
                "trigger_search": False
            })
    
    async def _handle_help_request(self, user_input: str, session_state: Dict[str, Any],
                                 memory_context: List[Dict[str, Any]]) -> Content:
        """Handle help requests with context awareness."""
        try:
            # Generate contextual help based on current state
            help_message = "**I can help you with candidate search in several ways:**\n\n"
            
            # Core capabilities
            help_message += "**🔍 Search & Filters:**\n"
            help_message += "• Add skills: 'Add Python skill' or 'Search with Java'\n"
            help_message += "• Set experience: 'Set experience 5-10 years'\n"
            help_message += "• Modify salary: 'Set salary range 10-25 lakhs'\n"
            help_message += "• Add locations: 'Add Mumbai location'\n\n"
            
            help_message += "**🚀 Smart Expansion:**\n"
            help_message += "• Find related skills: 'Find similar skills to Python'\n"
            help_message += "• Discover locations: 'Add nearby locations to Bangalore'\n"
            help_message += "• Expand job titles: 'Find similar titles to Data Scientist'\n\n"
            
            help_message += "**📊 Result Operations:**\n"
            help_message += "• Sort results: 'Sort by experience' or 'Sort by salary'\n"
            help_message += "• Filter results: 'Show candidates with more than 8 years experience'\n"
            help_message += "• View more: 'Show more candidates'\n\n"
            
            # Context-specific help
            current_keywords = session_state.get('keywords', [])
            candidates = session_state.get('candidates', [])
            
            if current_keywords:
                help_message += f"**Current search:** {', '.join(current_keywords[:3])}\n"
                help_message += "Try: 'Remove Java skill' or 'Add React skill'\n\n"
            
            if candidates:
                help_message += f"**Current results:** {len(candidates)} candidates loaded\n"
                help_message += "Try: 'Sort by experience' or 'Show more candidates'\n\n"
            
            help_message += "**💡 Examples:**\n"
            help_message += "• 'Search with Python and 5+ years experience in Mumbai'\n"
            help_message += "• 'Find data scientists with similar skills to machine learning'\n"
            help_message += "• 'Add nearby tech cities to Bangalore and search'\n"
            
            return self.create_content({
                "success": True,
                "message": help_message,
                "type": "help_request",
                "trigger_search": False,
                "session_state": session_state
            })
            
        except Exception as e:
            logger.error(f"Help request handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "I can help you search for candidates, modify filters, and analyze results. Try asking 'Add Python skill' or 'Search with Java'.",
                "type": "help_request",
                "trigger_search": False
            })
    
    async def _handle_capability_question(self, user_input: str, session_state: Dict[str, Any],
                                        memory_context: List[Dict[str, Any]]) -> Content:
        """Handle questions about system capabilities."""
        try:
            capabilities_message = "**🤖 My Capabilities:**\n\n"
            
            capabilities_message += "**🎯 Intelligent Search:**\n"
            capabilities_message += "• Natural language filter modification\n"
            capabilities_message += "• Multi-step search orchestration\n"
            capabilities_message += "• Memory-aware conversations\n\n"
            
            capabilities_message += "**🧠 Smart Expansion:**\n"
            capabilities_message += "• Find related/similar skills automatically\n"
            capabilities_message += "• Discover nearby locations using AI\n"
            capabilities_message += "• Expand job titles to related roles\n\n"
            
            capabilities_message += "**⚡ Advanced Features:**\n"
            capabilities_message += "• Real-time candidate search\n"
            capabilities_message += "• Dynamic result sorting and filtering\n"
            capabilities_message += "• Conversation memory across sessions\n"
            capabilities_message += "• Multi-intent query processing\n\n"
            
            capabilities_message += "**🛠️ Technical Stack:**\n"
            capabilities_message += "• LLM-powered intent understanding\n"
            capabilities_message += "• Multi-agent architecture\n"
            capabilities_message += "• Real-time API integration\n"
            capabilities_message += "• Persistent session management\n\n"
            
            total_results = session_state.get('total_results', 0)
            if total_results > 0:
                capabilities_message += f"**📊 Current Status:**\n"
                capabilities_message += f"• {total_results:,} candidates available\n"
                capabilities_message += f"• Ready for search and analysis\n"
            
            return self.create_content({
                "success": True,
                "message": capabilities_message,
                "type": "capability_question",
                "trigger_search": False,
                "session_state": session_state
            })
            
        except Exception as e:
            logger.error(f"Capability question handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "I'm an AI assistant that helps with candidate search, filter management, and result analysis. I can understand natural language and remember our conversations.",
                "type": "capability_question",
                "trigger_search": False
            })
    
    async def _handle_explanation_request(self, user_input: str, session_state: Dict[str, Any],
                                        memory_context: List[Dict[str, Any]]) -> Content:
        """Handle explanation requests using LLM with memory context."""
        try:
            print(f"📚 EXPLANATION REQUEST: '{user_input}'")
            
            # Build explanation prompt with memory context
            prompt = self._build_explanation_prompt(user_input, session_state, memory_context)
            
            # Use LLM for explanation
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="explanation"
            )
            
            if llm_result["success"]:
                explanation = llm_result.get("response_text", "I'd be happy to explain, but I need more context about what you'd like to know.")
                
                return self.create_content({
                    "success": True,
                    "message": explanation,
                    "type": "explanation",
                    "trigger_search": False,
                    "session_state": session_state,
                    "llm_generated": True
                })
            else:
                # Fallback explanation
                return self.create_content({
                    "success": True,
                    "message": "I'd be happy to explain! Could you be more specific about what you'd like to understand? I can explain how to use search filters, candidate analysis, or any other features.",
                    "type": "explanation",
                    "trigger_search": False,
                    "suggestions": [
                        "How do search filters work?",
                        "How to find similar skills?",
                        "How to expand locations?",
                        "How does candidate ranking work?"
                    ]
                })
                
        except Exception as e:
            logger.error(f"Explanation handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "I can help explain how the candidate search system works. What would you like to know more about?",
                "type": "explanation",
                "trigger_search": False
            })
    
    async def _handle_memory_query(self, user_input: str, memory_context: List[Dict[str, Any]], 
                                 user_id: str) -> Content:
        """Handle memory-related queries."""
        try:
            print(f"🧠 MEMORY QUERY: '{user_input}'")
            
            if not memory_context:
                return self.create_content({
                    "success": True,
                    "message": "I don't have any previous conversation history with you yet. This might be our first interaction! Feel free to start by asking me to search for candidates or modify filters.",
                    "type": "memory_query",
                    "trigger_search": False
                })
            
            # Format memory results for user
            memory_response = "📚 **Here's what I remember from our conversations:**\n\n"
            
            for i, memory in enumerate(memory_context[:3], 1):
                content = memory.get("content", "")
                timestamp = memory.get("timestamp", "")
                
                if content:
                    # Extract meaningful information
                    if "search" in content.lower():
                        memory_response += f"**{i}.** 🔍 {content[:100]}...\n"
                    elif "added" in content.lower() or "skill" in content.lower():
                        memory_response += f"**{i}.** ⚙️ {content[:100]}...\n"
                    else:
                        memory_response += f"**{i}.** 💬 {content[:100]}...\n"
                    
                    if timestamp:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            memory_response += f"   *{dt.strftime('%B %d, %Y at %I:%M %p')}*\n\n"
                        except:
                            memory_response += f"   *{timestamp}*\n\n"
            
            if len(memory_context) > 3:
                memory_response += f"*...and {len(memory_context) - 3} more conversations.*\n\n"
            
            memory_response += "💡 **Would you like to:**\n"
            memory_response += "• Continue with a previous search\n"
            memory_response += "• Start a new candidate search\n"
            memory_response += "• Modify existing filters\n"
            
            return self.create_content({
                "success": True,
                "message": memory_response,
                "type": "memory_query",
                "trigger_search": False,
                "memory_count": len(memory_context)
            })
            
        except Exception as e:
            logger.error(f"Memory query handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "I have some memory of our conversations, but I'm having trouble accessing the details right now. How can I help you today?",
                "type": "memory_query",
                "trigger_search": False
            })
    
    async def _handle_general_conversation(self, user_input: str, session_state: Dict[str, Any],
                                         memory_context: List[Dict[str, Any]], user_id: str) -> Content:
        """Handle general conversational queries with LLM."""
        try:
            print(f"💬 GENERAL CONVERSATION: '{user_input}'")
            
            # Build conversational prompt with memory context
            prompt = self._build_conversation_prompt(user_input, session_state, memory_context)
            
            # Use LLM for conversational response
            llm_result = await self.tools["llm_tool"]._call_llm_direct(
                prompt=prompt,
                task="general_conversation"
            )
            
            if llm_result["success"]:
                response = llm_result.get("response_text", "I'm here to help with candidate search! What would you like to do?")
                
                return self.create_content({
                    "success": True,
                    "message": response,
                    "type": "general_conversation",
                    "trigger_search": False,
                    "session_state": session_state,
                    "llm_generated": True,
                    "memory_enhanced": len(memory_context) > 0
                })
            else:
                # Fallback conversational response
                fallback_response = self._get_fallback_conversation_response(user_input, session_state, memory_context)
                
                return self.create_content({
                    "success": True,
                    "message": fallback_response,
                    "type": "general_conversation",
                    "trigger_search": False,
                    "session_state": session_state,
                    "fallback_response": True
                })
                
        except Exception as e:
            logger.error(f"General conversation handling failed: {e}")
            return self.create_content({
                "success": True,
                "message": "I'm here to help with candidate search and analysis. What would you like to do?",
                "type": "general_conversation",
                "trigger_search": False
            })
    
    def _build_explanation_prompt(self, user_input: str, session_state: Dict[str, Any],
                                memory_context: List[Dict[str, Any]]) -> str:
        """Build prompt for explanation requests."""
        
        memory_summary = ""
        if memory_context:
            memory_items = [f"- {mem.get('content', '')[:60]}" for mem in memory_context[:2]]
            memory_summary = f"\nPrevious context:\n{chr(10).join(memory_items)}\n"
        
        current_state = f"""Current search state:
- Skills: {session_state.get('keywords', [])}
- Experience: {session_state.get('min_exp', 0)}-{session_state.get('max_exp', 10)} years
- Locations: {session_state.get('current_cities', [])}
- Results: {len(session_state.get('candidates', []))} candidates"""
        
        return f"""You are a helpful AI assistant for a candidate search system. Provide clear, informative explanations.

{current_state}

{memory_summary}

User question: "{user_input}"

Provide a helpful explanation that:
1. Directly answers their question
2. Uses simple, clear language
3. Includes practical examples if relevant
4. Offers next steps or suggestions
5. Keeps response under 300 words

Be conversational and helpful. If you're not sure what they're asking about, ask for clarification.

Response:"""
    
    def _build_conversation_prompt(self, user_input: str, session_state: Dict[str, Any],
                                 memory_context: List[Dict[str, Any]]) -> str:
        """Build prompt for general conversation."""
        
        user_name = self._extract_user_name_from_memory(memory_context)
        name_context = f"User's name: {user_name}" if user_name else "User's name: Not known"
        
        memory_summary = ""
        if memory_context:
            memory_items = [f"- {mem.get('content', '')[:50]}" for mem in memory_context[:2]]
            memory_summary = f"\nRecent conversation:\n{chr(10).join(memory_items)}\n"
        
        total_results = session_state.get('total_results', 0)
        
        return f"""You are a friendly AI assistant for candidate search. Respond naturally and helpfully.

{name_context}
Available candidates: {total_results:,}
Current skills: {session_state.get('keywords', [])}

{memory_summary}

User message: "{user_input}"

Instructions:
1. Be conversational and helpful
2. Use the user's name if you know it
3. Reference conversation history naturally when relevant
4. Keep responses under 200 words
5. Offer specific help with candidate search
6. If they seem confused, provide clear next steps

Capabilities to mention when relevant:
- Add/modify search filters (skills, experience, salary, locations)  
- Find related skills and nearby locations
- Sort and analyze candidate results
- Remember conversations for continuity

Response:"""
    
    def _get_fallback_conversation_response(self, user_input: str, session_state: Dict[str, Any],
                                          memory_context: List[Dict[str, Any]]) -> str:
        """Generate fallback conversation response."""
        user_name = self._extract_user_name_from_memory(memory_context)
        greeting = f"Hi {user_name}! " if user_name else "Hello! "
        
        total_results = session_state.get('total_results', 0)
        current_skills = session_state.get('keywords', [])
        
        response = greeting + "I'm your AI assistant for candidate search. "
        
        if total_results > 0:
            response += f"You have {total_results:,} candidates available. "
            
        if current_skills:
            response += f"Current search includes: {', '.join(current_skills[:3])}. "
        
        response += "\n\nI can help you:\n"
        response += "• Add or modify search filters\n"
        response += "• Find related skills and locations\n"
        response += "• Sort and analyze results\n"
        response += "• Remember our conversation history\n\n"
        
        response += "What would you like to do?"
        
        return response
    
    def _extract_user_name_from_memory(self, memory_context: List[Dict[str, Any]]) -> Optional[str]:
        """Extract user name from memory context."""
        try:
            for memory in memory_context:
                content = memory.get("content", "").lower()
                original_content = memory.get("original_content", {})
                
                # Check for name in content
                if "my name is" in content:
                    import re
                    name_match = re.search(r'my name is (\w+)', content)
                    if name_match:
                        return name_match.group(1).title()
                
                # Check in metadata
                if isinstance(original_content, dict):
                    user_name = original_content.get("user_name")
                    if user_name:
                        return user_name
                
                # Check in metadata field
                metadata = memory.get("metadata", {})
                if isinstance(metadata, dict) and metadata.get("user_name"):
                    return metadata["user_name"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract user name: {e}")
            return None
    
    def extract_memory_search_terms(self, content: Content) -> str:
        """Extract search terms for memory context - general query agent specific."""
        user_input = content.data.get("user_input", "")
        
        # Focus on conversational and help-related terms
        conversation_keywords = ["help", "explain", "how", "what", "why", "remember", "previous"]
        words = user_input.lower().split()
        
        relevant_terms = []
        for word in words:
            if word in conversation_keywords or len(word) > 4:
                relevant_terms.append(word)
        
        return " ".join(relevant_terms[:4])



