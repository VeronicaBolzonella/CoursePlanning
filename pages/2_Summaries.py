import streamlit as st
import pandas as pd
import os
from style import load_custom_css
load_custom_css()


EXCEL_FILE = "courses.xlsx"
SHEET_NAME = "courses_data"

REQUIRED_ECS = {
    "Mandatory (core)": 15,
    "Mandatory (track)": 18,
    "Electives (track)": 18,
    "Electives (core)": 18,
    "Restricted": 6,
    "Thesis & Research": 45
}

st.title("EC Summary & Timeline")

if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
else:
    st.error("Course data not found.")
    st.stop()

selected = df[df["Selected? (Y/N)"] == True]

# --- EC Summary ---
st.subheader("EC Summary by Category")

selected_ecs_by_cat = selected.groupby("Category")["ECs"].sum().to_dict()
summary_rows = []
electives_core_total = 0

for cat, required in REQUIRED_ECS.items():
    selected_ecs = selected_ecs_by_cat.get(cat, 0)
    if cat != "Electives (core)" and selected_ecs > required:
        overflow = selected_ecs - required
        electives_core_total += overflow
        selected_ecs = required
    elif cat != "Electives (core)":
        overflow = 0
    else:
        overflow = 0

    remaining = required - selected_ecs
    summary_rows.append({
        "Category": cat,
        "Required ECs": required,
        "Selected ECs": selected_ecs,
        "Remaining ECs": remaining
    })

# Add overflow into Electives (core)
selected_ecs_core = selected_ecs_by_cat.get("Electives (core)", 0)
total_core = selected_ecs_core + electives_core_total
core_required = REQUIRED_ECS["Electives (core)"]
core_remaining = core_required - total_core

for row in summary_rows:
    if row["Category"] == "Electives (core)":
        row["Selected ECs"] = total_core
        row["Remaining ECs"] = core_remaining

summary_df = pd.DataFrame(summary_rows)

def highlight_remaining(val):
    if val <= 0:
        return "background-color: #d4edda; color: black;"
    else:
        return "background-color: #f8d7da; color: black;"

styled_df = summary_df.style.map(highlight_remaining, subset=["Remaining ECs"])
st.dataframe(styled_df, use_container_width=True)

# --- Timeline ---
st.subheader("Course Timeline by Quarter")

timeline_df = selected.copy()

for q in ["Q1", "Q2", "Q3", "Q4"]:
    timeline_df[q] = ""

for idx, row in timeline_df.iterrows():
    if pd.notna(row["Quarter"]):
        for q in str(row["Quarter"]).split(","):
            q = q.strip()
            col = f"Q{q}"
            if col in timeline_df.columns:
                timeline_df.at[idx, col] = " "

def highlight_quarters(val):
    if val == " ":
        return "background-color: #ff9999; color: black;"
    return ""

for year in [1, 2]:
    year_df = timeline_df[timeline_df["Year"] == year]
    if not year_df.empty:
        st.markdown(f"### Year {year}")
        view = year_df[["Course Name", "Q1", "Q2", "Q3", "Q4"]]
        styled = view.style.map(highlight_quarters, subset=["Q1", "Q2", "Q3", "Q4"])
        st.dataframe(styled, use_container_width=True)

        # Calculate ECs per quarter for this year
        ec_totals = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
        for _, row in year_df.iterrows():
            course_name = row["Course Name"]
            ec = row["ECs"]
            if pd.notna(row["Quarter"]):
                quarters = [q.strip() for q in str(row["Quarter"]).split(",")]
                ec_per_q = ec / len(quarters)  # evenly distribute ECs
                for q in quarters:
                    q_col = f"Q{q}"
                    if q_col in ec_totals:
                        ec_totals[q_col] += ec_per_q

        # Display EC totals below each quarter
        # Compute semester totals
        sem1_ecs = ec_totals["Q1"] + ec_totals["Q2"]
        sem2_ecs = ec_totals["Q3"] + ec_totals["Q4"]

        # Create empty-left and right-aligned column layout
        col_spacer, col_right = st.columns([3, 1])  # Adjust ratio as needed

        with col_right:
            st.markdown(f"<div style='text-align:right;'><strong>Semester 1 ECs:</strong> {sem1_ecs}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:right;'><strong>Semester 2 ECs:</strong> {sem2_ecs}</div>", unsafe_allow_html=True)


