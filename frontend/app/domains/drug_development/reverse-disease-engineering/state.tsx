/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * State container.
 *
 * Four small reducers, combined into one Context value:
 *
 *   statusReducer    — the fetch lifecycle (idle/loading/loaded/error)
 *   selectionReducer — what the user has selected or hovered
 *   narrationReducer — the scientific guide's transcript state
 *   filtersReducer   — which node types and support classes are visible
 *
 * Splitting them means a hover does not re-render the
 * narration panel, and toggling a filter does not re-render
 * the input form. Components read the slice they need.
 *
 * Public API:
 *
 *   <RDEProvider>          wraps the page
 *   useRDEStatus()         read status
 *   useRDESelection()      read selection
 *   useRDENarration()      read narration
 *   useRDEFilters()        read filters
 *   useRDEActions()        dispatch all actions
 *
 * The state lives entirely on the client. Nothing is
 * persisted; a page reload resets everything.
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

import { analyzeReverseDisease, ApiError } from "./api";
import type {
  ReverseDiseaseResult,
  SelectionTarget,
} from "./types";

// ---------------------------------------------------------------------------
// Status
// ---------------------------------------------------------------------------

export type RDEStatus =
  | { kind: "idle" }
  | {
      kind: "loading";
      query: string;
      fetchChembl: boolean;
      startedAt: number;
    }
  | {
      kind: "loaded";
      query: string;
      fetchChembl: boolean;
      result: ReverseDiseaseResult;
    }
  | { kind: "error"; query: string; error: ApiError };

type StatusAction =
  | { type: "RESET" }
  | {
      type: "FETCH_START";
      query: string;
      fetchChembl: boolean;
    }
  | { type: "FETCH_SUCCESS"; result: ReverseDiseaseResult }
  | { type: "FETCH_ERROR"; error: ApiError };

