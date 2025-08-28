"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState("loading...");
  const [total, setTotal] = useState<number | null>(null);

  useEffect(() => {
    // Call backend root
    fetch("http://localhost:8000/")
      .then((res) => res.json())
      .then((data) => setStatus(data.message))
      .catch(() => setStatus("error"));

    // Call /summary to get total ECs
    fetch("http://localhost:8000/summary")
      .then((res) => res.json())
      .then((data) => setTotal(data.total_selected_ecs))
      .catch(() => setTotal(null));
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>Course Planner (React)</h1>
      <p>Backend says: <strong>{status}</strong></p>
      <p>Total selected ECs: <strong>{total ?? "…"}</strong></p>
    </main>
  );
}
