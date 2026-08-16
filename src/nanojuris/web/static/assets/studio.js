const state = {
  sources: [],
  defaultSources: [],
  selected: new Set(),
  results: [],
  documents: {},
  documentLoading: new Set(),
  documentErrors: {},
  status: {},
  searchMeta: null,
  routing: [],
  loading: false,
  validation: null,
  validationLoading: false,
  validationError: "",
  error: "",
  lastQuery: "",
  sourceFilter: "",
  filters: {
    date_from: "",
    date_to: "",
    number: "",
    page_size: "10",
  },
};

const app = document.querySelector("#app");

function sourceLabel(source) {
  return source.display_name || source.source;
}

function resultTitle(result) {
  return (
    result.title ||
    result.case_class ||
    result.decision_type ||
    result.precedent_type ||
    result.type ||
    result.id
  );
}

function resultSummary(result) {
  return result.summary || result.thesis || result.question || result.full_text || result.text || "";
}

function metadata(result) {
  return [
    ["Fonte", result.source],
    ["Tribunal", result.court],
    ["Processo", result.case_number || result.number],
    ["Classe", result.case_class],
    ["Relator", result.rapporteur],
    ["Orgao julgador", result.judging_body],
    ["Julgamento", result.judgment_date],
    ["Publicacao", result.publication_date || result.updated_at],
    ["Tipo", result.decision_type || result.precedent_type || result.type],
    ["Documento", result.document_url || result.url],
  ].filter(([, value]) => value !== undefined && value !== null && String(value).trim());
}

function render() {
  app.innerHTML = `
    <main class="studio">
      <div class="shell">
        <header class="topbar">
          <div class="brand">
            <div class="mark">NJ</div>
            <div>
              <h1>NanoJuris Studio</h1>
              <p>Pesquisa unificada de jurisprudencia publica brasileira</p>
            </div>
          </div>
          <div class="terminal-pill"><span class="terminal-dot"></span> local-first - aurora terminal</div>
        </header>

        <section class="search-panel">
          <form class="command" id="search-form">
            <input
              class="query-input"
              id="query"
              autocomplete="off"
              placeholder="> idpj desconsideracao personalidade juridica"
              value="${escapeAttribute(state.lastQuery)}"
            />
            <button class="primary" type="submit" ${state.loading ? "disabled" : ""}>
              ${state.loading ? "Buscando..." : "Buscar"}
            </button>
          </form>

          <div class="filters">
            <div class="field">
              <label for="date-from">Publicacao de</label>
              <input id="date-from" type="date" value="${escapeAttribute(state.filters.date_from)}" />
            </div>
            <div class="field">
              <label for="date-to">Publicacao ate</label>
              <input id="date-to" type="date" value="${escapeAttribute(state.filters.date_to)}" />
            </div>
            <div class="field">
              <label for="number">Processo ou tema</label>
              <input
                id="number"
                placeholder="0000000-00.0000.0.00.0000"
                value="${escapeAttribute(state.filters.number)}"
              />
            </div>
            <div class="field">
              <label for="limit">Limite por fonte</label>
              <select id="limit">
                ${[5, 10, 20, 50]
                  .map(
                    (value) =>
                      `<option value="${value}" ${
                        String(value) === String(state.filters.page_size) ? "selected" : ""
                      }>${value}</option>`,
                  )
                  .join("")}
              </select>
            </div>
          </div>

          <div class="workspace">
            <aside class="sidebar">
              <div class="sidebar-header">
                <h2>Fontes</h2>
                <span class="selection-count" aria-live="polite">${state.selected.size}/${state.sources.length}</span>
              </div>
              <p class="source-policy">
                ${state.defaultSources.length} estaveis por padrao ·
                ${state.sources.filter((source) => source.recommended_for_studio).length} recomendadas ·
                ${state.sources.length} catalogadas
              </p>
              <div class="source-presets" aria-label="Presets de fontes">
                <button class="ghost" data-preset="default" type="button" title="Fontes estaveis para uma primeira consulta">maduras (${state.defaultSources.length})</button>
                <button class="ghost" data-preset="juris" type="button" title="Todas as fontes recomendadas para jurisprudencia">jurisprudencia (${state.sources.filter((source) => source.recommended_for_studio).length})</button>
                <button class="ghost" data-preset="all" type="button" title="Todo o catalogo registrado">todas (${state.sources.length})</button>
                <button class="ghost" data-preset="clear" type="button" title="Limpar a selecao atual">limpar</button>
                <button class="ghost validate-button" data-action="validate" type="button" title="Executar uma verificacao live limitada nas fontes selecionadas" ${
                  state.validationLoading ? "disabled" : ""
                }>verificar fontes</button>
              </div>
              <label class="source-filter" for="source-filter">
                Filtrar catalogo
                <input
                  id="source-filter"
                  type="search"
                  autocomplete="off"
                  placeholder="TJDFT, STF, eproc..."
                  value="${escapeAttribute(state.sourceFilter)}"
                />
              </label>
              <p class="source-filter-count">${visibleSources().length} de ${state.sources.length} fontes visiveis</p>
              ${renderSelectionWarning()}
              <div class="source-list">
                ${visibleSources().map(renderSource).join("") || '<p class="source-filter-empty">Nenhuma fonte corresponde ao filtro.</p>'}
              </div>
            </aside>

            <section class="content">
              ${renderStatus()}
              ${renderValidation()}
              ${renderDiagnostics()}
              ${state.error ? `<div class="empty">${escapeHtml(state.error)}</div>` : renderResults()}
            </section>
          </div>
        </section>
      </div>
    </main>
  `;
  bindEvents();
}

function renderSelectionWarning() {
  const restricted = selectedSources().filter((source) => source.studio_tier === "restricted");
  if (!restricted.length) return "";
  return `
    <div class="warning">
      ${restricted.length} fonte(s) com risco alto selecionada(s). A busca pode exigir validacao,
      falhar por SSL/WAF ou demorar mais.
    </div>
  `;
}

function renderSource(source) {
  const checked = state.selected.has(source.source) ? "checked" : "";
  const filters = (source.supported_filters || []).slice(0, 4).join(" - ");
  const tier = source.studio_tier || "experimental";
  const liveReport = (state.validation?.reports || []).find(
    (report) => report.source === source.source,
  );
  const liveStatus = liveReport ? ` - live ${validationStatusLabel(liveReport.status)}` : "";
  return `
    <label class="source-card ${escapeHtml(tier)}" title="${escapeAttribute(
      source.jurimetry_fit || "",
    )}">
      <input type="checkbox" data-source="${escapeAttribute(source.source)}" ${checked} />
      <span>
        <span class="source-name">
          <span>${escapeHtml(sourceLabel(source))}</span>
          <span class="muted">${escapeHtml(source.source)}</span>
        </span>
        <span class="source-meta">
          ${escapeHtml(source.category)}
          - nivel ${escapeHtml(source.contract_level || "?")}
          - risco ${escapeHtml(source.risk_level || "?")}
          - ${escapeHtml(tier)}
          ${filters ? ` - ${escapeHtml(filters)}` : ""}
          ${escapeHtml(liveStatus)}
          ${source.documentation_url ? ` - <a class="source-doc" href="${escapeAttribute(source.documentation_url)}" target="_blank" rel="noreferrer">contrato</a>` : ""}
        </span>
      </span>
    </label>
  `;
}

function renderValidation() {
  if (state.validationLoading) {
    return `
      <section class="validation-panel" aria-live="polite" aria-busy="true">
        <div class="validation-header">
          <div>
            <h2>Verificacao live</h2>
            <p>Consultando as fontes selecionadas com uma requisicao pequena e controlada.</p>
          </div>
          <span class="status-chip">em andamento</span>
        </div>
      </section>
    `;
  }
  if (!state.validation && !state.validationError) return "";
  if (state.validationError) {
    return `
      <section class="validation-panel validation-error" aria-live="polite">
        <div class="validation-header">
          <div>
            <h2>Verificacao live</h2>
            <p>${escapeHtml(state.validationError)}</p>
          </div>
          <span class="status-chip failed">erro</span>
        </div>
      </section>
    `;
  }
  const payload = state.validation;
  const summary = Object.entries(payload.summary || {});
  const reports = payload.reports || [];
  return `
    <section class="validation-panel" aria-live="polite">
      <div class="validation-header">
        <div>
          <h2>Verificacao live</h2>
          <p>${reports.length} fonte(s) verificadas para "${escapeHtml(payload.query?.text || "")}".</p>
        </div>
        <span class="status-chip ${payload.passed ? "ok" : "failed"}">${
          payload.complete ? (payload.passed ? "contrato ok" : "atencao") : "parcial"
        }</span>
      </div>
      <div class="validation-summary">
        ${summary
          .map(
            ([status, count]) =>
              `<span class="validation-count ${escapeHtml(status)}"><strong>${count}</strong>${escapeHtml(
                validationStatusLabel(status),
              )}</span>`,
          )
          .join("")}
      </div>
      <div class="validation-list">
        ${reports.map(renderValidationReport).join("")}
      </div>
      <p class="validation-note">A verificacao e um retrato live. Ela nao garante disponibilidade futura nem substitui a leitura da fonte oficial.</p>
    </section>
  `;
}

function renderValidationReport(report) {
  const details = [
    report.returned ? `${report.returned} resultado(s)` : "sem resultados",
    report.elapsed_ms ? `${Math.round(report.elapsed_ms)} ms` : "tempo nao informado",
  ];
  if (report.reported_total !== null && report.reported_total !== undefined) {
    details.push(`${report.reported_total} total na fonte`);
  }
  return `
    <div class="validation-row ${escapeHtml(report.status)}">
      <div>
        <strong>${escapeHtml(report.source)}</strong>
        <span>${escapeHtml(details.join(" - "))}</span>
      </div>
      <span class="status-chip ${escapeHtml(report.status)}">${escapeHtml(
        validationStatusLabel(report.status),
      )}</span>
      ${
        report.message
          ? `<p>${escapeHtml(validationHumanMessage(report))}</p>
             <details class="validation-details">
               <summary>detalhes tecnicos</summary>
               <span>${escapeHtml(report.message)}</span>
             </details>`
          : ""
      }
    </div>
  `;
}

function validationHumanMessage(report) {
  return {
    blocked: "A fonte exige controle de acesso externo.",
    rate_limited: "A fonte sinalizou limite de requisicoes.",
    source_unavailable: "A fonte nao respondeu ou ficou indisponivel nesta verificacao.",
    source_changed: "A resposta da fonte mudou e precisa de revisao do provider.",
    contract_invalid: "A resposta nao passou pelo contrato normalizado minimo.",
    timeout: "A fonte excedeu o limite de tempo da verificacao.",
    error: "A verificacao encontrou um erro no provider.",
    query_rejected: "A fonte rejeitou a combinacao de consulta enviada.",
    unsupported_query: "Este provider nao oferece esta modalidade de consulta.",
  }[report.status] || report.message;
}

function validationStatusLabel(status) {
  return {
    valid: "valida",
    empty: "vazia",
    blocked: "bloqueada",
    rate_limited: "limite",
    source_unavailable: "indisponivel",
    source_changed: "contrato alterado",
    contract_invalid: "contrato invalido",
    timeout: "timeout",
    error: "erro",
    query_rejected: "consulta rejeitada",
    unsupported_query: "nao aplicavel",
  }[status] || status;
}

function renderStatus() {
  const entries = Object.entries(state.status);
  const total = state.results.length;
  const meta = state.searchMeta || {};
  const sourcesWithResults = entries.filter(([, item]) => Number(item.count || 0) > 0).length;
  const partial = entries.filter(([, item]) => item.status === "partial").length;
  const empty = entries.filter(([, item]) => item.status === "empty").length;
  const failed = entries.filter(([, item]) => item.status === "failed").length;
  const skipped = entries.filter(([, item]) => item.status === "skipped").length;
  const complete = meta.collection_complete === true;
  return `
    <div class="metrics">
      <div class="metric"><strong>${total}</strong><span>resultados nesta pagina</span></div>
      <div class="metric"><strong>${meta.total_available ?? total}</strong><span>disponiveis na coleta</span></div>
      <div class="metric"><strong>${sourcesWithResults}</strong><span>fontes com resultados</span></div>
      <div class="metric"><strong>${partial}</strong><span>fontes parciais</span></div>
      <div class="metric"><strong>${empty}</strong><span>fontes sem resultados</span></div>
      <div class="metric"><strong>${skipped}</strong><span>fora do escopo</span></div>
      <div class="metric"><strong>${failed}</strong><span>falhas visiveis</span></div>
    </div>
    ${
      meta.collection_complete !== null && meta.collection_complete !== undefined
        ? `<div class="completeness-banner ${complete ? "complete" : "partial"}" role="status">
             <strong>${complete ? "coleta completa" : "coleta parcial"}</strong>
             <span>${escapeHtml(meta.completeness_reason || "Consulte o estado de cada fonte antes de interpretar a amostra.")}</span>
             <span>Deduplicados: ${meta.deduplicated_total ?? total}</span>
           </div>`
        : ""
    }
    <div class="status-strip">
      ${
        entries.length
          ? entries
              .map(
                ([source, item]) =>
                  `<span class="status-chip ${escapeHtml(item.status)}" title="${escapeAttribute(
                    item.message || "",
                  )}">${escapeHtml(source)} - ${item.count || 0} - ${escapeHtml(
                    statusLabel(item.status),
                  )}</span>`,
              )
              .join("")
          : '<span class="status-chip">pronto para pesquisar</span>'
      }
    </div>
  `;
}