function statusReducer(
  state: RDEStatus,
  action: StatusAction,
): RDEStatus {
  switch (action.type) {
    case "RESET":
      return { kind: "idle" };

    case "FETCH_START":
      return {
        kind: "loading",
        query: action.query,
        fetchChembl: action.fetchChembl,
        startedAt: Date.now(),
      };

    case "FETCH_SUCCESS":
      if (state.kind !== "loading") {
        return state;
      }
      return {
        kind: "loaded",
        query: state.query,
        fetchChembl: state.fetchChembl,
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
// Selection
// ---------------------------------------------------------------------------

export interface SelectionState {
  selected: SelectionTarget;
  hoveredId: string | null;
}

type SelectionAction =
  | { type: "SELECT"; target: SelectionTarget }
  | { type: "CLEAR_SELECTION" }
  | { type: "HOVER"; id: string | null }
  | { type: "RESET" };

function selectionReducer(
  state: SelectionState,
  action: SelectionAction,
): SelectionState {
  switch (action.type) {
    case "SELECT":
      return { ...state, selected: action.target };

    case "CLEAR_SELECTION":
      return { ...state, selected: null };

    case "HOVER":
      return { ...state, hoveredId: action.id };

    case "RESET":
      return { selected: null, hoveredId: null };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Narration
// ---------------------------------------------------------------------------

export interface NarrationState {
  currentSegmentIndex: number;
  isPlaying: boolean;
  voiceEnabled: boolean;
}

type NarrationAction =
  | { type: "PLAY"; index: number }
  | { type: "PAUSE" }
  | { type: "STOP" }
  | { type: "NEXT"; totalSegments: number }
  | { type: "PREV" }
  | { type: "TOGGLE_VOICE" }
  | { type: "SET_VOICE"; enabled: boolean }
  | { type: "RESET" };

const INITIAL_NARRATION: NarrationState = {
  currentSegmentIndex: -1,
  isPlaying: false,
  voiceEnabled: true,
};

function narrationReducer(
  state: NarrationState,
  action: NarrationAction,
): NarrationState {
  switch (action.type) {
    case "PLAY":
      return {
        ...state,
        currentSegmentIndex: action.index,
        isPlaying: true,
      };

    case "PAUSE":
      return { ...state, isPlaying: false };

    case "STOP":
      return {
        ...state,
        currentSegmentIndex: -1,
        isPlaying: false,
      };

    case "NEXT": {
      const next = state.currentSegmentIndex + 1;
      if (next >= action.totalSegments) {
        return {
          ...state,
          currentSegmentIndex: action.totalSegments - 1,
          isPlaying: false,
        };
      }
      return {
        ...state,
        currentSegmentIndex: next,
        isPlaying: true,
      };
    }

    case "PREV": {
      const prev = Math.max(
        0,
        state.currentSegmentIndex - 1,
      );
      return {
        ...state,
        currentSegmentIndex: prev,
        isPlaying: true,
      };
    }

    case "TOGGLE_VOICE":
      return { ...state, voiceEnabled: !state.voiceEnabled };

    case "SET_VOICE":
      return { ...state, voiceEnabled: action.enabled };

    case "RESET":
      return { ...INITIAL_NARRATION };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------

export const ALL_SUPPORT_CLASSES = [
  "retrieved_fact",
  "supported_association",
  "mechanistic_inference",
  "unknown",
] as const;

export type SupportClass =
  (typeof ALL_SUPPORT_CLASSES)[number];

export interface FiltersState {
  visibleSupportClasses: Set<string>;
  highlightedNodeTypes: Set<string>;
}

type FiltersAction =
  | { type: "TOGGLE_SUPPORT_CLASS"; value: string }
  | { type: "SET_SUPPORT_CLASSES"; values: string[] }
  | { type: "TOGGLE_NODE_TYPE"; value: string }
  | { type: "CLEAR_NODE_TYPES" }
  | { type: "SET_NODE_TYPES"; values: string[] }
  | { type: "RESET" };

const INITIAL_FILTERS: FiltersState = {
  visibleSupportClasses: new Set([
    "retrieved_fact",
    "supported_association",
    "mechanistic_inference",
    "unknown",
  ]),
  highlightedNodeTypes: new Set(),
};

function filtersReducer(
  state: FiltersState,
  action: FiltersAction,
): FiltersState {
  switch (action.type) {
    case "TOGGLE_SUPPORT_CLASS": {
      const next = new Set(state.visibleSupportClasses);
      if (next.has(action.value)) {
        next.delete(action.value);
      } else {
        next.add(action.value);
      }
      return { ...state, visibleSupportClasses: next };
    }

    case "SET_SUPPORT_CLASSES":
      return {
        ...state,
        visibleSupportClasses: new Set(action.values),
      };

    case "TOGGLE_NODE_TYPE": {
      const next = new Set(state.highlightedNodeTypes);
      if (next.has(action.value)) {
        next.delete(action.value);
      } else {
        next.add(action.value);
      }
      return { ...state, highlightedNodeTypes: next };
    }

    case "CLEAR_NODE_TYPES":
      return {
        ...state,
        highlightedNodeTypes: new Set(),
      };

    case "SET_NODE_TYPES":
      return {
        ...state,
        highlightedNodeTypes: new Set(action.values),
      };

    case "RESET":
      return {
        visibleSupportClasses: new Set(
          INITIAL_FILTERS.visibleSupportClasses,
        ),
        highlightedNodeTypes: new Set(),
      };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Combined Provider
// ---------------------------------------------------------------------------

export interface RDEActions {
  analyze: (
    query: string,
    fetchChembl?: boolean,
  ) => Promise<void>;
  reset: () => void;

  select: (target: SelectionTarget) => void;
  clearSelection: () => void;
  hover: (id: string | null) => void;

  playSegment: (index: number) => void;
  pauseNarration: () => void;
  stopNarration: () => void;
  nextSegment: (totalSegments: number) => void;
  prevSegment: () => void;
  toggleVoice: () => void;
  setVoice: (enabled: boolean) => void;

  toggleSupportClass: (value: string) => void;
  setSupportClasses: (values: string[]) => void;
  toggleNodeType: (value: string) => void;
  clearNodeTypes: () => void;
  setNodeTypes: (values: string[]) => void;
}

interface RDEContextValue {
  status: RDEStatus;
  selection: SelectionState;
  narration: NarrationState;
  filters: FiltersState;
  actions: RDEActions;
}

const RDEContext = createContext<RDEContextValue | null>(null);

export function RDEProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [status, dispatchStatus] = useReducer(
    statusReducer,
    { kind: "idle" } as RDEStatus,
  );
  const [selection, dispatchSelection] = useReducer(
    selectionReducer,
    { selected: null, hoveredId: null } as SelectionState,
  );
  const [narration, dispatchNarration] = useReducer(
    narrationReducer,
    INITIAL_NARRATION,
  );
  const [filters, dispatchFilters] = useReducer(
    filtersReducer,
    INITIAL_FILTERS,
  );

  const analyze = useCallback(
    async (query: string, fetchChembl = false) => {
      const trimmed = (query || "").trim();
      if (!trimmed) return;

      // Reset transient UI state whenever a new query starts.
      dispatchSelection({ type: "RESET" });
      dispatchNarration({ type: "RESET" });

      dispatchStatus({
        type: "FETCH_START",
        query: trimmed,
        fetchChembl,
      });

      try {
        const result = await analyzeReverseDisease(trimmed, {
          fetch_chembl: fetchChembl,
        });
        dispatchStatus({ type: "FETCH_SUCCESS", result });
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
        dispatchStatus({ type: "FETCH_ERROR", error: apiError });
      }
    },
    [],
  );

  const reset = useCallback(() => {
    dispatchStatus({ type: "RESET" });
    dispatchSelection({ type: "RESET" });
    dispatchNarration({ type: "RESET" });
    dispatchFilters({ type: "RESET" });
  }, []);

  const actions = useMemo<RDEActions>(
    () => ({
      analyze,
      reset,

      select: (target) =>
        dispatchSelection({ type: "SELECT", target }),
      clearSelection: () =>
        dispatchSelection({ type: "CLEAR_SELECTION" }),
      hover: (id) =>
        dispatchSelection({ type: "HOVER", id }),

      playSegment: (index) =>
        dispatchNarration({ type: "PLAY", index }),
      pauseNarration: () =>
        dispatchNarration({ type: "PAUSE" }),
      stopNarration: () =>
        dispatchNarration({ type: "STOP" }),
      nextSegment: (totalSegments) =>
        dispatchNarration({
          type: "NEXT",
          totalSegments,
        }),
      prevSegment: () =>
        dispatchNarration({ type: "PREV" }),
      toggleVoice: () =>
        dispatchNarration({ type: "TOGGLE_VOICE" }),
      setVoice: (enabled) =>
        dispatchNarration({ type: "SET_VOICE", enabled }),

      toggleSupportClass: (value) =>
        dispatchFilters({
          type: "TOGGLE_SUPPORT_CLASS",
          value,
        }),
      setSupportClasses: (values) =>
        dispatchFilters({
          type: "SET_SUPPORT_CLASSES",
          values,
        }),
      toggleNodeType: (value) =>
        dispatchFilters({ type: "TOGGLE_NODE_TYPE", value }),
      clearNodeTypes: () =>
        dispatchFilters({ type: "CLEAR_NODE_TYPES" }),
      setNodeTypes: (values) =>
        dispatchFilters({ type: "SET_NODE_TYPES", values }),
    }),
    [analyze, reset],
  );

  const value = useMemo<RDEContextValue>(
    () => ({ status, selection, narration, filters, actions }),
    [status, selection, narration, filters, actions],
  );

  return (
    <RDEContext.Provider value={value}>
      {children}
    </RDEContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

function useRDEContext(): RDEContextValue {
  const ctx = useContext(RDEContext);
  if (ctx === null) {
    throw new Error(
      "useRDE* hooks must be used inside <RDEProvider>.",
    );
  }
  return ctx;
}

/** Fetch lifecycle. */
export function useRDEStatus(): RDEStatus {
  return useRDEContext().status;
}

/** Selected node/edge and hover id. */
export function useRDESelection(): SelectionState {
  return useRDEContext().selection;
}

/** Narration transcript state. */
export function useRDENarration(): NarrationState {
  return useRDEContext().narration;
}

/** Support-class and node-type filters. */
export function useRDEFilters(): FiltersState {
  return useRDEContext().filters;
}

/** Dispatch functions. Stable identity across renders. */
export function useRDEActions(): RDEActions {
  return useRDEContext().actions;
}

/** Convenience hook for the very few places that need everything. */
export function useRDE(): RDEContextValue {
  return useRDEContext();
}
