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
    if val < 0:
        return "background-color: #cce5ff; color: black;"  # light blue
    elif val == 0:
        return "background-color: #d4edda; color: black;"  # green
    else:
        return "background-color: #f8d7da; color: black;"  # red


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

def quarter_order(row):
    if pd.isna(row["Quarter"]):
        return 99  # put empty quarter courses at the end
    quarters = [int(q.strip()) for q in str(row["Quarter"]).split(",") if q.strip().isdigit()]
    return min(quarters) if quarters else 99



# def highlight_quarters(val):
#     if val == " ":
#         return "background-color: #ff9999; color: black;"
#     return ""


def highlight_quarters(row):
    style = {}
    is_elective = "Electives" in row.get("Category", "")  # fallback if missing

    color = "#fccccc" if is_elective else "#f8b0b0"  # light vs dark red

    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if row[q] == " ":
            style[q] = f"background-color: {color}; color: black;"
        else:
            style[q] = ""
    return pd.Series(style)


# Loop through valid years
for year in [1, 2]:
    year_df = timeline_df[timeline_df["Year"] == year].copy()
    year_df["__sort__"] = year_df.apply(quarter_order, axis=1)
    year_df = year_df.sort_values("__sort__").drop(columns="__sort__")

    if not year_df.empty:
        st.markdown(f"### Year {year}")
        # Include Category for styling but don't display it
        full_view = year_df[["Course Name", "Category", "Q1", "Q2", "Q3", "Q4"]]
        visible_view = full_view.drop(columns="Category")

        styled = visible_view.style.apply(
            lambda row: highlight_quarters(full_view.loc[row.name]), axis=1
        )

        st.dataframe(styled, use_container_width=True)


        # Calculate ECs per quarter
        ec_totals = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
        for _, row in year_df.iterrows():
            ec = row["ECs"]
            if pd.notna(row["Quarter"]):
                quarters = [q.strip() for q in str(row["Quarter"]).split(",")]
                ec_per_q = ec / len(quarters)
                for q in quarters:
                    q_col = f"Q{q}"
                    if q_col in ec_totals:
                        ec_totals[q_col] += ec_per_q

        sem1_ecs = ec_totals["Q1"] + ec_totals["Q2"]
        sem2_ecs = ec_totals["Q3"] + ec_totals["Q4"]

        col_spacer, col_right = st.columns([3, 1])
        with col_right:
            st.markdown(f"<div style='text-align:right;'><strong>Semester 1 ECs:</strong> {sem1_ecs}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:right;'><strong>Semester 2 ECs:</strong> {sem2_ecs}</div>", unsafe_allow_html=True)

# Handle courses with no valid Year
unassigned_df = timeline_df[pd.isna(timeline_df["Year"])].copy()

if not unassigned_df.empty:
    unassigned_df["__sort__"] = unassigned_df.apply(quarter_order, axis=1)
    unassigned_df = unassigned_df.sort_values("__sort__").drop(columns="__sort__")

    st.markdown("### 🕗 Unassigned Courses")
    full_view = unassigned_df[["Course Name", "Category", "Q1", "Q2", "Q3", "Q4"]]
    visible_view = full_view.drop(columns="Category")

    styled = visible_view.style.apply(
        lambda row: highlight_quarters(full_view.loc[row.name]), axis=1
    )

    st.dataframe(styled, use_container_width=True)


    # Optional: EC summary here too
    ec_totals = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for _, row in unassigned_df.iterrows():
        ec = row["ECs"]
        if pd.notna(row["Quarter"]):
            quarters = [q.strip() for q in str(row["Quarter"]).split(",")]
            ec_per_q = ec / len(quarters)
            for q in quarters:
                q_col = f"Q{q}"
                if q_col in ec_totals:
                    ec_totals[q_col] += ec_per_q

    sem1_ecs = ec_totals["Q1"] + ec_totals["Q2"]
    sem2_ecs = ec_totals["Q3"] + ec_totals["Q4"]

    col_spacer, col_right = st.columns([3, 1])
    with col_right:
        st.markdown(f"<div style='text-align:right;'><strong>Semester 1 ECs:</strong> {sem1_ecs}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;'><strong>Semester 2 ECs:</strong> {sem2_ecs}</div>", unsafe_allow_html=True)
