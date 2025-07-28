import streamlit as st
import pandas as pd
import os
from style import load_custom_css
load_custom_css()


EXCEL_FILE = "courses.xlsx"
SHEET_NAME = "courses_data"

CATEGORY_OPTIONS = [
    "Mandatory (core)",
    "Mandatory (track)",
    "Electives (track)",
    "Electives (core)",
    "Restricted",
    "Thesis & Research"
]

if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
else:
    df = pd.DataFrame(columns=[
        "Course Name", "Category", "ECs", "Quarter", "Year",
        "Selected? (Y/N)", "Notes", "Prerequisite"
    ])

st.title("Course Editor")

st.subheader("Selected Courses")
selected_df = df[df["Selected? (Y/N)"] == True]
st.dataframe(selected_df[["Course Name", "ECs", "Quarter", "Year"]], use_container_width=True)

st.subheader("Edit or Add Courses")
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    column_config={
        "Category": st.column_config.SelectboxColumn(
            label="Category",
            options=CATEGORY_OPTIONS,
            help="Choose the course category",
            required=True
        )
    }
)

if st.button("Save Changes"):
    edited_df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
    st.success("Changes saved to courses.xlsx!")
    st.rerun()
