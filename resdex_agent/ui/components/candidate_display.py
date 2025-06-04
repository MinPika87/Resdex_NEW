"""
Candidate display component for ResDex Agent UI.
"""

import streamlit as st
from typing import Dict, Any, List


class CandidateDisplay:
    """Component for displaying candidate search results."""
    
    def __init__(self, session_state: Dict[str, Any]):
        self.session_state = session_state
        self.page_size = 5
    
    def render_results(self):
        """Render the complete results section."""
        candidates = self.session_state.get('candidates', [])
        total_results = self.session_state.get('total_results', 0)
        selected_keywords = self.session_state.get('selected_keywords', [])
        
        # Results header
        self._render_results_header(total_results, selected_keywords)
        
        # Pagination info
        current_page = self.session_state.get('page', 0)
        start_idx = current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(candidates))
        page_candidates = candidates[start_idx:end_idx]
        
        # Display candidates
        for i, candidate in enumerate(page_candidates, start=start_idx + 1):
            self._render_candidate_card(candidate, i)
        
        # Pagination controls
        self._render_pagination_controls(len(candidates))
    
    def _render_results_header(self, total_results: int, selected_keywords: List[str]):
        """Render results header with summary."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            keywords_text = ", ".join([kw.replace("★ ", "") for kw in selected_keywords])
            st.markdown(f"""
            <div style="color: #1f77b4; font-weight: bold; font-size: 1.1rem;">
                🎯 AI found: {total_results:,} profiles for {keywords_text}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("💾 Save Search"):
                st.success("Search saved successfully!")
    
    def _render_candidate_card(self, candidate: Dict[str, Any], index: int):
        """Render a single candidate card."""
        with st.container():
            st.markdown(f"""
            <div class="candidate-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center;">
                        <input type="checkbox" style="margin-right: 0.5rem;">
                        <h4 style="margin: 0; color: #2c3e50;">{candidate.get('name', 'Unknown')}</h4>
                        <span style="margin-left: 1rem; color: #27ae60; font-weight: bold;">₹{candidate.get('salary', 0)} Lakhs</span>
                        <span style="margin-left: 1rem; color: #7f8c8d;">📍 {candidate.get('current_location', 'Not specified')}</span>
                    </div>
                    <div>
                        <span style="cursor: pointer;">⬆️</span>
                        <span style="cursor: pointer; margin-left: 0.5rem;">💾</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Professional details
            self._render_professional_details(candidate)
            
            # Skills section
            self._render_skills_section(candidate)
            
            # Preferred locations
            self._render_preferred_locations(candidate)
            
            # Action buttons
            self._render_action_buttons(candidate, index)
            
            # Footer stats
            self._render_candidate_footer(candidate)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_professional_details(self, candidate: Dict[str, Any]):
        """Render professional experience details."""
        current_role = candidate.get('current_role', 'Not specified')
        current_company = candidate.get('current_company', 'Not specified')
        previous_role = candidate.get('previous_role', 'Not specified')
        previous_company = candidate.get('previous_company', 'Not specified')
        education = candidate.get('education_display', 'Not specified')
        experience = candidate.get('experience', 0)
        
        # Highlight ML/AI related roles
        ml_keywords = ["Machine Learning", "Data Science", "AI", "Analytics", "ML Engineer"]
        should_highlight = any(keyword.lower() in current_role.lower() for keyword in ml_keywords)
        
        if should_highlight:
            current_html = f'<span style="background-color: #fff3cd; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{current_role}</span>'
        else:
            current_html = current_role
        
        st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <strong>Current:</strong> {current_html} at {current_company} ({experience} years exp)
        </div>
        <div style="margin: 0.5rem 0;">
            <strong>Previous:</strong> {previous_role} at {previous_company}
        </div>
        <div style="margin: 0.5rem 0;">
            <strong>Education:</strong> {education}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_skills_section(self, candidate: Dict[str, Any]):
        """Render candidate skills with highlighting."""
        skills = candidate.get('skills', [])
        may_also_know = candidate.get('may_also_know', [])
        selected_keywords = self.session_state.get('selected_keywords', [])
        
        # Clean selected keywords for comparison
        search_keywords = [kw.replace('★ ', '').lower() for kw in selected_keywords]
        
        if skills:
            st.markdown("**Key Skills:**")
            skills_html = ""
            
            for skill in skills[:12]:  # Show up to 12 main skills
                should_highlight = any(search_kw in skill.lower() for search_kw in search_keywords)
                
                if should_highlight:
                    skills_html += f'<span style="background-color: #ffeb3b; padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin: 0.125rem; display: inline-block; font-size: 0.875rem;">{skill}</span>'
                else:
                    skills_html += f'<span class="skill-tag">{skill}</span>'
            
            st.markdown(skills_html, unsafe_allow_html=True)
        
        if may_also_know:
            st.markdown("**May also know:**")
            may_know_html = ""
            
            for skill in may_also_know[:5]:  # Show up to 5 additional skills
                may_know_html += f'<span style="background-color: white; border: 1px solid #dee2e6; padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin: 0.125rem; display: inline-block; font-size: 0.875rem;">{skill}</span>'
            
            if len(may_also_know) > 5:
                may_know_html += f'<span style="color: #007bff; font-size: 0.875rem; margin-left: 0.5rem;">+{len(may_also_know) - 5} more</span>'
            
            st.markdown(may_know_html, unsafe_allow_html=True)
    
    def _render_preferred_locations(self, candidate: Dict[str, Any]):
        """Render preferred locations."""
        current_loc = candidate.get('current_location', 'Not specified')
        pref_locs = candidate.get('preferred_locations', [])
        
        locations_text = current_loc
        if pref_locs:
            other_locs = [loc for loc in pref_locs if loc != current_loc][:3]
            if other_locs:
                locations_text += f", {', '.join(other_locs)}"
                if len(pref_locs) > 4:
                    locations_text += f" +{len(pref_locs) - 4} more"
        
        st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <strong>Preferred locations:</strong> {locations_text}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_action_buttons(self, candidate: Dict[str, Any], index: int):
        """Render action buttons for candidate."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📞 View Phone", key=f"phone_{index}"):
                st.info("Phone number revealed!")
        
        with col2:
            if st.button("💬 Call Candidate", key=f"call_{index}"):
                st.info("Initiating call...")
        
        with col3:
            if st.button("📧 Send Email", key=f"email_{index}"):
                st.info("Email composer opened!")
    
    def _render_candidate_footer(self, candidate: Dict[str, Any]):
        """Render candidate footer with stats and actions."""
        views = candidate.get('views', 0)
        applications = candidate.get('applications', 0)
        last_modified = candidate.get('last_modified', '2025-01-01')
        last_active = candidate.get('last_active', '2025-01-01')
        similar_profiles = candidate.get('similar_profiles', 100)
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 0.5rem; border-top: 1px solid #e9ecef;">
            <div style="font-size: 0.875rem; color: #6c757d;">
                👁️ {views} views • 📄 {applications} applications • Modified {last_modified[:10]} • Active {last_active[:10]}
            </div>
            <div style="font-size: 0.875rem;">
                <a href="#" style="color: #007bff; text-decoration: none; margin-right: 1rem;">Comment</a>
                <a href="#" style="color: #007bff; text-decoration: none;">Save</a>
            </div>
        </div>
        <div style="margin-top: 0.25rem;">
            <a href="#" style="color: #007bff; text-decoration: none; font-size: 0.875rem;">{similar_profiles} similar profiles</a>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_pagination_controls(self, total_candidates: int):
        """Render pagination controls."""
        if total_candidates <= self.page_size:
            return
        
        current_page = self.session_state.get('page', 0)
        total_pages = (total_candidates - 1) // self.page_size + 1
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_page <= 0):
                self.session_state['page'] = max(0, current_page - 1)
                st.experimental_rerun()
        
        with col2:
            start_idx = current_page * self.page_size + 1
            end_idx = min((current_page + 1) * self.page_size, total_candidates)
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                Showing {start_idx}-{end_idx} of {total_candidates} candidates<br>
                <small>Page {current_page + 1} of {total_pages}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("Next ➡️", disabled=(current_page + 1) * self.page_size >= total_candidates):
                self.session_state['page'] = current_page + 1
                st.experimental_rerun()