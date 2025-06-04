"""
Search form component for ResDex Agent UI.
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
        col1, col2 = st.columns([3, 1])
        
        with col1:
            company = st.text_input(
                "Company Name *",
                value=self.session_state.get('recruiter_company', ''),
                placeholder="e.g., TCS, Infosys, Google",
                help="Enter your company name (required for search)"
            )
            self.session_state['recruiter_company'] = company
        
        with col2:
            if company.strip():
                st.markdown("""
                <div style="margin-top: 1.5rem; color: #28a745;">
                    ✅ Company set
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="margin-top: 1.5rem; color: #dc3545;">
                    ⚠️ Required
                </div>
                """, unsafe_allow_html=True)
    
    def render_keywords_section(self):
        """Render keywords/skills input section."""
        st.markdown("**Skills & Keywords**")
        
        # Skill input form
        with st.form(key="skill_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                skill_input = st.selectbox(
                    "Add skill",
                    [""] + TECH_SKILLS[:50],  # Show top 50 skills
                    help="Select a skill to add to your search"
                )
            
            with col2:
                is_mandatory = st.checkbox(
                    "Mandatory",
                    help="Mandatory skills must be present in candidate profiles"
                )
            
            skill_submitted = st.form_submit_button("Add Skill")
            
            if skill_submitted and skill_input:
                keywords = self.session_state.get('keywords', [])
                skill_to_add = f"★ {skill_input}" if is_mandatory else skill_input
                
                # Check if skill already exists
                existing_skills = [kw.replace('★ ', '') for kw in keywords]
                if skill_input not in existing_skills:
                    keywords.append(skill_to_add)
                    self.session_state['keywords'] = keywords
                    st.experimental_rerun()
        
        # Display current skills
        if self.session_state.get('keywords'):
            st.markdown("**Current Skills:**")
            for idx, keyword in enumerate(self.session_state['keywords']):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    is_mandatory = keyword.startswith('★ ')
                    display_skill = keyword.replace('★ ', '')
                    
                    if is_mandatory:
                        st.markdown(f"""
                        <span class="skill-tag mandatory-skill">
                            ⭐ {display_skill}
                        </span>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <span class="skill-tag">
                            {display_skill}
                        </span>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌", key=f"remove_skill_{idx}", help=f"Remove {display_skill}"):
                        keywords = self.session_state['keywords']
                        keywords.pop(idx)
                        self.session_state['keywords'] = keywords
                        st.experimental_rerun()
    
    def render_experience_section(self):
        """Render experience range input."""
        st.markdown("**Experience Range**")
        
        min_exp = st.number_input(
            "Min Years",
            min_value=0.0,
            max_value=50.0,
            value=self.session_state.get('min_exp', 0.0),
            step=0.5,
            help="Minimum years of experience"
        )
        
        max_exp = st.number_input(
            "Max Years",
            min_value=0.0,
            max_value=50.0,
            value=self.session_state.get('max_exp', 10.0),
            step=0.5,
            help="Maximum years of experience"
        )
        
        self.session_state['min_exp'] = min_exp
        self.session_state['max_exp'] = max_exp
        
        # Validation feedback
        if min_exp > max_exp:
            st.error("Min experience cannot be greater than max experience")
    
    def render_location_section(self):
        """Render location input section."""
        st.markdown("**Locations**")
        
        # Location input form
        with st.form(key="location_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                location_input = st.selectbox(
                    "Add location",
                    [""] + CITIES[:30],  # Show top 30 cities
                    help="Select a city to add to your search"
                )
            
            with col2:
                is_preferred = st.checkbox(
                    "Preferred",
                    help="Preferred locations get higher priority in search"
                )
            
            location_submitted = st.form_submit_button("Add Location")
            
            if location_submitted and location_input:
                if is_preferred:
                    preferred_cities = self.session_state.get('preferred_cities', [])
                    if location_input not in preferred_cities:
                        preferred_cities.append(location_input)
                        self.session_state['preferred_cities'] = preferred_cities
                else:
                    current_cities = self.session_state.get('current_cities', [])
                    if location_input not in current_cities:
                        current_cities.append(location_input)
                        self.session_state['current_cities'] = current_cities
                
                st.experimental_rerun()
        
        # Display current locations
        all_locations = []
        for city in self.session_state.get('current_cities', []):
            all_locations.append((city, False))
        for city in self.session_state.get('preferred_cities', []):
            all_locations.append((city, True))
        
        if all_locations:
            st.markdown("**Current Locations:**")
            for idx, (city, is_preferred) in enumerate(all_locations):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if is_preferred:
                        st.markdown(f"⭐ {city} (Preferred)")
                    else:
                        st.markdown(f"📍 {city}")
                
                with col2:
                    if st.button("❌", key=f"remove_location_{idx}", help=f"Remove {city}"):
                        if is_preferred:
                            preferred = self.session_state['preferred_cities']
                            preferred.remove(city)
                            self.session_state['preferred_cities'] = preferred
                        else:
                            current = self.session_state['current_cities']
                            current.remove(city)
                            self.session_state['current_cities'] = current
                        st.experimental_rerun()
    
    def render_salary_section(self):
        """Render salary range input."""
        st.markdown("**Salary Range (Lakhs)**")
        
        min_salary = st.number_input(
            "Min Salary",
            min_value=0.0,
            max_value=100.0,
            value=self.session_state.get('min_salary', 0.0),
            step=0.5,
            help="Minimum salary in lakhs per annum"
        )
        
        max_salary = st.number_input(
            "Max Salary",
            min_value=0.0,
            max_value=100.0,
            value=self.session_state.get('max_salary', 15.0),
            step=0.5,
            help="Maximum salary in lakhs per annum"
        )
        
        self.session_state['min_salary'] = min_salary
        self.session_state['max_salary'] = max_salary
        
        # Validation feedback
        if min_salary > max_salary:
            st.error("Min salary cannot be greater than max salary")
    
    def validate_form(self) -> List[str]:
        """Validate the search form and return list of errors."""
        errors = []
        
        # Check required fields
        if not self.session_state.get('recruiter_company', '').strip():
            errors.append("Company name is required")
        
        if not self.session_state.get('keywords', []):
            errors.append("At least one skill/keyword is required")
        
        # Validate ranges
        if self.session_state.get('min_exp', 0) > self.session_state.get('max_exp', 10):
            errors.append("Minimum experience cannot be greater than maximum experience")
        
        if self.session_state.get('min_salary', 0) > self.session_state.get('max_salary', 15):
            errors.append("Minimum salary cannot be greater than maximum salary")
        
        return errors