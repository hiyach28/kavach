import { useEffect, useState } from "react";

/** Phase 0 shell — replaced by Terminal shell (F40) in Phase 4. */
export default function App() {
  const [health, setHealth] = useState<string>("checking…");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((b) => setHealth(`${b.status} (llm_mode=${b.llm_mode})`))
      .catch(() => setHealth("backend unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "monospace", padding: "2rem", color: "#E6EDF3", background: "#0B0F14", minHeight: "100vh" }}>
      <h1>KAVACH v2 — Phase 0</h1>
      <p>backend health: {health}</p>
    </main>
  );
}
