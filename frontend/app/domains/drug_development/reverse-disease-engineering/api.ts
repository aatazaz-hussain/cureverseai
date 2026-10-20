/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Backend API client.
 *
 * One function: analyzeReverseDisease(query, options).
 * Posts to the backend's /api/v1/analyze endpoint with the
 * drug_development / reverse_disease_engineering task, and
 * returns the typed ReverseDiseaseResult.
 *
 * Errors are normalized into a single ApiError class with
 * a `kind` discriminator so the UI can branch on the
 * failure category without parsing message strings.
 *
 * Three successful resolution statuses are all valid
 * responses, not errors:
 *
 *   "resolved"   — the graph is populated
 *   "partial"    — the disease was ambiguous; candidates
 *                  are returned but no graph is populated
 *   "unresolved" — no disease was found
 *
 * The client returns data.result in all three cases. The
 * caller distinguishes them by reading
 * `result.resolution_status`.
 */

import type {
  AnalyzeResponseEnvelope,
  ReverseDiseaseResult,
} from "./types";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

/**
 * Backend base URL. Uses NEXT_PUBLIC_CUREVERSEAI_API_URL
 * when set, otherwise localhost:8000 (dev default).
 */
const API_BASE =
  process.env.NEXT_PUBLIC_CUREVERSEAI_API_URL ||
  "http://localhost:8000";

/**
 * W02 full pipeline runtime:
 *
 *   fetch_chembl=false  →  2-5s warm,  20-40s cold
 *   fetch_chembl=true   →  30-60s warm, 60-120s cold
 *
 * The client allows up to 300s to match the backend's own
 * client timeout against the AI Engine.
 */
const REQUEST_TIMEOUT_MS = 300_000;

/**
 * Default for the ChEMBL enrichment toggle.
 *
 * False: fast, no ChEMBL bioactivity evidence on genes.
 * True:  slower, adds target->compound->activity edges.
 *
 * Callers may override per-request via the options arg.
 * The frontend exposes this as a UI toggle.
 */
const DEFAULT_FETCH_CHEMBL = false;

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export type ApiErrorKind =
  | "network"   // Backend not reachable
  | "timeout"   // Request exceeded timeout
  | "server"    // 5xx
  | "client"    // 4xx
  | "invalid"   // 200 but unexpected body shape
  | "unknown";  // Anything else

/**
 * A normalized error thrown by analyzeReverseDisease().
 *
 * Callers should branch on `kind`, not on `message`.
 */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | null;
  readonly detail: unknown;

  constructor(
    kind: ApiErrorKind,
    message: string,
    status: number | null = null,
    detail: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

function isEnvelope(
  value: unknown,
): value is AnalyzeResponseEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const v = value as Record<string, unknown>;

  if (v.success !== true) {
    return false;
  }

  const data = v.data;

  if (!data || typeof data !== "object") {
    return false;
  }

  const result = (data as Record<string, unknown>).result;

  return !!result && typeof result === "object";
}

/**
 * Best-effort extraction of a human-readable error message
 * from a backend error response body.
 *
 * The backend returns:
 *   { "detail": { "error": "...", "message": "..." } }
 * for its own validation errors, and
 *   { "detail": { "error": "...", "message": "..." } }
 * for forwarded AI Engine errors.
 *
 * FastAPI's own validation errors return:
 *   { "detail": [ { "msg": "...", "loc": [...] }, ... ] }
 */
function extractErrorMessage(body: unknown): string {
  if (!body || typeof body !== "object") {
    return "Request failed.";
  }

  const v = body as Record<string, unknown>;
  const detail = v.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object") {
    // Our backend's error shape
    const d = detail as Record<string, unknown>;
    if (typeof d.message === "string") {
      return d.message;
    }
    if (typeof d.error === "string") {
      return d.error;
    }

    // FastAPI's own validation errors: array of { msg, loc }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (first && typeof first === "object") {
        const f = first as Record<string, unknown>;
        if (typeof f.msg === "string") {
          const loc = Array.isArray(f.loc)
            ? f.loc.join(".")
            : "";
          return loc ? `${loc}: ${f.msg}` : f.msg;
        }
      }
    }
  }

  if (typeof v.message === "string") {
    return v.message;
  }

  return "Request failed.";
}

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------

export interface AnalyzeOptions {
  /**
   * Whether the AI Engine should also query ChEMBL for
   * bioactivity evidence on each gene. Slower but richer.
   *
   * Default: false (see DEFAULT_FETCH_CHEMBL).
   */
  fetch_chembl?: boolean;

  /**
   * Optional caller-supplied abort signal. Combined with
   * the internal timeout, whichever fires first aborts the
   * request.
   */
  signal?: AbortSignal;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Run the W02 Reverse Disease Engineering pipeline for a
 * free-text disease query.
 *
 * Resolves with the typed result on success.
 * Rejects with ApiError on every failure path.
 *
 * An unresolved or ambiguous disease is NOT an error. It
 * resolves with a ReverseDiseaseResult whose
 * resolution_status is "unresolved" or "partial".
 */
export async function analyzeReverseDisease(
  query: string,
  options: AnalyzeOptions = {},
): Promise<ReverseDiseaseResult> {
  const trimmed = (query || "").trim();

  if (!trimmed) {
    throw new ApiError(
      "client",
      "Disease query cannot be empty.",
    );
  }

  const fetchChembl =
    options.fetch_chembl === undefined
      ? DEFAULT_FETCH_CHEMBL
      : Boolean(options.fetch_chembl);

  // Combine caller signal with our internal timeout.
  const controller = new AbortController();
  const timeoutHandle = setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );

  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener(
        "abort",
        () => controller.abort(),
        { once: true },
      );
    }
  }

  const url = `${API_BASE.replace(/\/$/, "")}/api/v1/analyze`;

  const body = {
    domain: "drug_development",
    task: "reverse_disease_engineering",
    input: {
      disease: trimmed,
      fetch_chembl: fetchChembl,
    },
  };

  let response: Response;

  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutHandle);

    if (
      err instanceof DOMException &&
      err.name === "AbortError"
    ) {
      throw new ApiError(
        "timeout",
        `Analysis timed out after ${REQUEST_TIMEOUT_MS / 1000}s.`,
      );
    }

    const message =
      err instanceof Error ? err.message : String(err);

    throw new ApiError(
      "network",
      `Could not reach the backend at ${API_BASE}: ${message}`,
    );
  }

  clearTimeout(timeoutHandle);

  // ---- Non-2xx responses ----------------------------------

  if (!response.ok) {
    let detail: unknown = null;

    try {
      detail = await response.json();
    } catch {
      try {
        detail = await response.text();
      } catch {
        detail = null;
      }
    }

    const message = extractErrorMessage(detail);

    if (response.status >= 500) {
      throw new ApiError(
        "server",
        message || `Server error (HTTP ${response.status}).`,
        response.status,
        detail,
      );
    }

    throw new ApiError(
      "client",
      message || `Client error (HTTP ${response.status}).`,
      response.status,
      detail,
    );
  }

  // ---- Parse 2xx response ---------------------------------

  let parsed: unknown;

  try {
    parsed = await response.json();
  } catch (err) {
    throw new ApiError(
      "invalid",
      "Backend returned a non-JSON response.",
      response.status,
      err,
    );
  }

  if (!isEnvelope(parsed)) {
    throw new ApiError(
      "invalid",
      "Backend response did not match the expected envelope.",
      response.status,
      parsed,
    );
  }

  return parsed.data.result;
}
