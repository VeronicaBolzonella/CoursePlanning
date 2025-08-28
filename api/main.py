from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI()

DATA_DIR = Path(__file__).parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

# --- Pydantic model for validation ---
class Settings(BaseModel):
    required_ecs: dict[str, int]
    overflow_target: str

def load_settings() -> Settings:
    if not SETTINGS_FILE.exists():
        raise HTTPException(status_code=500, detail="settings.json not found")
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    try:
        return Settings(**raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid settings.json: {e}")

def save_settings(s: Settings) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s.model_dump(), f, indent=2, ensure_ascii=False)

@app.get("/")
def home():
    return {"message": "Hello, backend is working!"}

@app.get("/settings", response_model=Settings)
def get_settings():
    return load_settings()

@app.put("/settings", response_model=Settings)
def update_settings(new_settings: Settings):
    # ensure overflow_target exists among categories
    if new_settings.overflow_target not in new_settings.required_ecs:
        raise HTTPException(
            status_code=400,
            detail="overflow_target must be one of the category names in required_ecs",
        )
    save_settings(new_settings)
    return new_settings

# -------------------------
# Courses (Excel) endpoints
# -------------------------
from typing import Optional, List
from pydantic import BaseModel
import pandas as pd

COURSES_XLSX = DATA_DIR / "courses.xlsx"
SHEET_NAME = "courses_data"
REQUIRED_COLUMNS = [
    "Course Name", "Category", "ECs", "Quarter", "Year",
    "Selected? (Y/N)", "Notes", "Prerequisite"
]

class CourseRow(BaseModel):
    Course_Name: str | None = None
    Category: str | None = None
    ECs: Optional[float] = None
    Quarter: str | None = None            # e.g. "1", "1, 3"
    Year: Optional[float] = None          # keep float to match Excel then cast
    Selected__Y_N: Optional[bool] = None  # Pydantic can't take '?' and '/' in field names
    Notes: str | None = None
    Prerequisite: str | None = None

    # Map back to real Excel column names when saving
    def to_excel_row(self) -> dict:
        return {
            "Course Name": self.Course_Name or "",
            "Category": self.Category or "",
            "ECs": float(self.ECs) if self.ECs is not None else None,
            "Quarter": self.Quarter or "",
            "Year": int(self.Year) if self.Year is not None and pd.notna(self.Year) else None,
            "Selected? (Y/N)": bool(self.Selected__Y_N) if self.Selected__Y_N is not None else False,
            "Notes": self.Notes or "",
            "Prerequisite": self.Prerequisite or "",
        }

def _ensure_courses_df() -> pd.DataFrame:
    """Load Excel if present; otherwise an empty, well-typed DataFrame."""
    if COURSES_XLSX.exists():
        df = pd.read_excel(COURSES_XLSX, sheet_name=SHEET_NAME, engine="openpyxl")
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Ensure required columns exist and normalize types similar to your Streamlit logic
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")

    df["Course Name"] = df["Course Name"].fillna("").astype(str)
    df["Category"] = df["Category"].fillna("").astype(str)
    df["ECs"] = pd.to_numeric(df["ECs"], errors="coerce")
    df["Quarter"] = df["Quarter"].fillna("").astype(str)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Selected? (Y/N)"] = df["Selected? (Y/N)"].fillna(False).astype(bool)
    df["Notes"] = df["Notes"].fillna("").astype(str)
    df["Prerequisite"] = df["Prerequisite"].fillna("").astype(str)
    return df

@app.get("/courses")
def get_courses():
    df = _ensure_courses_df()
    # Return records with JSON-safe keys (no spaces or punctuation)
    # so the frontend form bindings are simple:
    out = []
    for _, r in df.iterrows():
        out.append({
            "Course_Name": r["Course Name"],
            "Category": r["Category"],
            "ECs": None if pd.isna(r["ECs"]) else float(r["ECs"]),
            "Quarter": r["Quarter"],
            "Year": None if pd.isna(r["Year"]) else int(r["Year"]),
            "Selected__Y_N": bool(r["Selected? (Y/N)"]),
            "Notes": r["Notes"],
            "Prerequisite": r["Prerequisite"],
        })
    return out

