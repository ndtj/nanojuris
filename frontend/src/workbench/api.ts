import type { WorkbenchPayload, WorkbenchResult, WorkbenchSource, WorkbenchSourceStatus } from "./types";

const DATA_MODE = import.meta.env.VITE_DATA_MODE === "mock" ? "mock" : "api";

function statusForSource(status: string): WorkbenchSource["status"] {
  status = status.toLowerCase();
  if (["ok", "healthy", "valid"].includes(status)) return "healthy";
  if (["partial", "degraded"].includes(status)) return "partial";
  if (["blocked", "access_controlled", "restricted"].includes(status)) return "blocked";
  if (["ssl_error", "ssl_verification_error", "certificate_error", "tls_error"].includes(status)) return "ssl_error";
  if (["failed", "error", "unavailable", "timeout"].includes(status)) return "failed";
  if (["skipped", "not_attempted"].includes(status)) return "skipped";
  if (["empty", "real_empty"].includes(status)) return "empty";
  return "unknown";
}

function stringValue(value: unknown, fallback = ""): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function objectValue(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : undefined;
}

function adaptSource(item: Record<string, unknown>, sourceStatus: Record<string, WorkbenchSourceStatus> = {}): WorkbenchSource {
  const id = stringValue(item.source || item.id, "unknown");
  const observed = sourceStatus[id];
  return {
    source: id,
    displayName: stringValue(item.display_name || item.displayName, id),
    category: stringValue(item.category, "outras"),
    count: observed?.count,
    status: statusForSource(observed?.status || (Object.keys(sourceStatus).length ? "skipped" : "unknown")),
    fullText: item.supports_full_text ? "available" : "summary_only",
    tier: stringValue(item.studio_tier || item.maturity_tier, "experimental"),
    recommended: item.recommended_for_studio !== false,
    statusReason: stringValue(observed?.reason),
    statusMessage: stringValue(observed?.message),
    original: item,
  };
}

export function adaptResult(raw: Record<string, unknown>, index: number, sourceStatus: Record<string, WorkbenchSourceStatus> = {}): WorkbenchResult {
  const source = stringValue(raw.source || raw.provider, "unknown");
  const trace = objectValue(raw.source_trace || raw.sourceTrace);
  const extractionTrace = objectValue(raw.extraction_trace || raw.extractionTrace);
  const fullText = stringValue(raw.full_text || raw.fullText || raw.text || raw.content);
  const documentId = stringValue(raw.document_id || raw.documentId || raw.id || `${source}-${index}`);
  const officialUrl = stringValue(
    raw.document_url || raw.documentUrl || raw.full_text_url || raw.fullTextUrl || raw.source_url || raw.sourceUrl ||
      trace?.source_url || trace?.sourceUrl || raw.endpoint,
  );
  const accessStatus = stringValue(raw.access_status || raw.accessStatus, "public").toLowerCase();
  const retrievalStatus = stringValue(raw.retrieval_status || raw.retrievalStatus, "unknown").toLowerCase();
  const extractionStatus = stringValue(raw.extraction_status || raw.extractionStatus, "unknown").toLowerCase();
  const observedStatus = stringValue(sourceStatus[source]?.status).toLowerCase();
  const blocked = ["blocked", "access_controlled", "challenge_required", "captcha", "forbidden", "restricted"].some((value) => accessStatus.includes(value)) ||
    ["blocked", "access_controlled", "challenge_required"].includes(observedStatus) || extractionStatus.includes("access_control");
  const hasDocument = Boolean(raw.document_url || raw.documentUrl || raw.full_text_url || raw.fullTextUrl || raw.document_id || raw.documentId);
  const documentStatus: WorkbenchResult["documentStatus"] = blocked ? "blocked" : fullText ? "loaded" : hasDocument ? "available" : "summary_only";
  return {
    id: stringValue(raw.id, `${source}-${index}`),
    source,
    court: stringValue(raw.court || raw.court_name, source),
    type: stringValue(raw.decision_type || raw.type || raw.document_type, "Tipo não informado"),
    title: stringValue(raw.title || raw.case_class || raw.thesis || raw.summary, "Registro sem título informado pela fonte"),
    summary: stringValue(raw.summary || raw.ementa || raw.thesis || raw.question, "Conteúdo textual não informado pela fonte."),
    fullText,
    caseNumber: stringValue(raw.case_number || raw.number || raw.process_number, "Não informado"),
    rapporteur: stringValue(raw.rapporteur || raw.relator, "Não informado"),
    judgingBody: stringValue(raw.judging_body || raw.orgao_julgador, "Não informado"),
    judgmentDate: stringValue(raw.judgment_date || raw.decision_date, "Não informado"),
    publicationDate: stringValue(raw.publication_date, "Não informado"),
    documentStatus,
    contentType: stringValue(raw.content_type || raw.contentType, "não informado"),
    byteSize: stringValue(raw.response_bytes || raw.byte_size || raw.byteSize, "não informado"),
    sha256: stringValue(raw.content_sha256 || raw.sha256, "não calculado"),
    parser: stringValue(raw.parser || raw.parser_name, "não informado"),
    endpoint: stringValue(raw.endpoint || trace?.endpoint, "não informado"),
    officialUrl: officialUrl || undefined,
    documentId: documentId || undefined,
    collectedAt: stringValue(raw.retrieved_at || raw.collected_at || trace?.retrieved_at) || undefined,
    accessStatus,
    retrievalStatus,
    extractionStatus,
    sourceTrace: trace,
    extractionTrace,
    raw,
  };
}

