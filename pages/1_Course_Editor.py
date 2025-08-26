import streamlit as st
import pandas as pd
import os
from style import load_custom_css
load_custom_css()

st.set_page_config(layout="wide")

EXCEL_FILE = "courses.xlsx"
SHEET_NAME = "courses_data"

# --- Categories: mirror the other page (2_summaries.py) ---
DEFAULT_REQUIRED_ECS = {
    "Mandatory (core)": 15,
    "Mandatory (track)": 18,
    "Electives (track)": 18,
    "Electives (core)": 18,
    "Restricted": 6,
    "Thesis & Research": 45
}

# Use categories from session state if available; else defaults
if "required_ecs" in st.session_state and isinstance(st.session_state.required_ecs, dict):
    CATEGORY_OPTIONS = list(st.session_state.required_ecs.keys())
else:
    CATEGORY_OPTIONS = list(DEFAULT_REQUIRED_ECS.keys())

# --- Load or initialize data ---
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
else:
    df = pd.DataFrame(columns=[
        "Course Name", "Category", "ECs", "Quarter", "Year",
        "Selected? (Y/N)", "Notes", "Prerequisite"
    ])

# Ensure required columns exist
required_columns = [
    "Course Name", "Category", "ECs", "Quarter", "Year",
    "Selected? (Y/N)", "Notes", "Prerequisite"
]
for col in required_columns:
    if col not in df.columns:
        df[col] = pd.Series(dtype="object")

# Normalize types / clean up
df["Course Name"] = df["Course Name"].fillna("").astype(str)
df["Category"] = df["Category"].fillna("").astype(str)
# keep ECs numeric where possible
df["ECs"] = pd.to_numeric(df["ECs"], errors="coerce")
df["Quarter"] = df["Quarter"].fillna("").astype(str)
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["Selected? (Y/N)"] = df["Selected? (Y/N)"].fillna(False).astype(bool)
df["Notes"] = df["Notes"].fillna("").astype(str)           # (2) ensure textual field
df["Prerequisite"] = df["Prerequisite"].fillna("").astype(str)

st.title("📚 Course Planning Tool")

# ─── Selected Courses Table (TOP) ─────────────────────────
st.subheader("✅ Selected Courses")
selected_df = df[df["Selected? (Y/N)"] == True]
if not selected_df.empty:
    st.dataframe(
        selected_df[["Course Name", "ECs", "Quarter", "Year"]],
        use_container_width=True
    )
    total_ecs = pd.to_numeric(selected_df["ECs"], errors="coerce").fillna(0).sum()
    st.markdown(
        f"<div style='text-align: right; font-weight: bold;'>Total ECs selected: {total_ecs:.1f}</div>",
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
            options=CATEGORY_OPTIONS,           # (1) synced with other page
            required=True
        ),
        "ECs": st.column_config.NumberColumn(
            label="ECs",
            min_value=0,
            step=1
        ),
        "Year": st.column_config.NumberColumn(
            label="Year",
            min_value=1,
            max_value=2,
            step=1
        ),
        "Selected? (Y/N)": st.column_config.CheckboxColumn(
            label="Selected",
            help="Check if the course is selected"
        ),
        "Prerequisite": st.column_config.TextColumn(
            label="Prerequisites",
            help="Comma-separated course names"
        ),
        "Notes": st.column_config.TextColumn(
            label="Notes",
            help="Any notes about this course",
            max_chars=5000,
            width="medium"   # or "large" if you want more space
        )

    }
)

if st.button("Save Changes"):
    # Ensure datatypes are saved cleanly
    out = edited_df.copy()
    out["Selected? (Y/N)"] = out["Selected? (Y/N)"].fillna(False).astype(bool)
    out["ECs"] = pd.to_numeric(out["ECs"], errors="coerce")
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce")
    out.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
    st.success("Changes saved!")
    st.rerun()
