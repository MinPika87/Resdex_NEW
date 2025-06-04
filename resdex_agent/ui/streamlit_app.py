"""
Streamlit application for ResDex Agent following ADK patterns.
"""

import streamlit as st
import asyncio
import logging
from typing import Dict, Any, Optional
from google.adk.core.content import Content
from ..agent import ResDexRootAgent
from ..config import AgentConfig
from .components.search_form import SearchForm
from .components.candidate_display import CandidateDisplay
from .components.chat_interface import ChatInterface

logger = logging.getLogger(__name__)


class StreamlitApp:
    """
    Streamlit application interface for ResDex Agent.
    """
    
    def __init__(self):
        self.config = AgentConfig.from_env()
        self.root_agent = ResDexRootAgent(self.config)
        
        # UI components
        self.search_form = None
        self.candidate_display = None
        self.chat_interface = None
        
        logger.info("Streamlit app initialized with ResDex Agent")
    
    def run(self):
        """Main application entry point."""
        # Page configuration
        st.set_page_config(
            page_title="ResDex AI Agent",
            page_icon="🔍",
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
            'agent_debug_info': {}
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
        """Render application header."""
        st.title("🔍 ResDex AI Agent")
        st.markdown("*Powered by Google ADK - Advanced candidate search with AI assistance*")
        
        # Agent status indicator
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
        """Render main content area."""
        # Search form
        with st.container():
            st.markdown("### Search Configuration")
            
            # Company input
            self.search_form.render_company_input()
            
            # Search filters in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                self.search_form.render_keywords_section()
            
            with col2:
                self.search_form.render_experience_section()
            
            with col3:
                self.search_form.render_location_section()
            
            with col4:
                self.search_form.render_salary_section()
            
            # Search button
            search_button = st.button("🔍 Search Candidates", type="primary")
            
            if search_button:
                asyncio.run(self._handle_search_request())
        
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
        """Render sidebar with chat interface."""
        with st.sidebar:
            if st.session_state['candidates']:
                self.chat_interface.render()
            else:
                st.markdown("### 🔧 Debug Info")
                if st.session_state.get('agent_debug_info'):
                    st.json(st.session_state['agent_debug_info'])
                else:
                    st.info("Debug information will appear here after agent interactions.")
    
    async def _handle_search_request(self):
        """Handle search button click."""
        try:
            # Validate search form
            validation_errors = self.search_form.validate_form()
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                return
            
            with st.spinner("🔍 Searching candidates..."):
                # Prepare search filters
                search_filters = {
                    'keywords': st.session_state['keywords'],
                    'min_exp': st.session_state['min_exp'],
                    'max_exp': st.session_state['max_exp'],
                    'min_salary': st.session_state['min_salary'],
                    'max_salary': st.session_state['max_salary'],
                    'current_cities': st.session_state['current_cities'],
                    'preferred_cities': st.session_state['preferred_cities'],
                    'recruiter_company': st.session_state['recruiter_company']
                }
                
                # Execute search through root agent
                content = Content(data={
                    "request_type": "candidate_search",
                    "search_filters": search_filters
                })
                
                result = await self.root_agent.execute(content)
                
                if result.data["success"]:
                    # Update session state with results
                    st.session_state['candidates'] = result.data["candidates"]
                    st.session_state['total_results'] = result.data["total_count"]
                    st.session_state['search_applied'] = True
                    st.session_state['selected_keywords'] = st.session_state['keywords'].copy()
                    st.session_state['page'] = 0
                    
                    # Clear chat history for new search
                    st.session_state['chat_history'] = []
                    
                    # Add welcome message
                    if st.session_state['candidates']:
                        welcome_msg = f"🎉 Found {len(st.session_state['candidates'])} candidates from {st.session_state['total_results']:,} total matches! How can I help you analyze these results?"
                        st.session_state['chat_history'].append({
                            "role": "assistant",
                            "content": welcome_msg
                        })
                    
                    st.success(result.data["message"])
                    
                    # Store debug info
                    st.session_state['agent_debug_info'] = result.data.get("root_agent", {})
                    
                else:
                    st.error(f"❌ Search failed: {result.data.get('error', 'Unknown error')}")
                    if 'details' in result.data:
                        st.error(f"Details: {result.data['details']}")
                
                st.experimental_rerun()
                
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            st.error(f"❌ An unexpected error occurred: {str(e)}")
    
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
        
        .status-indicator {
            display: inline-block;
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-healthy {
            background-color: #28a745;
        }
        
        .status-warning {
            background-color: #ffc107;
        }
        
        .status-error {
            background-color: #dc3545;
        }
        </style>
        """


# Main entry point
def main():
    """Main entry point for the Streamlit app."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()