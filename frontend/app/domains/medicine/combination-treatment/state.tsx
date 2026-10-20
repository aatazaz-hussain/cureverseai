"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 03 state.
 */

import { createMedicineContext } from "../_shared/state-base";

export interface W03Filters {
  selectedTab: "scenarios" | "mechanism" | "evidence";
}

export const W03Context = createMedicineContext<W03Filters>({
  selectedTab: "scenarios",
});

export const W03Provider = W03Context.Provider;
export const useW03Status = W03Context.useStatus;
export const useW03Selection = W03Context.useSelection;
export const useW03Narration = W03Context.useNarration;
export const useW03Filters = W03Context.useFilters;
