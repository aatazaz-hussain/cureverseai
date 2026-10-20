/**
 * CureVerseAI — Disease → Biological Impact
 * State container.
 *
 * A React Context + useReducer that holds the current
 * pipeline status for the page.
 *
 * Shape:
 *
 *     idle     → no query submitted yet
 *     loading  → request in flight
 *     loaded   → request succeeded (resolved or unresolved)
 *     error    → request failed (network / server / etc.)
 *
 * The reducer is deliberately small. Every state change is
 * a named action, so it is obvious where any transition
 * originates. Component code reads state through hooks and
 * dispatches through a single action creator.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";

import { analyzeDisease, ApiError } from "./api";
import type { BiologicalImpactResult } from "./types";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

export type ImpactStatus =
  | { kind: "idle" }
  | { kind: "loading"; query: string; startedAt: number }
  | {
      kind: "loaded";
      query: string;
      result: BiologicalImpactResult;
    }
  | { kind: "error"; query: string; error: ApiError };

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

type Action =
  | { type: "RESET" }
  | { type: "FETCH_START"; query: string }
  | { type: "FETCH_SUCCESS"; result: BiologicalImpactResult }
  | { type: "FETCH_ERROR"; error: ApiError };

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function reducer(
  state: ImpactStatus,
  action: Action,
): ImpactStatus {
  switch (action.type) {
    case "RESET":
      return { kind: "idle" };

    case "FETCH_START":
      return {
        kind: "loading",
        query: action.query,
        startedAt: Date.now(),
      };

    case "FETCH_SUCCESS":
      // If we are not in a loading state, the caller
      // dispatched out of order. Drop the update.
      if (state.kind !== "loading") {
        return state;
      }
      return {
        kind: "loaded",
        query: state.query,
        result: action.result,
      };

    case "FETCH_ERROR":
      if (state.kind !== "loading") {
        return state;
      }
      return {
        kind: "error",
        query: state.query,
        error: action.error,
      };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface ImpactContextValue {
  status: ImpactStatus;
  analyze: (query: string) => Promise<void>;
  reset: () => void;
}

const ImpactContext = createContext<ImpactContextValue | null>(
  null,
);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function ImpactProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [status, dispatch] = useReducer(
    reducer,
    { kind: "idle" } as ImpactStatus,
  );

  const analyze = useCallback(
    async (query: string) => {
      const trimmed = (query || "").trim();

      if (!trimmed) {
        return;
      }

      dispatch({ type: "FETCH_START", query: trimmed });

      try {
        const result = await analyzeDisease(trimmed);
        dispatch({ type: "FETCH_SUCCESS", result });
      } catch (err) {
        const apiError =
          err instanceof ApiError
            ? err
            : new ApiError(
                "unknown",
                err instanceof Error
                  ? err.message
                  : String(err),
              );
        dispatch({ type: "FETCH_ERROR", error: apiError });
      }
    },
    [],
  );

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const value = useMemo<ImpactContextValue>(
    () => ({ status, analyze, reset }),
    [status, analyze, reset],
  );

  return (
    <ImpactContext.Provider value={value}>
      {children}
    </ImpactContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/**
 * Full context value. Throws if used outside a provider
 * so mistakes surface immediately during development.
 */
export function useImpact(): ImpactContextValue {
  const ctx = useContext(ImpactContext);

  if (ctx === null) {
    throw new Error(
      "useImpact must be used inside <ImpactProvider>.",
    );
  }

  return ctx;
}

/**
 * Just the status. Convenience for components that read
 * but never dispatch.
 */
export function useImpactStatus(): ImpactStatus {
  return useImpact().status;
}

/**
 * Just the analyze function. Convenience for forms.
 */
export function useAnalyze(): (query: string) => Promise<void> {
  return useImpact().analyze;
}
