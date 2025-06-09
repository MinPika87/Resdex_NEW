"""
Pagination components for candidate results - EXACT match to your original but fixed for Streamlit v1.12.0
"""

import streamlit as st#type: ignore
from resdex_agent.utils.constants import UI_CONFIG

class Pagination:
    """Handles pagination UI and logic - EXACT match to your original"""
    
    def __init__(self, session_state):
        self.session_state = session_state
        self.page_size = UI_CONFIG["pagination_size"]
    
    def display_pagination_with_chat_context(self):
        """Display pagination with chat-friendly context - Fixed for no nested columns"""
        candidates = st.session_state.get('candidates', [])
        if not candidates:
            return
        
        current_page = st.session_state.get('page', 0)
        start_idx = current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(candidates))
        total_pages = (len(candidates) - 1) // self.page_size + 1
        
        pagination_container = st.container()
        with pagination_container:
            # NO NESTED COLUMNS - Use sequential layout instead
            
            # Previous button
            if st.button("◀ Previous", key="prev_page", disabled=(current_page <= 0)):
                if current_page > 0:
                    st.session_state['page'] = current_page - 1
                    # Add AI message about navigation
                    ai_message = f"Moved to page {current_page}. Showing candidates {(current_page - 1) * self.page_size + 1}-{min(current_page * self.page_size, len(candidates))}."
                    st.session_state.setdefault('chat_history', []).append({"role": "assistant", "content": ai_message})
                    st.experimental_rerun()
            
            # Page info
            st.write(f"Showing {start_idx+1}-{end_idx} of {len(candidates)} profiles (Page {current_page + 1} of {total_pages})")
            total_results = st.session_state.get('total_results', 0)
            if total_results > 0:
                st.write(f"Total search results: {total_results:,}")
            
            # Next button
            if st.button("Next ▶", key="next_page", disabled=((current_page + 1) * self.page_size >= len(candidates))):
                if (current_page + 1) * self.page_size < len(candidates):
                    st.session_state['page'] = current_page + 1
                    # Add AI message about navigation
                    ai_message = f"Moved to page {current_page + 2}. Showing candidates {(current_page + 1) * self.page_size + 1}-{min((current_page + 2) * self.page_size, len(candidates))}."
                    st.session_state.setdefault('chat_history', []).append({"role": "assistant", "content": ai_message})
                    st.experimental_rerun()
    
    def get_current_page_candidates(self):
        """Get candidates for current page - EXACT match"""
        candidates = st.session_state.get('candidates', [])
        current_page = st.session_state.get('page', 0)
        start_idx = current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(candidates))
        
        return candidates[start_idx:end_idx], start_idx
    
    def reset_to_first_page(self):
        """Reset pagination to first page - EXACT match"""
        st.session_state['page'] = 0
    
    def get_pagination_info(self):
        """Get current pagination information - EXACT match"""
        candidates = st.session_state.get('candidates', [])
        current_page = st.session_state.get('page', 0)
        total_pages = (len(candidates) - 1) // self.page_size + 1 if candidates else 0
        
        return {
            "current_page": current_page + 1,  # 1-based for display
            "total_pages": total_pages,
            "total_candidates": len(candidates),
            "showing_start": current_page * self.page_size + 1,
            "showing_end": min((current_page + 1) * self.page_size, len(candidates))
        }