import streamlit as st
import requests
import pickle

API_URL = "http://10.10.112.238:8005/generate"
LOGS_API_URL = "http://10.10.112.238:8005/logs"

SEGEMENT_LIST = ["Finance",
                "BPO",
                "IT",
                "HR/Admin",
                "Sales & Marketing",
                "Misc",
                "Core Engineering",
                "Strategic & Top Management",
                "Health",
                "Purchase & Logistics",
                "BFSI Sales"]

with open("city_dict.pickle", "rb") as f:
    city_map = pickle.load(f)
    
daysold_map = {
    '': "None",
    63: "6 months",
    1: "1 day",
    3: "3 day",
    7: "7 day",
    15: "15 day",
    23: "30 day",
    31: "2  months",
    39: "3 months",
    51: "4 months",
    75: "9 months",
    365: "1 year",
    11: "4 to 7 days",
    19: "8 to 15 days",
    27: "16 to 30 days",
    35: "1 to 2 months",
    43: "1 to 3 months",
    47: "2 to 3 months",
    55: "2 to 4 months",
    59: "3 to 4 months",
    67: "3 to 6 months",
    71: "4 to 6 months",
    79: "6 to 9 months",
    83: "6 to 12 months",
    87: "9 to 12 months",
    91: "> 1 year",
    3650: "No filter"
}
notice_period_map =   {0: "Any",
                        1:	"0-15 days",
                        2:	"1 months",
                        3:	"2 months",
                        4:	"3 months",
                        5:	"more than 3 months",
                        6:	"currently serving notice period"}

daysold_label_to_key = {v: k for k, v in daysold_map.items()}
np_label_to_key = {v: k for k, v in notice_period_map.items()}
city_label_to_key = {v: k for k, v in city_map.items()}

PRESET_EXAMPLES = {
    "Accenture-IT-Java": {
        "CID": 27117,
        "MINEXP": 2,
        "MAXEXP": 8,
        "MINCTC": 3,
        "MAXCTC": 53.99,
        "CITY": ["Bengaluru / Bangalore"],
        "PREF_LOC": [],
        "NOTICE_PERIOD": ["0-15 days", "1 months"],
        "DAYSOLD": "6 months",
        "query_segment": "IT",
        "combined": "java, java developer, springboot"
    },
    "Accenture-Finance": {
        "CID": 27117,
        "MINEXP": 0,
        "MAXEXP": 1,
        "MINCTC": 3,
        "MAXCTC": 53.99,
        "CITY": ["Bengaluru / Bangalore"],
        "PREF_LOC": [],
        "NOTICE_PERIOD": ["0-15 days", "1 months"],
        "DAYSOLD": "6 months",
        "query_segment": "Finance",
        "combined": "finance"
    },
    "Deloitte-Finance":{
        "CID": 12386,
        "MINEXP": 2,
        "MAXEXP": 53.99,
        "MINCTC": 53.99,
        "MAXCTC": 53.99,
        "CITY": ["Hyderabad / Secunderabad"],
        "PREF_LOC": ['Hyderabad / Secunderabad'],
        "NOTICE_PERIOD": [],
        "DAYSOLD": "6 months",
        "query_segment": "Finance",
        "combined": "risk management"
    },
    "Deloitte-IT":{
        "CID": 12386,
        "MINEXP": 2,
        "MAXEXP": 53.99,
        "MINCTC": 53.99,
        "MAXCTC": 53.99,
        "CITY": ["Hyderabad / Secunderabad"],
        "PREF_LOC": ['Hyderabad / Secunderabad'],
        "NOTICE_PERIOD": [],
        "DAYSOLD": "30 day",
        "query_segment": "IT",
        "combined": "python,data science"
    }
}
def fetch_facets(payload, prefiltering, llm_clean):
    try:
        resp = requests.post(API_URL, json={"data": payload, "num_results": 5, "prefiltering": prefiltering, "llm_clean":llm_clean})
        resp.raise_for_status()
        data = resp.json()
        return {
            "facet1": data.get("result_1", {}),
            "facet2": data.get("result_2", {})
        }
    except Exception as e:
        return {"Error": {"error": [str(e)]}}
        
