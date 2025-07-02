# resdex_agent/ui/components/chat_interface.py - ENHANCED with Memory Integration
"""
Chat interface component with Memory Integration and LIVE step streaming
"""

import streamlit as st #type: ignore
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List

# Step logging imports
from ...utils.step_logger import step_logger
from .step_display import StepDisplay, poll_and_update_steps
from .facet_display import FacetDisplay


class ChatInterface:
    """Chat interface component with Memory Integration and LIVE step streaming."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
        self.step_display = StepDisplay()
        
        # NEW: Memory integration
        self.memory_service = getattr(root_agent, 'memory_service', None)
        self.session_manager = getattr(root_agent, 'session_manager', None)
        
        # NEW: Initialize facet display
        from .facet_display import FacetDisplay
        self.facet_display = FacetDisplay(session_state, root_agent)
        
        # Generate or get user ID for memory
        if 'user_id' not in self.session_state:
            self.session_state['user_id'] = f"user_{uuid.uuid4().hex[:8]}"
        
        # Track current conversation session for memory
        if 'conversation_session_id' not in self.session_state:
            self.session_state['conversation_session_id'] = str(uuid.uuid4())
        
        print(f"🧠 ChatInterface initialized with memory for user: {self.session_state['user_id']}")
    def _render_relaxation_in_sidebar(self):
        """Render relaxation suggestions in sidebar if available."""
        if self.session_state.get('relaxation_available') and self.session_state.get('current_relaxation_data'):
            # Use the relaxation display component to render in sidebar
            from .relaxation_display import RelaxationDisplay
            relaxation_display = RelaxationDisplay(self.session_state, self.root_agent)
            relaxation_display.render_relaxation_in_sidebar(self.session_state['current_relaxation_data'])
    def render(self):
        """Render the complete chat interface with memory features."""
        st.markdown("### 🤖 AI Assistant with Memory")
        st.markdown("*Ask me to modify search filters, analyze results, or remember past conversations.*")
        
        # Memory status indicator
        self._render_memory_status()
        
        # Display chat history
        self._render_chat_history()
        
        # Chat input with memory
        self._render_chat_input_with_memory()
        
        # Memory management section
        self._render_memory_management()
        
        # NEW: Render facets if available (in sidebar)
        self._render_facets_in_sidebar()
        self._render_relaxation_in_sidebar()

    def _render_facets_in_sidebar(self):
        """Render facets in sidebar if available."""
        if self.session_state.get('facets_available') and self.session_state.get('current_facets'):
            # Use the facet display component to render in sidebar
            self.facet_display.render_facets_in_sidebar(self.session_state['current_facets'])

    
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
                    response=ai_message,
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
    
    async def _handle_search_response_with_memory(self, result, user_id: str, conversation_session_id: str, update_callback):
        """ENHANCED method with query relaxation support."""
        try:
            step_logger.log_step("🔧 Processing search modifications with memory", "tool")
            update_callback()
            await asyncio.sleep(0.5)
            
            # Update session state if provided
            if "session_state" in result.data:
                updated_state = result.data["session_state"]
                if isinstance(updated_state, dict):
                    self._update_session_state_safely(updated_state)
                    step_logger.log_step("💾 Session state updated", "system")
                    update_callback()
                    await asyncio.sleep(0.5)
            
            # Check response type to handle different agent responses
            response_type = result.data.get("type", "")
            refinement_type = result.data.get("refinement_type", "")
            
            # Handle refinement responses specially
            if response_type == "refinement_response":
                step_logger.log_step(f"🎯 Refinement response processed: {refinement_type}", "refinement")
                update_callback()
                
                # Handle facet generation
                if refinement_type == "facet_generation" and result.data.get("facets_data"):
                    # Store facets for sidebar display
                    facets_data = result.data["facets_data"]
                    self.session_state['current_facets'] = facets_data
                    self.session_state['facets_available'] = True
                    
                    # Create enhanced facet summary message
                    total_items = self._count_total_facet_items(facets_data)
                    facet_message = self._create_enhanced_facet_summary_for_chat(facets_data, total_items)
                    
                    # Check for duplicates and add message
                    if not self._is_duplicate_chat_message(facet_message):
                        self.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": facet_message
                        })
                    
                    step_logger.log_completion("Enhanced facets ready for sidebar display")
                    update_callback()
                
                # NEW: Handle query relaxation
                elif refinement_type == "query_relaxation":
                    relaxation_data = result.data
                    
                    # Store relaxation data for sidebar and future use
                    self.session_state['current_relaxation_data'] = relaxation_data
                    self.session_state['relaxation_available'] = True
                    
                    # Create enhanced relaxation summary message
                    relaxation_message = self._create_enhanced_relaxation_summary_for_chat(relaxation_data)
                    
                    # Check for duplicates and add message
                    if not self._is_duplicate_chat_message(relaxation_message):
                        self.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": relaxation_message
                        })
                    
                    step_logger.log_completion("Query relaxation suggestions ready")
                    update_callback()
                
                # Don't process further for refinement responses
                return
            
            # Regular message handling for non-refinement responses
            ai_message = result.data.get("message", "Request processed successfully.")
            if not self._is_duplicate_chat_message(ai_message):
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": ai_message
                })
            
            # Add interaction result to conversation memory
            if self.session_manager:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=conversation_session_id,
                    interaction_type="search_interaction_result",
                    content={
                        "modifications": result.data.get("modifications", []),
                        "trigger_search": result.data.get("trigger_search", False),
                        "response": ai_message,
                        "success": result.data.get("success", True),
                        "response_type": response_type,
                        "refinement_type": refinement_type
                    }
                )
            
            # Handle search triggering
            if result.data.get("trigger_search", False):
                step_logger.log_step("🚀 Search triggered by agent", "search")
                update_callback()
                await asyncio.sleep(0.5)
                
                await self._handle_triggered_search_with_memory(
                    result.data, user_id, conversation_session_id, update_callback
                )
            else:
                step_logger.log_completion("Request processed without search trigger")
                update_callback()
                
        except Exception as e:
            step_logger.log_error(f"Search response handling failed: {str(e)}")
            update_callback()
            
            error_msg = f"❌ Error processing request: {str(e)}"
            if not self._is_duplicate_chat_message(error_msg):
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": error_msg
                })
            
            print(f"❌ _handle_search_response_with_memory failed: {e}")
            import traceback
            traceback.print_exc()
    def _is_duplicate_chat_message(self, new_message: str) -> bool:
        """Check if the new message is a duplicate of the last chat message."""
        chat_history = self.session_state.get('chat_history', [])
        if not chat_history:
            return False
        
        last_message = chat_history[-1].get('content', '')
        
        # Simple duplicate check - could be enhanced with fuzzy matching
        return new_message.strip() == last_message.strip()
    def _create_enhanced_facet_summary_for_chat(self, facets_data: Dict[str, Any], total_items: int) -> str:
        """Create enhanced facet summary for chat (existing method with improvements)."""
        # This method already exists - enhance it to be consistent with relaxation messaging
        try:
            if not facets_data:
                return "No facet categories could be generated for your current search criteria."
            
            # Count categories
            primary_categories = len(facets_data.get("result_1", {}))
            secondary_categories = len(facets_data.get("result_2", {}))
            total_categories = primary_categories + secondary_categories
            
            if total_categories > 0:
                # Get sample category names
                sample_categories = []
                if facets_data.get("result_1"):
                    sample_categories.extend(list(facets_data["result_1"].keys())[:2])
                if facets_data.get("result_2") and len(sample_categories) < 3:
                    remaining_slots = 3 - len(sample_categories)
                    sample_categories.extend(list(facets_data["result_2"].keys())[:remaining_slots])
                
                categories_text = f'"{sample_categories[0]}"' if sample_categories else "various categories"
                if len(sample_categories) > 1:
                    categories_text += f', "{sample_categories[1]}"'
                if len(sample_categories) > 2:
                    categories_text += f', and "{sample_categories[2]}"'
                if total_categories > len(sample_categories):
                    remaining = total_categories - len(sample_categories)
                    categories_text += f" (+ {remaining} more)"
                
                breakdown_text = f"{primary_categories} primary and {secondary_categories} additional categories" if primary_categories > 0 and secondary_categories > 0 else f"{total_categories} categories"
                items_text = f"{total_items:,} items" if total_items > 0 else "multiple items"
                
                enhanced_message = f"""I analyzed your search results and generated comprehensive facets:

    🔍 **Facet Generation Complete**

    📊 **Generated {total_categories} facet categories** ({breakdown_text}) with {items_text} across all categories

    🎯 **Categories include:** {categories_text}

    💡 **Use these insights** to:
    • Explore different aspects of your candidate pool
    • Identify skill clusters and job role patterns  
    • Refine your search with specific facet values
    • Understand the composition of your results

    🔍 **Browse the colorful category cards below** to dive into specific facets!"""
                
                return enhanced_message
            else:
                return "Facet categories have been generated for your search criteria."
                
        except Exception as e:
            logger.error(f"Error formatting facets response: {e}")
            return "Facet categories have been generated for your search."
    def _create_enhanced_facet_summary(self, total_count: int, primary_count: int, 
                                 secondary_count: int, total_items: int, 
                                 sample_categories: List[str]) -> str:
        """Create an enhanced, informative facet summary message."""
        
        # Create sample categories text
        if sample_categories:
            if len(sample_categories) == 1:
                categories_text = f'"{sample_categories[0]}"'
            elif len(sample_categories) == 2:
                categories_text = f'"{sample_categories[0]}" and "{sample_categories[1]}"'
            else:
                categories_text = f'"{sample_categories[0]}", "{sample_categories[1]}", and "{sample_categories[2]}"'
            
            if total_count > len(sample_categories):
                remaining = total_count - len(sample_categories)
                categories_text += f" (+ {remaining} more)"
        else:
            categories_text = "various categories"
        
        # Create breakdown text
        if primary_count > 0 and secondary_count > 0:
            breakdown_text = f"{primary_count} primary and {secondary_count} additional categories"
        elif primary_count > 0:
            breakdown_text = f"{primary_count} primary categories"
        else:
            breakdown_text = f"{secondary_count} categories"
        
        # Format total items
        items_text = f"{total_items:,} items" if total_items > 0 else "multiple items"
        
        # Create the enhanced message
        enhanced_message = f"""I refined your query and

    📊 **Generated {total_count} facet categories** ({breakdown_text}) with {items_text} across all categories.

    🔍 **Categories include:** {categories_text}

    💡 **Browse the colorful category cards below** to explore different facets of your search results. Each card shows the category name and item count - perfect for understanding the composition of your candidate pool!

    🎯 **Use these insights** to refine your search criteria or identify new skill areas and job roles in your results."""
        
        return enhanced_message

    def _create_enhanced_relaxation_summary_for_chat(self, relaxation_data: Dict[str, Any]) -> str:
        """Create an enhanced, informative relaxation summary message for chat."""
        try:
            suggestions = relaxation_data.get("relaxation_suggestions", [])
            current_count = relaxation_data.get("current_count", 0)
            estimated_increase = relaxation_data.get("estimated_new_count", 0)
            method = relaxation_data.get("method", "unknown")
            
            if not suggestions:
                return "I analyzed your search criteria but couldn't generate specific relaxation suggestions at this time."
            
            # Count suggestion types
            suggestion_types = {}
            high_confidence_count = 0
            
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'general')
                suggestion_types[suggestion_type] = suggestion_types.get(suggestion_type, 0) + 1
                
                if suggestion.get('confidence', 0) >= 0.8:
                    high_confidence_count += 1
            
            # Create type breakdown text
            type_names = {
                'skill_relaxation': 'skill optimization',
                'experience_relaxation': 'experience range expansion', 
                'location_relaxation': 'location broadening',
                'salary_relaxation': 'salary range adjustment',
                'remote_work': 'remote work options'
            }
            
            type_descriptions = []
            for suggestion_type, count in suggestion_types.items():
                type_name = type_names.get(suggestion_type, suggestion_type.replace('_', ' '))
                if count == 1:
                    type_descriptions.append(type_name)
                else:
                    type_descriptions.append(f"{count} {type_name} strategies")
            
            types_text = ", ".join(type_descriptions) if type_descriptions else "various strategies"
            
            # Create impact text
            if estimated_increase > 0:
                if current_count > 0:
                    improvement_pct = int((estimated_increase / current_count) * 100)
                    impact_text = f"potentially increasing your candidate pool by **{estimated_increase:,} candidates** ({improvement_pct}% improvement)"
                else:
                    impact_text = f"potentially finding **{estimated_increase:,} additional candidates**"
            else:
                impact_text = "with **significant potential** for increasing your results"
            
            # Create confidence text
            if high_confidence_count > 0:
                confidence_text = f"**{high_confidence_count} high-confidence recommendations** "
            else:
                confidence_text = ""
            
            # Create method text
            method_text = ""
            if method == "api_integration":
                method_text = "using advanced query analysis"
            elif method in ["rule_based_fallback", "rule_based"]:
                method_text = "using intelligent rule-based analysis"
            
            # Build the enhanced message
            enhanced_message = f"""I analyzed your search constraints {method_text} and found **{len(suggestions)} optimization opportunities**:

    🔄 **Query Relaxation Analysis Complete**

    📊 **Recommendations:** {types_text} {impact_text}

    {f"🎯 **{confidence_text}** are available for immediate implementation" if high_confidence_count > 0 else "💡 **Multiple strategies** are available to explore"}

    🛠️ **Next Steps:** 
    • Review the detailed suggestion cards below
    • Apply individual suggestions or try multiple approaches  
    • Each suggestion shows expected impact and confidence level

    💡 **Pro Tip:** Start with the highest confidence suggestions for the best results!"""
            
            return enhanced_message
            
        except Exception as e:
            logger.error(f"Error creating relaxation summary: {e}")
            return f"I've generated {len(relaxation_data.get('relaxation_suggestions', []))} suggestions to help expand your candidate search. Review the options below to see which approach works best."
    def _count_total_facet_items(self, facets_data: Dict[str, Any]) -> int:
        """Count total items across all facet categories."""
        total_items = 0
        
        try:
            for result_key in ["result_1", "result_2"]:
                result_data = facets_data.get(result_key, {})
                for category_data in result_data.values():
                    total_items += self._count_items_in_facet_category(category_data)
        except Exception:
            total_items = 0
        
        return total_items


    def _count_items_in_facet_category(self, category_data: Dict[str, Any]) -> int:
        """Count items in facet category (helper method)."""
        total_count = 0
        
        try:
            if isinstance(category_data, dict):
                for key, value in category_data.items():
                    if isinstance(value, list):
                        total_count += len(value)
                    elif isinstance(value, str):
                        if "," in value:
                            total_count += len([item.strip() for item in value.split(",") if item.strip()])
                        else:
                            total_count += 1 if value.strip() else 0
                    else:
                        total_count += 1
            elif isinstance(category_data, list):
                total_count = len(category_data)
            else:
                total_count = 1
        except Exception:
            total_count = 0
        
        return total_count
    async def _handle_triggered_search_with_memory(self, result_data: Dict[str, Any], user_id: str, conversation_session_id: str, update_callback):
        """Handle search triggered by AI agent with memory context - ENHANCED VERSION."""
        try:
            step_logger.log_step("⚙️ Preparing memory-enhanced search execution", "search")
            update_callback()
            await asyncio.sleep(0.1)
            
            # Get updated session state
            updated_state = result_data.get("session_state", self.session_state)
            if not isinstance(updated_state, dict):
                updated_state = self._get_clean_session_state()
            
            # Build search filters from current state
            search_filters = {
                'keywords': updated_state.get('keywords', []),
                'min_exp': updated_state.get('min_exp', 0),
                'max_exp': updated_state.get('max_exp', 10),
                'min_salary': updated_state.get('min_salary', 0),
                'max_salary': updated_state.get('max_salary', 15),
                'current_cities': updated_state.get('current_cities', []),
                'preferred_cities': updated_state.get('preferred_cities', []),
                'recruiter_company': updated_state.get('recruiter_company', ''),
                'max_candidates': 100  # Standard limit
            }
            
            # Add search context to memory
            if self.session_manager:
                await self.session_manager.add_interaction(
                    user_id=user_id,
                    session_id=conversation_session_id,
                    interaction_type="triggered_search",
                    content={"filters": search_filters, "trigger_reason": "filter_modification"}
                )
            
            step_logger.log_search_execution(search_filters)
            update_callback()
            await asyncio.sleep(0.1)
            
            # Execute search through root agent
            from ...agent import Content
            search_content = Content(data={
                "request_type": "candidate_search",
                "search_filters": search_filters,
                "user_id": user_id
            })
            
            step_logger.log_step("📡 Calling ResDex API with memory context", "search")
            update_callback()
            await asyncio.sleep(0.1)
            
            # Execute the search
            search_result = await self.root_agent.execute(search_content)
            
            if search_result.data["success"]:
                candidates = search_result.data["candidates"]
                total_count = search_result.data["total_count"]
                
                step_logger.log_results(len(candidates), total_count)
                update_callback()
                await asyncio.sleep(0.1)
                
                # Update session state with search results
                self.session_state['candidates'] = candidates
                self.session_state['all_candidates'] = candidates  # For batch display
                self.session_state['displayed_candidates'] = candidates[:20]  # Show first 20
                self.session_state['total_results'] = total_count
                self.session_state['search_applied'] = True
                self.session_state['page'] = 0
                
                # Add search results to memory
                if self.session_manager:
                    await self.session_manager.add_interaction(
                        user_id=user_id,
                        session_id=conversation_session_id,
                        interaction_type="search_results",
                        content={
                            "candidates_found": len(candidates),
                            "total_count": total_count,
                            "filters_used": search_filters,
                            "success": True
                        }
                    )
                
                # Add success message to chat
                success_msg = f"🎯 Search completed! Found {len(candidates)} candidates from {total_count:,} total matches."
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": success_msg
                })
                
                step_logger.log_completion("Memory-enhanced search completed successfully")
                update_callback()
                
            else:
                # Handle search failure
                error_msg = search_result.data.get('error', 'Unknown error')
                step_logger.log_error(f"Search failed: {error_msg}")
                update_callback()
                
                error_response = f"❌ Search failed: {error_msg}"
                self.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": error_response
                })
                
                # Add search failure to memory
                if self.session_manager:
                    await self.session_manager.add_interaction(
                        user_id=user_id,
                        session_id=conversation_session_id,
                        interaction_type="search_failed",
                        content={"error": error_msg, "filters_attempted": search_filters}
                    )
                    
        except Exception as e:
            step_logger.log_error(f"Memory-enhanced search execution failed: {str(e)}")
            update_callback()
            
            error_msg = f"❌ Search execution failed: {str(e)}"
            self.session_state['chat_history'].append({
                "role": "assistant",
                "content": error_msg
            })
            
            print(f"❌ _handle_triggered_search_with_memory failed: {e}")
            import traceback
            traceback.print_exc()

    
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