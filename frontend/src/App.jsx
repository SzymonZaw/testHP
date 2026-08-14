import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [datasets, setDatasets] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/status`).then((r) => r.json()),
      fetch(`${API}/api/datasets`).then((r) => r.json()),
    ])
      .then(([s, d]) => {
        setStatus(s);
        setDatasets(d);
      })
      .catch((e) => setError(`Nie można połączyć z FastAPI: ${e.message}`));
  }, []);

  return (
    <main className="page">
      <header>
        <div>
          <p className="eyebrow">HUMAN PATHOLOGY PLATFORM</p>
          <h1>Project dashboard</h1>
          <p className="muted">Podgląd danych i stanu pipeline'u.</p>
        </div>
        <span className={`badge ${status?.status === "ready" ? "ok" : ""}`}>
          {status?.status || "connecting…"}
        </span>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="cards">
        <article className="card">
          <span>Raw data</span>
          <strong>{status?.raw_data ? "Detected" : "Not found"}</strong>
          <small>{status?.raw_path || "data/raw"}</small>
        </article>
        <article className="card">
          <span>Dataset groups</span>
          <strong>{datasets?.datasets?.length ?? "—"}</strong>
          <small>Wykryte automatycznie</small>
        </article>
        <article className="card">
          <span>Pipeline</span>
          <strong>Ready</strong>
          <small>Integracja z modułami projektu — następny etap</small>
        </article>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Data / raw</h2>
          <span>{datasets?.raw_exists ? "available" : "missing"}</span>
        </div>
        {datasets?.datasets?.length ? (
          <div className="dataset-list">
            {datasets.datasets.map((item) => (
              <div className="dataset" key={item.name}>
                <div>
                  <strong>{item.name}</strong>
                  <small>{item.files} files · {formatBytes(item.bytes)}</small>
                </div>
                <span>{item.children?.length || 0} folders</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">Brak wykrytych katalogów danych.</p>
        )}
      </section>
    </main>
  );
}