export async function loadWorkbenchDocument(item: WorkbenchResult): Promise<WorkbenchResult> {
  if (DATA_MODE === "mock") {
    return item.documentStatus === "available" ? { ...item, documentStatus: "loaded", extractionStatus: "complete" } : item;
  }
  const response = await fetch(`/api/documents/${encodeURIComponent(item.source)}/${encodeURIComponent(item.documentId || item.id)}`);
  if (!response.ok) throw new Error("O documento não pôde ser carregado.");
  const payload = (await response.json()) as Record<string, unknown>;
  return adaptResult({ ...item.raw, ...payload, id: payload.id || item.id, source: payload.source || item.source }, 0);
}

export type WorkbenchSearchOptions = {
  sources?: string[];
  filters?: Record<string, unknown>;
  types?: string[];
  page?: number;
  pageSize?: number;
  onSources?: (sources: WorkbenchSource[]) => void;
};

export async function loadWorkbench(query: string, state: string, options: WorkbenchSearchOptions = {}): Promise<WorkbenchPayload> {
  if (DATA_MODE === "mock") {
    const { createMockPayload } = await import("./mock");
    return createMockPayload(query, state);
  }
  const startedAt = performance.now();
  const filters = Object.fromEntries(Object.entries(options.filters || {}).filter(([, value]) => value !== "" && value !== undefined && value !== null));
  const sourcesResponsePromise = fetch("/api/sources").then(async (response) => {
    if (!response.ok) throw new Error("Não foi possível carregar o catálogo de fontes.");
    const payload = (await response.json()) as Record<string, unknown>;
    const rawSources = Array.isArray(payload.sources) ? payload.sources : [];
    options.onSources?.(rawSources.map((item) => adaptSource(item as Record<string, unknown>)));
    return payload;
  });
  const searchResponse = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, sources: options.sources || [], types: options.types || [], page: options.page || 1, page_size: options.pageSize || 10, filters }),
  });
  const sourcesPayload = await sourcesResponsePromise;
  if (!searchResponse.ok) throw new Error("Não foi possível carregar a pesquisa.");
  const searchPayload = (await searchResponse.json()) as Record<string, unknown>;
  const sourceStatus = (searchPayload.source_status || {}) as Record<string, WorkbenchSourceStatus>;
  const rawSources = Array.isArray(sourcesPayload.sources) ? sourcesPayload.sources : [];
  const rawResults = Array.isArray(searchPayload.results) ? searchPayload.results : [];
  const totalReturned = Number(searchPayload.total_returned ?? rawResults.length);
  const deduplicatedTotal = Number(searchPayload.deduplicated_total ?? totalReturned);
  return {
    sources: rawSources.map((item) => adaptSource(item as Record<string, unknown>, sourceStatus)),
    results: rawResults.map((item, index) => adaptResult(item as Record<string, unknown>, index, sourceStatus)),
    total: deduplicatedTotal,
    totalAvailable: Number(searchPayload.total_available ?? totalReturned),
    totalReturned,
    deduplicatedTotal,
    page: Number(searchPayload.page ?? options.page ?? 1),
    pageSize: Number(searchPayload.page_size ?? options.pageSize ?? 10),
    hasMore: Boolean(searchPayload.has_more),
    nextPage: searchPayload.next_page === null || searchPayload.next_page === undefined ? null : Number(searchPayload.next_page),
    elapsed: `${((performance.now() - startedAt) / 1000).toFixed(2)} s`,
    completeness: stringValue(searchPayload.completeness_reason, "Completude não informada"),
    sourceStatus,
    skippedSources: Array.isArray(searchPayload.skipped_sources) ? searchPayload.skipped_sources.map(String) : [],
    errors: Array.isArray(searchPayload.errors) ? searchPayload.errors as Array<Record<string, unknown>> : [],
    sourcesComplete: Array.isArray(searchPayload.sources_complete) ? searchPayload.sources_complete.map(String) : [],
    sourcesPartial: Array.isArray(searchPayload.sources_partial) ? searchPayload.sources_partial.map(String) : [],
    sourcesUnknown: Array.isArray(searchPayload.sources_unknown) ? searchPayload.sources_unknown.map(String) : [],
    collectionComplete: searchPayload.collection_complete as boolean | null | undefined,
    query: stringValue(searchPayload.query, query),
    mode: "api",
  };
}
