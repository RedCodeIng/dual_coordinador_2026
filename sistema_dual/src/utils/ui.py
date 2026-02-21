import streamlit as st
import base64
import os
import textwrap

def load_image_as_base64(path):
    """Loads an image file and returns it as a base64 string."""
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None

def inject_custom_css():
    """Injects robust CSS to force institutional branding."""
    st.markdown("""
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

        /* ROOT VARIABLES */
        :root {
            --primary: #8d2840; /* Guinda */
            --primary-dark: #6d1f31;
            --secondary: #a48857; /* Dorado */
            --text-main: #000000;
            --text-light: #ffffff;
            --bg-body: #ffffff;
            --bg-panel: #f8f9fa;
        }

        /* GLOBAL RESET */
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
            color: var(--text-main);
            background-color: var(--bg-body);
        }

        /* STREAMLIT OVERRIDES */
        /* Hide default footer and menu, leave header for sidebar toggle */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Main Container Padding */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }

        /* HEADINGS */
        h1, h2, h3 {
            color: var(--primary) !important;
            font-weight: 700;
        }
        h1 { font-size: 2.5rem; border-bottom: 2px solid var(--secondary); padding-bottom: 10px; margin-bottom: 20px; }
        h2 { font-size: 1.8rem; margin-top: 20px; }
        h3 { font-size: 1.4rem; color: var(--secondary) !important; }

        /* BUTTONS */
        .stButton button {
            background-color: var(--primary) !important;
            color: var(--text-light) !important;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            background-color: var(--primary-dark) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transform: translateY(-1px);
        }

        /* INPUTS */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: var(--secondary);
            box-shadow: 0 0 0 2px rgba(164, 136, 87, 0.2);
        }

        /* SIDEBAR FONT SIZES */
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
            font-size: 1.25rem !important;
            padding-top: 0.3rem;
            padding-bottom: 0.3rem;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
            font-size: 1.5rem !important;
        }

        /* CARDS (METRICS) */
        div[data-testid="stMetricValue"] {
            color: var(--primary) !important;
        }

        /* CUSTOM NAVBAR/HEADER CLASS */
        .custom-header {
            background-color: var(--bg-body);
            border-bottom: 4px solid var(--primary);
            padding: 10px 0;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .logo-box {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .logo-img {
            max-height: 80px;
            max-width: 100%;
            height: auto;
        }
        .title-box {
            flex: 2;
            text-align: center;
            color: var(--primary);
        }
        .title-box h1 {
            border: none; 
            margin: 0; 
            padding: 0; 
            font-size: 28px; 
            line-height: 1.2;
            text-transform: uppercase;
        }
        .title-box p {
            margin: 0; 
            font-size: 14px; 
            color: var(--secondary);
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        /* TABLE STYLES */
        thead tr th {
            background-color: var(--primary) !important;
            color: white !important;
        }
        tbody tr:nth-child(even) {
            background-color: #f2f2f2;
        }

        /* TABS (PESTAÑAS) */
        button[data-baseweb="tab"] {
            font-size: 1.25rem !important; /* Larger text */
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            font-weight: 500 !important;
        }
        button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p {
            font-size: 1.25rem !important; /* Force text inside tab to be larger */
        }
        div[data-baseweb="tab-list"] {
            gap: 15px; /* Spacing between tabs */
        }

        /* MOBILE RESPONSIVENESS */
        @media (max-width: 768px) {
            .custom-header {
                flex-direction: column;
                gap: 10px;
            }
            .logo-img {
                max-height: 50px;
            }
            .title-box h1 {
                font-size: 18px;
            }
            
            /* Responsive Tabs for Mobile */
            button[data-baseweb="tab"] {
                font-size: 1rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p {
                font-size: 1rem !important;
            }
            div[data-baseweb="tab-list"] {
                gap: 5px;
                flex-wrap: wrap; /* Ensure tabs wrap if they do not fit */
            }
            
            /* Make columns stack on mobile */
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
            div[data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                margin-bottom: 15px;
            }
        }
        /* SIDEBAR TOGGLE VISIBILITY */
        button[kind="header"] {
            color: var(--primary) !important;
            background-color: transparent !important;
        }
        
        [data-testid="stSidebarCollapsedControl"] {
            color: var(--primary) !important;
            background-color: rgba(141, 40, 64, 0.1);
            border-radius: 8px;
            padding: 5px;
            border: 2px solid var(--secondary);
            z-index: 999999;
        }
        
        [data-testid="stSidebarCollapsedControl"]:hover {
            background-color: var(--secondary);
            color: white !important;
            transform: scale(1.1);
        }
        
        [data-testid="stSidebarCollapsedControl"] svg {
            width: 30px !important;
            height: 30px !important;
            stroke-width: 3px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Renders the custom header with base64 logos."""
    # Define paths - Correcting filenames based on user screenshot
    # logo_institucional_tese.png
    # logo_dual_sistema.png
    # logo_estado_mexico.png
    
    base_path = os.path.join(os.path.dirname(__file__), "../assets/images/logos")
    if not os.path.exists(base_path):
        # Fallback or check if running from root without src in path (unlikely with our fix)
        base_path = "src/assets/images/logos"

    logo_tese = load_image_as_base64(os.path.join(base_path, "logo_institucional_tese.png"))
    logo_edomex = load_image_as_base64(os.path.join(base_path, "logo_estado_mexico.png"))
    
    # HTML IMG tags with refined styling
    img_tese = f'<img src="{logo_tese}" style="height: 60px; width: auto;">' if logo_tese else ''
    img_edomex = f'<img src="{logo_edomex}" style="height: 60px; width: auto;">' if logo_edomex else ''
    
    # We use a flush-left string to ensure st.markdown does not interpret it as a code block
    html = f"""
<div style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; border-bottom: 4px solid #8d2840; padding-bottom: 8px; margin-bottom: 15px; background-color: white;">
    <div style="flex: 1; display: flex; justify-content: flex-start; padding-left: 10px;">
        {img_tese}
    </div>
    <div style="flex: 2; display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <h1 style="border: none; margin: 0; font-size: 24px; color: #8d2840; text-transform: uppercase; font-weight: bold; text-align: center; line-height: 1.2;">
            Sistema de Gestión DUAL
        </h1>
        <p style="margin: 0; color: #a48857; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">
            Gobierno del Estado de México
        </p>
    </div>
    <div style="flex: 1; display: flex; justify-content: flex-end; padding-right: 10px;">
        {img_edomex}
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
