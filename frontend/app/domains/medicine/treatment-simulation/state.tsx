"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 02 state.
 */

import { createMedicineContext } from "../_shared/state-base";

export interface W02Filters {
  selectedTab: "overview" | "comparison" | "evidence";
}

export const W02Context = createMedicineContext<W02Filters>({
  selectedTab: "overview",
});

export const W02Provider = W02Context.Provider;
export const useW02Status = W02Context.useStatus;
export const useW02Selection = W02Context.useSelection;
export const useW02Narration = W02Context.useNarration;
export const useW02Filters = W02Context.useFilters;
