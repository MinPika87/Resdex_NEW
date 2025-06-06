# Replace resdx_agent/ui/components/chat_interface.py with this fixed version

"""
Chat interface component for ResDex Agent UI - Compatible with Streamlit 1.12
"""

import streamlit as st
import asyncio
from typing import Dict, Any, Optional


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
            
            # Simple buttons without nested columns for Streamlit 1.12
            chat_submitted = st.form_submit_button("Send 💬")
            
            if chat_submitted and user_input.strip():
                asyncio.run(self._handle_chat_message(user_input.strip()))
        
        # Clear chat button outside the form
        if st.button("Clear Chat 🗑️"):
            self.session_state['chat_history'] = []
            st.experimental_rerun()
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.markdown("**Quick Actions:**")
        
        # Simple buttons without nested columns for Streamlit 1.12
        if st.button("📊 Analyze Results", help="Get insights about current search results"):
            asyncio.run(self._handle_chat_message("analyze the current search results"))
        
        if st.button("🔧 Sort by Experience", help="Sort candidates by experience level"):
            asyncio.run(self._handle_chat_message("sort candidates by experience"))
        
        if st.button("💰 Sort by Salary", help="Sort candidates by salary expectations"):
            asyncio.run(self._handle_chat_message("sort candidates by salary"))
        
        if st.button("📍 Filter by Location", help="Help with location-based filtering"):
            asyncio.run(self._handle_chat_message("help me filter by location"))
    
    async def _handle_chat_message(self, user_input: str):
        try:
            # Add user message to history
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Check for "show more candidates" command
            if self._is_show_more_command(user_input):
                return await self._handle_show_more_command()
            
            # Show processing indicator
            with st.spinner("🤖 AI is thinking..."):
                # ENHANCED: Use auto-routing system for other commands
                session_state_dict = self._get_clean_session_state()
                
                print(f"🔍 Prepared clean session state: {list(session_state_dict.keys())}")
                
                # Use auto-routing (no explicit request_type)
                from ...agent import Content
                
                content = Content(data={
                    "user_input": user_input,
                    "session_state": session_state_dict
                })
                
                # Process through enhanced root agent
                result = await self.root_agent.execute(content)
                
                print(f"🔍 Root agent result: {result.data.get('success', False)}")
                print(f"🔍 Response type: {result.data.get('type', 'unknown')}")
                
                if result.data["success"]:
                    # Handle different response types
                    response_type = result.data.get("type", "search_interaction")
                    
                    if response_type == "general_query":
                        # Handle general query responses
                        ai_message = result.data.get("message", "I'm here to help!")
                        self.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": ai_message
                        })
                        
                    else:
                        # Handle search interaction responses
                        if "session_state" in result.data:
                            updated_state = result.data["session_state"]
                            if isinstance(updated_state, dict):
                                self._update_session_state_safely(updated_state)
                        
                        # Add AI response to chat
                        ai_message = result.data.get("message", "Request processed successfully.")
                        self.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": ai_message
                        })
                        
                        # Handle search trigger
                        if result.data.get("trigger_search", False):
                            await self._handle_triggered_search(result.data)
                        
                        # Handle automatic search results (from task breakdown)
                        if "candidates" in result.data.get("session_state", {}):
                            success_msg = "🎯 Search completed with task breakdown!"
                            self.session_state['chat_history'].append({
                                "role": "assistant", 
                                "content": success_msg
                            })
                    
                    # Store debug info
                    if "task_breakdown" in result.data:
                        self.session_state['agent_debug_info'] = result.data["task_breakdown"]
                    elif "processing_details" in result.data:
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
            
            # Use experimental_rerun for Streamlit 1.12
            st.experimental_rerun()
            
        except Exception as e:
            print(f"❌ Chat message handling error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            st.experimental_rerun()

    def _is_show_more_command(self, user_input: str) -> bool:
        """Check if user is asking to show more candidates."""
        show_more_phrases = [
            "show more candidates", "show more", "display more candidates", 
            "more candidates", "load more", "see more candidates",
            "show additional", "display additional", "next batch"
        ]
        
        user_lower = user_input.lower().strip()
        return any(phrase in user_lower for phrase in show_more_phrases)
    # Update the show more responses in chat_interface.py

    async def _handle_show_more_command(self):
        """Handle show more candidates command - FIXED response formatting."""
        try:
            all_candidates = self.session_state.get('all_candidates', [])
            current_display_size = self.session_state.get('display_batch_size', 20)
            
            # Calculate new display size (add 20 more)
            new_display_size = current_display_size + 20
            
            # If we have enough candidates already fetched
            if new_display_size <= len(all_candidates):
                # Use existing candidates
                self.session_state['displayed_candidates'] = all_candidates[:new_display_size]
                self.session_state['candidates'] = all_candidates[:new_display_size]
                self.session_state['display_batch_size'] = new_display_size
                self.session_state['page'] = 0  # Reset to first page
                
                total_results = self.session_state.get('total_results', 0)
                # FIXED: Only mention total results, no displayed count
                ai_response = f"✅ Showing more candidates! You now have access to additional profiles from {total_results:,} total matches. Use pagination to browse through them."
                
            else:
                # Need to fetch more candidates from API
                await self._fetch_more_candidates_from_api()
                return  # _fetch_more_candidates_from_api handles the response
            
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": ai_response
            })
            
            st.experimental_rerun()
            
        except Exception as e:
            error_msg = f"❌ Error showing more candidates: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            st.experimental_rerun()

    async def _fetch_more_candidates_from_api(self):
        """Fetch additional candidates from API when local pool is exhausted - FIXED response."""
        try:
            with st.spinner("🔍 Fetching more candidates from API..."):
                # ... existing fetch logic ...
                
                if result.data["success"] and result.data["candidates"]:
                    new_candidates = result.data["candidates"]
                    
                    # Merge with existing candidates
                    updated_all_candidates = all_candidates + new_candidates
                    self.session_state['all_candidates'] = updated_all_candidates
                    
                    # Update display to show 20 more
                    current_display_size = self.session_state.get('display_batch_size', 20)
                    new_display_size = current_display_size + 20
                    
                    self.session_state['displayed_candidates'] = updated_all_candidates[:new_display_size]
                    self.session_state['candidates'] = updated_all_candidates[:new_display_size]
                    self.session_state['display_batch_size'] = new_display_size
                    self.session_state['page'] = 0
                    
                    # FIXED: Success message mentions only total results
                    total_results = self.session_state.get('total_results', 0)
                    ai_response = f"✅ Fetched additional candidates from the database! You now have access to more profiles from {total_results:,} total matches."
                    
                else:
                    # FIXED: No more candidates message mentions only total results
                    total_results = self.session_state.get('total_results', 0)
                    ai_response = f"ℹ️ No additional candidates available at this time from {total_results:,} total matches. Try refining your search criteria for different results."
                
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                st.experimental_rerun()
                
        except Exception as e:
            error_msg = f"❌ Error fetching more candidates: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            st.experimental_rerun()
    
    def _get_clean_session_state(self) -> Dict[str, Any]:
        """Get session state without Streamlit's internal keys."""
        # CRITICAL FIX: Filter out Streamlit internal keys
        streamlit_keys_to_exclude = [
            # Form submitter keys
            'FormSubmitter:chat_input_form-Send 💬',
            'FormSubmitter:keyword_form-Add Keyword',
            'FormSubmitter:location_form-Add Location',
            # Button state keys (these change frequently)
            'call_1', 'call_2', 'call_3', 'call_4', 'call_5',
            'phone_1', 'phone_2', 'phone_3', 'phone_4', 'phone_5',
            'email_1', 'email_2', 'email_3', 'email_4', 'email_5',
            'remove_kw_0', 'remove_city_0'
        ]
        
        # Additional patterns to exclude
        def should_exclude_key(key: str) -> bool:
            """Check if a key should be excluded from session state."""
            # Exclude FormSubmitter keys
            if key.startswith('FormSubmitter:'):
                return True
            # Exclude button state keys with patterns
            if any(pattern in key for pattern in ['call_', 'phone_', 'email_', 'remove_']):
                return True
            return False
        
        clean_state = {}
        for key, value in self.session_state.items():
            if not should_exclude_key(key):
                try:
                    # Ensure all values are serializable
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        clean_state[key] = value
                    else:
                        clean_state[key] = str(value)
                except Exception as e:
                    print(f"⚠️ Skipping session state key {key}: {e}")
                    continue
        
        return clean_state
    
    def _update_session_state_safely(self, updated_state: Dict[str, Any]):
        """Update session state while avoiding Streamlit internal keys."""
        # CRITICAL FIX: Only update keys that are safe to modify
        safe_keys = [
            'keywords', 'min_exp', 'max_exp', 'min_salary', 'max_salary',
            'current_cities', 'preferred_cities', 'recruiter_company',
            'candidates', 'total_results', 'search_applied', 'page',
            'selected_keywords', 'agent_debug_info', 'active_days',
            'chat_history'
        ]
        
        for key, value in updated_state.items():
            if key in safe_keys:
                try:
                    self.session_state[key] = value
                    print(f"✅ Updated session state key: {key}")
                except Exception as e:
                    print(f"⚠️ Failed to update session state key {key}: {e}")
            else:
                print(f"🔒 Skipped updating protected key: {key}")
    
    async def _handle_triggered_search(self, result_data: Dict[str, Any]):
        """Handle search triggered by AI agent."""
        try:
            # Prepare search filters from updated session state
            updated_state = result_data.get("session_state", self.session_state)
            
            # Ensure updated_state is a dict
            if not isinstance(updated_state, dict):
                print(f"⚠️ Updated state is not a dict: {type(updated_state)}")
                updated_state = self._get_clean_session_state()
            
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
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters
            })
            
            search_result = await self.root_agent.execute(search_content)
            
            if search_result.data["success"]:
                # Update candidates and results safely
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
            print(f"❌ Triggered search error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })