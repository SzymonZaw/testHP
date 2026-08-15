import { useEffect, useMemo, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const stageLabels = {
  ingestion_validation: ["Input & ingestion", "Read the selected sources and check what is actually available."],
  normalization_preprocessing: ["Normalization", "Convert source files into common observations."],
  multimodal_fusion: ["Multimodal fusion", "Combine dataset-level evidence without inventing subject links."],
  quality_uncertainty: ["Quality & uncertainty", "Check observation quality and propagate limitations."],
  hierarchical_biological_state: ["Biological state", "Organize observations into the supported biological hierarchy."],
  digital_biological_twin: ["Digital twin snapshot", "Create a provenance-preserving computational snapshot."],
  anomaly_longitudinal_analysis: ["Anomaly & longitudinal analysis", "Look for signals while refusing unsupported trajectory claims."],
  pipeline_evaluation: ["Research evaluation", "Summarize evidence coverage and readiness."],
  decision_support: ["Research decision support", "Return a conservative research-level outcome."],
  audit_and_provenance: ["Audit & provenance", "Record what happened, when, and with which limitations."],
};

const modalityLabels = { image: "Images", wsi: "Whole-slide images", rna: "RNA / transcriptomics", hand: "Hand / pose" };

function formatBytes(bytes = 0) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

function prettyStatus(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

function StatusDot({ status }) {
  const tone = status === "completed" || status === "ok" ? "good" : status === "warning" ? "warn" : "neutral";
  return <span className={`status-dot ${tone}`} aria-label={status} />;
}

function Metric({ label, value, detail }) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [datasets, setDatasets] = useState(null);
  const [selected, setSelected] = useState([]);
  const [run, setRun] = useState(null);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    setError("");
    try {
      const [statusResponse, datasetsResponse] = await Promise.all([
        fetch(`${API}/api/status`),
        fetch(`${API}/api/datasets`),
      ]);
      if (!statusResponse.ok || !datasetsResponse.ok) throw new Error("API request failed");
      const [nextStatus, nextDatasets] = await Promise.all([statusResponse.json(), datasetsResponse.json()]);
      setStatus(nextStatus);
      setDatasets(nextDatasets);
      setSelected((current) => current.filter((name) => nextDatasets.registry?.some((item) => item.name === name)));
    } catch (e) {
      setError(`Cannot connect to the research API: ${e.message}`);
    }
  };

  useEffect(() => { refresh(); }, []);

  const registry = datasets?.registry || [];
  const visibleRegistry = useMemo(
    () => filter === "all" ? registry : registry.filter((item) => item.modality === filter),
    [registry, filter],
  );

  const toggle = (name) => {
    setSelected((current) => current.includes(name)
      ? current.filter((item) => item !== name)
      : [...current, name]);
    setRun(null);
  };

  const selectVisible = () => {
    const names = visibleRegistry.map((item) => item.name);
    setSelected((current) => [...new Set([...current, ...names])]);
  };

  const clearSelection = () => setSelected([]);

  const execute = async () => {
    setBusy(true);
    setError("");
    setRun(null);
    try {
      const response = await fetch(`${API}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ datasets: selected }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setRun(await response.json());
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    } catch (e) {
      setError(`The research run could not be completed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const runModalities = useMemo(() => {
    const map = {};
    (run?.datasets || []).forEach((item) => {
      map[item.modality] = (map[item.modality] || 0) + item.files;
    });
    return map;
  }, [run]);

  const runFiles = Object.values(runModalities).reduce((sum, value) => sum + value, 0);
  const runDatasetNames = new Set((run?.datasets || []).map((item) => item.name));
  const unavailable = run?.invalid || [];
  const limitations = run?.limitations || [];

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">RESEARCH PLATFORM</p>
          <h1>Human Pathology Platform</h1>
          <p className="hero-copy">From multimodal input to transparent research evidence.</p>
        </div>
        <div className="system-state">
          <StatusDot status={status?.status === "ready" ? "completed" : "warning"} />
          <div><strong>{status?.status === "ready" ? "System ready" : "Connecting"}</strong><small>Local research environment</small></div>
        </div>
      </header>

      {error && <div className="notice danger">{error}</div>}

      <section className="overview panel">
        <div className="section-heading">
          <div><p className="eyebrow">RUN OVERVIEW</p><h2>Understand what entered the platform and what happened to it.</h2></div>
          <button className="primary large" onClick={execute} disabled={busy || !datasets}>
            {busy ? "Running…" : "Run research pipeline"}
          </button>
        </div>
        <p className="muted">The dashboard separates data availability, processing state and biological inference. Missing or unsupported data is shown as a limitation rather than silently converted into a result.</p>
        <div className="metrics">
          <Metric label="Datasets" value={selected.length || registry.length} detail={selected.length ? "selected for this run" : "available in the registry"} />
          <Metric label="Input files" value={run ? runFiles : "—"} detail={run ? "processed files" : "shown after a run"} />
          <Metric label="Modalities" value={run ? Object.keys(runModalities).length : 4} detail="represented in the run" />
          <Metric label="Subject links" value={run?.fusion?.linked_subjects ?? 0} detail="explicit links only" />
        </div>
      </section>

      <section className="panel">
        <div className="section-heading compact"><div><p className="eyebrow">PIPELINE</p><h2>What happened?</h2></div>{run && <span className="run-badge"><StatusDot status={run.status === "completed" ? "completed" : "warning"} /> Run {prettyStatus(run.status)}</span>}</div>
        <div className="pipeline-track">
          {(run?.stages || [
            { stage: 1, name: "ingestion_validation", status: "pending" },
            { stage: 2, name: "normalization_preprocessing", status: "pending" },
            { stage: 3, name: "multimodal_fusion", status: "pending" },
            { stage: 4, name: "quality_uncertainty", status: "pending" },
            { stage: 5, name: "hierarchical_biological_state", status: "pending" },
            { stage: 6, name: "digital_biological_twin", status: "pending" },
            { stage: 7, name: "anomaly_longitudinal_analysis", status: "pending" },
            { stage: 8, name: "pipeline_evaluation", status: "pending" },
            { stage: 9, name: "decision_support", status: "pending" },
            { stage: 10, name: "audit_and_provenance", status: "pending" },
          ]).map((stage) => {
            const [title, description] = stageLabels[stage.name] || [prettyStatus(stage.name), "Research pipeline stage"];
            return <div className={`stage ${stage.status}`} key={stage.stage}><div className="stage-number">{stage.stage}</div><div><div className="stage-title"><strong>{title}</strong><StatusDot status={stage.status} /></div><small>{description}</small>{stage.reason && <p className="stage-reason">{stage.reason}</p>}</div></div>;
          })}
        </div>
      </section>

      {run && <>
        <section className="panel">
          <div className="section-heading compact"><div><p className="eyebrow">INPUT</p><h2>Data coverage</h2></div><span className="muted">{runDatasetNames.size} datasets contributed observations</span></div>
          <div className="coverage-grid">
            {Object.entries(runModalities).map(([modality, count]) => <div className="coverage" key={modality}><div><strong>{modalityLabels[modality] || modality}</strong><span>{count}</span></div><div className="bar"><i style={{ width: `${runFiles ? Math.max(4, count / runFiles * 100) : 0}%` }} /></div></div>)}
          </div>
          <div className="coverage-note">Fusion reports <strong>{run.fusion?.linked_subjects ?? 0} explicit subject links</strong>. Similarity between public datasets is not treated as a patient identity.</div>
        </section>

        <section className="panel evidence-panel">
          <div className="section-heading compact"><div><p className="eyebrow">EVIDENCE</p><h2>Research result</h2></div><span className={`result-status ${run.status === "completed" ? "good" : "warn"}`}>{run.status === "completed" ? "✓" : "!"}</span></div>
          <div className="evidence-main"><div><strong>dataset-level research evidence</strong><p>{run.snapshot ? `${run.snapshot.observation_count} state entries were integrated into the computational snapshot.` : "No snapshot was created."}</p></div><span className="evidence-label">Not a clinical diagnosis</span></div>
          <div className="result-callout"><strong>Next:</strong> Review the modality coverage and validation warnings before enabling downstream models.</div>
          {limitations.length > 0 && <div className="limitations"><h3>Limitations to review</h3>{limitations.map((item, index) => <div className="limitation" key={`${item}-${index}`}><span>!</span><p>{item}</p></div>)}</div>}
        </section>
      </>}

      <section className="panel">
        <div className="section-heading compact"><div><p className="eyebrow">DATASET EXPLORER</p><h2>Input by dataset</h2></div><div className="explorer-actions"><button onClick={selectVisible}>Select visible</button><button onClick={clearSelection}>Clear</button></div></div>
        <div className="filters"><button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>All</button>{["image", "wsi", "rna", "hand"].map((modality) => <button className={filter === modality ? "active" : ""} key={modality} onClick={() => setFilter(modality)}>{modalityLabels[modality]}</button>)}</div>
        <div className="table">
          <div className="table-row table-head"><span>Dataset</span><span>Modality</span><span>Task</span><span>Files</span><span>Coverage</span><span>Status</span></div>
          {visibleRegistry.map((item) => {
            const unavailableHere = run && unavailable.includes(item.name);
            const contributed = runDatasetNames.has(item.name);
            return <div className={`table-row ${expanded === item.name ? "expanded" : ""}`} key={item.name}>
              <button className="dataset-name" onClick={() => setExpanded(expanded === item.name ? null : item.name)}><span className="chevron">{expanded === item.name ? "⌄" : "›"}</span><strong>{item.name}</strong></button>
              <span className="cell-muted">{item.modality}</span>
              <span className="cell-muted">{item.task || "research dataset"}</span>
              <span className="cell-muted">{run && contributed ? (run.datasets.find((d) => d.name === item.name)?.files ?? 0) : "—"}</span>
              <span className="cell-muted">{run && contributed ? "processed" : item.has_data ? "available" : "not present"}</span>
              <span className={unavailableHere ? "status-text warn" : contributed ? "status-text good" : "status-text"}>{unavailableHere ? "Unavailable" : contributed ? "Available" : item.has_data ? "Ready" : "Unavailable"}</span>
              {expanded === item.name && <div className="dataset-detail"><p>{item.description || "Registered research dataset."}</p><small>{item.path}</small>{item.tags?.length > 0 && <div className="tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>}<label className="select-row"><input type="checkbox" checked={selected.includes(item.name)} onChange={() => toggle(item.name)} /> Include in next run</label></div>}
            </div>;
          })}
        </div>
      </section>

      <footer>Human Pathology Platform · research prototype · evidence and limitations are shown explicitly.</footer>
    </main>
  );
}
