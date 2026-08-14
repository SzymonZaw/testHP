import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [datasets, setDatasets] = useState(null);
  const [selected, setSelected] = useState([]);
  const [pipeline, setPipeline] = useState(null);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = () => {
    setError("");
    Promise.all([
      fetch(`${API}/api/status`).then((r) => r.json()),
      fetch(`${API}/api/datasets`).then((r) => r.json()),
    ])
      .then(([s, d]) => {
        setStatus(s);
        setDatasets(d);
        setSelected((current) => current.filter((name) => d.registry?.some((item) => item.name === name)));
      })
      .catch((e) => setError(`Nie można połączyć z FastAPI: ${e.message}`));
  };

  useEffect(() => { refresh(); }, []);

  const toggle = (name) => setSelected((current) => current.includes(name)
    ? current.filter((item) => item !== name)
    : [...current, name]);

  const post = async (path) => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ datasets: selected }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (e) {
      setError(`Operacja nie powiodła się: ${e.message}`);
      return null;
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page">
      <header>
        <div>
          <p className="eyebrow">HUMAN PATHOLOGY PLATFORM</p>
          <h1>Research pipeline</h1>
          <p className="muted">Wybierz dane z <code>data/raw</code>, zweryfikuj je i uruchom ścieżkę ingest → observation → digital twin.</p>
        </div>
        <span className={`badge ${status?.status === "ready" ? "ok" : ""}`}>{status?.status || "connecting…"}</span>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="cards">
        <article className="card"><span>Raw data</span><strong>{status?.raw_data ? "Detected" : "Not found"}</strong><small>{status?.raw_path || "data/raw"}</small></article>
        <article className="card"><span>Registered datasets</span><strong>{status?.registered_datasets ?? "—"}</strong><small>Źródła obecne w registry</small></article>
        <article className="card"><span>Selected</span><strong>{selected.length}</strong><small>Źródeł do uruchomienia</small></article>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Datasets</h2>
          <div className="actions">
            <button disabled={busy || !datasets?.registry?.length} onClick={async () => setPipeline(await post("/api/pipeline/validate"))}>Validate</button>
            <button className="primary" disabled={busy || !datasets?.registry?.length} onClick={async () => setRun(await post("/api/run"))}>Run ingestion</button>
          </div>
        </div>
        {datasets?.registry?.length ? <div className="dataset-list">
          {datasets.registry.map((item) => <label className="dataset" key={item.name}><div><strong>{item.name}</strong><small>{item.modality} · {item.task || "general"} · {item.path}</small></div><input type="checkbox" checked={selected.includes(item.name)} onChange={() => toggle(item.name)} /></label>)}
        </div> : <p className="muted">Brak zarejestrowanych danych.</p>}
      </section>

      {pipeline && <section className="panel">
        <div className="panel-title"><h2>Validation</h2><span className={pipeline.valid ? "success" : "error-text"}>{pipeline.valid ? "VALID" : "BLOCKED"}</span></div>
        <div className="dataset-list">{pipeline.steps.map((step) => <div className="dataset" key={step.name}><div><strong>{step.name}</strong><small>{step.purpose}</small></div><span>{step.status}</span></div>)}</div>
      </section>}

      {run && <section className="panel">
        <div className="panel-title"><h2>Execution result</h2><span className={run.status === "completed" ? "success" : "error-text"}>{run.status}</span></div>
        {run.datasets?.length > 0 && <div className="dataset-list">{run.datasets.map((item) => <div className="dataset" key={item.name}><div><strong>{item.name}</strong><small>{item.modality} · {item.observations} accepted observations · {item.files} files · {formatBytes(item.bytes)}</small></div><span>{item.status}</span></div>)}</div>}
        {run.snapshot && <div className="result-box"><strong>Digital twin snapshot: {run.snapshot.timepoint_id}</strong><small>{run.snapshot.observation_count} state entries · provenance: {run.snapshot.provenance.join(", ") || "none"}</small></div>}
        <p className="muted">{run.note}</p>
      </section>}

      <section className="panel">
        <div className="panel-title"><h2>Physical data/raw</h2><span>{datasets?.raw_exists ? "available" : "missing"}</span></div>
        {datasets?.datasets?.length ? <div className="dataset-list">{datasets.datasets.map((item) => <div className="dataset" key={item.name}><div><strong>{item.name}</strong><small>{item.files} files · {formatBytes(item.bytes)}</small></div><span>{item.children?.length || 0} folders</span></div>)}</div> : <p className="muted">Brak wykrytych katalogów danych.</p>}
      </section>
    </main>
  );
}
