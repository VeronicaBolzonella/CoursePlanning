import streamlit as st
import pandas as pd
import os
from style import load_custom_css
load_custom_css()

st.set_page_config(page_title="ECs Summary & Timeline", layout="wide")

# ---- Defaults (used as starting values) ----
DEFAULT_REQUIRED_ECS = {
    "Mandatory (core)": 15,
    "Mandatory (track)": 18,
    "Electives (track)": 18,
    "Electives (core)": 18,
    "Restricted": 6,
    "Thesis & Research": 45
}
DEFAULT_OVERFLOW_TARGET = "Electives (core)"  # where overflow goes by default

# ---- Session state init ----
if "required_ecs" not in st.session_state:
    st.session_state.required_ecs = DEFAULT_REQUIRED_ECS.copy()
if "overflow_target" not in st.session_state:
    st.session_state.overflow_target = (
        DEFAULT_OVERFLOW_TARGET
        if DEFAULT_OVERFLOW_TARGET in st.session_state.required_ecs
        else next(iter(st.session_state.required_ecs))
    )

# ---- Sidebar: Category manager ----
st.sidebar.header("Categories & Required ECs")

with st.sidebar.expander("Edit required ECs", expanded=True):
    with st.form("required_ecs_form", clear_on_submit=False):
        new_required = {}
        for cat in list(st.session_state.required_ecs.keys()):
            # For each existing category, allow editing of its required ECs
            new_required[cat] = st.number_input(
                f"{cat}",
                min_value=0,
                max_value=300,
                value=int(st.session_state.required_ecs[cat]),
                step=1,
                key=f"num_{cat}"
            )

        col_save, col_reset = st.columns(2)
        save_clicked = col_save.form_submit_button("Apply changes")
        reset_clicked = col_reset.form_submit_button("Reset to defaults")

    if reset_clicked:
        st.session_state.required_ecs = DEFAULT_REQUIRED_ECS.copy()
        st.session_state.overflow_target = (
            DEFAULT_OVERFLOW_TARGET if DEFAULT_OVERFLOW_TARGET in DEFAULT_REQUIRED_ECS
            else next(iter(DEFAULT_REQUIRED_ECS))
        )
    elif save_clicked:
        st.session_state.required_ecs = new_required

with st.sidebar.expander("Add / remove categories", expanded=False):
    # Add
    with st.form("add_cat_form", clear_on_submit=True):
        new_cat = st.text_input("New category name")
        new_cat_ecs = st.number_input("Required ECs for new category", min_value=0, max_value=300, value=0, step=1)
        add_clicked = st.form_submit_button("Add category")
    if add_clicked:
        name = new_cat.strip()
        if name:
            if name in st.session_state.required_ecs:
                st.warning(f"Category '{name}' already exists.")
            else:
                st.session_state.required_ecs[name] = int(new_cat_ecs)
                # If it's the first category or no overflow target, set it
                if not st.session_state.overflow_target:
                    st.session_state.overflow_target = name
        else:
            st.warning("Please enter a category name.")

    # Remove
    if st.session_state.required_ecs:
        removable = list(st.session_state.required_ecs.keys())
        remove_choices = st.multiselect("Select categories to remove", removable)
        if st.button("Remove selected"):
            for rc in remove_choices:
                # Remove from dict
                if rc in st.session_state.required_ecs:
                    del st.session_state.required_ecs[rc]
            # Repair overflow target if it was deleted
            if st.session_state.overflow_target not in st.session_state.required_ecs:
                st.session_state.overflow_target = (
                    next(iter(st.session_state.required_ecs)) if st.session_state.required_ecs else ""
                )

# Overflow target selector (only if we have categories)
if st.session_state.required_ecs:
    st.sidebar.selectbox(
        "Overflow target (gets any extra ECs beyond other categories’ requirements)",
        options=list(st.session_state.required_ecs.keys()),
        index=list(st.session_state.required_ecs.keys()).index(st.session_state.overflow_target)
              if st.session_state.overflow_target in st.session_state.required_ecs else 0,
        key="overflow_target"
    )
else:
    st.sidebar.info("Add at least one category to continue.")

# ---- Use the current categories everywhere below ----
REQUIRED_ECS = st.session_state.required_ecs
OVERFLOW_TARGET = st.session_state.overflow_target

# ---- Data load ----
EXCEL_FILE = "courses.xlsx"
SHEET_NAME = "courses_data"

st.title("ECs Summary & Timeline")

if not REQUIRED_ECS:
    st.error("No categories defined. Please add at least one category in the sidebar.")
    st.stop()

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
overflow_bucket_total = 0

# 1) Compute capping and overflow for all categories except the overflow target
for cat, required in REQUIRED_ECS.items():
    selected_ecs = selected_ecs_by_cat.get(cat, 0)
    if cat != OVERFLOW_TARGET and required is not None:
        if selected_ecs > required:
            overflow = selected_ecs - required
            overflow_bucket_total += overflow
            selected_ecs = required
        else:
            overflow = 0
    else:
        # For the overflow target, we don't cap here (we'll add overflow later)
        overflow = 0

    remaining = required - selected_ecs
    summary_rows.append({
        "Category": cat,
        "Required ECs": required,
        "Selected ECs": selected_ecs,
        "Remaining ECs": remaining
    })

# 2) Add the overflow into the overflow target’s selected ECs and recompute remaining
if OVERFLOW_TARGET in REQUIRED_ECS:
    for row in summary_rows:
        if row["Category"] == OVERFLOW_TARGET:
            base_selected = selected_ecs_by_cat.get(OVERFLOW_TARGET, 0)
            total_target = base_selected + overflow_bucket_total
            row["Selected ECs"] = total_target
            row["Remaining ECs"] = REQUIRED_ECS[OVERFLOW_TARGET] - total_target
            break  # only one target

summary_df = pd.DataFrame(summary_rows).set_index("Category").loc[list(REQUIRED_ECS.keys())].reset_index()

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

def highlight_quarters(row):
    style = {}
    # Keep the heuristic: anything with "Electives" in its name uses a lighter shade
    is_elective = "Electives" in row.get("Category", "")
    color = "#fccccc" if is_elective else "#f8b0b0"
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
            st.markdown(f"<div style='text-align:right;'><strong>Semester 1 ECs:</strong> {sem1_ecs:.1f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:right;'><strong>Semester 2 ECs:</strong> {sem2_ecs:.1f}</div>", unsafe_allow_html=True)

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
        st.markdown(f"<div style='text-align:right;'><strong>Semester 1 ECs:</strong> {sem1_ecs:.1f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;'><strong>Semester 2 ECs:</strong> {sem2_ecs:.1f}</div>", unsafe_allow_html=True)
