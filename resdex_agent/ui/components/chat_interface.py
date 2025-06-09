# resdex_agent/ui/components/chat_interface.py - FIXED for Streamlit threading
"""
Chat interface component - FIXED to avoid threading issues with Streamlit 1.12
"""

import streamlit as st
import asyncio
import time
import uuid
from typing import Dict, Any, Optional

# Step logging imports
from ...utils.step_logger import step_logger
from .step_display import StepDisplay


class ChatInterface:
    """Chat interface component with FIXED step display (no threading)."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
        self.step_display = StepDisplay()
    
    def render(self):
        """Render the complete chat interface."""
        st.markdown("### 🤖 AI Assistant")
        st.markdown("*Ask me to modify search filters, analyze results, or help with candidate selection.*")
        
        # Display chat history
        self._render_chat_history()
        
        # Chat input - FIXED to avoid threading
        self._render_chat_input_fixed()
        
        # Quick action buttons
        self._render_quick_actions()
    
    def _render_chat_history(self):
        """Render chat message history."""
        chat_history = self.session_state.get('chat_history', [])
        
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
    
    def _render_chat_input_fixed(self):
        """FIXED: Render chat input without threading issues."""
        with st.form(key="chat_input_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant",
                placeholder="e.g., 'add python as mandatory', 'search with java', 'sort by experience'",
                help="Ask me to modify filters, search candidates, or analyze results"
            )
            
            chat_submitted = st.form_submit_button("Send 💬")
            
            if chat_submitted and user_input.strip():
                # FIXED: Process immediately without threading
                session_id = str(uuid.uuid4())
                self._process_message_with_simple_steps(user_input.strip(), session_id)
        
        # Clear chat button
        if st.button("Clear Chat 🗑️"):
            self.session_state['chat_history'] = []
            st.experimental_rerun()
    
    def _process_message_with_simple_steps(self, user_input: str, session_id: str):
        """ENHANCED: Process message with REAL step display from step_logger."""
        try:
            # Create step placeholder
            step_placeholder = st.empty()
            
            # Initialize step logging
            step_logger.start_session(session_id)
            
            # Add user message to history
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Process the message with REAL-TIME step updates
            result = asyncio.run(self._handle_chat_message_with_live_steps(user_input, session_id, step_placeholder))
            
            # Show final completion message briefly then clear
            step_placeholder.markdown("🎯 **Processing complete!**")
            time.sleep(10)
            
            # Clear step display
            step_placeholder.empty()
            
            # Trigger rerun to show new messages
            st.experimental_rerun()
            
        except Exception as e:
            step_logger.log_error(f"Chat processing failed: {str(e)}")
            st.error(f"❌ An error occurred: {str(e)}")
    
    def _display_step_summary(self, placeholder, steps):
        """REMOVED: No more HTML step summary - just clear the placeholder."""
        # Simply clear the placeholder instead of showing HTML
        placeholder.empty()
    
    async def _handle_chat_message_with_live_steps(self, user_input: str, session_id: str, step_placeholder) -> bool:
        """ENHANCED: Handle chat message with REAL-TIME live step updates."""
        try:
            # Show steps as they happen - ONE AT A TIME
            def update_steps():
                current_steps = step_logger.get_steps(session_id)
                if current_steps:
                    latest_step = current_steps[-1]
                    icon = self.step_display.step_icons.get(latest_step["type"], "💡")
                    # Show ONLY the latest step in real-time
                    step_placeholder.markdown(f"**{icon} {latest_step['message']}**")
            
            # Log and show initial step
            step_logger.log_step(f"🔍 Analyzing: \"{user_input[:40]}{'...' if len(user_input) > 40 else ''}\"", "routing")
            update_steps()
            
            # Check for "show more candidates" command
            if self._is_show_more_command(user_input):
                step_logger.log_step("📋 Show more candidates detected", "decision")
                update_steps()
                step_logger.log_tool_activation("Candidate Manager", "expanding results")
                update_steps()
                await self._handle_show_more_command()
                step_logger.log_completion("Additional candidates loaded")
                update_steps()
                return True
            
            # Prepare session state
            session_state_dict = self._get_clean_session_state()
            step_logger.log_step("🔧 Preparing agent context", "system")
            update_steps()
            
            # Determine routing
            if self._is_search_related(user_input):
                step_logger.log_routing_decision(user_input, "search_interaction", 0.9)
                update_steps()
                step_logger.log_tool_activation("Search Interaction Agent")
                update_steps()
            else:
                step_logger.log_routing_decision(user_input, "general_query", 0.85)
                update_steps()
                step_logger.log_tool_activation("General LLM Responder")
                update_steps()
            
            # Process through agent
            from ...agent import Content
            content = Content(data={
                "user_input": user_input,
                "session_state": session_state_dict,
                "session_id": session_id
            })
            
            step_logger.log_llm_call("Qwen/Qwen3-32B", "processing")
            update_steps()
            
            result = await self.root_agent.execute(content)
            
            if result.data["success"]:
                response_type = result.data.get("type", "search_interaction")
                
                if response_type == "general_query":
                    step_logger.log_step("💬 Generating conversational response", "llm")
                    update_steps()
                    
                    ai_message = result.data.get("message", "I'm here to help!")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    step_logger.log_completion("Response ready")
                    update_steps()
                    
                else:
                    # Handle search interaction responses
                    step_logger.log_step("🔧 Processing search modifications", "tool")
                    update_steps()
                    
                    if "session_state" in result.data:
                        updated_state = result.data["session_state"]
                        if isinstance(updated_state, dict):
                            self._update_session_state_safely(updated_state)
                            step_logger.log_step("💾 Session state updated", "system")
                            update_steps()
                    
                    ai_message = result.data.get("message", "Request processed successfully.")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    # Handle search trigger
                    if result.data.get("trigger_search", False):
                        step_logger.log_step("🔍 Search triggered", "search")
                        update_steps()
                        await self._handle_triggered_search_simple(result.data, session_id)
                        # Update steps after search
                        update_steps()
                    
                    # Handle automatic search results
                    if "candidates" in result.data.get("session_state", {}):
                        step_logger.log_results(
                            len(result.data["session_state"]["candidates"]),
                            result.data["session_state"].get("total_results", 0)
                        )
                        update_steps()
                        success_msg = "🎯 Search completed!"
                        self.session_state['chat_history'].append({
                            "role": "assistant", 
                            "content": success_msg
                        })
                    
                    step_logger.log_completion("Processing complete")
                    update_steps()
                
                return True
                
            else:
                # Handle error
                step_logger.log_error(result.data.get("error", "Unknown error"))
                update_steps()
                error_message = result.data.get("error", "Sorry, I couldn't process that request.")
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": f"❌ {error_message}"
                })
                return False
            
        except Exception as e:
            step_logger.log_error(f"Chat processing failed: {str(e)}")
            step_placeholder.markdown(f"❌ **Error:** {str(e)}")
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            return False
    
    async def _handle_chat_message_simple(self, user_input: str, session_id: str) -> bool:
        """SIMPLIFIED: Handle chat message without complex threading."""
        try:
            # Log basic steps
            step_logger.log_step(f"🔍 Analyzing: \"{user_input[:40]}{'...' if len(user_input) > 40 else ''}\"", "routing")
            
            # Check for "show more candidates" command
            if self._is_show_more_command(user_input):
                step_logger.log_step("📋 Show more candidates detected", "decision")
                await self._handle_show_more_command()
                step_logger.log_completion("Additional candidates loaded")
                return True
            
            # Prepare session state
            session_state_dict = self._get_clean_session_state()
            step_logger.log_step("🔧 Preparing agent context", "system")
            
            # Determine routing
            if self._is_search_related(user_input):
                step_logger.log_routing_decision(user_input, "search_interaction", 0.9)
            else:
                step_logger.log_routing_decision(user_input, "general_query", 0.85)
            
            # Process through agent
            from ...agent import Content
            content = Content(data={
                "user_input": user_input,
                "session_state": session_state_dict,
                "session_id": session_id
            })
            
            step_logger.log_llm_call("Qwen/Qwen3-32B", "processing")
            result = await self.root_agent.execute(content)
            
            if result.data["success"]:
                response_type = result.data.get("type", "search_interaction")
                
                if response_type == "general_query":
                    ai_message = result.data.get("message", "I'm here to help!")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    step_logger.log_completion("Response ready")
                    
                else:
                    # Handle search interaction responses
                    if "session_state" in result.data:
                        updated_state = result.data["session_state"]
                        if isinstance(updated_state, dict):
                            self._update_session_state_safely(updated_state)
                    
                    ai_message = result.data.get("message", "Request processed successfully.")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    # Handle search trigger
                    if result.data.get("trigger_search", False):
                        await self._handle_triggered_search_simple(result.data, session_id)
                    
                    # Handle automatic search results
                    if "candidates" in result.data.get("session_state", {}):
                        step_logger.log_results(
                            len(result.data["session_state"]["candidates"]),
                            result.data["session_state"].get("total_results", 0)
                        )
                        success_msg = "🎯 Search completed!"
                        self.session_state['chat_history'].append({
                            "role": "assistant", 
                            "content": success_msg
                        })
                    
                    step_logger.log_completion("Processing complete")
                
                return True
                
            else:
                # Handle error
                step_logger.log_error(result.data.get("error", "Unknown error"))
                error_message = result.data.get("error", "Sorry, I couldn't process that request.")
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": f"❌ {error_message}"
                })
                return False
            
        except Exception as e:
            step_logger.log_error(f"Chat processing failed: {str(e)}")
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            return False
    
    def _render_quick_actions(self):
        """Render quick action buttons - ENHANCED to show real steps."""
        st.markdown("**Quick Actions:**")
        
        if st.button("📊 Analyze Results", help="Get insights about current search results"):
            session_id = str(uuid.uuid4())
            self._process_message_with_simple_steps("analyze the current search results", session_id)
        
        if st.button("🔧 Sort by Experience", help="Sort candidates by experience level"):
            session_id = str(uuid.uuid4())
            self._process_message_with_simple_steps("sort candidates by experience", session_id)
        
        if st.button("💰 Sort by Salary", help="Sort candidates by salary expectations"):
            session_id = str(uuid.uuid4())
            self._process_message_with_simple_steps("sort candidates by salary", session_id)
        
        if st.button("📍 Filter by Location", help="Help with location-based filtering"):
            session_id = str(uuid.uuid4())
            self._process_message_with_simple_steps("help me filter by location", session_id)
    
    def _is_search_related(self, user_input: str) -> bool:
        """Determine if input is search-related."""
        search_keywords = [
            "search", "find", "add", "remove", "filter", "set", "modify", 
            "candidates", "python", "java", "javascript", "skill", "experience",
            "salary", "location", "bangalore", "mumbai", "delhi"
        ]
        return any(keyword in user_input.lower() for keyword in search_keywords)
    
    async def _handle_triggered_search_simple(self, result_data: Dict[str, Any], session_id: str):
        """SIMPLIFIED: Handle search triggered by AI agent."""
        try:
            step_logger.log_step("⚙️ Preparing search", "search")
            
            updated_state = result_data.get("session_state", self.session_state)
            if not isinstance(updated_state, dict):
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
            
            step_logger.log_search_execution(search_filters)
            
            # Execute search
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters,
                "session_id": session_id
            })
            
            step_logger.log_step("📡 Calling ResDex API", "search")
            search_result = await self.root_agent.execute(search_content)
            
            if search_result.data["success"]:
                candidates = search_result.data["candidates"]
                total_count = search_result.data["total_count"]
                step_logger.log_results(len(candidates), total_count)
                
                # Update session state
                self.session_state['candidates'] = candidates
                self.session_state['total_results'] = total_count
                self.session_state['search_applied'] = True
                self.session_state['page'] = 0
                
                # Add success message
                success_msg = f"🔄 {search_result.data['message']}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": success_msg
                })
                
                step_logger.log_completion("Search completed")
            else:
                error_msg = search_result.data.get('error', 'Unknown error')
                step_logger.log_error(f"Search failed: {error_msg}")
                
                error_response = f"❌ Search failed: {error_msg}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": error_response
                })
                
        except Exception as e:
            step_logger.log_error(f"Search execution failed: {str(e)}")
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })

    def _is_show_more_command(self, user_input: str) -> bool:
        """Check if user is asking to show more candidates."""
        show_more_phrases = [
            "show more candidates", "show more", "display more candidates", 
            "more candidates", "load more", "see more candidates",
            "show additional", "display additional", "next batch"
        ]
        
        user_lower = user_input.lower().strip()
        return any(phrase in user_lower for phrase in show_more_phrases)

    async def _handle_show_more_command(self):
        """Handle show more candidates command."""
        try:
            all_candidates = self.session_state.get('all_candidates', [])
            current_display_size = self.session_state.get('display_batch_size', 20)
            
            new_display_size = current_display_size + 20
            
            if new_display_size <= len(all_candidates):
                self.session_state['displayed_candidates'] = all_candidates[:new_display_size]
                self.session_state['candidates'] = all_candidates[:new_display_size]
                self.session_state['display_batch_size'] = new_display_size
                self.session_state['page'] = 0
                
                total_results = self.session_state.get('total_results', 0)
                ai_response = f"✅ Showing more candidates! You now have access to additional profiles from {total_results:,} total matches."
                
            else:
                await self._fetch_more_candidates_from_api()
                return
            
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": ai_response
            })
            
        except Exception as e:
            error_msg = f"❌ Error showing more candidates: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })

    async def _fetch_more_candidates_from_api(self):
        """Fetch additional candidates from API."""
        try:
            search_filters = {
                'keywords': self.session_state.get('keywords', []),
                'min_exp': self.session_state.get('min_exp', 0),
                'max_exp': self.session_state.get('max_exp', 10),
                'min_salary': self.session_state.get('min_salary', 0),
                'max_salary': self.session_state.get('max_salary', 15),
                'current_cities': self.session_state.get('current_cities', []),
                'preferred_cities': self.session_state.get('preferred_cities', []),
                'recruiter_company': self.session_state.get('recruiter_company', ''),
                'max_candidates': 100
            }
            
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters
            })
            
            result = await self.root_agent.execute(search_content)
            
            if result.data["success"] and result.data["candidates"]:
                new_candidates = result.data["candidates"]
                all_candidates = self.session_state.get('all_candidates', [])
                
                updated_all_candidates = all_candidates + new_candidates
                self.session_state['all_candidates'] = updated_all_candidates
                
                current_display_size = self.session_state.get('display_batch_size', 20)
                new_display_size = current_display_size + 20
                
                self.session_state['displayed_candidates'] = updated_all_candidates[:new_display_size]
                self.session_state['candidates'] = updated_all_candidates[:new_display_size]
                self.session_state['display_batch_size'] = new_display_size
                self.session_state['page'] = 0
                
                total_results = self.session_state.get('total_results', 0)
                ai_response = f"✅ Fetched additional candidates from the database! You now have access to more profiles from {total_results:,} total matches."
                
            else:
                total_results = self.session_state.get('total_results', 0)
                ai_response = f"ℹ️ No additional candidates available at this time from {total_results:,} total matches."
            
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": ai_response
            })
            
        except Exception as e:
            error_msg = f"❌ Error fetching more candidates: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
    
    def _get_clean_session_state(self) -> Dict[str, Any]:
        """Get session state without Streamlit's internal keys."""
        streamlit_keys_to_exclude = [
            'FormSubmitter:chat_input_form-Send 💬',
            'FormSubmitter:keyword_form-Add Keyword',
            'FormSubmitter:location_form-Add Location',
        ]
        
        def should_exclude_key(key: str) -> bool:
            if key.startswith('FormSubmitter:'):
                return True
            if any(pattern in key for pattern in ['call_', 'phone_', 'email_', 'remove_']):
                return True
            return False
        
        clean_state = {}
        for key, value in self.session_state.items():
            if not should_exclude_key(key):
                try:
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        clean_state[key] = value
                    else:
                        clean_state[key] = str(value)
                except Exception as e:
                    print(f"⚠️ Skipping session state key {key}: {e}")
                    continue
        
        return clean_state
    
    def _update_session_state_safely(self, updated_state: Dict[str, Any]):
        """Update session state safely."""
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
                except Exception as e:
                    print(f"⚠️ Failed to update session state key {key}: {e}")