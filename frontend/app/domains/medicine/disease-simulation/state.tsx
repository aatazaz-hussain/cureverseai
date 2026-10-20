"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 01 state.
 *
 * Thin wrapper around the shared state base. Supplies the
 * initial filter set for the disease-simulation view.
 */

import { createMedicineContext } from "../_shared/state-base";

export interface W01Filters {
  selectedTab: "overview" | "mechanism" | "evidence";
}

export const W01Context = createMedicineContext<W01Filters>({
  selectedTab: "overview",
});

export const W01Provider = W01Context.Provider;
export const useW01Status = W01Context.useStatus;
export const useW01Selection = W01Context.useSelection;
export const useW01Narration = W01Context.useNarration;
export const useW01Filters = W01Context.useFilters;
