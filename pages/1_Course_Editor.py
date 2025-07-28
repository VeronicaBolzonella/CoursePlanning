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

# Load or initialize
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
else:
    df = pd.DataFrame(columns=[
        "Course Name", "Category", "ECs", "Quarter", "Year",
        "Selected? (Y/N)", "Notes", "Prerequisite"
    ])

# Ensure all required columns are present
required_columns = [
    "Course Name", "Category", "ECs", "Quarter", "Year",
    "Selected? (Y/N)", "Notes", "Prerequisite"
]
for col in required_columns:
    if col not in df.columns:
        df[col] = ""

# Normalize types
df["Prerequisite"] = df["Prerequisite"].fillna("").astype(str)
df["Selected? (Y/N)"] = df["Selected? (Y/N)"].astype(bool)

st.title("📚 Course Planning Tool")

# ─── Selected Courses Table (TOP) ─────────────────────────
st.subheader("✅ Selected Courses")
selected_df = df[df["Selected? (Y/N)"] == True]
if not selected_df.empty:
    st.dataframe(
        selected_df[["Course Name", "ECs", "Quarter", "Year"]],
        use_container_width=True
    )

    # Show total ECs as text
    total_ecs = selected_df["ECs"].sum()
    st.markdown(
    f"<div style='text-align: right; font-weight: bold;'>Total ECs selected: {total_ecs}</div>",
    unsafe_allow_html=True
)
else:
    st.info("No courses selected yet.")


# ─── Editable Full Course Table ───────────────────────────
st.subheader("📋 All Courses")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    column_config={
        "Category": st.column_config.SelectboxColumn(
            label="Category",
            options=CATEGORY_OPTIONS,
            required=True
        ),
        "Selected? (Y/N)": st.column_config.CheckboxColumn(
            label="Selected",
            help="Check if the course is selected"
        ),
        "Prerequisite": st.column_config.TextColumn(
            label="Prerequisites",
            help="Comma-separated course names"
        )
    }
)


if st.button("Save Changes"):
    edited_df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
    st.success("Changes saved!")
    st.rerun()

