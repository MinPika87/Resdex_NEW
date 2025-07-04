"""
Candidate display component for ResDex Agent UI - Cleaned version without unwanted elements
"""

import streamlit as st
from typing import Dict, Any, List


class CandidateDisplay:
    """Component for displaying candidate search results."""
    
    def __init__(self, session_state: Dict[str, Any]):
        self.session_state = session_state
        self.page_size = 5
    
    def render_results(self):
        """Render the complete results section - FIXED for batch display system."""
        candidates = self.session_state.get('displayed_candidates', [])
        total_results = self.session_state.get('total_results', 0)
        all_candidates_count = len(self.session_state.get('all_candidates', []))
        selected_keywords = self.session_state.get('selected_keywords', [])
        
        # Results header with batch info
        self._render_results_header_with_batch_info(total_results, selected_keywords, len(candidates), all_candidates_count)
        
        # FIXED: Pagination - 5 per page consistently
        page_size = 5
        current_page = self.session_state.get('page', 0)
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(candidates))
        
        # Get current page candidates
        page_candidates = candidates[start_idx:end_idx]
        
        # Display candidates
        for i, candidate in enumerate(page_candidates, start=start_idx + 1):
            self._render_candidate_card(candidate, i)
        
        # Pagination controls
        self._render_pagination_controls_with_batch_info(len(candidates), page_size)

    def _render_results_header_with_batch_info(self, total_results: int, selected_keywords: List[str], displayed_count: int, fetched_count: int):
        """Render results header with complete filter information."""
        # Build comprehensive filter summary
        filter_parts = []
        
        # Skills
        if selected_keywords:
            skills_text = ", ".join([kw.replace("★ ", "") for kw in selected_keywords])
            filter_parts.append(f"Skills: {skills_text}")
        
        # Experience range
        min_exp = self.session_state.get('min_exp', 0)
        max_exp = self.session_state.get('max_exp', 10)
        if min_exp > 0 or max_exp < 50:
            filter_parts.append(f"Experience: {min_exp}-{max_exp} years")
        
        # Salary range
        min_sal = self.session_state.get('min_salary', 0)
        max_sal = self.session_state.get('max_salary', 15)
        if min_sal > 0 or max_sal < 100:
            filter_parts.append(f"Salary: {min_sal}-{max_sal} lakhs")
        
        # Locations
        current_cities = self.session_state.get('current_cities', [])
        preferred_cities = self.session_state.get('preferred_cities', [])
        all_locations = current_cities + preferred_cities
        if all_locations:
            locations_text = ", ".join(list(dict.fromkeys(all_locations)))  # Remove duplicates
            filter_parts.append(f"Locations: {locations_text}")
        
        # Target Companies
        target_companies = self.session_state.get('target_companies', [])
        if target_companies:
            companies_text = ", ".join(target_companies)
            filter_parts.append(f"Target Companies: {companies_text}")
        
        # Create the filter summary
        if filter_parts:
            filters_summary = " | ".join(filter_parts)
        else:
            filters_summary = "All candidates"
        
        # Main result summary with complete filters
        st.markdown(f"""
        <div style="color: #1f77b4; font-weight: bold; font-size: 1.1rem; margin-bottom: 0.5rem;">
            🎯 AI Found: {total_results:,} total matches for {filters_summary}
        </div>
        """, unsafe_allow_html=True)

    def _render_pagination_controls_with_batch_info(self, total_candidates: int, page_size: int):
        """Render pagination controls with batch information."""
        if total_candidates <= page_size:
            return
        
        current_page = self.session_state.get('page', 0)
        total_pages = (total_candidates - 1) // page_size + 1
        
        st.markdown("---")
        
        # Previous button
        if st.button("⬅️ Previous", disabled=current_page <= 0):
            self.session_state['page'] = max(0, current_page - 1)
            st.experimental_rerun()
        
        # Page info with batch context
        start_idx = current_page * page_size + 1
        end_idx = min((current_page + 1) * page_size, total_candidates)
        all_candidates_count = len(self.session_state.get('all_candidates', []))
        
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem;">
            Showing {start_idx}-{end_idx} of {total_candidates} displayed candidates<br>
            <small>Page {current_page + 1} of {total_pages} | {all_candidates_count} fetched total</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Next button
        if st.button("Next ➡️", disabled=(current_page + 1) * page_size >= total_candidates):
            self.session_state['page'] = current_page + 1
            st.experimental_rerun()
        
    
    def _render_results_header(self, total_results: int, selected_keywords: List[str]):
        """Render results header with summary (REMOVED save search button)."""
        keywords_text = ", ".join([kw.replace("★ ", "") for kw in selected_keywords])
        st.markdown(f"""
        <div style="color: #1f77b4; font-weight: bold; font-size: 1.1rem; margin-bottom: 1rem;">
            🎯 AI found: {total_results:,} profiles for {keywords_text}
        </div>
        """, unsafe_allow_html=True)
        
    
    def _render_candidate_card(self, candidate: Dict[str, Any], index: int):
        """Render a single candidate card (CLEANED VERSION)."""
        with st.container():
            st.markdown(f"""
            <div class="candidate-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center;">
                        <h4 style="margin: 0; color: #2c3e50;">{candidate.get('name', 'Unknown')}</h4>
                        <span style="margin-left: 1rem; color: #27ae60; font-weight: bold;">₹{candidate.get('salary', 0)} Lakhs</span>
                        <span style="margin-left: 1rem; color: #7f8c8d;">📍 {candidate.get('current_location', 'Not specified')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            self._render_professional_details(candidate)
            
            self._render_skills_section(candidate)
            
            self._render_preferred_locations(candidate)
            
            st.markdown("</div>", unsafe_allow_html=True)
    def _render_professional_details(self, candidate: Dict[str, Any]):
        """Render professional experience details with light highlighting."""
        current_role = candidate.get('current_role', 'Not specified')
        current_company = candidate.get('current_company', 'Not specified')
        education = candidate.get('education_display', 'Not specified')
        experience = candidate.get('experience', 0)
        
        # Get ALL search criteria for highlighting
        selected_keywords = self.session_state.get('selected_keywords', [])
        target_companies = self.session_state.get('target_companies', [])
        
        # Check if current role should be highlighted (skills match)
        role_highlighted = False
        for kw in selected_keywords:
            clean_kw = kw.replace('★ ', '').lower()
            if clean_kw in current_role.lower():
                role_highlighted = True
                break
        
        # Check if current company should be highlighted (company match)
        company_highlighted = False
        for company in target_companies:
            if company.lower() in current_company.lower():
                company_highlighted = True
                break
        
        # Apply light highlighting, no bold
        if role_highlighted:
            current_role_html = f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{current_role}</span>'
        else:
            current_role_html = current_role
        
        if company_highlighted:
            current_company_html = f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{current_company}</span>'
        else:
            current_company_html = current_company
        
        # Check experience range highlighting
        min_exp = self.session_state.get('min_exp', 0)
        max_exp = self.session_state.get('max_exp', 10)
        experience_highlighted = False
        
        if (min_exp > 0 or max_exp < 50) and min_exp <= experience <= max_exp:
            experience_highlighted = True
        
        if experience_highlighted:
            experience_html = f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">({experience} years exp)</span>'
        else:
            experience_html = f'({experience} years exp)'
        
        st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <strong>Current:</strong> {current_role_html} at {current_company_html} {experience_html}
        </div>
        <div style="margin: 0.5rem 0;">
            <strong>Education:</strong> {education}
        </div>
        """, unsafe_allow_html=True)
    def _render_skills_section(self, candidate: Dict[str, Any]):
        """Render candidate skills with comprehensive highlighting - Light yellow, no bold."""
        skills = candidate.get('skills', [])
        may_also_know = candidate.get('may_also_know', [])
        
        # Get ALL search criteria for highlighting
        selected_keywords = self.session_state.get('selected_keywords', [])
        target_companies = self.session_state.get('target_companies', [])
        current_cities = self.session_state.get('current_cities', [])
        preferred_cities = self.session_state.get('preferred_cities', [])
        
        # Prepare highlight terms (normalize for case-insensitive matching)
        highlight_terms = []
        
        # Add skills from search
        for kw in selected_keywords:
            clean_kw = kw.replace('★ ', '').lower()
            highlight_terms.append(clean_kw)
        
        # Add target companies
        for company in target_companies:
            highlight_terms.append(company.lower())
        
        # Add locations
        for location in current_cities + preferred_cities:
            highlight_terms.append(location.lower())
        
        print(f"🔍 Highlight terms: {highlight_terms}")  # Debug
        
        if skills:
            st.markdown("**Key Skills:**")
            skills_html = ""
            
            for skill in skills[:12]:  # Show up to 12 main skills
                should_highlight = any(term in skill.lower() for term in highlight_terms)
                
                if should_highlight:
                    # Light yellow background, no bold
                    skills_html += f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin: 0.125rem; display: inline-block; font-size: 0.875rem;">{skill}</span>'
                else:
                    skills_html += f'<span class="skill-tag">{skill}</span>'
            
            st.markdown(skills_html, unsafe_allow_html=True)
        
        if may_also_know:
            st.markdown("**May also know:**")
            may_know_html = ""
            
            for skill in may_also_know[:5]:  # Show up to 5 additional skills
                should_highlight = any(term in skill.lower() for term in highlight_terms)
                
                if should_highlight:
                    # Light yellow background, no bold
                    may_know_html += f'<span style="background-color: #fff9c4; border: 1px solid #f0e68c; padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin: 0.125rem; display: inline-block; font-size: 0.875rem;">{skill}</span>'
                else:
                    may_know_html += f'<span style="background-color: white; border: 1px solid #dee2e6; padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin: 0.125rem; display: inline-block; font-size: 0.875rem;">{skill}</span>'
            
            if len(may_also_know) > 5:
                may_know_html += f'<span style="color: #007bff; font-size: 0.875rem; margin-left: 0.5rem;">+{len(may_also_know) - 5} more</span>'
            
            st.markdown(may_know_html, unsafe_allow_html=True)
    
    def _render_preferred_locations(self, candidate: Dict[str, Any]):
        """Render preferred locations with light highlighting."""
        current_loc = candidate.get('current_location', 'Not specified')
        pref_locs = candidate.get('preferred_locations', [])
        
        # Get search locations for highlighting
        search_locations = self.session_state.get('current_cities', []) + self.session_state.get('preferred_cities', [])
        search_locations_lower = [loc.lower() for loc in search_locations]
        
        # Highlight current location if it matches search - light yellow, no bold
        current_highlighted = any(current_loc.lower() == search_loc for search_loc in search_locations_lower)
        if current_highlighted:
            current_loc_html = f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{current_loc}</span>'
        else:
            current_loc_html = current_loc
        
        locations_html = current_loc_html
        
        if pref_locs:
            other_locs = [loc for loc in pref_locs if loc != current_loc][:3]
            if other_locs:
                other_locs_html = []
                for loc in other_locs:
                    loc_highlighted = any(loc.lower() == search_loc for search_loc in search_locations_lower)
                    if loc_highlighted:
                        other_locs_html.append(f'<span style="background-color: #fff9c4; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{loc}</span>')
                    else:
                        other_locs_html.append(loc)
                
                locations_html += f", {', '.join(other_locs_html)}"
                
                if len(pref_locs) > 4:
                    locations_html += f" +{len(pref_locs) - 4} more"
        
        st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <strong>Preferred locations:</strong> {locations_html}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_pagination_controls(self, total_candidates: int):
        """Render pagination controls."""
        if total_candidates <= self.page_size:
            return
        
        current_page = self.session_state.get('page', 0)
        total_pages = (total_candidates - 1) // self.page_size + 1
        
        st.markdown("---")
        
        # Previous button
        if st.button("⬅️ Previous", disabled=current_page <= 0):
            self.session_state['page'] = max(0, current_page - 1)
            st.experimental_rerun()
        
        # Page info
        start_idx = current_page * self.page_size + 1
        end_idx = min((current_page + 1) * self.page_size, total_candidates)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem;">
            Showing {start_idx}-{end_idx} of {total_candidates} candidates<br>
            <small>Page {current_page + 1} of {total_pages}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Next button
        if st.button("Next ➡️", disabled=(current_page + 1) * self.page_size >= total_candidates):
            self.session_state['page'] = current_page + 1
            st.experimental_rerun()