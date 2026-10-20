/**
 * CureVerseAI — Disease → Biological Impact
 * Backend API client.
 *
 * One function: analyzeDisease(query). Posts to the
 * backend's /api/v1/analyze endpoint with the
 * drug_development / disease_biological_impact task, and
 * returns the typed BiologicalImpactResult.
 *
 * Errors are normalized into a single ApiError class with
 * a `kind` discriminator so the UI can branch on the
 * failure category without parsing message strings.
 */

import type {
  AnalyzeResponseEnvelope,
  BiologicalImpactResult,
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
 * Full pipeline takes 40–90 seconds in practice. The
 * frontend allows up to 300 seconds to match the
 * backend's own client timeout against the AI Engine.
 */
const REQUEST_TIMEOUT_MS = 300_000;

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
 * A normalized error thrown by analyzeDisease().
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

function isEnvelope(value: unknown): value is AnalyzeResponseEnvelope {
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
 */
function extractErrorMessage(body: unknown): string {
  if (!body || typeof body !== "object") {
    return "Request failed.";
  }

  const v = body as Record<string, unknown>;

  // FastAPI standard shape:
  //   { "detail": "message" }
  //   { "detail": { "error": "...", "message": "..." } }
  const detail = v.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (typeof d.message === "string") {
      return d.message;
    }
    if (typeof d.error === "string") {
      return d.error;
    }
  }

  if (typeof v.message === "string") {
    return v.message;
  }

  return "Request failed.";
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Run the full Disease → Biological Impact pipeline for a
 * free-text disease query.
 *
 * Resolves with the typed result on success.
 * Rejects with ApiError on every failure path.
 *
 * An unresolvable disease is NOT an error. It resolves
 * with a BiologicalImpactResult whose
 * resolution_status === "unresolved" and whose nodes /
 * relationships / evidence arrays are empty.
 */
export async function analyzeDisease(
  query: string,
  options: { signal?: AbortSignal } = {},
): Promise<BiologicalImpactResult> {
  const trimmed = (query || "").trim();

  if (!trimmed) {
    throw new ApiError(
      "client",
      "Disease query cannot be empty.",
    );
  }

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
    task: "disease_biological_impact",
    input: { disease: trimmed },
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

    if (err instanceof DOMException && err.name === "AbortError") {
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
