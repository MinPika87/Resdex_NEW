# resdx_agent/ui/components/facet_display.py - PURE STREAMLIT VERSION
"""
Facet Display - Using Pure Streamlit Components (No HTML rendering issues)
"""

import streamlit as st #type: ignore
from typing import Dict, Any, List
import hashlib

class FacetDisplay:
    """Component for displaying facet title cards using only native Streamlit components."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
        
        # Category type mapping for emoji selection
        self.category_emojis = {
            # Data & Analytics
            "data": "📊",
            "science": "🔬", 
            "analytics": "📈",
            "visualization": "📉",
            
            # Programming & Development
            "java": "☕",
            "python": "🐍",
            "development": "💻",
            "programming": "⌨️",
            "backend": "🔧",
            "full": "🔨",
            "stack": "📚",
            
            # Leadership & Management
            "leadership": "👑",
            "senior": "🎖️",
            "lead": "🎯",
            "architect": "🏗️",
            "management": "📋",
            
            # Cloud & Infrastructure
            "cloud": "☁️",
            "deployment": "🚀",
            "integration": "🔗",
            "api": "🌐",
            "microservices": "⚙️",
            
            # Experience & Skills
            "experience": "💼",
            "skills": "🛠️",
            "expert": "⭐",
            "specialist": "🎓",
            "experienced": "📊",
            
            # Machine Learning & AI
            "machine": "🤖",
            "learning": "🧠", 
            "ai": "🤖",
            "nlp": "💬",
            "generative": "✨",
            
            # Corporate & Organizations
            "corporate": "🏢",
            "startup": "🚀",
            "top": "🏆",
            "organizations": "🏛️",
            "firms": "🏢",
            "mnc": "🌍",
            
            # Job Roles
            "roles": "👔",
            "job": "💼",
            "position": "📍",
            "relevant": "🎯"
        }
    
    def render_facets_in_sidebar(self, facets_data: Dict[str, Any]):
        """Render facet title cards in sidebar using native Streamlit."""
        if not facets_data:
            return
        
        st.markdown("---")
        st.markdown("### 🔍 **Facet Categories**")
        
        # Get primary and secondary facets
        primary_facets = facets_data.get("result_1", {})
        secondary_facets = facets_data.get("result_2", {})
        
        total_categories = len(primary_facets) + len(secondary_facets)
        
        if total_categories > 0:
            st.info(f"📊 {total_categories} categories generated")
            
            # Render primary categories
            if primary_facets:
                st.markdown("**🎯 Primary Categories:**")
                self._render_categories_native(primary_facets)
            
            # Render secondary categories  
            if secondary_facets:
                st.markdown("**📈 Additional Categories:**")
                self._render_categories_native(secondary_facets)
        else:
            st.warning("No categories available")
    
    def _render_categories_native(self, facets: Dict[str, Any]):
        """Render categories using native Streamlit containers in 2-column layout."""
        
        if not facets:
            return
        
        category_names = list(facets.keys())
        
        # Process categories in pairs for 2-column layout
        for i in range(0, len(category_names), 2):
            # Get categories for this row
            left_category = category_names[i] if i < len(category_names) else None
            right_category = category_names[i + 1] if i + 1 < len(category_names) else None
            
            # Use Streamlit columns for layout
            col1, col2 = st.columns(2)
            
            # Left column
            if left_category:
                with col1:
                    self._render_single_category_native(left_category, facets[left_category])
            
            # Right column
            if right_category:
                with col2:
                    self._render_single_category_native(right_category, facets[right_category])
    
    def _render_single_category_native(self, category_name: str, category_data: Dict[str, Any]):
        """Render a single category using native Streamlit components."""
        
        # Get emoji and count
        emoji = self._get_category_emoji(category_name)        
        # Determine category type for styling
        category_type = self._get_category_type(category_name)
        
        # Create category card using appropriate Streamlit component
        if category_type == "primary_tech":
            st.success(f"""
            {emoji} **{category_name}**""")
        elif category_type == "leadership":
            st.info(f"""
            {emoji} **{category_name}**""")
        elif category_type == "experience":
            st.warning(f"""
            {emoji} **{category_name}**""")
        elif category_type == "corporate":
            st.error(f"""
            {emoji} **{category_name}**""")
        else:
            # Default styling
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: #f0f2f6;
                    padding: 10px;
                    border-radius: 5px;
                    border-left: 4px solid #1f77b4;
                    margin: 2px 0;
                ">
                    <strong>{emoji} {category_name}</strong><br>
                </div>
                """, unsafe_allow_html=True)
    
    def _get_category_type(self, category_name: str) -> str:
        """Determine category type for styling."""
        category_lower = category_name.lower()
        
        # Technical/Programming categories
        if any(word in category_lower for word in ["java", "python", "development", "programming", "backend", "full", "stack", "machine", "learning", "ai", "data", "science"]):
            return "primary_tech"
        
        # Leadership categories
        elif any(word in category_lower for word in ["leadership", "senior", "lead", "architect", "management"]):
            return "leadership"
        
        # Experience categories
        elif any(word in category_lower for word in ["experience", "skills", "expert", "specialist", "experienced"]):
            return "experience"
        
        # Corporate categories
        elif any(word in category_lower for word in ["corporate", "startup", "top", "organizations", "firms", "mnc"]):
            return "corporate"
        
        # Default
        else:
            return "default"
    
    def _get_category_emoji(self, category_name: str) -> str:
        """Get emoji for category based on name keywords."""
        category_lower = category_name.lower()
        
        # Check for keywords in category name
        for keyword, emoji in self.category_emojis.items():
            if keyword in category_lower:
                return emoji
        
        # Default emoji
        return "📁"