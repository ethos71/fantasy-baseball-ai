"""Configuration and styling for Streamlit dashboard"""
import streamlit as st

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="FB-AI Sit/Start Report",
        page_icon="⚾",
        layout="wide"
    )

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
        .section-header-container {
            background-color: #f0f2f6;
            padding: 10px 15px;
            border-radius: 5px;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .section-header-container h2 {
            margin: 0;
            padding: 0;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
    </style>
    """, unsafe_allow_html=True)

def section_header(text, icon=""):
    """Create a styled section header"""
    st.markdown(f'<div class="section-header-container"><h2>{icon} {text}</h2></div>', unsafe_allow_html=True)
