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

# ─── Add New Course Form ──────────────────────────────────
with st.expander("➕ Add New Course"):
    with st.form("add_course_form"):
        st.markdown("### Add New Course")

        course_name = st.text_input("Course Name")
        category = st.selectbox("Category", CATEGORY_OPTIONS)
        ecs = st.number_input("ECs", step=1, min_value=0)
        quarter = st.text_input("Quarter")
        year = st.text_input("Year")
        selected = st.checkbox("Selected?")
        notes = st.text_area("Notes")

        existing_courses = df["Course Name"].dropna().unique().tolist()
        if course_name in existing_courses:
            existing_courses.remove(course_name)  # prevent self-dependency

        prerequisites = st.multiselect("Prerequisites", options=existing_courses)

        submit = st.form_submit_button("➕ Add Course")

        if submit:
            if course_name.strip() == "":
                st.warning("Course name is required.")
            elif course_name in df["Course Name"].values:
                st.warning("A course with this name already exists.")
            else:
                new_course = {
                    "Course Name": course_name,
                    "Category": category,
                    "ECs": ecs,
                    "Quarter": quarter,
                    "Year": year,
                    "Selected? (Y/N)": selected,
                    "Notes": notes,
                    "Prerequisite": ",".join(prerequisites)
                }
                df = pd.concat([df, pd.DataFrame([new_course])], ignore_index=True)
                df.to_excel(EXCEL_FILE, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
                st.success(f"Course '{course_name}' added successfully!")
                st.experimental_rerun()
