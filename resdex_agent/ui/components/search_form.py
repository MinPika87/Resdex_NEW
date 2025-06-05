# Replace resdx_agent/ui/components/search_form.py with this fixed version for Streamlit 1.12

"""
Search form component for ResDex Agent UI - Compatible with Streamlit 1.12
"""

import streamlit as st
from typing import Dict, Any, List
from ...utils.constants import TECH_SKILLS, CITIES


class SearchForm:
    """Search form component for configuring search filters."""
    
    def __init__(self, session_state: Dict[str, Any]):
        self.session_state = session_state
    
    def render_company_input(self):
        """Render company name input."""
        company = st.text_input(
            "Company Name *",
            value=self.session_state.get('recruiter_company', ''),
            placeholder="e.g., TCS, Infosys, Google",
            help="Enter your company name (required for search)"
        )
        self.session_state['recruiter_company'] = company
        
        if not company.strip():
            st.error("⚠️ Company name is required")
        else:
            st.success("✅ Company set")
    
    def render_keywords_section(self):
        """Render keywords/skills input section."""
        st.subheader("Keywords")
        
        # Skill input form
        with st.form(key="keyword_form", clear_on_submit=True):
            keyword_input = st.text_input("Add keyword", placeholder="e.g., Python")
            make_mandatory = st.checkbox("Mark as mandatory")
            
            form_submit = st.form_submit_button("Add Keyword")
            
            if form_submit and keyword_input.strip():
                clean_keyword = keyword_input.strip()
                if clean_keyword not in [k.replace('★ ', '') for k in self.session_state.get('keywords', [])]:
                    if make_mandatory:
                        self.session_state.setdefault('keywords', []).append(f"★ {clean_keyword}")
                    else:
                        self.session_state.setdefault('keywords', []).append(clean_keyword)
                    st.experimental_rerun()
        
        # Display current keywords
        self._display_keywords()
    
    def render_experience_section(self):
        """Render experience input section."""
        st.subheader("Experience")
        min_exp = st.number_input("Min (years)", 
                                  min_value=0.0, 
                                  max_value=50.0, 
                                  value=self.session_state.get('min_exp', 0.0), 
                                  step=1.0)
        max_exp = st.number_input("Max (years)", 
                                  min_value=0.0, 
                                  max_value=50.0, 
                                  value=self.session_state.get('max_exp', 10.0), 
                                  step=1.0)
        
        self.session_state['min_exp'] = min_exp
        self.session_state['max_exp'] = max_exp
        
        if min_exp > max_exp:
            st.error("Min experience cannot be greater than max experience")
    
    def render_location_section(self):
        """Render location input section."""
        st.subheader("Location")
        
        with st.form(key="location_form", clear_on_submit=True):
            city_input = st.selectbox("Add location", [""] + CITIES)
            set_as_preferred = st.checkbox("Set as preferred")
            
            location_form_submit = st.form_submit_button("Add Location")
            
            if location_form_submit and city_input:
                if set_as_preferred:
                    if city_input not in self.session_state.get('preferred_cities', []):
                        self.session_state.setdefault('preferred_cities', []).append(city_input)
                else:
                    if city_input not in self.session_state.get('current_cities', []):
                        self.session_state.setdefault('current_cities', []).append(city_input)
                st.experimental_rerun()
        
        # Display current locations
        self._display_locations()
    
    def render_salary_section(self):
        """Render salary input section."""
        st.subheader("Annual Salary")
        min_salary = st.number_input("Min (lakhs)", 
                                     min_value=0.0, 
                                     max_value=100.0, 
                                     value=self.session_state.get('min_salary', 0.0), 
                                     step=1.0)
        max_salary = st.number_input("Max (lakhs)", 
                                     min_value=0.0, 
                                     max_value=100.0, 
                                     value=self.session_state.get('max_salary', 15.0), 
                                     step=1.0)
        
        self.session_state['min_salary'] = min_salary
        self.session_state['max_salary'] = max_salary
        
        if min_salary > max_salary:
            st.error("Min salary cannot be greater than max salary")
    
    def render_search_controls(self):
        """Render search controls section."""
        st.subheader("Search Controls")
        
        active_options = ["1 day", "15 days", "1 month", "2 months", "3 months", "6 months", "1 year"]
        st.session_state['active_days'] = st.selectbox(
            "Active in", 
            active_options, 
            index=active_options.index(st.session_state.get('active_days', '1 month'))
        )
        
        st.markdown("")
        st.markdown("")
        return st.button("🔍 Search Candidates")
    
    def validate_form(self) -> List[str]:
        """Validate search form inputs."""
        errors = []
        
        if not self.session_state.get('recruiter_company', '').strip():
            errors.append("Please enter your company name to proceed with the search.")
        
        if not self.session_state.get('keywords', []):
            errors.append("Please add at least one keyword to search.")
        
        if self.session_state.get('min_exp', 0) > self.session_state.get('max_exp', 10):
            errors.append("Minimum experience cannot be greater than maximum experience.")
        
        if self.session_state.get('min_salary', 0) > self.session_state.get('max_salary', 15):
            errors.append("Minimum salary cannot be greater than maximum salary.")
        
        return errors
    
    def _display_keywords(self):
        """Display current keywords with remove buttons."""
        if self.session_state.get('keywords', []):
            st.markdown("**Current Keywords**")
            for idx, keyword in enumerate(self.session_state['keywords']):
                display_keyword = keyword.replace('★ ', '') if keyword.startswith('★ ') else keyword
                is_mandatory = keyword.startswith('★ ')
                button_text = f"{'★ ' if is_mandatory else ''}✕ {display_keyword}"
                
                if st.button(button_text, 
                           key=f"remove_kw_{idx}", 
                           help=f"Remove {display_keyword}"):
                    st.session_state['keywords'].remove(keyword)
                    st.experimental_rerun()
    
    def _display_locations(self):
        """Display current and preferred locations with remove buttons."""
        if st.session_state.get('current_cities', []) or st.session_state.get('preferred_cities', []):
            st.markdown("**Current Locations**")
            
            for idx, city in enumerate(st.session_state.get('current_cities', [])):
                button_text = f"✕ {city}"
                if st.button(button_text, 
                           key=f"remove_city_{idx}", 
                           help=f"Remove {city}"):
                    st.session_state['current_cities'].remove(city)
                    st.experimental_rerun()
            
            for idx, city in enumerate(st.session_state.get('preferred_cities', [])):
                button_text = f"★ ✕ {city}"
                if st.button(button_text, 
                           key=f"remove_pref_city_{idx}", 
                           help=f"Remove preferred location {city}"):
                    st.session_state['preferred_cities'].remove(city)
                    st.experimental_rerun()