function renderDiagnostics() {
  const entries = Object.entries(state.status).filter(([, item]) =>
    ["failed", "skipped", "partial", "empty", "unknown"].includes(item.status),
  );
  if (!entries.length) return "";
  return `
    <details class="diagnostics" open>
      <summary>Diagnostico das fontes</summary>
      <div class="diagnostic-list">
        ${entries
          .map(
            ([source, item]) => `
              <div class="diagnostic ${escapeHtml(item.status)}">
                <strong>${escapeHtml(source)} - ${escapeHtml(statusLabel(item.status))}</strong>
                <span>${escapeHtml(item.reason || "sem motivo declarado")}</span>
                <p>${escapeHtml(item.message || sourceStatusMessage(item))}</p>
                <small>${item.count || 0} coletados${item.reported_total !== null && item.reported_total !== undefined ? ` de ${item.reported_total} informados pela fonte` : ""}</small>
              </div>
            `,
          )
          .join("")}
      </div>
    </details>
  `;
}

function renderResults() {
  if (state.loading) {
    return '<div class="empty">Consultando fontes publicas. Algumas rotas podem demorar ou exigir validacao externa.</div>';
  }
  if (!state.results.length) {
    return state.searchMeta
      ? '<div class="empty">Nenhum resultado nesta coleta. Verifique o estado de cada fonte e a completude antes de concluir que nao existem resultados.</div>'
      : '<div class="empty">Digite uma tese, termo juridico ou numero de processo para iniciar.</div>';
  }
  return `
    <div class="results-header">
      <h2>Resultados da coleta</h2>
      <button class="ghost" id="copy-all" type="button">copiar JSON</button>
    </div>
    <div class="results">
      ${state.results.map(renderResult).join("")}
    </div>
  `;
}

function renderResult(result, index) {
  const summary = resultSummary(result);
  const sourceUrl = result.document_url || result.url;
  const resultKey = documentKey(result);
  const loadedDocument = state.documents[resultKey];
  const documentError = state.documentErrors[resultKey];
  const source = state.sources.find((item) => item.source === result.source);
  const canLoadDocument = Boolean(
    result.full_text || result.document_url || source?.supports_full_text,
  );
  return `
    <details class="result" ${index === 0 ? "open" : ""}>
      <summary>
        <div class="result-top">
          <span class="badge source">${escapeHtml(result.source || "")}</span>
          <span class="badge">${escapeHtml(result.court || "tribunal")}</span>
          <span class="badge">${escapeHtml(result.decision_type || result.precedent_type || result.type || "registro")}</span>
        </div>
        <h3 class="result-title">${escapeHtml(resultTitle(result))}</h3>
        <p class="result-summary">${escapeHtml(summary || "Resultado publico sem resumo textual normalizado.")}</p>
      </summary>
      <div class="result-body">
        <div class="metadata-grid">
          ${metadata(result)
            .map(
              ([label, value]) =>
                `<div class="metadata"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`,
            )
            .join("")}
        </div>
        ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
        ${renderEvidence(result)}
        <div class="actions">
          <button class="ghost" data-copy="${index}" type="button">copiar resultado</button>
          ${
            canLoadDocument && !loadedDocument
              ? `<button class="ghost" data-load-document="${escapeAttribute(resultKey)}" type="button" ${
                  state.documentLoading.has(resultKey) ? "disabled" : ""
                }>${state.documentLoading.has(resultKey) ? "carregando inteiro teor..." : "carregar inteiro teor"}</button>`
              : ""
          }
          ${
            sourceUrl
              ? `<a class="ghost source-doc" href="${escapeAttribute(sourceUrl)}" target="_blank" rel="noreferrer">abrir fonte</a>`
              : ""
          }
        </div>
        ${documentError ? `<p class="document-error">${escapeHtml(documentError)}</p>` : ""}
        ${loadedDocument ? renderLoadedDocument(loadedDocument) : ""}
        <details class="raw-payload">
          <summary>ver JSON completo</summary>
          <pre class="json-view">${escapeHtml(JSON.stringify(result, null, 2))}</pre>
        </details>
      </div>
    </details>
  `;
}

