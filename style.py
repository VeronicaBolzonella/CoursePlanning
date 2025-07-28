# style.py
import streamlit as st
def load_custom_css():
    st.markdown("""
        <style>
        /* Stronger selectors for headers inside Streamlit */
        .stApp h1, .stApp h2, .stApp h3 {
            color: #E68080 !important;
            font-family: 'Segoe UI', sans-serif;
        }

        .css-1d391kg {
            border: 1px solid #444;
            border-radius: 10px;
            background-color: #1e1e1e;
            font-size: 16px;
        }

        .stButton > button {
            background-color: #E68080;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        thead th {
            background-color: #FFCCCC !important;
            font-weight: bold;
        }
        tbody td {
            background-color: #FFF0F0;
        }
        tbody tr:hover td {
            background-color: #FFE5E5;
        }
        [data-testid="stDataFrame"] .css-1d391kg {
            border-radius: 10px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)
