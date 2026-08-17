import React from "react";
import { createRoot } from "react-dom/client";
import { Search } from "lucide-react";
import "./styles.css";
import Workbench from "./workbench/Workbench";

type Source = {
  source: string;
  display_name: string;
  category: string;
  supported_filters: string[];
  recommended_for_studio: boolean;
  contract_level?: number;
  risk_level?: string;
  jurimetry_fit?: string;
  studio_tier?: string;
};

type SourceStatus = {
  status: string;
  count: number;
  reason?: string;
  message?: string;
};

type SearchResult = Record<string, unknown>;

type Filters = {
  date_from: string;
  date_to: string;
  number: string;
  page_size: string;
};

function StudioApp() {
  const [sources, setSources] = React.useState<Source[]>([]);
  const [defaultSources, setDefaultSources] = React.useState<string[]>([]);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [query, setQuery] = React.useState("");
  const [filters, setFilters] = React.useState<Filters>({
    date_from: "",
    date_to: "",
    number: "",
    page_size: "10",
  });
  const [results, setResults] = React.useState<SearchResult[]>([]);
  const [status, setStatus] = React.useState<Record<string, SourceStatus>>({});
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    fetch("/api/sources")
      .then((response) => response.json())
      .then((payload) => {
        setSources(payload.sources || []);
        setDefaultSources(payload.default_sources || []);
        setSelected(new Set(payload.default_sources || []));
      })
      .catch((reason) => setError(String(reason)));
  }, []);

  async function search(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          sources: [...selected],
          page_size: Number(filters.page_size || 10),
          filters: {
            date_from: filters.date_from,
            date_to: filters.date_to,
            number: filters.number,
          },
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setResults(payload.results || []);
      setStatus(payload.source_status || {});
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(preset: string) {
    if (preset === "clear") {
      setSelected(new Set());
      return;
    }
    if (preset === "all") {
      setSelected(new Set(sources.map((source) => source.source)));
      return;
    }
    if (preset === "juris") {
      setSelected(
        new Set(
          sources
            .filter((source) => source.recommended_for_studio)
            .map((source) => source.source),
        ),
      );
      return;
    }
    setSelected(new Set(defaultSources));
  }

  const failedOrSkipped = Object.entries(status).filter(([, item]) =>
    ["failed", "skipped", "unknown"].includes(item.status),
  );
  const restrictedSelected = sources.filter(
    (source) => selected.has(source.source) && source.studio_tier === "restricted",
  );

  return (
    <main className="studio">
      <header>
        <div>
          <strong>NanoJuris Studio</strong>
          <span>pesquisa unificada - local-first - aurora terminal</span>
        </div>
      </header>
      <form className="command" onSubmit={search}>
        <Search size={18} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="idpj desconsideracao personalidade juridica"
        />
        <button disabled={loading}>{loading ? "Buscando..." : "Buscar"}</button>
      </form>
      <section className="filters">
        <input
          type="date"
          value={filters.date_from}
          onChange={(event) => setFilters({ ...filters, date_from: event.target.value })}
        />
        <input
          type="date"
          value={filters.date_to}
          onChange={(event) => setFilters({ ...filters, date_to: event.target.value })}
        />
        <input
          value={filters.number}
          onChange={(event) => setFilters({ ...filters, number: event.target.value })}
          placeholder="processo ou tema"
        />
        <select
          value={filters.page_size}
          onChange={(event) => setFilters({ ...filters, page_size: event.target.value })}
        >
          {[5, 10, 20, 50].map((value) => (
            <option key={value} value={value}>
              {value} por fonte
            </option>
          ))}
        </select>
      </section>
      <section className="grid">
        <aside>
          <div className="presets">
            <button type="button" onClick={() => applyPreset("default")}>
              maduras
            </button>
            <button type="button" onClick={() => applyPreset("juris")}>
              jurisprudencia
            </button>
            <button type="button" onClick={() => applyPreset("all")}>
              todas
            </button>
            <button type="button" onClick={() => applyPreset("clear")}>
              limpar
            </button>
          </div>
          {restrictedSelected.length > 0 && (
            <p className="warning">
              {restrictedSelected.length} fonte(s) com risco alto selecionada(s).
            </p>
          )}
          {sources.map((source) => (
            <label key={source.source} className={source.studio_tier || ""}>
              <input
                type="checkbox"
                checked={selected.has(source.source)}
                onChange={(event) => {
                  const next = new Set(selected);
                  if (event.target.checked) next.add(source.source);
                  else next.delete(source.source);
                  setSelected(next);
                }}
              />
              <span>
                <strong>{source.display_name}</strong>
                <small>
                  {source.source} - nivel {source.contract_level || "?"} - risco{" "}
                  {source.risk_level || "?"}
                </small>
              </span>
            </label>
          ))}
        </aside>
        <section>
          <div className="status">
            {Object.entries(status).map(([source, item]) => (
              <span key={source} className={item.status}>
                {source}: {item.count} - {item.status}
              </span>
            ))}
          </div>
          {failedOrSkipped.length > 0 && (
            <details className="diagnostics" open>
              <summary>Diagnostico das fontes</summary>
              {failedOrSkipped.map(([source, item]) => (
                <article key={source}>
                  <strong>
                    {source} - {item.status}
                  </strong>
                  <p>{item.message || item.reason}</p>
                </article>
              ))}
            </details>
          )}
          {error && <div className="empty">{error}</div>}
          {loading && <div className="empty">Consultando fontes publicas...</div>}
          {!loading &&
            !error &&
            results.map((result) => (
              <article key={String(result.id)} className="result">
                <strong>
                  {String(result.case_class || result.decision_type || result.type || result.id)}
                </strong>
                <p>{String(result.summary || result.thesis || result.question || "")}</p>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </article>
            ))}
        </section>
      </section>
    </main>
  );
}

function App() {
  const pathname = window.location.pathname;
  const workbenchDefault = import.meta.env.VITE_WORKBENCH_DEFAULT !== "0";
  const workbenchRoute = pathname === "/workbench" || pathname.startsWith("/workbench/");
  const rootUsesWorkbench = pathname === "/" && workbenchDefault;
  React.useEffect(() => {
    document.title = workbenchRoute || rootUsesWorkbench ? "NanoJuris Workbench" : "NanoJuris Studio";
  }, [rootUsesWorkbench, workbenchRoute]);
  return workbenchRoute || rootUsesWorkbench ? <Workbench /> : <StudioApp />;
}

createRoot(document.getElementById("root")!).render(<App />);
