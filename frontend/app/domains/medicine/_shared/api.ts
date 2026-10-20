/**
 * CureVerseAI — Medicine domain
 * Shared API client.
 *
 * All three Medicine workflows call the same backend endpoint
 * (`POST /api/v1/analyze`) with a different task name and
 * different input. This module centralises that call and the
 * two read-only lookups (curated list).
 *
 * Errors are surfaced as `ApiError` instances carrying the
 * HTTP status, the backend's error message (when present),
 * and the parsed body. Callers decide how to render them.
 *
 * Never fabricates a response. If the backend returns an
 * unexpected shape, this module throws.
 */

import type {
  AnalyzeResponse,
  CuratedResponse,
  SimulationTask,
  SimulationResult,
} from "./types";

// ---------------------------------------------------------------------------
// API base
// ---------------------------------------------------------------------------

/**
 * Resolve the API base URL the same way every other CureVerseAI
 * workflow does:
 *   NEXT_PUBLIC_CUREVERSEAI_API_URL  (default http://localhost:8000)
 *
 * The trailing slash is stripped so callers can append a path
 * deterministically.
 */
function resolveApiBase(): string {
  const raw =
    process.env.NEXT_PUBLIC_CUREVERSEAI_API_URL ||
    "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

const API_BASE = resolveApiBase();

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ---------------------------------------------------------------------------
// Analyze call
// ---------------------------------------------------------------------------

interface AnalyzeInput {
  [key: string]: unknown;
}

async function callAnalyze(
  task: SimulationTask,
  input: AnalyzeInput,
): Promise<SimulationResult> {
  const url = `${API_BASE}/api/v1/analyze`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        domain: "medicine",
        task,
        input,
      }),
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error
        ? `Network error: ${err.message}`
        : "Network error: unable to reach the backend.",
      0,
      null,
    );
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? (body as { detail?: unknown }).detail
        : undefined;
    const message =
      typeof detail === "string"
        ? detail
        : detail && typeof detail === "object" && "message" in detail
        ? String((detail as { message?: unknown }).message)
        : `Backend returned ${response.status}.`;
    throw new ApiError(message, response.status, body);
  }

  const parsed = body as AnalyzeResponse | null;

  if (
    !parsed ||
    typeof parsed !== "object" ||
    !("data" in parsed) ||
    !parsed.data ||
    typeof parsed.data !== "object" ||
    !("result" in parsed.data)
  ) {
    throw new ApiError(
      "Backend returned an unexpected response shape.",
      response.status,
      body,
    );
  }

  return parsed.data.result;
}

// ---------------------------------------------------------------------------
// Public entry points
// ---------------------------------------------------------------------------

export async function runVirtualDiseaseSimulation(
  disease: string,
  cellType?: string | null,
  context?: string | null,
): Promise<SimulationResult> {
  const input: AnalyzeInput = { disease };
  if (cellType) input.cell_type = cellType;
  if (context) input.context = context;
  return callAnalyze("virtual_disease_simulation", input);
}

export async function runTreatmentSimulation(
  disease: string,
  interventionId: string,
  baselineId?: string | null,
): Promise<SimulationResult> {
  const input: AnalyzeInput = {
    disease,
    intervention_id: interventionId,
  };
  if (baselineId) input.baseline_id = baselineId;
  return callAnalyze("treatment_simulation", input);
}

export async function runCombinationTreatmentSimulation(
  disease: string,
  interventionAId: string,
  interventionBId: string,
  baselineId?: string | null,
): Promise<SimulationResult> {
  const input: AnalyzeInput = {
    disease,
    intervention_a_id: interventionAId,
    intervention_b_id: interventionBId,
  };
  if (baselineId) input.baseline_id = baselineId;
  return callAnalyze("combination_treatment_simulation", input);
}

// ---------------------------------------------------------------------------
// Curated vocabulary
// ---------------------------------------------------------------------------

export async function fetchCurated(): Promise<CuratedResponse> {
  const url = `${API_BASE}/api/v1/analyze/medicine/curated`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error
        ? `Network error: ${err.message}`
        : "Network error: unable to reach the backend.",
      0,
      null,
    );
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    throw new ApiError(
      `Curated lookup failed with status ${response.status}.`,
      response.status,
      body,
    );
  }

  const parsed = body as CuratedResponse | null;
  if (!parsed || typeof parsed !== "object" || !("curated" in parsed)) {
    throw new ApiError(
      "Backend returned an unexpected curated response shape.",
      response.status,
      body,
    );
  }

  return parsed;
}
