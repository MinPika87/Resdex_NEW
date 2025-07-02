# resdx_agent/ui/components/facet_display.py - NEW FILE
"""
Facet Display Component for beautiful facet visualization and interaction.
"""

import streamlit as st #type: ignore
import asyncio
from typing import Dict, Any, List

class FacetDisplay:
    """Component for displaying and interacting with facets."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent):
        self.session_state = session_state
        self.root_agent = root_agent
        
        # Facet color mapping for different categories
        self.facet_colors = {
            # Skills-related facets (Blue tones)
            "skills": "#3498db",
            "technical": "#2980b9", 
            "programming": "#3498db",
            "expertise": "#5dade2",
            
            # Job roles/titles (Green tones)
            "roles": "#27ae60",
            "titles": "#2ecc71",
            "positions": "#58d68d",
            "designations": "#82e5aa",
            
            # Organizations (Orange tones)
            "organizations": "#e67e22",
            "companies": "#f39c12",
            "employers": "#f5b041",
            
            # Experience/Level (Purple tones)
            "experience": "#8e44ad",
            "level": "#9b59b6",
            "seniority": "#bb8fce",
            
            # Default (Gray)
            "default": "#95a5a6"
        }
    
    def render_facets(self, facets_data: Dict[str, Any]):
        """Render facets in a beautiful, interactive layout."""
        if not facets_data:
            return
        
        st.markdown("### 🔍 **Search Refinement Facets**")
        st.markdown("*Click any facet below to add it to your search filters*")
        
        # Get primary and secondary facets
        primary_facets = facets_data.get("result_1", {})
        secondary_facets = facets_data.get("result_2", {})
        
        if primary_facets:
            st.markdown("#### 📊 **Primary Facets**")
            self._render_facet_group(primary_facets, "primary")
        
        if secondary_facets:
            st.markdown("#### 📈 **Additional Facets**")
            self._render_facet_group(secondary_facets, "secondary")
    
    def _render_facet_group(self, facets: Dict[str, Any], group_type: str):
        """Render a group of facets with beautiful styling."""
        
        # Convert facets to list for easier handling
        facet_items = list(facets.items())
        
        # Render in rows of 2 facet categories each (since nested columns aren't supported)
        for i in range(0, len(facet_items), 2):
            col1, col2 = st.columns(2)
            
            # First facet in the row
            if i < len(facet_items):
                category_name, category_data = facet_items[i]
                with col1:
                    self._render_single_facet_category(category_name, category_data, group_type)
            
            # Second facet in the row (if exists)
            if i + 1 < len(facet_items):
                category_name, category_data = facet_items[i + 1]
                with col2:
                    self._render_single_facet_category(category_name, category_data, group_type)
    
    def _render_single_facet_category(self, category_name: str, category_data: Dict[str, Any], group_type: str):
        """Render a single facet category with clickable items."""
        
        # Determine color based on category name
        color = self._get_facet_color(category_name)
        
        # Create container with colored border
        st.markdown(f"""
        <div style="
            border-left: 4px solid {color};
            background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h5 style="
                color: {color};
                margin: 0 0 8px 0;
                font-weight: 600;
                font-size: 14px;
            ">{category_name}</h5>
        </div>
        """, unsafe_allow_html=True)
        
        # Extract facet items
        facet_items = self._extract_facet_items(category_data)
        
        if facet_items:
            # Show first few items as buttons
            for i, item in enumerate(facet_items[:4]):  # Limit to 4 items per category
                if st.button(
                    f"➕ {item}", 
                    key=f"facet_{group_type}_{category_name}_{i}",
                    help=f"Add '{item}' to your search filters"
                ):
                    asyncio.run(self._add_facet_to_filters(item, category_name))
            
            # Show "..." if there are more items
            if len(facet_items) > 4:
                if st.button(
                    f"... +{len(facet_items) - 4} more", 
                    key=f"facet_more_{group_type}_{category_name}",
                    help=f"Show all items in {category_name}"
                ):
                    self._show_all_facet_items(category_name, facet_items, color)
        else:
            st.markdown("*No items available*")
    
    def _show_all_facet_items(self, category_name: str, all_items: List[str], color: str):
        """Show all items in a facet category in an expander."""
        with st.expander(f"All items in {category_name} ({len(all_items)} total)", expanded=True):
            # Show in chunks to avoid too many buttons
            for i, item in enumerate(all_items):
                if st.button(
                    f"➕ {item}", 
                    key=f"facet_all_{category_name}_{i}",
                    help=f"Add '{item}' to your search filters"
                ):
                    asyncio.run(self._add_facet_to_filters(item, category_name))
                    st.success(f"Added '{item}' to filters!")
                    st.experimental_rerun()
    
    def _extract_facet_items(self, category_data: Dict[str, Any]) -> List[str]:
        """Extract individual items from facet category data."""
        items = []
        
        if isinstance(category_data, dict):
            for key, value in category_data.items():
                if isinstance(value, list):
                    # Value is a list - extract all items
                    items.extend([str(item).strip() for item in value if str(item).strip()])
                elif isinstance(value, str):
                    # Value is a string - split by comma if needed
                    if "," in value:
                        items.extend([item.strip() for item in value.split(",") if item.strip()])
                    else:
                        items.append(value.strip())
                else:
                    # Other types - convert to string
                    items.append(str(value).strip())
        elif isinstance(category_data, list):
            # Direct list of items
            items.extend([str(item).strip() for item in category_data if str(item).strip()])
        
        # Clean and deduplicate
        cleaned_items = []
        for item in items:
            # Skip empty, very short, or clearly invalid items
            if len(item) > 2 and item.lower() not in ['none', 'null', 'undefined', '']:
                # Clean up common patterns
                cleaned_item = item.replace('"', '').replace("'", "")
                if cleaned_item not in cleaned_items:
                    cleaned_items.append(cleaned_item)
        
        return cleaned_items[:20]  # Limit to 20 items max per category
    
    def _get_facet_color(self, category_name: str) -> str:
        """Get color for facet category based on name."""
        category_lower = category_name.lower()
        
        # Check for keywords in category name
        for keyword, color in self.facet_colors.items():
            if keyword in category_lower:
                return color
        
        # Default color
        return self.facet_colors["default"]
    
    async def _add_facet_to_filters(self, item: str, category_name: str):
        """Add a facet item to the current search filters."""
        try:
            # Determine the type of filter based on category name
            category_lower = category_name.lower()
            
            if any(skill_word in category_lower for skill_word in ["skill", "technical", "programming", "expertise", "technology"]):
                # Add as skill/keyword
                await self._add_as_skill(item)
            elif any(location_word in category_lower for location_word in ["location", "city", "region", "area"]):
                # Add as location
                await self._add_as_location(item)
            elif any(role_word in category_lower for role_word in ["role", "title", "position", "designation", "job"]):
                # Add as skill (job titles are often searched as keywords)
                await self._add_as_skill(item)
            else:
                # Default: add as skill
                await self._add_as_skill(item)
            
            st.success(f"✅ Added '{item}' to search filters!")
            
        except Exception as e:
            st.error(f"❌ Failed to add '{item}': {str(e)}")
    
    async def _add_as_skill(self, skill: str):
        """Add item as a skill/keyword."""
        from ...agent import Content
        
        # Use the root agent to add the skill
        content = Content(data={
            "user_input": f"add {skill} skill",
            "session_state": self._get_clean_session_state(),
            "session_id": "facet_interaction"
        })
        
        result = await self.root_agent.execute(content)
        
        if result.data.get("success") and "session_state" in result.data:
            # Update the UI session state
            updated_state = result.data["session_state"]
            if isinstance(updated_state, dict):
                self._update_session_state_safely(updated_state)
    
    async def _add_as_location(self, location: str):
        """Add item as a location."""
        from ...agent import Content
        
        # Use the root agent to add the location
        content = Content(data={
            "user_input": f"add {location} location",
            "session_state": self._get_clean_session_state(),
            "session_id": "facet_interaction"
        })
        
        result = await self.root_agent.execute(content)
        
        if result.data.get("success") and "session_state" in result.data:
            # Update the UI session state
            updated_state = result.data["session_state"]
            if isinstance(updated_state, dict):
                self._update_session_state_safely(updated_state)
    
    def _get_clean_session_state(self) -> Dict[str, Any]:
        """Get clean session state for agent calls."""
        return {
            'keywords': self.session_state.get('keywords', []),
            'min_exp': self.session_state.get('min_exp', 0),
            'max_exp': self.session_state.get('max_exp', 10),
            'min_salary': self.session_state.get('min_salary', 0),
            'max_salary': self.session_state.get('max_salary', 15),
            'current_cities': self.session_state.get('current_cities', []),
            'preferred_cities': self.session_state.get('preferred_cities', []),
            'recruiter_company': self.session_state.get('recruiter_company', ''),
        }
    
    def _update_session_state_safely(self, updated_state: Dict[str, Any]):
        """Update session state safely."""
        safe_keys = [
            'keywords', 'min_exp', 'max_exp', 'min_salary', 'max_salary',
            'current_cities', 'preferred_cities', 'recruiter_company'
        ]
        
        for key, value in updated_state.items():
            if key in safe_keys:
                try:
                    self.session_state[key] = value
                except Exception as e:
                    print(f"⚠️ Failed to update session state key {key}: {e}")

    def render_facets_summary(self, facets_data: Dict[str, Any]):
        """Render a compact summary of available facets."""
        if not facets_data:
            return
        
        primary_count = len(facets_data.get("result_1", {}))
        secondary_count = len(facets_data.get("result_2", {}))
        total_count = primary_count + secondary_count
        
        if total_count > 0:
            st.info(f"🔍 **{total_count} facet categories available** ({primary_count} primary + {secondary_count} secondary) - Click items below to add to your search!")