function documentKey(result) {
  return `${result.source || "unknown"}:${result.id || result.document_url || "document"}`;
}

function renderLoadedDocument(document) {
  const trace = document.extraction_trace || {};
  const sourceTrace = document.source_trace || {};
  return `
    <section class="full-text-panel" aria-label="Inteiro teor carregado">
      <div class="full-text-heading">
        <strong>Inteiro teor carregado sob demanda</strong>
        <span class="status-chip ok">${escapeHtml(evidenceLabel(document.extraction_status || "loaded"))}</span>
      </div>
      <div class="evidence-grid">
        <div><span>Formato</span><strong>${escapeHtml(document.content_type || "nao informado")}</strong></div>
        <div><span>Tamanho</span><strong>${escapeHtml(formatBytes(document.byte_size))}</strong></div>
        <div><span>SHA-256</span><strong class="hash-value">${escapeHtml(document.sha256 || "nao informado")}</strong></div>
        <div><span>Bytes originais</span><strong>${document.raw_bytes_preserved ? "preservados" : "nao informado"}</strong></div>
      </div>
      <p class="document-provenance">${escapeHtml(sourceTrace.final_url || document.url || "Fonte oficial nao informada")}</p>
      ${document.text ? `<pre class="full-text-content">${escapeHtml(document.text)}</pre>` : `<p>O documento foi carregado, mas nao possui texto extraivel (${escapeHtml(trace.status || "status nao informado")}).</p>`}
    </section>
  `;
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!bytes) return "nao informado";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function renderEvidence(result) {
  const fullTextStatus = result.full_text_status || (result.full_text ? "loaded" : result.document_url ? "document_available" : "not_returned");
  const accessStatus = result.access_status || result.extraction_trace?.access_status || "not_observed";
  const extractionStatus = result.extraction_status || result.extraction_trace?.extraction_status || "not_observed";
  return `
    <div class="evidence-grid" aria-label="Estado da evidencia">
      <div><span>Conteudo textual</span><strong>${escapeHtml(evidenceLabel(fullTextStatus))}</strong></div>
      <div><span>Acesso observado</span><strong>${escapeHtml(evidenceLabel(accessStatus))}</strong></div>
      <div><span>Extracao</span><strong>${escapeHtml(evidenceLabel(extractionStatus))}</strong></div>
    </div>
  `;
}

function evidenceLabel(value) {
  return {
    loaded: "inteiro teor carregado",
    document_available: "documento disponivel",
    not_returned: "nao retornado na busca",
    public: "publico observado",
    partial: "parcial ou nao observado",
    complete: "completa",
    not_observed: "nao observado",
  }[value] || value;
}

function statusLabel(value) {
  return {
    ok: "resultado",
    complete: "completa",
    partial: "parcial",
    empty: "vazia",
    failed: "falha",
    skipped: "fora do escopo",
    unknown: "desconhecida",
  }[value] || value;
}

function sourceStatusMessage(item) {
  if (item.status === "empty") return "A fonte respondeu sem resultados para esta consulta.";
  if (item.status === "partial") return "A fonte retornou apenas uma janela parcial do total informado.";
  if (item.status === "skipped") return "A fonte nao foi consultada por incompatibilidade com a consulta.";
  if (item.status === "failed") return "A fonte falhou; isso nao significa ausencia de jurisprudencia.";
  return "Sem mensagem tecnica retornada.";
}

