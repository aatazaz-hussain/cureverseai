/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Backend API client.
 *
 * One public function: analyzeTherapeuticDiscovery().
 * Posts to /api/v1/analyze with domain=drug_development,
 * task=therapeutic_discovery, and optional mechanism_id /
 * target_id handoff fields.
 *
 * Mirrors W02's api.ts pattern exactly.
 */

import type {
  AnalyzeResponseEnvelope,
  TherapeuticDiscoveryResult,
} from "./types";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const API_BASE =
  process.env.NEXT_PUBLIC_CUREVERSEAI_API_URL ||
  "http://localhost:8000";

/**
 * W03 pipeline runtime:
 *   cold:  60–150s (first run for a disease, ChEMBL-heavy)
 *   warm:  15–40s
 *
 * The client allows up to 300s, matching the backend's
 * httpx timeout against the AI Engine.
 */
const REQUEST_TIMEOUT_MS = 300_000;

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "server"
  | "client"
  | "invalid"
  | "unknown";

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
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (v.success !== true) return false;
  const data = v.data;
  if (!data || typeof data !== "object") return false;
  const result = (data as Record<string, unknown>).result;
  return !!result && typeof result === "object";
}

function extractErrorMessage(body: unknown): string {
  if (!body || typeof body !== "object") {
    return "Request failed.";
  }

  const v = body as Record<string, unknown>;
  const detail = v.detail;

  if (typeof detail === "string") return detail;

  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (typeof d.message === "string") return d.message;
    if (typeof d.error === "string") return d.error;

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

  if (typeof v.message === "string") return v.message;
  return "Request failed.";
}

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------

export interface AnalyzeOptions {
  /** Optional W02 handoff. */
  mechanism_id?: string | null;

  /** Optional direct target focus. */
  target_id?: string | null;

  /** Optional caller-supplied abort signal. */
  signal?: AbortSignal;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function analyzeTherapeuticDiscovery(
  query: string,
  options: AnalyzeOptions = {},
): Promise<TherapeuticDiscoveryResult> {
  const trimmed = (query || "").trim();

  if (!trimmed) {
    throw new ApiError(
      "client",
      "Disease query cannot be empty.",
    );
  }

  const mechanism_id =
    options.mechanism_id && options.mechanism_id.trim()
      ? options.mechanism_id.trim()
      : null;

  const target_id =
    options.target_id && options.target_id.trim()
      ? options.target_id.trim()
      : null;

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
    task: "therapeutic_discovery",
    input: {
      disease: trimmed,
      mechanism_id,
      target_id,
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
