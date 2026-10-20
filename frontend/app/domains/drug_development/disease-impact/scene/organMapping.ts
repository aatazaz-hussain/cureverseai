/**
 * CureVerseAI — Disease → Biological Impact
 * System → organ mapping.
 *
 * Monarch's histopheno endpoint returns system labels like
 * "nervous_system" or "respiratory_system". This module
 * maps those labels to the organs we render (see
 * organs.ts).
 *
 * The mapping is deliberately generous: if a system label
 * is not in the map, we fall back to a group-level match
 * so nothing is silently dropped. If nothing matches, we
 * return an empty list, and the scene simply renders the
 * body without highlights.
 */

import { ORGANS, type OrganDef } from "./organs";

// ---------------------------------------------------------------------------
// Explicit label → organ id map
// ---------------------------------------------------------------------------

/**
 * Monarch system label (lowercased) → list of organ ids.
 *
 * Keys are matched after normalizing the input:
 * lowercased, spaces → underscores, trailing/leading
 * whitespace removed.
 */
const LABEL_TO_ORGAN_IDS: Record<string, string[]> = {
  // Nervous
  nervous_system: ["brain", "eye_left", "eye_right", "spine"],
  central_nervous_system: ["brain", "spine"],
  peripheral_nervous_system: ["spine"],
  brain: ["brain"],
  eye: ["eye_left", "eye_right"],

  // Cardiovascular
  cardiovascular_system: ["heart"],
  heart: ["heart"],
  vascular_system: ["heart"],

  // Respiratory
  respiratory_system: ["lung_left", "lung_right"],
  respiratory: ["lung_left", "lung_right"],
  lung: ["lung_left", "lung_right"],

  // Digestive
  digestive_system: ["liver", "stomach", "pancreas", "intestine_large", "intestine_small"],
  gastrointestinal_system: ["stomach", "intestine_large", "intestine_small"],
  liver: ["liver"],
  stomach: ["stomach"],
  pancreas: ["pancreas"],
  intestine: ["intestine_large", "intestine_small"],

  // Renal / urinary
  renal_system: ["kidney_left", "kidney_right", "bladder"],
  urinary_system: ["kidney_left", "kidney_right", "bladder"],
  kidney: ["kidney_left", "kidney_right"],
  bladder: ["bladder"],

  // Endocrine
  endocrine_system: ["thyroid", "adrenal_left", "adrenal_right"],
  thyroid: ["thyroid"],
  adrenal_gland: ["adrenal_left", "adrenal_right"],

  // Immune
  immune_system: ["spleen", "thymus"],
  lymphatic_system: ["spleen", "thymus"],
  spleen: ["spleen"],
  thymus: ["thymus"],

  // Reproductive
  reproductive_system: ["uterus"],
  reproductive: ["uterus"],
  uterus: ["uterus"],

  // Musculoskeletal
  musculoskeletal_system: ["spine", "ribs", "pelvis", "skull"],
  skeletal_system: ["spine", "ribs", "pelvis", "skull"],
  skeletal: ["spine", "ribs", "pelvis", "skull"],
  bone: ["spine", "ribs", "pelvis", "skull"],

  // Integumentary (body surface)
  integumentary_system: [],
  body_surface: [],

  // Metabolism (fallback — touches several systems)
  metabolism_homeostasis: ["liver", "kidney_left", "kidney_right", "pancreas"],
  metabolism: ["liver", "kidney_left", "kidney_right", "pancreas"],

  // Head / neck is a broad category that usually implies
  // brain or thyroid involvement.
  head_neck: ["brain", "thyroid", "eye_left", "eye_right"],
  head: ["brain"],
  neck: ["thyroid"],

  // Blood is broad; we highlight the spleen as the primary
  // blood-related organ.
  blood: ["spleen"],

  // Musculature is broad; no specific organ to highlight.
  musculature: [],
};

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Normalize a Monarch system label to the key format
 * used by LABEL_TO_ORGAN_IDS.
 */
function normalizeLabel(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/-/g, "_");
}

/**
 * Resolve a system label to a list of organ definitions.
 *
 * Matching order:
 *   1. Exact match in LABEL_TO_ORGAN_IDS
 *   2. Fallback: substring match against known labels
 *      (e.g. "respiratory_disorder" → respiratory_system)
 *   3. Empty list
 *
 * Duplicate organs are removed; the returned list is
 * ordered by ORGANS definition order for deterministic
 * rendering.
 */
export function organsForSystem(label: string): OrganDef[] {
  if (!label) return [];

  const normalized = normalizeLabel(label);

  // 1) Exact match
  let ids = LABEL_TO_ORGAN_IDS[normalized];

  // 2) Fallback: substring search
  if (!ids) {
    for (const [key, value] of Object.entries(LABEL_TO_ORGAN_IDS)) {
      if (normalized.includes(key) || key.includes(normalized)) {
        ids = value;
        break;
      }
    }
  }

  if (!ids || ids.length === 0) {
    return [];
  }

  // Deduplicate and return in ORGANS order.
  const idSet = new Set(ids);
  return ORGANS.filter((o) => idSet.has(o.id));
}

/**
 * Given a list of system labels (from the AI Engine's
 * reasoning or system nodes), return the union of organs
 * they touch.
 *
 * The order is the ORGANS definition order.
 */
export function organsForSystems(
  labels: string[],
): OrganDef[] {
  const idSet = new Set<string>();

  for (const label of labels) {
    for (const organ of organsForSystem(label)) {
      idSet.add(organ.id);
    }
  }

  return ORGANS.filter((o) => idSet.has(o.id));
}

/**
 * Extract the system labels from a BiologicalImpactResult
 * and map them to highlighted organs in a single call.
 *
 * This is the function the scene calls when it needs to
 * know which organs to illuminate for the current result.
 *
 * Labels are drawn from the system nodes' `name` field,
 * which the AI Engine populates with Monarch's raw labels
 * (e.g. "nervous_system").
 */
export function highlightedOrgansForResult(
  systemNodeNames: string[],
): OrganDef[] {
  return organsForSystems(systemNodeNames);
}
