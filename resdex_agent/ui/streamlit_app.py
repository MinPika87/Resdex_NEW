"""
Streamlit application for ResDex Agent - FIXED for live step streaming
"""

import streamlit as st
import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Optional
from resdex_agent.agent import ResDexRootAgent, Content
from resdex_agent.config import AgentConfig
from resdex_agent.ui.components.search_form import SearchForm
from resdex_agent.ui.components.candidate_display import CandidateDisplay
from resdex_agent.ui.components.chat_interface import ChatInterface
from resdex_agent.ui.components.step_display import StepDisplay
from resdex_agent.utils.step_logger import step_logger

logger = logging.getLogger(__name__)


class StreamlitApp:
    def __init__(self):
        self.config = AgentConfig.from_env()
        self.root_agent = ResDexRootAgent(self.config)
        
        # UI components
        self.search_form = None
        self.candidate_display = None
        self.chat_interface = None
        self.step_display = StepDisplay()
        
        logger.info("FIXED Streamlit app initialized with ResDex Agent")
    
    def run(self):
        # Page configuration
        st.set_page_config(
            page_title="ResDex AI Agent",
            layout="wide"
        )
        
        # Custom CSS
        st.markdown(self._get_custom_css(), unsafe_allow_html=True)
        
        # Initialize session state
        self._initialize_session_state()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Render UI
        self._render_header()
        self._render_main_content()
        self._render_sidebar()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state."""
        defaults = {
            'chat_history': [],
            'candidates': [],
            'search_applied': False,
            'total_results': 0,
            'page': 0,
            'keywords': [],
            'selected_keywords': [],
            'current_cities': [],
            'preferred_cities': [],
            'active_days': "1 month",
            'min_exp': 0.0,
            'max_exp': 10.0,
            'min_salary': 0.0,
            'max_salary': 15.0,
            'recruiter_company': "",
            'agent_debug_info': {},
            # Enhanced session state
            'all_candidates': [],
            'displayed_candidates': [],
            'display_batch_size': 20
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _initialize_ui_components(self):
        """Initialize UI components."""
        self.search_form = SearchForm(st.session_state)
        self.candidate_display = CandidateDisplay(st.session_state)
        self.chat_interface = ChatInterface(st.session_state, self.root_agent)
    
    def _render_header(self):
            st.title("🔍 ResDex AI Agent")
            st.markdown("*Real-time AI processing with step-by-step insights*")
            
            # Simple agent status indicator
            with st.expander("🤖 Agent Status", expanded=False):
                if st.button("Check Agent Health"):
                    health_status = asyncio.run(self._check_agent_health())
                    if health_status["success"]:
                        st.success("✅ All systems operational")
                        st.json(health_status)
                    else:
                        st.error("❌ System issues detected")
                        st.json(health_status)
    
    def _render_main_content(self):
        # Search form
        with st.container():
            st.markdown("### Search Configuration")
            
            # Company input
            self.search_form.render_company_input()
            
            # Reduced gap
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            
            # Create 5 columns for the search filters
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown("**Keywords**")
                self.search_form.render_keywords_section()
            
            with col2:
                st.markdown("**Experience**")
                self.search_form.render_experience_section()
            
            with col3:
                st.markdown("**Location**")
                self.search_form.render_location_section()
            
            with col4:
                st.markdown("**Salary**")
                self.search_form.render_salary_section()
            
            with col5:
                st.markdown("**Search**")
                search_button = self.search_form.render_search_controls()
                if search_button:
                    asyncio.run(self._handle_search_request_with_live_steps())
        
        # Results section
        st.markdown("---")
        
        if st.session_state['search_applied']:
            if st.session_state['candidates']:
                st.markdown("### Search Results")
                self.candidate_display.render_results()
            else:
                st.warning("No candidates found. Try adjusting your search criteria.")
        else:
            st.info("👆 Configure your search criteria above and click 'Search Candidates' to get started.")
    
    def _render_sidebar(self):
        """Render sidebar."""
        with st.sidebar:
            if not st.session_state.get('search_applied', False):
                # Show current request object and stats before search
                st.markdown("### 🔧 Current Search Request")
                
                current_request = self._build_current_request_object()
                
                with st.expander("View Request Object", expanded=False):
                    st.json(current_request)
                
                self._render_search_stats()
                
                st.info("🤖 AI Assistant will appear here after you search for candidates.")
            
            else:
                # After search: Show the chat interface
                if st.session_state['candidates']:
                    self.chat_interface.render()
                else:
                    st.markdown("### 🤖 AI Assistant")
                    st.warning("No candidates found with current criteria.")
                    st.info("Try adjusting your search filters and search again.")
                    
                    with st.expander("🔧 Debug: View Last Search Request", expanded=False):
                        if 'last_search_request' in st.session_state:
                            st.json(st.session_state['last_search_request'])
                        else:
                            st.text("No search request available")
    
    def _build_current_request_object(self):
        """Build current request object for display."""
        from resdex_agent.utils.api_client import api_client
        
        current_state = {
            'keywords': st.session_state.get('keywords', []),
            'min_exp': st.session_state.get('min_exp', 0.0),
            'max_exp': st.session_state.get('max_exp', 10.0),
            'min_salary': st.session_state.get('min_salary', 0.0),
            'max_salary': st.session_state.get('max_salary', 15.0),
            'current_cities': st.session_state.get('current_cities', []),
            'preferred_cities': st.session_state.get('preferred_cities', []),
            'recruiter_company': st.session_state.get('recruiter_company', ''),
            'active_days': st.session_state.get('active_days', '1 month')
        }
        
        return api_client.build_search_request(current_state)

    def _render_search_stats(self):
        """Render quick search statistics."""
        keywords_count = len(st.session_state.get('keywords', []))
        locations_count = (len(st.session_state.get('current_cities', [])) + 
                        len(st.session_state.get('preferred_cities', [])))
        
        st.markdown("**Quick Stats:**")
        st.markdown(f"• Keywords: {keywords_count}")
        st.markdown(f"• Locations: {locations_count}")
        st.markdown(f"• Experience: {st.session_state.get('min_exp', 0)}-{st.session_state.get('max_exp', 10)} years")
        st.markdown(f"• Salary: {st.session_state.get('min_salary', 0)}-{st.session_state.get('max_salary', 15)} lakhs")
        
        company = st.session_state.get('recruiter_company', '').strip()
        has_keywords = keywords_count > 0
        
        if company and has_keywords:
            st.success("✅ Ready to search!")
        elif not company:
            st.warning("⚠️ Company name required")
        elif not has_keywords:
            st.warning("⚠️ Add at least one keyword")
        else:
            st.info("📝 Configure search criteria")
    
    async def _handle_search_request_with_live_steps(self):
        """SIMPLIFIED: Handle search request WITHOUT live steps - direct results only."""
        try:
            # Validate search form
            validation_errors = self.search_form.validate_form()
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                return
            
            # Build search filters
            search_filters = {
                'keywords': st.session_state['keywords'],
                'min_exp': st.session_state['min_exp'],
                'max_exp': st.session_state['max_exp'],
                'min_salary': st.session_state['min_salary'],
                'max_salary': st.session_state['max_salary'],
                'current_cities': st.session_state['current_cities'],
                'preferred_cities': st.session_state['preferred_cities'],
                'recruiter_company': st.session_state['recruiter_company'],
                'max_candidates': 100
            }
            
            # Show simple loading message
            with st.spinner("🔍 Searching candidates..."):
                
                # Execute search
                from resdex_agent.agent import Content
                content = Content(data={
                    "request_type": "candidate_search",
                    "search_filters": search_filters
                })
                
                result = await self.root_agent.execute(content)
                
                if result.data["success"]:
                    all_candidates = result.data["candidates"]
                    total_results = result.data["total_count"]
                    
                    # Store results
                    st.session_state['all_candidates'] = all_candidates
                    st.session_state['displayed_candidates'] = all_candidates[:20]
                    st.session_state['display_batch_size'] = 20
                    st.session_state['candidates'] = all_candidates[:20]
                    st.session_state['total_results'] = total_results
                    st.session_state['search_applied'] = True
                    st.session_state['selected_keywords'] = st.session_state['keywords'].copy()
                    st.session_state['page'] = 0
                    
                    # Clear chat history for new search
                    st.session_state['chat_history'] = []
                    
                    if all_candidates:
                        # Create search summary
                        current_request = self._build_current_request_object()
                        search_summary = self._create_search_summary(current_request, result.data)
                        
                        welcome_msg = f"🎉 Search completed! Found {total_results:,} total matches.\n\n{search_summary}\n\nShowing top candidates with 5 per page. Ask me to 'show more candidates' to see additional results!"
                        
                        st.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": welcome_msg
                        })
                        
                        st.session_state['last_search_request'] = current_request
                    
                    fetched_count = len(all_candidates)
                    displayed_count = len(st.session_state['displayed_candidates'])
                    
                    # Simple success message
                    st.success(f"✅ Found {total_results:,} matches, displaying {displayed_count} candidates.")
                    
                    st.session_state['agent_debug_info'] = result.data.get("root_agent", {})
                    
                else:
                    # Handle search failure
                    st.error(f"❌ Search failed: {result.data.get('error', 'Unknown error')}")
                    if 'details' in result.data:
                        st.error(f"Details: {result.data['details']}")
            
            # Use experimental_rerun for Streamlit 1.12
            st.experimental_rerun()
            
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            st.error(f"❌ An unexpected error occurred: {str(e)}")
    
    def _create_search_summary(self, request_object: dict, search_result: dict) -> str:
        """Create a human-readable search summary."""
        keywords = st.session_state.get('keywords', [])
        locations = (st.session_state.get('current_cities', []) + 
                    st.session_state.get('preferred_cities', []))
        
        summary_parts = []
        
        if keywords:
            mandatory_skills = [k.replace('★ ', '') for k in keywords if k.startswith('★ ')]
            optional_skills = [k for k in keywords if not k.startswith('★ ')]
            
            if mandatory_skills:
                summary_parts.append(f"**Required Skills:** {', '.join(mandatory_skills)}")
            if optional_skills:
                summary_parts.append(f"**Optional Skills:** {', '.join(optional_skills)}")
        
        min_exp = st.session_state.get('min_exp', 0)
        max_exp = st.session_state.get('max_exp', 10)
        if min_exp > 0 or max_exp < 50:
            summary_parts.append(f"**Experience:** {min_exp}-{max_exp} years")
        
        min_sal = st.session_state.get('min_salary', 0)
        max_sal = st.session_state.get('max_salary', 15)
        if min_sal > 0 or max_sal < 100:
            summary_parts.append(f"**Salary:** {min_sal}-{max_sal} lakhs")
        
        if locations:
            summary_parts.append(f"**Locations:** {', '.join(locations)}")
        
        return "\n".join(summary_parts) if summary_parts else "Basic search criteria applied."
    
    async def _check_agent_health(self) -> Dict[str, Any]:
        """Check agent health status."""
        try:
            content = Content(data={"request_type": "health_check"})
            result = await self.root_agent.execute(content)
            return result.data
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    def _get_custom_css(self) -> str:
        """Get custom CSS for the application."""
        return """
        <style>
        .stApp {
            background-color: #f8f9fa;
        }
        
        .skill-tag {
            background-color: #e9ecef;
            padding: 0.25rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            margin: 0.125rem;
            display: inline-block;
        }
        
        .mandatory-skill {
            background-color: #ffeaa7;
            border: 1px solid #fdcb6e;
        }
        
        .candidate-card {
            border: 1px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            background-color: white;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
        
        .chat-message {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 0.375rem;
        }
        
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        
        .assistant-message {
            background-color: #f1f8e9;
        }
        
        /* Hide Streamlit menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Animation for live steps */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .step-container {
            animation: fadeInUp 0.3s ease-out;
        }
        </style>
        """


# Main entry point
def main():
    """Main entry point for the FIXED Streamlit app with live step streaming."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()