def fetch_logs():
    try:
        resp = requests.get(LOGS_API_URL)
        resp.raise_for_status()
        data = resp.json()
        return data.get("logs", "No logs found.")
    except Exception as e:
        return f"Error fetching logs: {str(e)}"

def format_field_value_pairs(data):
    lines = []
    for key, value in data.items():
        formatted_value = ", ".join(map(str, value)) if isinstance(value, list) else value
        lines.append(f"**{key}**: {formatted_value}")
    return "<br>".join(lines)
    
def colored_box(content, bg_color):
    return f"""
    <div style="
        background-color: {bg_color};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #e6e9ef;
    ">
        {content}
    </div>
    """
def create_colored_expander(title, content, bg_color):
    """Create an expander with colored header and content"""
    # Color indicator dot
    color_dot = f"""
    <div style="
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: {bg_color};
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    "></div>
    """
    
    # Custom CSS for expander styling
    st.markdown(f"""
    <style>
    .stExpander > div:first-child {{
        background-color: {bg_color}20 !important;
        border-left: 4px solid {bg_color} !important;
        border-radius: 4px !important;
    }}
    .stExpander > div:first-child:hover {{
        background-color: {bg_color}30 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Display color dot with title
    st.markdown(f"{color_dot}<strong>{title}</strong>", unsafe_allow_html=True)
    
    return st.expander("", expanded=False)
    
def get_box_color(facet_data):
    keys = set(facet_data.keys())
    
    # Check if facet contains skills_keywords
    has_skills = "skills_keywords" in keys
    # Check if facet contains designations or job_roles
    has_designations = "designations" in keys or "job_roles" in keys
    has_org = "Current Organization Type" in keys or "organizations" in keys
    
    if has_skills and not has_designations:
        # Only skills_keywords - Blue
        return "#64a2ec"
    elif has_skills and has_designations:
        # Skills + designations/roles - Green
        return "#83fb88"
    elif has_designations and not has_skills:
        # Only designations/roles - Yellow
        return "#ffd85e"
    elif has_org and not has_skills and not has_designations:
        # Everything else - Red
        return "#ff6c6c"
    else:
        return "#fd87ff"

# Streamlit UI
st.set_page_config(page_title="Facets Generator", layout="wide")
st.title("Facet Generator")

# Sidebar inputs
with st.sidebar:
    st.header("Input Parameters")
    st.subheader("Quick Presets")
    
    # Create preset buttons in a grid layout
    preset_names = list(PRESET_EXAMPLES.keys())
    cols = st.columns(3)
    
    for i, preset_name in enumerate(preset_names):
        col = cols[i % 3]
        with col:
            if st.button(preset_name, key=f"preset_{i}"):
                st.session_state.preset_data = PRESET_EXAMPLES[preset_name].copy()
                st.rerun()

    if st.button("Clear All", key="clear_all"):
        st.session_state.preset_data = {
            "CID": 27117,
            "MINEXP": 0,
            "MAXEXP": 0,
            "MINCTC": 0,
            "MAXCTC": 0,
            "CITY": [],
            "PREF_LOC": [],
            "NOTICE_PERIOD": [],
            "DAYSOLD": "6 months",
            "query_segment": "Finance",
            "combined": ""
        }
        st.rerun()
    
    st.divider()
    
    # Initialize session state if not exists
    if 'preset_data' not in st.session_state:
        st.session_state.preset_data = {}
    
    # Use preset data if available, otherwise use defaults
    preset = st.session_state.preset_data
    prefiltering = st.toggle("Enable Prefiltering", value=False)
    llm_clean = st.toggle("Enable Context Cleaning by LLM (BETA-feature)", value=False)
    CID = st.number_input("CID", value=preset.get("CID", 27117))
    default_minexp = st.checkbox("Use Default MINEXP", value=False,disabled=not prefiltering)
    if default_minexp:
        MINEXP = 53.99
        st.info("MINEXP set to default")
    else:
        MINEXP = st.number_input("MINEXP", value=float(preset.get("MINEXP", 0.0)), step=0.01, format="%.2f",disabled=not prefiltering)

    default_maxexp = st.checkbox("Use Default MAXEXP", value=False,disabled=not prefiltering)
    
    if default_maxexp:
        MAXEXP = 53.99
        st.info("MAXEXP set to default")
    else:
        MAXEXP = st.number_input("MAXEXP", value=float(preset.get("MAXEXP", 0.0)), step=0.01, format="%.2f",disabled=not prefiltering)
    
    default_minctc = st.checkbox("Use Default MINCTC", value=False,disabled=not prefiltering)
    
    if default_minctc:
        MINCTC = 53.99
        st.info("MINCTC set to default")
    else:
        MINCTC = st.number_input("MINCTC", value=float(preset.get("MINCTC", 0.0)), step=0.01, format="%.2f",disabled=not prefiltering)
    
    default_maxctc = st.checkbox("Use Default MAXCTC", value=False, disabled=not prefiltering)
    
    if default_maxctc:
        MAXCTC = 53.99
        st.info("MAXCTC set to default")
    else:
        MAXCTC = st.number_input("MAXCTC", value=float(preset.get("MAXCTC", 0.0)), step=0.01, format="%.2f",disabled=not prefiltering)
        
    CITY = st.multiselect(
        "CITY",
        options=list(city_map.values()),
        default=preset.get("CITY", [])
    )
    PREF_LOC = st.multiselect(
        "PREF_LOC",
        options=list(city_map.values()),
        default=preset.get("PREF_LOC", [])
    )
    NOTICE_PERIOD = st.multiselect(
        "NOTICE_PERIOD",
        options=list(notice_period_map.values()),
        default=preset.get("NOTICE_PERIOD", [])
    )

    DAYSOLD = st.selectbox(
        "DAYSOLD",
        options=list(daysold_map.values()),
        index=list(daysold_map.values()).index(preset.get("DAYSOLD", "None")) if preset.get("DAYSOLD", "None") in list(daysold_map.values()) else 0,
        disabled=not prefiltering
    )
    query_segment = st.selectbox(
        "Query Segment",
        options=SEGEMENT_LIST,
        index=SEGEMENT_LIST.index(preset.get("query_segment", "Finance")) if preset.get("query_segment", "Finance") in SEGEMENT_LIST else 0
    )
    combined = st.text_input("Query (comma-separated)", value=preset.get("combined", ""))
    
    
    submit = st.button("Generate Facets")
if submit:
    CITY_keys = [str(city_label_to_key[label]) for label in CITY]
    PREF_LOC_keys = [str(city_label_to_key[label]) for label in PREF_LOC]
    NOTICE_PERIOD_keys = [str(np_label_to_key[label]) for label in NOTICE_PERIOD]
    payload = {
        "MINEXP": float(MINEXP),
        "MAXEXP": float(MAXEXP),
        "MINCTC": float(MINCTC),
        "MAXCTC": float(MAXCTC),
        "CITY": "~".join(CITY_keys),
        "NOTICE_PERIOD": "~".join(NOTICE_PERIOD_keys),
        "PREF_LOC": "~".join(PREF_LOC_keys), 
        "DAYSOLD": int(daysold_label_to_key[DAYSOLD]) if DAYSOLD != "None" else None,
        "CID": int(CID),
        "query_segment": query_segment,
        "combined": [x.strip() for x in combined.split(",") if x.strip()]
    }

    with st.spinner("Generating facets..."):
        facets = fetch_facets(payload, prefiltering, llm_clean)
    with st.spinner("Fetching logs..."):
        logs = fetch_logs()
        
    if facets and not facets.get("Error"):
        st.success("Facets generated successfully!")
        tab1, tab2, tab3 = st.tabs(["Facets with User Details", "Facets with Search Attributes", "Logs"])
        for tab, facet_key in zip([tab1, tab2], ["facet1", "facet2"]):
            with tab:
                facet_data = facets.get(facet_key, {})
                if facet_data:
                    cols = st.columns(4)
                    items = list(facet_data.items())
                    for idx in range(len(items)):
                        col = cols[idx % 4]
                        title, data = items[idx]
                        box_color = get_box_color(data)
                        html_content = f"<b>{title}</b><br>{format_field_value_pairs(data)}"
                        
                        with col:
                            # Add colored header with dot indicator
                            color_dot = f"""
                            <div style="
                                display: flex;
                                align-items: center;
                                margin-bottom: 8px;
                                padding: 8px;
                                background-color: {box_color}20;
                                border-left: 4px solid {box_color};
                                border-radius: 4px;
                            ">
                                <div style="
                                    width: 12px;
                                    height: 12px;
                                    background-color: {box_color};
                                    border-radius: 50%;
                                    margin-right: 8px;
                                "></div>
                                <strong style="color: {box_color};">{title}</strong>
                            </div>
                            """
                            st.markdown(color_dot, unsafe_allow_html=True)
                            
                            # Create expander with colored content
                            with st.expander("View Details", expanded=False):
                                st.markdown(colored_box(html_content, box_color), unsafe_allow_html=True)
                else:
                    st.info("No data for this facet.")
        with tab3:
            st.subheader("API Logs")
            st.code(logs, language="log")
    else:
        st.error("No facets returned. Check API or inputs.")


        
# import streamlit as st
# import requests
# import pickle
# from streamlit_autorefresh import st_autorefresh  # <-- new

# API_URL = "http://10.10.112.238:8004/generate"
# LOGS_API_URL = "http://10.10.112.238:8004/logs"

# SEGEMENT_LIST = ["Finance",
#                 "BPO",
#                 "IT",
#                 "HR/Admin",
#                 "Sales & Marketing",
#                 "Misc",
#                 "Core Engineering",
#                 "Strategic & Top Management",
#                 "Health",
#                 "Purchase & Logistics",
#                 "BFSI Sales"]
# with open("city_dict.pickle", "rb") as f:
#     city_map = pickle.load(f)
    
# daysold_map = {
#     63: "6 months",
#     1: "1 day",
#     3: "3 day",
#     7: "7 day",
#     15: "15 day",
#     23: "30 day",
#     31: "2  months",
#     39: "3 months",
#     51: "4 months",
#     75: "9 months",
#     365: "1 year",
#     11: "4 to 7 days",
#     19: "8 to 15 days",
#     27: "16 to 30 days",
#     35: "1 to 2 months",
#     43: "1 to 3 months",
#     47: "2 to 3 months",
#     55: "2 to 4 months",
#     59: "3 to 4 months",
#     67: "3 to 6 months",
#     71: "4 to 6 months",
#     79: "6 to 9 months",
#     83: "6 to 12 months",
#     87: "9 to 12 months",
#     91: "> 1 year",
#     3650: "no filter all resumes"
# }
# notice_period_map =   {0: "Any",
#                         1:	"0-15 days",
#                         2:	"1 months",
#                         3:	"2 months",
#                         4:	"3 months",
#                         5:	"more than 3 months",
#                         6:	"currently serving notice period"}

# daysold_label_to_key = {v: k for k, v in daysold_map.items()}
# np_label_to_key = {v: k for k, v in notice_period_map.items()}
# city_label_to_key = {v: k for k, v in city_map.items()}

# def fetch_facets(payload, prefiltering, llm_clean):
#     try:
#         resp = requests.post(API_URL, json={"data": payload, "num_results": 5, "prefiltering": prefiltering, "llm_clean":llm_clean})
#         resp.raise_for_status()
#         data = resp.json()
#         return {
#             "facet1": data.get("result_1", {}),
#             "facet2": data.get("result_2", {})
#         }
#     except Exception as e:
#         return {"Error": {"error": [str(e)]}}
        
# def fetch_logs():
#     try:
#         resp = requests.get(LOGS_API_URL)
#         resp.raise_for_status()
#         data = resp.json()
#         return data.get("logs", "No logs found.")
#     except Exception as e:
#         return f"Error fetching logs: {str(e)}"

# def format_field_value_pairs(data):
#     lines = []
#     for key, value in data.items():
#         if isinstance(value, list):
#             lines.append(f"**{key}**: {', '.join(map(str, value))}")
#         else:
#             lines.append(f"**{key}**: {value}")
#     return "\n\n".join(lines)

# # Streamlit UI
# st.set_page_config(page_title="Interactive Facet Viewer", layout="wide")
# st.title("Interactive Facet Viewer")

# # Sidebar inputs
# with st.sidebar:
#     st.header("Input Parameters")
#     prefiltering = st.toggle("Enable Prefiltering", value=False)
#     llm_clean = st.toggle("Enable Context Cleaning by LLM", value=False)
#     CID = st.number_input("CID", value=27117)
#     MINEXP = st.text_input("MINEXP", value="")
#     MAXEXP = st.text_input("MAXEXP", value="")
#     MINCTC = st.text_input("MINCTC", value="")
#     MAXCTC = st.text_input("MAXCTC", value="")
#     CITY = st.multiselect(
#         "CITY",
#         options=list(city_map.values()),
#         default=[]
#     )
#     PREF_LOC = st.multiselect(
#         "PREF_LOC",
#         options=list(city_map.values()),
#         default=[]
#     )
#     NOTICE_PERIOD = st.multiselect(
#         "NOTICE_PERIOD",
#         options=list(notice_period_map.values()),
#         default=[]
#     )
#     DAYSOLD = st.selectbox(
#             "DAYSOLD",
#             options=list(daysold_map.values()),
#             index=list(daysold_map.keys()).index(63) if 63 in daysold_map else 0
#         )
#     query_segment = st.selectbox(
#         "Query Segment",
#         options=SEGEMENT_LIST,
#         index=0
#     )
#     combined = st.text_input("Combined (comma-separated)")
    
#     submit = st.button("Generate Facets")
    
# col_main, col_logs = st.columns([3,1])   # 75% / 25% split

# with col_main:
#     if submit:
#         CITY_keys = [str(city_label_to_key[label]) for label in CITY]
#         PREF_LOC_keys = [str(city_label_to_key[label]) for label in PREF_LOC]
#         NOTICE_PERIOD_keys = [str(np_label_to_key[label]) for label in NOTICE_PERIOD]
#         payload = {
#             "MINEXP": int(MINEXP),
#             "MAXEXP": int(MAXEXP),
#             "MINCTC": int(MINCTC),
#             "MAXCTC": int(MAXCTC),
#             "CITY": "~".join(CITY_keys),
#             "NOTICE_PERIOD": "~".join(NOTICE_PERIOD_keys),
#             "PREF_LOC": "~".join(PREF_LOC_keys), 
#             "DAYSOLD": int(daysold_label_to_key[DAYSOLD]),
#             "CID": int(CID),
#             "query_segment": query_segment,
#             "combined": [x.strip() for x in combined.split(",") if x.strip()]
#         }
#         with st.spinner("Generating facets..."):
#             facets = fetch_facets(payload, prefiltering, llm_clean)

#         if facets and not facets.get("Error"):
#             st.success("Facets generated successfully!")
#             tab1, tab2 = st.tabs([
#                 "Facets with User Details",
#                 "Facets with Search Attributes"
#             ])
#             for tab, key in zip([tab1, tab2], ["facet1", "facet2"]):
#                 with tab:
#                     data = facets.get(key, {})
#                     if data:
#                         cols = st.columns(4)
#                         for i, (title, vals) in enumerate(data.items()):
#                             col = cols[i % 4]
#                             with col.expander(title):
#                                 st.markdown(format_field_value_pairs(vals))
#                     else:
#                         st.info("No data for this facet.")
#         else:
#             st.error("No facets returned. Check API or inputs.")

# with col_logs:
#     st.subheader("API Logs")
#     st_autorefresh(interval=2000, key="logs_refresh")
#     logs = fetch_logs()
#     st.code(logs, language="log")


        