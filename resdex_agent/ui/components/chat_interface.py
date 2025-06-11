# resdex_agent/ui/components/chat_interface.py - ENHANCED with Memory Integration
"""
Chat interface component with Memory Integration and LIVE step streaming
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
    """Chat interface component with Memory Integration and LIVE step streaming."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
        self.step_display = StepDisplay()
        
        # NEW: Memory integration
        self.memory_service = getattr(root_agent, 'memory_service', None)
        self.session_manager = getattr(root_agent, 'session_manager', None)
        
        # Generate or get user ID for memory
        if 'user_id' not in self.session_state:
            self.session_state['user_id'] = f"user_{uuid.uuid4().hex[:8]}"
        
        # Track current conversation session for memory
        if 'conversation_session_id' not in self.session_state:
            self.session_state['conversation_session_id'] = str(uuid.uuid4())
        
        print(f"🧠 ChatInterface initialized with memory for user: {self.session_state['user_id']}")
    
    def render(self):
        """Render the complete chat interface with memory features."""
        st.markdown("### 🤖 AI Assistant with Memory")
        st.markdown("*Ask me to modify search filters, analyze results, or remember past conversations.*")
        
        # NEW: Memory status indicator
        self._render_memory_status()
        
        # Display chat history
        self._render_chat_history()
        
        # Chat input with memory
        self._render_chat_input_with_memory()
        
        # Enhanced quick action buttons with memory
        self._render_enhanced_quick_actions()
        
        # NEW: Memory management section
        self._render_memory_management()
    
    def _render_memory_status(self):
        """NEW: Render memory status indicator."""
        if self.memory_service:
            try:
                memory_stats = self.memory_service.get_memory_stats()
                total_entries = memory_stats.get("total_entries", 0)
                total_users = memory_stats.get("total_users", 0)
                
                with st.expander("🧠 Memory Status", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Memories", total_entries)
                    with col2:
                        st.metric("Total Users", total_users)
                    with col3:
                        st.metric("Current User", self.session_state['user_id'][:8] + "...")
                    
                    if st.button("🔍 Search My Memory"):
                        self._show_memory_search_interface()
            except Exception as e:
                st.warning(f"Memory status unavailable: {e}")
        else:
            st.warning("🧠 Memory service not available")
    
    def _show_memory_search_interface(self):
        """NEW: Show memory search interface."""
        st.markdown("#### 🔍 Search Your Conversation Memory")
        
        search_query = st.text_input(
            "Search your past conversations:",
            placeholder="e.g., 'python searches', 'bangalore candidates', 'machine learning'"
        )
        
        if st.button("Search Memory") and search_query:
            asyncio.run(self._perform_memory_search(search_query))
    
    async def _perform_memory_search(self, query: str):
        """NEW: Perform memory search and display results."""
        try:
            if not self.memory_service:
                st.error("Memory service not available")
                return
            
            # Use memory tool to search
            memory_tool = self.root_agent.tools.get("memory_tool")
            if memory_tool:
                with st.spinner("🔍 Searching memory..."):
                    result = await memory_tool(
                        user_id=self.session_state['user_id'],
                        query=query,
                        max_results=10
                    )
                
                if result["success"] and result["results"]:
                    st.success(f"📚 Found {len(result['results'])} relevant memories:")
                    
                    for i, memory in enumerate(result["results"][:5], 1):
                        with st.container():
                            content = memory.get("content", "")
                            timestamp = memory.get("timestamp", "")
                            session_id = memory.get("session_id", "")
                            
                            st.markdown(f"""
                            **{i}.** {content[:150]}{'...' if len(content) > 150 else ''}
                            
                            *Session: {session_id[:8]}... • Time: {timestamp}*
                            """)
                            st.markdown("---")
                else:
                    st.info(f"No memories found for '{query}'. Try different keywords.")
            else:
                st.error("Memory tool not available")
                
        except Exception as e:
            st.error(f"Memory search failed: {e}")
    
    def _render_chat_history(self):
        """Render chat message history with memory context."""
        chat_history = self.session_state.get('chat_history', [])
        
        with st.container():
            st.markdown("**Chat History:**")
            
            if not chat_history:
                if self.memory_service:
                    st.info("👋 Start a conversation! I can remember our discussions and help with search insights. Try asking 'add python skill' or 'what did we discuss about java before?'")
                else:
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
    
    def _render_chat_input_with_memory(self):
        """Render chat input with memory integration."""
        with st.form(key="chat_input_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant (with Memory)",
                placeholder="e.g., 'add python as mandatory', 'what did we discuss about React?', 'remember my last search'",
                help="Ask me to modify filters, search candidates, analyze results, or recall past conversations"
            )
            
            chat_submitted = st.form_submit_button("Send 💬")
            
            if chat_submitted and user_input.strip():
                # Process with memory integration
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps(user_input.strip(), session_id)
        
        # Clear chat button with memory save option
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat 🗑️"):
                # Save current conversation to memory before clearing
                if self.session_manager and len(self.session_state.get('chat_history', [])) > 0:
                    asyncio.run(self._save_conversation_to_memory())
                self.session_state['chat_history'] = []
                self.session_state['conversation_session_id'] = str(uuid.uuid4())  # New conversation session
                st.experimental_rerun()
        
        with col2:
            if st.button("💾 Save to Memory") and self.session_manager:
                asyncio.run(self._save_conversation_to_memory())
                st.success("Conversation saved to memory!")
                time.sleep(1)
                st.experimental_rerun()
    
    async def _save_conversation_to_memory(self):
        """NEW: Save current conversation to long-term memory."""
        try:
            if not self.session_manager:
                return
            
            user_id = self.session_state['user_id']
            conversation_session_id = self.session_state['conversation_session_id']
            
            # Add all chat history to the session
            chat_history = self.session_state.get('chat_history', [])
            for message in chat_history:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=conversation_session_id,
                    interaction_type="chat_message",
                    content=message
                )
            
            # Save the session to memory
            await self.root_agent.save_session_to_memory(user_id, conversation_session_id)
            
            print(f"🧠 Saved conversation to memory: {len(chat_history)} messages")
            
        except Exception as e:
            print(f"❌ Failed to save conversation to memory: {e}")
    
    def _process_message_with_memory_and_steps(self, user_input: str, session_id: str):
        """Process message with memory integration and live step streaming."""
        try:
            # Create step display container
            st.markdown("---")
            st.markdown("### 🔄 AI Processing (Live with Memory)")
            step_container = st.empty()
            
            # Initialize step logging
            step_logger.start_session(session_id)
            
            # Add user message to history
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Process the message with memory integration
            success = asyncio.run(self._handle_chat_message_with_memory_and_steps(
                user_input, session_id, step_container
            ))
            
            # Keep the step display visible with final status
            final_steps = step_logger.get_steps(session_id)
            if final_steps:
                with step_container.container():
                    if success:
                        st.success("✅ AI Processing Complete (Memory Enhanced)")
                    else:
                        st.error("❌ AI Processing Failed")
                    
                    # Memory-aware step display
                    self._render_memory_enhanced_steps(final_steps)
            
            # Trigger rerun to show new messages
            st.experimental_rerun()
                
        except Exception as e:
            step_logger.log_error(f"Memory-enhanced chat processing failed: {str(e)}")
            st.error(f"❌ An error occurred: {str(e)}")
    
    def _render_memory_enhanced_steps(self, steps):
        """NEW: Render steps with memory enhancement indicators."""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**🔄 AI Processing Steps (Memory Enhanced)**")
        with col2:
            st.markdown('<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">DONE</span>', unsafe_allow_html=True)
        
        for step in steps:
            icon = self.step_display.step_icons.get(step["type"], "💡")
            
            # Add memory indicator for memory-related steps
            message = step['message']
            if any(keyword in message.lower() for keyword in ['memory', 'conversation', 'remember', 'recall']):
                icon = "🧠"
            
            step_col1, step_col2, step_col3 = st.columns([0.5, 6, 1.5])
            
            with step_col1:
                st.markdown(f"<div style='text-align: center; font-size: 14px;'>{icon}</div>", unsafe_allow_html=True)
            
            with step_col2:
                display_message = message
                if len(display_message) > 45:
                    display_message = display_message[:42] + "..."
                st.markdown(f"<div style='padding-top: 2px; color: #666; font-size: 12px; word-wrap: break-word;'>{display_message}</div>", unsafe_allow_html=True)
            
            with step_col3:
                timestamp = step['timestamp']
                st.markdown(f"<div style='text-align: right; font-size: 9px; color: #999; padding-top: 4px; font-family: monospace;'>{timestamp}</div>", unsafe_allow_html=True)
        
        st.caption(f"📊 {len(steps)} processing steps • 🧠 Memory integrated")
    
    async def _handle_chat_message_with_memory_and_steps(self, user_input: str, session_id: str, step_container) -> bool:
        """Handle chat message with memory integration and step streaming."""
        try:
            user_id = self.session_state['user_id']
            conversation_session_id = self.session_state['conversation_session_id']
            
            # Function to update steps display
            def update_all_steps():
                current_steps = step_logger.get_steps(session_id)
                if current_steps:
                    with step_container.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("**🔄 AI Processing Steps (Memory Enhanced)**")
                        with col2:
                            st.markdown('<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">LIVE</span>', unsafe_allow_html=True)
                        
                        for step in current_steps[-15:]:
                            icon = self.step_display.step_icons.get(step["type"], "💡")
                            
                            # Add memory indicator
                            message = step['message']
                            if any(keyword in message.lower() for keyword in ['memory', 'conversation', 'remember', 'recall']):
                                icon = "🧠"
                            
                            step_col1, step_col2, step_col3 = st.columns([0.5, 6, 1.5])
                            
                            with step_col1:
                                st.markdown(f"<div style='text-align: center; font-size: 14px;'>{icon}</div>", unsafe_allow_html=True)
                            
                            with step_col2:
                                display_message = message
                                if len(display_message) > 45:
                                    display_message = display_message[:42] + "..."
                                st.markdown(f"<div style='padding-top: 2px; font-size: 12px; word-wrap: break-word;'>{display_message}</div>", unsafe_allow_html=True)
                            
                            with step_col3:
                                timestamp = step['timestamp']
                                st.markdown(f"<div style='text-align: right; font-size: 9px; color: #999; padding-top: 4px; font-family: monospace;'>{timestamp}</div>", unsafe_allow_html=True)
            
            # Log initial step with memory awareness
            step_logger.log_step(f"🧠 Memory-enhanced analysis: \"{user_input[:40]}{'...' if len(user_input) > 40 else ''}\"", "routing")
            update_all_steps()
            await asyncio.sleep(0.3)
            
            # NEW: Add this interaction to conversation memory
            if self.session_manager:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=conversation_session_id,
                    interaction_type="user_input",
                    content={"message": user_input}
                )
                step_logger.log_step("💾 Added to conversation memory", "system")
                update_all_steps()
                await asyncio.sleep(0.3)
            
            # Check for memory-related commands
            if self._is_memory_command(user_input):
                step_logger.log_step("🧠 Memory command detected", "decision")
                update_all_steps()
                await asyncio.sleep(0.3)
                
                return await self._handle_memory_command(user_input, user_id, update_all_steps)
            
            # Check for "show more candidates" command
            if self._is_show_more_command(user_input):
                step_logger.log_step("📋 Show more candidates detected", "decision")
                update_all_steps()
                await asyncio.sleep(0.3)
                
                await self._handle_show_more_command()
                step_logger.log_completion("Additional candidates loaded")
                update_all_steps()
                return True
            
            # Prepare session state
            session_state_dict = self._get_clean_session_state()
            step_logger.log_step("🔧 Preparing agent context with memory", "system")
            update_all_steps()
            await asyncio.sleep(0.3)
            self.session_state['chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Process through agent with memory context
            from ...agent import Content
            content = Content(data={
                "user_input": user_input,
                "session_state": session_state_dict,
                "session_id": session_id,
                "user_id": user_id  # NEW: Include user_id for memory
            })
            
            step_logger.log_llm_call("Qwen/Qwen3-32B", "processing with memory")
            update_all_steps()
            await asyncio.sleep(0.3)
            
            # Execute the agent request
            result = await self.root_agent.execute(content)
            
            # Process the result with memory integration
            update_all_steps()
            await asyncio.sleep(0.5)
            
            if result.data["success"]:
                response_type = result.data.get("type", "search_interaction")
                if response_type == "general_query":
                    step_logger.log_step("💬 Memory-enhanced response generated", "llm")
                    update_all_steps()
                    await asyncio.sleep(0.5)
                    
                    ai_message = result.data.get("message", "I'm here to help!")
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": ai_message
                    })
                    await self.root_agent._handle_chat_message_complete(
                    user_input=user_input,
                    response=error_message,
                    user_id=user_id,
                    session_id=conversation_session_id
                )
                    step_logger.log_completion("Memory-enhanced response ready")
                    update_all_steps()
                    await asyncio.sleep(0.5)
                    
                else:
                    # Handle search interaction responses with memory
                    await self._handle_search_response_with_memory(
                        result, user_id, conversation_session_id, update_all_steps
                    )
                
                return True
                
            else:
                # Handle error with memory
                step_logger.log_error(result.data.get("error", "Unknown error"))
                update_all_steps()
                await asyncio.sleep(5.0)
                
                error_message = result.data.get("error", "Sorry, I couldn't process that request.")
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": f"❌ {error_message}"
                })
                
                
                return False
            
        except Exception as e:
            step_logger.log_error(f"Memory-enhanced chat processing failed: {str(e)}")
            step_container.error(f"❌ **Error:** {str(e)}")
            
            error_msg = f"❌ An error occurred: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            return False
    
    def _is_memory_command(self, user_input: str) -> bool:
        """NEW: Check if the input is a memory-related command."""
        memory_commands = [
            "remember", "recall", "what did we discuss", "previous conversation",
            "last time", "before", "earlier", "history", "past", "mentioned",
            "talked about", "said before", "previous search", "last search",
            "show my memory", "search memory", "conversation history"
        ]
        user_lower = user_input.lower()
        return any(cmd in user_lower for cmd in memory_commands)
    
    async def _handle_memory_command(self, user_input: str, user_id: str, update_callback) -> bool:
        """NEW: Handle memory-specific commands."""
        try:
            step_logger.log_step("🔍 Searching conversation memory", "search")
            update_callback()
            await asyncio.sleep(0.5)
            
            # Extract search query from the memory command
            search_query = self._extract_memory_search_query(user_input)
            
            # Search memory
            memory_tool = self.root_agent.tools.get("memory_tool")
            if memory_tool:
                memory_results = await memory_tool(
                    user_id=user_id,
                    query=search_query,
                    max_results=5
                )
                
                if memory_results["success"] and memory_results["results"]:
                    results = memory_results["results"]
                    step_logger.log_step(f"📚 Found {len(results)} relevant memories", "results")
                    update_callback()
                    await asyncio.sleep(0.5)
                    
                    # Format memory response
                    memory_response = self._format_memory_response_for_chat(results, search_query)
                    
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": memory_response
                    })
                    
                    step_logger.log_completion("Memory search completed")
                    update_callback()
                    
                    return True
                else:
                    step_logger.log_step("📭 No relevant memories found", "info")
                    update_callback()
                    
                    fallback_response = f"I don't have any previous conversations about '{search_query}'. This might be our first discussion on this topic!"
                    
                    self.session_state['chat_history'].append({
                        "role": "assistant",
                        "content": fallback_response
                    })
                    
                    return True
            else:
                step_logger.log_error("Memory tool not available")
                update_callback()
                return False
                
        except Exception as e:
            step_logger.log_error(f"Memory command failed: {str(e)}")
            update_callback()
            return False
    
    def _extract_memory_search_query(self, user_input: str) -> str:
        """Extract search query from memory command."""
        # Remove common memory command phrases
        memory_phrases = [
            "what did we discuss about", "do you remember", "recall",
            "what did we talk about", "previous conversation about",
            "last time we talked about", "show my memory about"
        ]
        
        query = user_input.lower()
        for phrase in memory_phrases:
            if phrase in query:
                parts = query.split(phrase, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                break
        
        # Clean up the query
        query = query.replace("?", "").strip()
        return query if query else user_input
    
    def _format_memory_response_for_chat(self, results, search_query: str) -> str:
        """Format memory results for chat display."""
        response_parts = [f"📚 **Found {len(results)} memories about '{search_query}':**\n"]
        
        for i, result in enumerate(results[:3], 1):
            content = result.get("content", "")
            timestamp = result.get("timestamp", "")
            
            # Shorten content for chat display
            if len(content) > 100:
                content = content[:97] + "..."
            
            response_parts.append(f"**{i}.** {content}")
            if timestamp:
                response_parts.append(f"   *{timestamp}*\n")
        
        if len(results) > 3:
            response_parts.append(f"*...and {len(results) - 3} more related memories.*")
        
        response_parts.append("\n💡 Would you like me to help you with something related to these past discussions?")
        
        return "\n".join(response_parts)
    
    async def _handle_search_response_with_memory(self, result, user_id: str, conversation_session_id: str, update_callback):
        """Handle search interaction responses with memory integration."""
        step_logger.log_step("🔧 Processing search modifications with memory", "tool")
        update_callback()
        await asyncio.sleep(0.5)
        
        if "session_state" in result.data:
            updated_state = result.data["session_state"]
            if isinstance(updated_state, dict):
                self._update_session_state_safely(updated_state)
                step_logger.log_step("💾 Session state updated", "system")
                update_callback()
                await asyncio.sleep(0.5)
        
        ai_message = result.data.get("message", "Request processed successfully.")
        self.session_state['chat_history'].append({
            "role": "assistant",
            "content": ai_message
        })
        
        # NEW: Add interaction result to conversation memory
        if self.session_manager:
            await self.session_manager.add_interaction(
                user_id=user_id,
                session_id=conversation_session_id,
                interaction_type="search_interaction_result",
                content={
                    "modifications": result.data.get("modifications", []),
                    "trigger_search": result.data.get("trigger_search", False),
                    "response": ai_message
                }
            )
        
        # Handle search trigger
        if result.data.get("trigger_search", False):
            step_logger.log_step("🔍 Search triggered with memory context", "search")
            update_callback()
            await asyncio.sleep(0.5)
            
            await self._handle_triggered_search_with_memory(result.data, user_id, conversation_session_id, update_callback)
        
        # Handle automatic search results
        if "candidates" in result.data.get("session_state", {}):
            step_logger.log_results(
                len(result.data["session_state"]["candidates"]),
                result.data["session_state"].get("total_results", 0)
            )
            update_callback()
            await asyncio.sleep(0.5)
            
            success_msg = "🎯 Search completed with memory context!"
            self.session_state['chat_history'].append({
                "role": "assistant", 
                "content": success_msg
            })
        
        step_logger.log_completion("Memory-enhanced processing complete")
        update_callback()
        await asyncio.sleep(5.0)
    
    async def _handle_triggered_search_with_memory(self, result_data: Dict[str, Any], user_id: str, conversation_session_id: str, update_callback):
        """Handle search triggered by AI agent with memory context."""
        try:
            step_logger.log_step("⚙️ Preparing memory-enhanced search execution", "search")
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
            
            # NEW: Add search context to memory
            if self.session_manager:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=conversation_session_id,
                    interaction_type="triggered_search",
                    content={"filters": search_filters}
                )
            
            step_logger.log_search_execution(search_filters)
            update_callback()
            await asyncio.sleep(0.1)
            
            # Execute search
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters,
                "user_id": user_id  # NEW: Include user_id
            })
            
            step_logger.log_step("📡 Calling ResDex API with memory context", "search")
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
                
                # NEW: Add search results to memory
                if self.session_manager:
                    await self.session_manager.add_interaction(
                        user_id=user_id,
                        session_id=conversation_session_id,
                        interaction_type="search_results",
                        content={
                            "candidates_found": len(candidates),
                            "total_count": total_count,
                            "filters_used": search_filters
                        }
                    )
                
                # Add success message
                success_msg = f"🔄 {search_result.data['message']} (Memory Enhanced)"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": success_msg
                })
                
                step_logger.log_completion("Memory-enhanced search completed successfully")
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
            step_logger.log_error(f"Memory-enhanced search execution failed: {str(e)}")
            update_callback()
            
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
    
    def _render_enhanced_quick_actions(self):
        """Render enhanced quick action buttons with memory features."""
        st.markdown("**Quick Actions (Memory Enhanced):**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Analyze Results", help="Get insights about current search results"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("analyze the current search results", session_id)
            
            if st.button("🔧 Sort by Experience", help="Sort candidates by experience level"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("sort candidates by experience", session_id)
            
            # NEW: Memory-specific quick actions
            if st.button("🧠 Recent Searches", help="Show recent search history"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("show me my recent searches", session_id)
        
        with col2:
            if st.button("💰 Sort by Salary", help="Sort candidates by salary expectations"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("sort candidates by salary", session_id)
            
            if st.button("📍 Filter by Location", help="Help with location-based filtering"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("help me filter by location", session_id)
            
            # NEW: Memory-specific quick actions
            if st.button("💭 Past Discussions", help="Search past conversations"):
                session_id = str(uuid.uuid4())
                self._process_message_with_memory_and_steps("what did we discuss about candidates before?", session_id)
    
    def _render_memory_management(self):
        """NEW: Render memory management section."""
        if not self.memory_service:
            return
        
        with st.expander("🧠 Memory Management", expanded=False):
            st.markdown("**Conversation Memory Controls**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📚 View All Memories"):
                    asyncio.run(self._show_all_user_memories())
            
            with col2:
                if st.button("🔍 Advanced Search"):
                    self._show_advanced_memory_search()
            
            with col3:
                if st.button("🗑️ Clear My Memory"):
                    self._show_clear_memory_confirmation()
    
    async def _show_all_user_memories(self):
        """NEW: Show all memories for the current user."""
        try:
            memory_tool = self.root_agent.tools.get("memory_tool")
            if memory_tool:
                # Search with a broad query to get all memories
                result = await memory_tool(
                    user_id=self.session_state['user_id'],
                    query="conversation search interaction general",
                    max_results=20
                )
                
                if result["success"] and result["results"]:
                    st.markdown(f"### 📚 Your Conversation Memory ({len(result['results'])} entries)")
                    
                    for i, memory in enumerate(result["results"], 1):
                        with st.container():
                            content = memory.get("content", "")
                            timestamp = memory.get("timestamp", "")
                            session_id = memory.get("session_id", "")
                            
                            st.markdown(f"""
                            **{i}.** {content}
                            
                            *Session: {session_id[:8]}... • {timestamp}*
                            """)
                            st.markdown("---")
                else:
                    st.info("No conversation memories found yet. Start chatting to build your memory!")
            else:
                st.error("Memory tool not available")
                
        except Exception as e:
            st.error(f"Failed to show memories: {e}")
    
    def _show_advanced_memory_search(self):
        """NEW: Show advanced memory search interface."""
        st.markdown("#### 🔍 Advanced Memory Search")
        
        search_type = st.selectbox(
            "Search Type:",
            ["General Search", "Search History", "Conversations", "Results & Analysis"]
        )
        
        search_query = st.text_input(
            "Search Query:",
            placeholder="Enter your search terms..."
        )
        
        max_results = st.slider("Max Results:", 1, 20, 10)
        
        if st.button("🔍 Advanced Search") and search_query:
            asyncio.run(self._perform_advanced_memory_search(search_type, search_query, max_results))
    
    async def _perform_advanced_memory_search(self, search_type: str, query: str, max_results: int):
        """NEW: Perform advanced memory search."""
        try:
            memory_tool = self.root_agent.tools.get("memory_tool")
            if not memory_tool:
                st.error("Memory tool not available")
                return
            
            # Enhance query based on search type
            if search_type == "Search History":
                enhanced_query = f"search candidate filter {query}"
            elif search_type == "Conversations":
                enhanced_query = f"conversation discussion talk {query}"
            elif search_type == "Results & Analysis":
                enhanced_query = f"results analysis found candidates {query}"
            else:
                enhanced_query = query
            
            with st.spinner(f"🔍 Searching {search_type.lower()}..."):
                result = await memory_tool(
                    user_id=self.session_state['user_id'],
                    query=enhanced_query,
                    max_results=max_results
                )
            
            if result["success"] and result["results"]:
                st.success(f"📚 Found {len(result['results'])} results for '{query}' in {search_type}")
                
                for i, memory in enumerate(result["results"], 1):
                    with st.container():
                        content = memory.get("content", "")
                        timestamp = memory.get("timestamp", "")
                        session_id = memory.get("session_id", "")
                        score = memory.get("score", 0.0)
                        
                        st.markdown(f"""
                        **{i}.** {content} (Relevance: {score:.2f})
                        
                        *Session: {session_id[:8]}... • {timestamp}*
                        """)
                        st.markdown("---")
            else:
                st.info(f"No results found for '{query}' in {search_type}")
                
        except Exception as e:
            st.error(f"Advanced search failed: {e}")
    
    def _show_clear_memory_confirmation(self):
        """NEW: Show memory clearing confirmation."""
        st.markdown("#### ⚠️ Clear Memory Confirmation")
        st.warning("This will permanently delete all your conversation memories. This action cannot be undone.")
        
        if st.button("🗑️ Yes, Clear All My Memories", type="secondary"):
            self._clear_user_memory()
    
    def _clear_user_memory(self):
        """NEW: Clear user memory."""
        try:
            if self.memory_service:
                self.memory_service.clear_user_memory(self.session_state['user_id'])
                st.success("🧹 All your conversation memories have been cleared.")
                
                # Also clear current chat history
                self.session_state['chat_history'] = []
                self.session_state['conversation_session_id'] = str(uuid.uuid4())
                
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Memory service not available")
                
        except Exception as e:
            st.error(f"Failed to clear memory: {e}")
    
    # Keep all existing methods unchanged but add memory context where appropriate
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
        """Handle show more candidates command with memory."""
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
                
                # NEW: Add to memory
                if self.session_manager:
                    await self.session_manager.add_interaction(
                        user_id=self.session_state['user_id'],
                        session_id=self.session_state['conversation_session_id'],
                        interaction_type="show_more_candidates",
                        content={"new_display_size": new_display_size, "total_available": len(all_candidates)}
                    )
                
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
        """Fetch additional candidates from API with memory logging."""
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
                "search_filters": search_filters,
                "user_id": self.session_state['user_id']  # NEW: Include user_id
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
                
                # NEW: Add to memory
                if self.session_manager:
                    await self.session_manager.add_interaction(
                        user_id=self.session_state['user_id'],
                        session_id=self.session_state['conversation_session_id'],
                        interaction_type="fetch_more_candidates",
                        content={"fetched_count": len(new_candidates), "total_now": len(updated_all_candidates)}
                    )
                
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