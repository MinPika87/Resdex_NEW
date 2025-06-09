"""
Chat interface component - FIXED to show LIVE streaming steps
"""

import streamlit as st
import asyncio
import time
import uuid
from typing import Dict, Any, Optional

# Step logging imports
from ...utils.step_logger import step_logger
from .step_display import StepDisplay, poll_and_update_steps


class ChatInterface:
    """Chat interface component with FIXED LIVE step streaming."""
    
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
        
        # Chat input - FIXED for live step streaming
        self._render_chat_input_with_live_steps()
        
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
    
    def _render_chat_input_with_live_steps(self):
        """FIXED: Render chat input with LIVE step streaming."""
        with st.form(key="chat_input_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant",
                placeholder="e.g., 'add python as mandatory', 'search with java', 'sort by experience'",
                help="Ask me to modify filters, search candidates, or analyze results"
            )
            
            chat_submitted = st.form_submit_button("Send 💬")
            
            if chat_submitted and user_input.strip():
                # FIXED: Process with LIVE step streaming
                session_id = str(uuid.uuid4())
                self._process_message_with_live_steps(user_input.strip(), session_id)
        
        # Clear chat button
        if st.button("Clear Chat 🗑️"):
            self.session_state['chat_history'] = []
            st.experimental_rerun()
    
    def _process_message_with_live_steps(self, user_input: str, session_id: str):
        """FIXED: Process message with LIVE step streaming display that STAYS visible."""
        try:
            # Create step display container that will STAY visible
            st.markdown("---")
            st.markdown("### 🔄 AI Processing (Live)")
            step_container = st.empty()
            
            # Initialize step logging
            step_logger.start_session(session_id)
            
            # Add user message to history
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Process the message with LIVE step updates
            success = asyncio.run(self._handle_chat_message_with_step_streaming(
                user_input, session_id, step_container
            ))
            
            final_steps = step_logger.get_steps(session_id)
            if final_steps:
                # Use clean Streamlit layout with proper boundaries
                with step_container.container():
                    # Status header
                    if success:
                        st.success("✅ AI Processing Complete")
                    else:
                        st.error("❌ AI Processing Failed")
                    
                    # Header with step count
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("**🔄 AI Processing Steps**")
                    with col2:
                        st.markdown('<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">DONE</span>', unsafe_allow_html=True)
                    
                    for step in final_steps:
                        icon = self.step_display.step_icons.get(step["type"], "💡")
                        
                        step_col1, step_col2, step_col3 = st.columns([0.5, 6, 1.5])
                        
                        with step_col1:
                            st.markdown(f"<div style='text-align: center; font-size: 14px;'>{icon}</div>", unsafe_allow_html=True)
                        
                        with step_col2:
                            message = step['message']
                            if len(message) > 45:
                                message = message[:42] + "..."
                            st.markdown(f"<div style='padding-top: 2px; color: #666; font-size: 12px; word-wrap: break-word;'>{message}</div>", unsafe_allow_html=True)
                        
                        with step_col3:
                            # Show clean timestamp in HH:MM:SS format
                            timestamp = step['timestamp']
                            st.markdown(f"<div style='text-align: right; font-size: 9px; color: #999; padding-top: 4px; font-family: monospace;'>{timestamp}</div>", unsafe_allow_html=True)
                    
                    # Summary
                    st.caption(f"📊 {len(final_steps)} processing steps")
            
            st.experimental_rerun()
                
        except Exception as e:
            step_logger.log_error(f"Chat processing failed: {str(e)}")
            st.error(f"❌ An error occurred: {str(e)}")
    
    async def _handle_chat_message_with_step_streaming(self, user_input: str, session_id: str, step_container) -> bool:
        """FIXED: Handle chat message with ALL steps accumulating in real-time."""
        try:
            def update_all_steps():
                """Update steps display with ALL accumulated steps using clean formatting"""
                current_steps = step_logger.get_steps(session_id)
                if current_steps:
                    # Use Streamlit components with better formatting
                    with step_container.container():
                        # Header with live badge
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("**🔄 AI Processing Steps**")
                        with col2:
                            st.markdown('<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">LIVE</span>', unsafe_allow_html=True)
                        
                        # Show steps with clean formatting and proper boundaries
                        for step in current_steps[-15:]:  # Show last 15 steps
                            icon = self.step_display.step_icons.get(step["type"], "💡")
                            
                            # Adjusted columns: smaller icon, larger message area, smaller timestamp
                            step_col1, step_col2, step_col3 = st.columns([0.5, 6, 1.5])
                            
                            with step_col1:
                                st.markdown(f"<div style='text-align: center; font-size: 14px;'>{icon}</div>", unsafe_allow_html=True)
                            
                            with step_col2:
                                # Add word wrap and limit text length
                                message = step['message']
                                if len(message) > 45:
                                    message = message[:42] + "..."
                                st.markdown(f"<div style='padding-top: 2px; font-size: 12px; word-wrap: break-word;'>{message}</div>", unsafe_allow_html=True)
                            
                            with step_col3:
                                # Show clean timestamp in HH:MM:SS format
                                timestamp = step['timestamp']
                                st.markdown(f"<div style='text-align: right; font-size: 9px; color: #999; padding-top: 4px; font-family: monospace;'>{timestamp}</div>", unsafe_allow_html=True)
            
            # Log initial step and update display
            step_logger.log_step(f"🔍 Analyzing: \"{user_input[:40]}{'...' if len(user_input) > 40 else ''}\"", "routing")
            update_all_steps()
            await asyncio.sleep(0.3)  # Longer delay to see step accumulation
            
            # Check for "show more candidates" command
            if self._is_show_more_command(user_input):
                step_logger.log_step("📋 Show more candidates detected", "decision")
                update_all_steps()
                await asyncio.sleep(0.3)
                
                step_logger.log_tool_activation("Candidate Manager", "expanding results")
                update_all_steps()
                await asyncio.sleep(0.3)
                
                await self._handle_show_more_command()
                
                step_logger.log_completion("Additional candidates loaded")
                update_all_steps()
                return True
            
            # Prepare session state
            session_state_dict = self._get_clean_session_state()
            step_logger.log_step("🔧 Preparing agent context", "system")
            update_all_steps()
            await asyncio.sleep(0.3)
            
            # Determine routing with visual feedback
            if self._is_search_related(user_input):
                step_logger.log_routing_decision(user_input, "search_interaction", 0.9)
                update_all_steps()
                await asyncio.sleep(0.3)
                
                step_logger.log_tool_activation("Search Interaction Agent")
                update_all_steps()
                await asyncio.sleep(0.3)
            else:
                step_logger.log_routing_decision(user_input, "general_query", 0.85)
                update_all_steps()
                await asyncio.sleep(0.3)
                
                step_logger.log_tool_activation("General LLM Responder")
                update_all_steps()
                await asyncio.sleep(0.3)
            
            # Process through agent
            from ...agent import Content
            content = Content(data={
                "user_input": user_input,
                "session_state": session_state_dict,
                "session_id": session_id
            })
            
            step_logger.log_llm_call("Qwen/Qwen3-32B", "processing")
            update_all_steps()
            await asyncio.sleep(0.3)
            
            # Execute the agent request and capture steps with error handling
            try:
                # Execute the agent request
                result = await self.root_agent.execute(content)
                
                # If there was a task breakdown error, log recovery step
                current_steps = step_logger.get_steps(session_id)
                if current_steps and any("Task breakdown failed" in step.get('message', '') for step in current_steps):
                    step_logger.log_step("🔄 Using fallback search processing", "tool")
                    update_all_steps()
                    await asyncio.sleep(2.0)
                
                # After execution, update display with ALL steps that were logged
                update_all_steps()
                await asyncio.sleep(0.5)
            except Exception as e:
                # Even on error, show what steps we captured
                step_logger.log_error(f"Agent execution failed: {str(e)}")
                update_all_steps()
                raise e
            
            # Process the result and update steps throughout with longer delays for post-LLM steps
            if result.data["success"]:
                response_type = result.data.get("type", "search_interaction")
                
                if response_type == "general_query":
                    step_logger.log_step("💬 Generating conversational response", "llm")
                    update_all_steps()
                    await asyncio.sleep(0.5)  # 5 second delay for post-LLM visibility
                    
                    ai_message = result.data.get("message", "I'm here to help!")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    step_logger.log_completion("Response ready")
                    update_all_steps()
                    await asyncio.sleep(0.5)  # 5 second delay for final step
                    
                else:
                    # Handle search interaction responses
                    step_logger.log_step("🔧 Processing search modifications", "tool")
                    update_all_steps()
                    await asyncio.sleep(0.5)  # 5 second delay
                    
                    if "session_state" in result.data:
                        updated_state = result.data["session_state"]
                        if isinstance(updated_state, dict):
                            self._update_session_state_safely(updated_state)
                            step_logger.log_step("💾 Session state updated", "system")
                            update_all_steps()
                            await asyncio.sleep(0.5)  # 5 second delay
                    
                    ai_message = result.data.get("message", "Request processed successfully.")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    
                    # Handle search trigger
                    if result.data.get("trigger_search", False):
                        step_logger.log_step("🔍 Search triggered", "search")
                        update_all_steps()
                        await asyncio.sleep(0.5)  # 5 second delay
                        
                        await self._handle_triggered_search_with_steps(result.data, session_id, update_all_steps)
                    
                    # Handle automatic search results
                    if "candidates" in result.data.get("session_state", {}):
                        step_logger.log_results(
                            len(result.data["session_state"]["candidates"]),
                            result.data["session_state"].get("total_results", 0)
                        )
                        update_all_steps()
                        await asyncio.sleep(0.5)  # 5 second delay
                        
                        success_msg = "🎯 Search completed!"
                        self.session_state['chat_history'].append({
                            "role": "assistant", 
                            "content": success_msg
                        })
                    
                    step_logger.log_completion("Processing complete")
                    update_all_steps()
                    await asyncio.sleep(5.0)  # 5 second delay for final step
                
                return True
                
            else:
                # Handle error
                step_logger.log_error(result.data.get("error", "Unknown error"))
                update_all_steps()
                await asyncio.sleep(5.0)  # 5 second delay for error visibility
                
                error_message = result.data.get("error", "Sorry, I couldn't process that request.")
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": f"❌ {error_message}"
                })
                return False
            
        except Exception as e:
            step_logger.log_error(f"Chat processing failed: {str(e)}")
            step_container.error(f"❌ **Error:** {str(e)}")
            
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            return False
    
    async def _handle_triggered_search_with_steps(self, result_data: Dict[str, Any], session_id: str, update_callback):
        """Handle search triggered by AI agent with live step updates."""
        try:
            step_logger.log_step("⚙️ Preparing search execution", "search")
            update_callback()
            await asyncio.sleep(0.1)
            
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
            update_callback()
            await asyncio.sleep(0.1)
            
            # Execute search
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters,
                "session_id": session_id
            })
            
            step_logger.log_step("📡 Calling ResDex API", "search")
            update_callback()
            await asyncio.sleep(0.1)
            
            search_result = await self.root_agent.execute(search_content)
            
            if search_result.data["success"]:
                candidates = search_result.data["candidates"]
                total_count = search_result.data["total_count"]
                
                step_logger.log_results(len(candidates), total_count)
                update_callback()
                await asyncio.sleep(0.1)
                
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
                
                step_logger.log_completion("Search completed successfully")
                update_callback()
            else:
                error_msg = search_result.data.get('error', 'Unknown error')
                step_logger.log_error(f"Search failed: {error_msg}")
                update_callback()
                
                error_response = f"❌ Search failed: {error_msg}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": error_response
                })
                
        except Exception as e:
            step_logger.log_error(f"Search execution failed: {str(e)}")
            update_callback()
            
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
    
    def _render_quick_actions(self):
        """Render quick action buttons with live step streaming."""
        st.markdown("**Quick Actions:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Analyze Results", help="Get insights about current search results"):
                session_id = str(uuid.uuid4())
                self._process_message_with_live_steps("analyze the current search results", session_id)
            
            if st.button("🔧 Sort by Experience", help="Sort candidates by experience level"):
                session_id = str(uuid.uuid4())
                self._process_message_with_live_steps("sort candidates by experience", session_id)
        
        with col2:
            if st.button("💰 Sort by Salary", help="Sort candidates by salary expectations"):
                session_id = str(uuid.uuid4())
                self._process_message_with_live_steps("sort candidates by salary", session_id)
            
            if st.button("📍 Filter by Location", help="Help with location-based filtering"):
                session_id = str(uuid.uuid4())
                self._process_message_with_live_steps("help me filter by location", session_id)
    
    def _is_search_related(self, user_input: str) -> bool:
        """Determine if input is search-related."""
        search_keywords = [
            "search", "find", "add", "remove", "filter", "set", "modify", 
            "candidates", "python", "java", "javascript", "skill", "experience",
            "salary", "location", "bangalore", "mumbai", "delhi"
        ]
        return any(keyword in user_input.lower() for keyword in search_keywords)

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