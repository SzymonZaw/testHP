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
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

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

  const toggle = (name) => {
    setSelected((current) => current.includes(name)
      ? current.filter((item) => item !== name)
      : [...current, name]);
  };

  const validate = async () => {
    setChecking(true);
    setError("");
    try {
      const response = await fetch(`${API}/api/pipeline/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ datasets: selected }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setPipeline(await response.json());
    } catch (e) {
      setError(`Walidacja pipeline'u nie powiodła się: ${e.message}`);
    } finally {
      setChecking(false);
    }
  };

  return (
    <main className="page">
      <header>
        <div>
          <p className="eyebrow">HUMAN PATHOLOGY PLATFORM</p>
          <h1>Project dashboard</h1>
          <p className="muted">Wybierz dostępne dane i sprawdź przepływ przez pipeline bez modyfikowania raw.</p>
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
          <span>Registered datasets</span>
          <strong>{status?.registered_datasets ?? "—"}</strong>
          <small>Źródła wykryte przez registry</small>
        </article>
        <article className="card">
          <span>Selected</span>
          <strong>{selected.length}</strong>
          <small>Źródeł do testu przepływu</small>
        </article>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Datasets</h2>
          <button onClick={validate} disabled={checking || !datasets?.registry?.length}>
            {checking ? "Sprawdzam…" : "Validate pipeline"}
          </button>
        </div>
        {datasets?.registry?.length ? (
          <div className="dataset-list">
            {datasets.registry.map((item) => (
              <label className="dataset" key={item.name}>
                <div>
                  <strong>{item.name}</strong>
                  <small>{item.modality} · {item.task || "general"} · {item.path}</small>
                </div>
                <input
                  type="checkbox"
                  checked={selected.includes(item.name)}
                  onChange={() => toggle(item.name)}
                />
              </label>
            ))}
          </div>
        ) : (
          <p className="muted">Brak zarejestrowanych danych.</p>
        )}
      </section>

      {pipeline && (
        <section className="panel">
          <div className="panel-title">
            <h2>Pipeline dry-run</h2>
            <span className={pipeline.valid ? "success" : "error-text"}>
              {pipeline.valid ? "VALID" : "BLOCKED"}
            </span>
          </div>
          <p className="muted">
            Wybrano: {pipeline.selected.length ? pipeline.selected.join(", ") : "wszystkie dostępne źródła"}.
          </p>
          <div className="dataset-list">
            {pipeline.steps.map((step) => (
              <div className="dataset" key={step.name}>
                <div>
                  <strong>{step.name}</strong>
                  <small>{step.purpose}</small>
                </div>
                <span>{step.status}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <div className="panel-title">
          <h2>Physical data/raw</h2>
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
