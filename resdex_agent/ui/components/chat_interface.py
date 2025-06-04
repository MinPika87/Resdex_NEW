# Replace the content of resdex_agent/ui/components/chat_interface.py

"""
Chat interface component for ResDex Agent UI.
"""

import streamlit as st
import asyncio
from typing import Dict, Any, Optional

# Import Content from agent.py
from ...agent import Content


class ChatInterface:
    """Chat interface component for AI interactions."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
    
    def render(self):
        """Render the complete chat interface."""
        st.markdown("### 🤖 AI Assistant")
        st.markdown("*Ask me to modify search filters, analyze results, or help with candidate selection.*")
        
        # Display chat history
        self._render_chat_history()
        
        # Chat input
        self._render_chat_input()
        
        # Quick action buttons
        self._render_quick_actions()
    
    def _render_chat_history(self):
        """Render chat message history."""
        chat_history = self.session_state.get('chat_history', [])
        
        # Create scrollable chat container
        with st.container():
            st.markdown("**Chat History:**")
            
            if not chat_history:
                st.info("👋 Start a conversation! Try asking 'add python skill' or 'sort by experience'")
                return
            
            # Show recent messages (last 6)
            recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
            
            for message in recent_messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 Assistant:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
            
            if len(chat_history) > 6:
                st.caption(f"Showing recent 6 messages of {len(chat_history)} total")
    
    def _render_chat_input(self):
        """Render chat input form."""
        with st.form(key="chat_input_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant",
                placeholder="e.g., 'add python as mandatory', 'search with java', 'sort by experience'",
                help="Ask me to modify filters, search candidates, or analyze results"
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                chat_submitted = st.form_submit_button("Send 💬", type="primary")
            
            with col2:
                if st.form_submit_button("Clear Chat 🗑️"):
                    self.session_state['chat_history'] = []
                    st.rerun()
            
            if chat_submitted and user_input.strip():
                asyncio.run(self._handle_chat_message(user_input.strip()))
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.markdown("**Quick Actions:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Analyze Results", help="Get insights about current search results"):
                asyncio.run(self._handle_chat_message("analyze the current search results"))
            
            if st.button("🔧 Sort by Experience", help="Sort candidates by experience level"):
                asyncio.run(self._handle_chat_message("sort candidates by experience"))
        
        with col2:
            if st.button("💰 Sort by Salary", help="Sort candidates by salary expectations"):
                asyncio.run(self._handle_chat_message("sort candidates by salary"))
            
            if st.button("📍 Filter by Location", help="Help with location-based filtering"):
                asyncio.run(self._handle_chat_message("help me filter by location"))
    
    async def _handle_chat_message(self, user_input: str):
        """Handle chat message processing."""
        try:
            # Add user message to history
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Show processing indicator
            with st.spinner("🤖 AI is thinking..."):
                # Prepare content for root agent
                content = Content(data={
                    "request_type": "search_interaction",
                    "user_input": user_input,
                    "session_state": dict(self.session_state)  # Convert to regular dict
                })
                
                # Process through root agent
                result = await self.root_agent.execute(content)
                
                if result.data["success"]:
                    # Update session state with any modifications
                    if "session_state" in result.data:
                        updated_state = result.data["session_state"]
                        for key, value in updated_state.items():
                            self.session_state[key] = value
                    
                    # Add AI response to chat
                    ai_message = result.data.get("message", "Request processed successfully.")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    # Handle search trigger
                    if result.data.get("trigger_search", False):
                        await self._handle_triggered_search(result.data)
                    
                    # Store debug info
                    if "processing_details" in result.data:
                        self.session_state['agent_debug_info'] = result.data["processing_details"]
                    
                else:
                    # Handle error response
                    error_message = result.data.get("error", "Sorry, I couldn't process that request.")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": f"❌ {error_message}"
                    })
                    
                    if "suggestions" in result.data:
                        suggestions = result.data["suggestions"]
                        suggestion_text = "Here are some suggestions:\n" + "\n".join([f"• {s}" for s in suggestions])
                        self.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": suggestion_text
                        })
            
            st.rerun()
            
        except Exception as e:
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            st.rerun()
    
    async def _handle_triggered_search(self, result_data: Dict[str, Any]):
        """Handle search triggered by AI agent."""
        try:
            # Prepare search filters from updated session state
            updated_state = result_data.get("session_state", self.session_state)
            
            search_filters = {
                'keywords': updated_state.get('keywords', []),
                'min_exp': updated_state.get('min_exp', 0),
                'max_exp': updated_state.get('max_exp', 10),
                'min_salary': updated_state.get('min_salary', 0),
                'max_salary': updated_state.get('max_salary', 15),
                'current_cities': updated_state.get('current_cities', []),
                'preferred_cities': updated_state.get('preferred_cities', []),
                'recruiter_company': updated_state.get('recruiter_company', '')
            }
            
            # Execute search through root agent
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters
            })
            
            search_result = await self.root_agent.execute(search_content)
            
            if search_result.data["success"]:
                # Update candidates and results
                self.session_state['candidates'] = search_result.data["candidates"]
                self.session_state['total_results'] = search_result.data["total_count"]
                self.session_state['search_applied'] = True
                self.session_state['page'] = 0  # Reset to first page
                
                # Add success message
                success_msg = f"🔄 {search_result.data['message']}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": success_msg
                })
            else:
                # Add error message
                error_msg = f"❌ Search failed: {search_result.data.get('error', 'Unknown error')}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": error_msg
                })
                
        except Exception as e:
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })