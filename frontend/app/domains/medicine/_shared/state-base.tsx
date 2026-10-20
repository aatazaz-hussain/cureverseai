"use client";

/**
 * CureVerseAI — Medicine domain
 * Shared state architecture.
 *
 * Four reducers combined in one context, matching the pattern
 * used by the W02/W03 drug_development frontends:
 *
 *     status    — idle | loading | loaded | error
 *     selection — { selectedId, hoveredId }
 *     narration — { currentSegmentIndex, isPlaying, voiceEnabled }
 *     filters   — workflow-specific visible sets
 *
 * Each workflow instantiates the factory with its own filter
 * shape and initial filter values. Everything else is shared.
 *
 * No workflow-specific business logic lives here. This file
 * only provides the reducer plumbing.
 */

import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  type Dispatch,
  type ReactElement,
  type ReactNode,
} from "react";

import type { SimulationResult, SimulationStatus } from "./types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type StatusPhase = "idle" | "loading" | "loaded" | "error";

export interface StatusState {
  phase: StatusPhase;
  status: SimulationStatus | null;
  error: string | null;
  result: SimulationResult | null;
}

export interface SelectionState {
  selectedId: string | null;
  hoveredId: string | null;
}

export interface NarrationState {
  currentSegmentIndex: number;
  isPlaying: boolean;
  voiceEnabled: boolean;
}

export interface FiltersState<F> {
  values: F;
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

export type StatusAction =
  | { type: "start" }
  | { type: "success"; result: SimulationResult }
  | { type: "failure"; message: string }
  | { type: "reset" };

export type SelectionAction =
  | { type: "select"; id: string | null }
  | { type: "hover"; id: string | null }
  | { type: "clear" };

export type NarrationAction =
  | { type: "setIndex"; index: number }
  | { type: "play" }
  | { type: "pause" }
  | { type: "toggleVoice" }
  | { type: "reset" };

// ---------------------------------------------------------------------------
// Reducers
// ---------------------------------------------------------------------------

export function statusReducer(
  state: StatusState,
  action: StatusAction,
): StatusState {
  switch (action.type) {
    case "start":
      return {
        phase: "loading",
        status: null,
        error: null,
        result: null,
      };
    case "success":
      return {
        phase: "loaded",
        status: action.result.run.status,
        error: null,
        result: action.result,
      };
    case "failure":
      return {
        phase: "error",
        status: null,
        error: action.message,
        result: null,
      };
    case "reset":
      return {
        phase: "idle",
        status: null,
        error: null,
        result: null,
      };
    default:
      return state;
  }
}

export function selectionReducer(
  state: SelectionState,
  action: SelectionAction,
): SelectionState {
  switch (action.type) {
    case "select":
      return { ...state, selectedId: action.id };
    case "hover":
      return { ...state, hoveredId: action.id };
    case "clear":
      return { selectedId: null, hoveredId: null };
    default:
      return state;
  }
}

export function narrationReducer(
  state: NarrationState,
  action: NarrationAction,
): NarrationState {
  switch (action.type) {
    case "setIndex":
      return { ...state, currentSegmentIndex: action.index };
    case "play":
      return { ...state, isPlaying: true };
    case "pause":
      return { ...state, isPlaying: false };
    case "toggleVoice":
      return { ...state, voiceEnabled: !state.voiceEnabled };
    case "reset":
      return {
        currentSegmentIndex: 0,
        isPlaying: false,
        voiceEnabled: state.voiceEnabled,
      };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

export interface MedicineContextValue<F> {
  status: StatusState;
  dispatchStatus: Dispatch<StatusAction>;
  selection: SelectionState;
  dispatchSelection: Dispatch<SelectionAction>;
  narration: NarrationState;
  dispatchNarration: Dispatch<NarrationAction>;
  filters: FiltersState<F>;
  setFilters: (next: F) => void;
}

export interface MedicineProviderProps<F> {
  initialFilters: F;
  children: ReactNode;
}

export interface MedicineContextBundle<F> {
  Provider: (props: MedicineProviderProps<F>) => ReactElement;
  useStatus: () => { state: StatusState; dispatch: Dispatch<StatusAction> };
  useSelection: () => {
    state: SelectionState;
    dispatch: Dispatch<SelectionAction>;
  };
  useNarration: () => {
    state: NarrationState;
    dispatch: Dispatch<NarrationAction>;
  };
  useFilters: () => {
    state: FiltersState<F>;
    set: (next: F) => void;
  };
}

export function createMedicineContext<F>(
  initialFilters: F,
): MedicineContextBundle<F> {
  const Context = createContext<MedicineContextValue<F> | null>(null);

  function Provider(props: MedicineProviderProps<F>) {
    const [status, dispatchStatus] = useReducer(statusReducer, {
      phase: "idle",
      status: null,
      error: null,
      result: null,
    });

    const [selection, dispatchSelection] = useReducer(
      selectionReducer,
      {
        selectedId: null,
        hoveredId: null,
      },
    );

    const [narration, dispatchNarration] = useReducer(
      narrationReducer,
      {
        currentSegmentIndex: 0,
        isPlaying: false,
        voiceEnabled: true,
      },
    );

    const [filters, setFilters] = useMemo(() => {
      let current: FiltersState<F> = {
        values: props.initialFilters ?? initialFilters,
      };
      const listeners = new Set<(next: FiltersState<F>) => void>();

      const get = () => current;
      const set = (next: F) => {
        current = { values: next };
        listeners.forEach((fn) => fn(current));
      };

      return [current, set] as const;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const value = useMemo<MedicineContextValue<F>>(
      () => ({
        status,
        dispatchStatus,
        selection,
        dispatchSelection,
        narration,
        dispatchNarration,
        filters,
        setFilters,
      }),
      [status, selection, narration, filters],
    );

    return (
      <Context.Provider value={value}>{props.children}</Context.Provider>
    );
  }

  function useCtx(): MedicineContextValue<F> {
    const ctx = useContext(Context);
    if (!ctx) {
      throw new Error(
        "Medicine context used outside its Provider. " +
          "Wrap the workflow page in the workflow's Provider.",
      );
    }
    return ctx;
  }

  return {
    Provider,
    useStatus: () => {
      const c = useCtx();
      return { state: c.status, dispatch: c.dispatchStatus };
    },
    useSelection: () => {
      const c = useCtx();
      return { state: c.selection, dispatch: c.dispatchSelection };
    },
    useNarration: () => {
      const c = useCtx();
      return { state: c.narration, dispatch: c.dispatchNarration };
    },
    useFilters: () => {
      const c = useCtx();
      return { state: c.filters, set: c.setFilters };
    },
  };
}
