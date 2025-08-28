"use client";

import { useEffect, useMemo, useState } from "react";

type Course = {
  Course_Name: string;
  Category: string;
  ECs: number | null;
  Quarter: string | null; // e.g. "1, 3"
  Year: number | null;    // 1 or 2
  Selected__Y_N: boolean;
  Notes: string | null;
};

type Settings = {
  required_ecs: Record<string, number>;
  overflow_target: string;
};

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const API = "http://localhost:8000";

  // Unique sorted list of course names 
  const courseNames = useMemo(
    () =>
      Array.from(
        new Set(
          (courses || [])
            .map((c) => (c.Course_Name || "").trim())
            .filter(Boolean)
        )
      ).sort((a, b) => a.localeCompare(b)),
    [courses]
  );

  // Helpers for add/delete
  const blankCourse: Course = {
    Course_Name: "",
    Category: "",
    ECs: null,
    Quarter: "",
    Year: null,
    Selected__Y_N: false,
    Notes: "",
  };

  const addCourse = () => setCourses((prev) => [...prev, { ...blankCourse }]);
  const deleteCourse = (index: number) =>
    setCourses((prev) => prev.filter((_, i) => i !== index));

  useEffect(() => {
    Promise.all([
      fetch(`${API}/courses`).then((r) => r.json()),
      fetch(`${API}/settings`).then((r) => r.json()),
    ])
      .then(([cs, s]: [Course[], Settings]) => {
        setCourses(cs);
        setCats(Object.keys(s.required_ecs || {}));
      })
      .catch(() => setErr("Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  const set = <K extends keyof Course>(i: number, key: K, val: Course[K]) => {
    setCourses((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], [key]: val };
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    setErr(null);
    try {
      const res = await fetch(`${API}/courses`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(courses),
      });
      if (!res.ok) throw new Error(await res.text());
    } catch {
      setErr("Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <main style={{ padding: 24 }}>Loading…</main>;
  if (err) return <main style={{ padding: 24, color: "crimson" }}>{err}</main>;

  const selected = courses.filter((c) => c.Selected__Y_N);
  const totalECs = selected.reduce((sum, c) => sum + (c.ECs ?? 0), 0);

  return (
    <main style={{ padding: 24 }}>
      <h1>Courses (Editor)</h1>

      <div
        style={{
          display: "flex",
          gap: 16,
          alignItems: "center",
          margin: "8px 0 16px",
          flexWrap: "wrap",
        }}
      >
        <button onClick={save} disabled={saving} style={{ padding: "8px 14px" }}>
          {saving ? "Saving…" : "Save Changes"}
        </button>
        <button onClick={addCourse} style={{ padding: "8px 14px" }}>
          + Add Course
        </button>
        <div>
          Selected courses: <strong>{selected.length}</strong>
        </div>
        <div>
          Total ECs selected: <strong>{totalECs}</strong>
        </div>
      </div>


      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 980 }}>
          <thead>
            <tr>
              {[
                "Selected",
                "Course Name",
                "Category",
                "ECs",
                "Quarter",
                "Year",
                "Notes",
                "Actions", // new column
              ].map((h) => (
                <th
                  key={h}
                  style={{
                    textAlign: "left",
                    borderBottom: "1px solid #444",
                    padding: "6px 8px",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {courses.map((c, i) => (
              <tr key={i}>
                {/* Selected */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    type="checkbox"
                    checked={!!c.Selected__Y_N}
                    onChange={(e) => set(i, "Selected__Y_N", e.target.checked)}
                  />
                </td>

                {/* Course Name */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    value={c.Course_Name || ""}
                    onChange={(e) => set(i, "Course_Name", e.target.value)}
                    style={{ width: "100%" }}
                  />
                </td>

                {/* Category (select from settings) */}
                <td style={{ padding: "6px 8px" }}>
                  <select
                    value={c.Category || ""}
                    onChange={(e) => set(i, "Category", e.target.value)}
                    style={{ width: "100%" }}
                  >
                    <option value=""></option>
                    {cats.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </td>

                {/* ECs */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    type="number"
                    step="1"
                    value={c.ECs ?? ""}
                    onChange={(e) =>
                      set(i, "ECs", e.target.value === "" ? null : Number(e.target.value))
                    }
                    style={{ width: "7ch" }}
                  />
                </td>

                {/* Quarter (free text like "1, 3") */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    value={c.Quarter || ""}
                    onChange={(e) => set(i, "Quarter", e.target.value)}
                    placeholder="e.g. 1, 3"
                    style={{ width: "12ch" }}
                  />
                </td>

                {/* Year (1/2 or empty) */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    type="number"
                    min={1}
                    max={2}
                    value={c.Year ?? ""}
                    onChange={(e) =>
                      set(i, "Year", e.target.value === "" ? null : Number(e.target.value))
                    }
                    style={{ width: "6ch" }}
                  />
                </td>

                {/* Notes */}
                <td style={{ padding: "6px 8px" }}>
                  <input
                    value={c.Notes || ""}
                    onChange={(e) => set(i, "Notes", e.target.value)}
                    style={{ width: "100%" }}
                  />
                </td>

                

                {/* Actions */}
                <td style={{ padding: "6px 8px" }}>
                  <button onClick={() => deleteCourse(i)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