function bindEvents() {
  document.querySelector("#search-form")?.addEventListener("submit", submitSearch);
  document.querySelectorAll("[data-preset]").forEach((item) => {
    item.addEventListener("click", () => applyPreset(item.dataset.preset));
  });
  document.querySelector("[data-action='validate']")?.addEventListener("click", validateSources);
  document.querySelector("#query")?.addEventListener("input", updateStateFromInputs);
  document.querySelector("#date-from")?.addEventListener("change", updateStateFromInputs);
  document.querySelector("#date-to")?.addEventListener("change", updateStateFromInputs);
  document.querySelector("#number")?.addEventListener("input", updateStateFromInputs);
  document.querySelector("#limit")?.addEventListener("change", updateStateFromInputs);
  document.querySelector("#source-filter")?.addEventListener("input", (event) => {
    state.sourceFilter = event.target.value || "";
    render();
    const filter = document.querySelector("#source-filter");
    filter?.focus();
    filter?.setSelectionRange(state.sourceFilter.length, state.sourceFilter.length);
  });
  document.querySelector("#copy-all")?.addEventListener("click", () => {
    copyText(JSON.stringify(state.results, null, 2));
  });
  document.querySelectorAll("[data-source]").forEach((item) => {
    item.addEventListener("change", (event) => {
      const source = event.target.dataset.source;
      if (event.target.checked) state.selected.add(source);
      else state.selected.delete(source);
      render();
    });
  });
  document.querySelectorAll(".source-doc").forEach((item) => {
    item.addEventListener("click", (event) => event.stopPropagation());
  });
  document.querySelectorAll("[data-copy]").forEach((item) => {
    item.addEventListener("click", (event) => {
      const result = state.results[Number(event.target.dataset.copy)];
      copyText(JSON.stringify(result, null, 2));
    });
  });
  document.querySelectorAll("[data-load-document]").forEach((item) => {
    item.addEventListener("click", () => loadDocument(item.dataset.loadDocument));
  });
}

async function loadDocument(key) {
  const result = state.results.find((item) => documentKey(item) === key);
  if (!result || !result.id) return;
  state.documentLoading.add(key);
  delete state.documentErrors[key];
  render();
  try {
    const source = encodeURIComponent(result.source || "");
    const documentId = encodeURIComponent(result.id);
    const response = await fetch(`/api/documents/${source}/${documentId}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "A fonte nao carregou o documento.");
    state.documents[key] = payload;
  } catch (error) {
    state.documentErrors[key] = error.message || String(error);
  } finally {
    state.documentLoading.delete(key);
    render();
  }
}

async function submitSearch(event) {
  event.preventDefault();
  updateStateFromInputs();
  const query = state.lastQuery.trim();
  const filters = {
    date_from: state.filters.date_from,
    date_to: state.filters.date_to,
    number: state.filters.number,
  };
  state.loading = true;
  state.error = "";
  render();
  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        sources: [...state.selected],
        page_size: Number(state.filters.page_size || 10),
        filters,
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    const payload = await response.json();
    state.results = payload.results || [];
    state.status = payload.source_status || {};
    state.routing = payload.routing_summary || [];
    state.searchMeta = payload;
  } catch (error) {
    state.error = error.message || String(error);
  } finally {
    state.loading = false;
    render();
  }
}

async function validateSources() {
  updateStateFromInputs();
  state.validationLoading = true;
  state.validationError = "";
  render();
  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sources: [...state.selected],
        query: state.lastQuery.trim() || "responsabilidade civil",
        timeout: 45,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Falha na verificacao live");
    state.validation = payload;
  } catch (error) {
    state.validationError = error.message || String(error);
  } finally {
    state.validationLoading = false;
    render();
  }
}

function updateStateFromInputs() {
  state.lastQuery = document.querySelector("#query")?.value || state.lastQuery;
  state.filters = {
    date_from: document.querySelector("#date-from")?.value || "",
    date_to: document.querySelector("#date-to")?.value || "",
    number: document.querySelector("#number")?.value || "",
    page_size: document.querySelector("#limit")?.value || state.filters.page_size,
  };
}

function applyPreset(preset) {
  updateStateFromInputs();
  if (preset === "clear") {
    state.selected.clear();
  } else if (preset === "all") {
    state.sources.forEach((source) => state.selected.add(source.source));
  } else if (preset === "juris") {
    state.selected = new Set(
      state.sources
        .filter((source) => source.recommended_for_studio)
        .map((source) => source.source),
    );
  } else {
    state.selected = new Set(state.defaultSources);
  }
  render();
}

function selectedSources() {
  return state.sources.filter((source) => state.selected.has(source.source));
}

function visibleSources() {
  const query = state.sourceFilter.trim().toLowerCase();
  if (!query) return state.sources;
  return state.sources.filter((source) =>
    [source.source, source.display_name, source.category]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(query),
  );
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const element = document.createElement("textarea");
    element.value = text;
    document.body.appendChild(element);
    element.select();
    document.execCommand("copy");
    element.remove();
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

async function init() {
  render();
  try {
    const response = await fetch("/api/sources");
    const payload = await response.json();
    state.sources = payload.sources || [];
    state.defaultSources = payload.default_sources || [];
    state.selected = new Set(state.defaultSources);
  } catch (error) {
    state.error = error.message || String(error);
  }
  render();
}

init();
