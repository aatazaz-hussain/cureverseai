/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * State container.
 *
 * Four small reducers combined into one Context:
 *
 *   statusReducer    — fetch lifecycle
 *   selectionReducer — selected node / edge / candidate
 *   narrationReducer — scientific guide transcript
 *   filtersReducer   — support class + activity quality
 *
 * Mirrors W02's state pattern with one addition: the
 * candidate filter set.
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

import {
  analyzeTherapeuticDiscovery,
  ApiError,
} from "./api";
import type {
  ActivityQuality,
  SelectionTarget,
  TherapeuticDiscoveryResult,
} from "./types";

// ---------------------------------------------------------------------------
// Status
// ---------------------------------------------------------------------------

export type TDStatus =
  | { kind: "idle" }
  | {
      kind: "loading";
      query: string;
      mechanism_id: string | null;
      target_id: string | null;
      startedAt: number;
    }
  | {
      kind: "loaded";
      query: string;
      mechanism_id: string | null;
      target_id: string | null;
      result: TherapeuticDiscoveryResult;
    }
  | { kind: "error"; query: string; error: ApiError };

type StatusAction =
  | { type: "RESET" }
  | {
      type: "FETCH_START";
      query: string;
      mechanism_id: string | null;
      target_id: string | null;
    }
  | { type: "FETCH_SUCCESS"; result: TherapeuticDiscoveryResult }
  | { type: "FETCH_ERROR"; error: ApiError };

function statusReducer(
  state: TDStatus,
  action: StatusAction,
): TDStatus {
  switch (action.type) {
    case "RESET":
      return { kind: "idle" };

    case "FETCH_START":
      return {
        kind: "loading",
        query: action.query,
        mechanism_id: action.mechanism_id,
        target_id: action.target_id,
        startedAt: Date.now(),
      };

    case "FETCH_SUCCESS":
      if (state.kind !== "loading") return state;
      return {
        kind: "loaded",
        query: state.query,
        mechanism_id: state.mechanism_id,
        target_id: state.target_id,
        result: action.result,
      };

    case "FETCH_ERROR":
      if (state.kind !== "loading") return state;
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
      const prev = Math.max(0, state.currentSegmentIndex - 1);
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
  "experimentally_measured",
  "predicted",
  "unresolved",
] as const;

export const ALL_ACTIVITY_QUALITIES: ActivityQuality[] = [
  "measured",
  "qualitative",
  "none",
];

export interface FiltersState {
  visibleSupportClasses: Set<string>;
  visibleActivityQualities: Set<ActivityQuality>;
  highlightedNodeTypes: Set<string>;
}

type FiltersAction =
  | { type: "TOGGLE_SUPPORT_CLASS"; value: string }
  | { type: "TOGGLE_ACTIVITY_QUALITY"; value: ActivityQuality }
  | { type: "TOGGLE_NODE_TYPE"; value: string }
  | { type: "CLEAR_NODE_TYPES" }
  | { type: "RESET" };

const INITIAL_FILTERS: FiltersState = {
  visibleSupportClasses: new Set(ALL_SUPPORT_CLASSES),
  visibleActivityQualities: new Set(ALL_ACTIVITY_QUALITIES),
  highlightedNodeTypes: new Set(),
};

function filtersReducer(
  state: FiltersState,
  action: FiltersAction,
): FiltersState {
  switch (action.type) {
    case "TOGGLE_SUPPORT_CLASS": {
      const next = new Set(state.visibleSupportClasses);
      if (next.has(action.value)) next.delete(action.value);
      else next.add(action.value);
      return { ...state, visibleSupportClasses: next };
    }
    case "TOGGLE_ACTIVITY_QUALITY": {
      const next = new Set(state.visibleActivityQualities);
      if (next.has(action.value)) next.delete(action.value);
      else next.add(action.value);
      return { ...state, visibleActivityQualities: next };
    }
    case "TOGGLE_NODE_TYPE": {
      const next = new Set(state.highlightedNodeTypes);
      if (next.has(action.value)) next.delete(action.value);
      else next.add(action.value);
      return { ...state, highlightedNodeTypes: next };
    }
    case "CLEAR_NODE_TYPES":
      return { ...state, highlightedNodeTypes: new Set() };
    case "RESET":
      return {
        visibleSupportClasses: new Set(ALL_SUPPORT_CLASSES),
        visibleActivityQualities: new Set(
          ALL_ACTIVITY_QUALITIES,
        ),
        highlightedNodeTypes: new Set(),
      };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export interface TDActions {
  analyze: (
    query: string,
    mechanism_id?: string | null,
    target_id?: string | null,
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
  toggleActivityQuality: (value: ActivityQuality) => void;
  toggleNodeType: (value: string) => void;
  clearNodeTypes: () => void;
}

interface TDContextValue {
  status: TDStatus;
  selection: SelectionState;
  narration: NarrationState;
  filters: FiltersState;
  actions: TDActions;
}

const TDContext = createContext<TDContextValue | null>(null);

export function TDProvider({ children }: { children: ReactNode }) {
  const [status, dispatchStatus] = useReducer(
    statusReducer,
    { kind: "idle" } as TDStatus,
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
    async (
      query: string,
      mechanism_id: string | null = null,
      target_id: string | null = null,
    ) => {
      const trimmed = (query || "").trim();
      if (!trimmed) return;

      dispatchSelection({ type: "RESET" });
      dispatchNarration({ type: "RESET" });

      dispatchStatus({
        type: "FETCH_START",
        query: trimmed,
        mechanism_id,
        target_id,
      });

      try {
        const result = await analyzeTherapeuticDiscovery(
          trimmed,
          {
            mechanism_id,
            target_id,
          },
        );
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

  const actions = useMemo<TDActions>(
    () => ({
      analyze,
      reset,

      select: (target) =>
        dispatchSelection({ type: "SELECT", target }),
      clearSelection: () =>
        dispatchSelection({ type: "CLEAR_SELECTION" }),
      hover: (id) => dispatchSelection({ type: "HOVER", id }),

      playSegment: (index) =>
        dispatchNarration({ type: "PLAY", index }),
      pauseNarration: () =>
        dispatchNarration({ type: "PAUSE" }),
      stopNarration: () => dispatchNarration({ type: "STOP" }),
      nextSegment: (totalSegments) =>
        dispatchNarration({ type: "NEXT", totalSegments }),
      prevSegment: () => dispatchNarration({ type: "PREV" }),
      toggleVoice: () =>
        dispatchNarration({ type: "TOGGLE_VOICE" }),
      setVoice: (enabled) =>
        dispatchNarration({ type: "SET_VOICE", enabled }),

      toggleSupportClass: (value) =>
        dispatchFilters({
          type: "TOGGLE_SUPPORT_CLASS",
          value,
        }),
      toggleActivityQuality: (value) =>
        dispatchFilters({
          type: "TOGGLE_ACTIVITY_QUALITY",
          value,
        }),
      toggleNodeType: (value) =>
        dispatchFilters({ type: "TOGGLE_NODE_TYPE", value }),
      clearNodeTypes: () =>
        dispatchFilters({ type: "CLEAR_NODE_TYPES" }),
    }),
    [analyze, reset],
  );

  const value = useMemo<TDContextValue>(
    () => ({ status, selection, narration, filters, actions }),
    [status, selection, narration, filters, actions],
  );

  return (
    <TDContext.Provider value={value}>
      {children}
    </TDContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

function useTDContext(): TDContextValue {
  const ctx = useContext(TDContext);
  if (ctx === null) {
    throw new Error(
      "useTD* hooks must be used inside <TDProvider>.",
    );
  }
  return ctx;
}

export function useTDStatus(): TDStatus {
  return useTDContext().status;
}

export function useTDSelection(): SelectionState {
  return useTDContext().selection;
}

export function useTDNarration(): NarrationState {
  return useTDContext().narration;
}

export function useTDFilters(): FiltersState {
  return useTDContext().filters;
}

export function useTDActions(): TDActions {
  return useTDContext().actions;
}

export function useTD(): TDContextValue {
  return useTDContext();
}
