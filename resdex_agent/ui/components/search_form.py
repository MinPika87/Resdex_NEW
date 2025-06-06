# Replace resdx_agent/ui/components/search_form.py with this sequential layout version

"""
Search form component for ResDex Agent UI - Sequential Layout (No Nested Columns)
"""

import streamlit as st
from typing import Dict, Any, List
from ...utils.constants import TECH_SKILLS, CITIES


class SearchForm:
    """Search form component for configuring search filters."""
    
    def __init__(self, session_state: Dict[str, Any]):
        self.session_state = session_state
    
    def render_company_input(self):
    # Use columns for compact validation display
        col1, col2 = st.columns([4, 1])
        
        with col1:
            company = st.text_input(
                "Company Name *",
                value=self.session_state.get('recruiter_company', ''),
                placeholder="e.g., TCS, Infosys, Google",
                help="Enter your company name (required for search)"
            )
            self.session_state['recruiter_company'] = company
        
        with col2:
            # Compact validation indicator at the side
            if not company.strip():
                st.markdown('<p style="color: #e74c3c; font-size: 1.2rem; margin-top: 25px;">⚠️ Required</p>', 
                        unsafe_allow_html=True)
            else:
                st.markdown('<p style="color: #27ae60; font-size: 1.2rem; margin-top: 25px;">✅ Set</p>', 
                        unsafe_allow_html=True)
    
    # Replace the search form methods in resdx_agent/ui/components/search_form.py

    def render_keywords_section(self):
        """Render keywords/skills input section with auto-clearing."""
        # Initialize counter for unique keys (this will clear inputs)
        if 'keyword_counter' not in st.session_state:
            st.session_state.keyword_counter = 0
        
        # Sequential layout - no nested columns
        keyword_input = st.text_input("Add Skill", 
                                    placeholder="e.g., Python",
                                    key=f"keyword_input_{st.session_state.keyword_counter}")
        
        make_mandatory = st.checkbox("Mark as Mandatory", 
                                    key=f"mandatory_checkbox_{st.session_state.keyword_counter}")
        
        # Button below
        add_keyword = st.button("Add Keyword", key="add_keyword_btn")
        
        # Handle adding keyword
        if add_keyword and keyword_input.strip():
            clean_keyword = keyword_input.strip()
            if clean_keyword not in [k.replace('★ ', '') for k in self.session_state.get('keywords', [])]:
                if make_mandatory:
                    self.session_state.setdefault('keywords', []).append(f"★ {clean_keyword}")
                else:
                    self.session_state.setdefault('keywords', []).append(clean_keyword)
                
                # Increment counter to create new widget keys (this clears the inputs)
                st.session_state.keyword_counter += 1
                st.experimental_rerun()
        
        # Display current keywords (compact)
        self._display_keywords_compact()

    def render_location_section(self):
        """Render location input section with auto-clearing."""
        # Initialize counter for unique keys (this will clear inputs)
        if 'location_counter' not in st.session_state:
            st.session_state.location_counter = 0
        
        # Sequential layout - no nested columns
        city_input = st.selectbox("Select City", 
                                [""] + CITIES,
                                key=f"city_input_{st.session_state.location_counter}")
        
        set_as_preferred = st.checkbox("Set as Preferred", 
                                    key=f"preferred_checkbox_{st.session_state.location_counter}")
        
        # Button below
        add_location = st.button("Add Location", key="add_location_btn")
        
        # Handle adding location
        if add_location and city_input:
            if set_as_preferred:
                if city_input not in self.session_state.get('preferred_cities', []):
                    self.session_state.setdefault('preferred_cities', []).append(city_input)
            else:
                if city_input not in self.session_state.get('current_cities', []):
                    self.session_state.setdefault('current_cities', []).append(city_input)
            
            # Increment counter to create new widget keys (this clears the inputs)
            st.session_state.location_counter += 1
            st.experimental_rerun()
        
        # Display current locations (compact)
        self._display_locations_compact()
    
    def render_experience_section(self):
        """Render experience input section - REFERENCE styling for uniformity."""
        min_exp = st.number_input("Min Years", 
                                  min_value=0.0, 
                                  max_value=50.0, 
                                  value=self.session_state.get('min_exp', 0.0), 
                                  step=1.0)
        max_exp = st.number_input("Max Years", 
                                  min_value=0.0, 
                                  max_value=50.0, 
                                  value=self.session_state.get('max_exp', 10.0), 
                                  step=1.0)
        
        self.session_state['min_exp'] = min_exp
        self.session_state['max_exp'] = max_exp
        
        if min_exp > max_exp:
            st.error("⚠️ Min experience cannot be greater than max experience")
    
    
    def render_salary_section(self):
        """Render salary input section - REFERENCE styling for uniformity."""
        min_salary = st.number_input("Min Lakhs", 
                                     min_value=0.0, 
                                     max_value=100.0, 
                                     value=self.session_state.get('min_salary', 0.0), 
                                     step=1.0)
        max_salary = st.number_input("Max Lakhs", 
                                     min_value=0.0, 
                                     max_value=100.0, 
                                     value=self.session_state.get('max_salary', 15.0), 
                                     step=1.0)
        
        self.session_state['min_salary'] = min_salary
        self.session_state['max_salary'] = max_salary
        
        if min_salary > max_salary:
            st.error("⚠️ Min salary cannot be greater than max salary")
    
    def render_search_controls(self):
        """Render search controls section - SEQUENTIAL layout like old version."""
        active_options = ["1 day", "15 days", "1 month", "2 months", "3 months", "6 months", "1 year"]
        st.session_state['active_days'] = st.selectbox(
            "Active in", 
            active_options, 
            index=active_options.index(st.session_state.get('active_days', '1 month'))
        )
        
        st.markdown("")  # Small spacing
        st.markdown("")  # Extra spacing
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
    
    def _display_keywords_compact(self):
        """Display current keywords with remove buttons - COMPACT for columns."""
        if self.session_state.get('keywords', []):
            st.markdown("**Current Keywords:**")
            for idx, keyword in enumerate(self.session_state['keywords']):
                display_keyword = keyword.replace('★ ', '') if keyword.startswith('★ ') else keyword
                is_mandatory = keyword.startswith('★ ')
                
                # Compact display - truncate long keywords
                display_text = display_keyword[:10] + "..." if len(display_keyword) > 10 else display_keyword
                button_text = f"{'★ ' if is_mandatory else ''}✕ {display_text}"
                
                if st.button(button_text, 
                           key=f"remove_kw_{idx}", 
                           help=f"Remove {display_keyword}"):
                    self.session_state['keywords'].remove(keyword)
                    st.experimental_rerun()
    
    def _display_locations_compact(self):
        """Display current and preferred locations with remove buttons - COMPACT for columns."""
        current_cities = self.session_state.get('current_cities', [])
        preferred_cities = self.session_state.get('preferred_cities', [])
        
        if current_cities or preferred_cities:
            st.markdown("**Current Locations:**")
            
            # Show current cities
            for idx, city in enumerate(current_cities):
                # Truncate long city names
                display_city = city[:10] + "..." if len(city) > 10 else city
                button_text = f"✕ {display_city}"
                if st.button(button_text, 
                           key=f"remove_city_{idx}", 
                           help=f"Remove {city}"):
                    st.session_state['current_cities'].remove(city)
                    st.experimental_rerun()
            
            # Show preferred cities
            for idx, city in enumerate(preferred_cities):
                # Truncate long city names
                display_city = city[:10] + "..." if len(city) > 10 else city
                button_text = f"★ ✕ {display_city}"
                if st.button(button_text, 
                           key=f"remove_pref_city_{idx}", 
                           help=f"Remove preferred location {city}"):
                    st.session_state['preferred_cities'].remove(city)
                    st.experimental_rerun()