@app.put("/courses")
def put_courses(rows: List[CourseRow]):
    df = pd.DataFrame([r.to_excel_row() for r in rows], columns=REQUIRED_COLUMNS)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(COURSES_XLSX, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
    return {"saved": len(df)}

# -------------------------
# Summary endpoint (caps + overflow)
# -------------------------
import pandas as pd  # (already imported above, safe to keep)

def _selected_df() -> pd.DataFrame:
    df = _ensure_courses_df()
    sel = df[df["Selected? (Y/N)"] == True].copy()
    # coerce ECs to numeric (already done in _ensure_courses_df, but safe)
    sel["ECs"] = pd.to_numeric(sel["ECs"], errors="coerce").fillna(0)
    return sel

@app.get("/summary")
def get_summary():
    # load settings
    settings = load_settings()
    REQUIRED_ECS: dict[str, int] = settings.required_ecs
    OVERFLOW_TARGET: str = settings.overflow_target

    sel = _selected_df()

    # Sum selected ECs by category
    selected_by_cat = sel.groupby("Category")["ECs"].sum().to_dict()

    summary_rows = []
    overflow_bucket_total = 0.0

    # 1) Cap all categories EXCEPT the overflow target, collect overflow
    for cat, required in REQUIRED_ECS.items():
        selected_ecs = float(selected_by_cat.get(cat, 0.0))
        if cat != OVERFLOW_TARGET:
            if selected_ecs > required:
                overflow = selected_ecs - required
                overflow_bucket_total += overflow
                selected_ecs = required
            else:
                overflow = 0.0
        else:
            # don't cap here; handle after collecting overflow
            overflow = 0.0

        remaining = float(required) - float(selected_ecs)
        summary_rows.append({
            "Category": cat,
            "Required_ECs": int(required),
            "Selected_ECs": float(selected_ecs),
            "Remaining_ECs": float(remaining),
        })

    # 2) Add overflow into the overflow target’s Selected_ECs and recompute remaining
    if OVERFLOW_TARGET in REQUIRED_ECS:
        for row in summary_rows:
            if row["Category"] == OVERFLOW_TARGET:
                base_selected = float(selected_by_cat.get(OVERFLOW_TARGET, 0.0))
                total_target = base_selected + overflow_bucket_total
                row["Selected_ECs"] = float(total_target)
                row["Remaining_ECs"] = float(REQUIRED_ECS[OVERFLOW_TARGET]) - float(total_target)
                break

    # Keep the original category order from settings
    ordered = sorted(summary_rows, key=lambda r: list(REQUIRED_ECS.keys()).index(r["Category"]))

    # Also include total ECs selected (useful for the UI)
    total_selected_ecs = float(sel["ECs"].sum()) if not sel.empty else 0.0

    return {
        "rows": ordered,
        "total_selected_ecs": total_selected_ecs,
        "overflow_target": OVERFLOW_TARGET,
        "categories": list(REQUIRED_ECS.keys()),
    }

# -------------------------
# Timeline endpoint
# -------------------------
def _parse_quarters(q_str: str) -> list[int]:
    if not q_str:
        return []
    out: list[int] = []
    for part in str(q_str).split(","):
        part = part.strip()
        if part.isdigit():
            n = int(part)
            if n in (1, 2, 3, 4):
                out.append(n)
    return out

def _row_quarter_cols(quarters: list[int]) -> dict[str, str]:
    # " " marks selected quarters (to mimic your Streamlit styling)
    return {f"Q{i}": (" " if i in quarters else "") for i in (1, 2, 3, 4)}

def _quarter_sort_key(quarter_str: str) -> int:
    qs = _parse_quarters(quarter_str)
    return min(qs) if qs else 99  # put empties last

def _accumulate_ecs_by_quarter(rows: list[dict]) -> dict[str, float]:
    totals = {"Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0}
    for r in rows:
        ec = float(r.get("ECs") or 0.0)
        qs = _parse_quarters(r.get("Quarter") or "")
        if qs:
            share = ec / len(qs)
            for q in qs:
                totals[f"Q{q}"] += share
    return totals

@app.get("/timeline")
def get_timeline():
    sel = _selected_df()
    # convert to list of dicts we can shape easily
    records: list[dict] = []
    for _, row in sel.iterrows():
        quarters = _parse_quarters(row["Quarter"])
        base = {
            "Course_Name": row["Course Name"],
            "Category": row["Category"],
            "ECs": float(row["ECs"]) if row["ECs"] == row["ECs"] else 0.0,  # NaN-safe
            "Quarter": row["Quarter"],
            "Year": (int(row["Year"]) if row["Year"] == row["Year"] else None),
        }
        base.update(_row_quarter_cols(quarters))
        records.append(base)

    # Split by year (1,2) and unassigned (None)
    by_year = {1: [], 2: []}
    unassigned: list[dict] = []
    for r in records:
        y = r.get("Year")
        if y in (1, 2):
            by_year[y].append(r)
        else:
            unassigned.append(r)

    # Sort each block by earliest quarter
    for y in (1, 2):
        by_year[y].sort(key=lambda r: _quarter_sort_key(r.get("Quarter") or ""))

    unassigned.sort(key=lambda r: _quarter_sort_key(r.get("Quarter") or ""))

    # Compute semester totals for each block
    def summarize(rows: list[dict]) -> dict:
        q_totals = _accumulate_ecs_by_quarter(rows)
        sem1 = q_totals["Q1"] + q_totals["Q2"]
        sem2 = q_totals["Q3"] + q_totals["Q4"]
        return {
            "rows": rows,
            "quarter_totals": q_totals,
            "semester1_ecs": sem1,
            "semester2_ecs": sem2,
        }

    return {
        "year1": summarize(by_year[1]),
        "year2": summarize(by_year[2]),
        "unassigned": summarize(unassigned),
    }

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
