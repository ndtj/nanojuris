export type WorkbenchSource = {
  source: string;
  displayName: string;
  category: string;
  count?: number;
  status: "healthy" | "partial" | "blocked" | "failed" | "ssl_error" | "skipped" | "empty" | "unknown";
  latency?: string;
  fullText: "loaded" | "available" | "summary_only" | "blocked" | "unknown";
  tier?: string;
  recommended?: boolean;
  statusReason?: string;
  statusMessage?: string;
  original?: Record<string, unknown>;
};

export type WorkbenchResult = {
  id: string;
  source: string;
  court: string;
  type: string;
  title: string;
  summary: string;
  fullText: string;
  caseNumber: string;
  rapporteur: string;
  judgingBody: string;
  judgmentDate: string;
  publicationDate: string;
  documentStatus: "loaded" | "available" | "summary_only" | "blocked";
  contentType: string;
  byteSize: string;
  sha256: string;
  parser: string;
  endpoint: string;
  officialUrl?: string;
  documentId?: string;
  collectedAt?: string;
  accessStatus: string;
  retrievalStatus: string;
  extractionStatus: string;
  sourceTrace?: Record<string, unknown>;
  extractionTrace?: Record<string, unknown>;
  raw: Record<string, unknown>;
};

export type WorkbenchSourceStatus = {
  status: string;
  count?: number;
  reportedTotal?: number | null;
  pagesFetched?: number;
  complete?: boolean | null;
  reason?: string;
  message?: string;
};

export type WorkbenchPayload = {
  sources: WorkbenchSource[];
  results: WorkbenchResult[];
  total: number;
  totalAvailable: number;
  totalReturned: number;
  deduplicatedTotal: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  nextPage?: number | null;
  elapsed: string;
  completeness: string;
  sourceStatus: Record<string, WorkbenchSourceStatus>;
  skippedSources: string[];
  errors: Array<Record<string, unknown>>;
  sourcesComplete: string[];
  sourcesPartial: string[];
  sourcesUnknown: string[];
  collectionComplete?: boolean | null;
  query: string;
  mode: "mock" | "api";
};
