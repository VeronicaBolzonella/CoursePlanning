import streamlit as st
from style import load_custom_css
load_custom_css()


# Page config (set title, icon, layout)
st.set_page_config(
    page_title="My Course Planner",
    page_icon="📘",
    layout="wide",
)
# Continue with your normal app content
st.title("Welcome to My Course Planner")
