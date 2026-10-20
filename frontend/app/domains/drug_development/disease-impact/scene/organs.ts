/**
 * CureVerseAI — Disease → Biological Impact
 * Human body organ definitions.
 *
 * Twenty organs positioned in an approximate anatomical
 * layout. Coordinates are in scene units where the body
 * is BODY_HEIGHT (40) units tall, head at +20, feet at
 * -20, centered on the y-axis.
 *
 * Shapes are approximated with Three.js primitives:
 *
 *   sphere   — brain, kidneys, bladder, thyroid, thymus,
 *              adrenal glands, eyes, testes/ovaries
 *   capsule  — spine, long bones, intestines segments
 *   box      — liver, stomach, pancreas, spleen, uterus
 *   torus    — large intestine ring
 *
 * Positions are visually tuned for recognizability, not
 * medical precision. The goal is "a judge sees a heart
 * where a heart should be", not "a surgeon could operate
 * using this."
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type OrganShape =
  | "sphere"
  | "capsule"
  | "box"
  | "torus";

export interface OrganDef {
  id: string;
  label: string;
  /** Body system this organ belongs to (matches Monarch system labels). */
  system: string;
  /** Anatomical group for grouping/highlighting. */
  group:
    | "nervous"
    | "cardiovascular"
    | "respiratory"
    | "digestive"
    | "renal"
    | "endocrine"
    | "immune"
    | "reproductive"
    | "musculoskeletal";
  position: [number, number, number];
  rotation?: [number, number, number];
  /** Base color used when the organ is not highlighted. */
  color: string;
  shape: OrganShape;
  /** Size parameters interpreted by the shape. */
  size: {
    /** Sphere / capsule radius; box half-extents; torus radius. */
    r?: number;
    /** Capsule / cylinder length. */
    length?: number;
    /** Box width/depth/height as a triple. */
    box?: [number, number, number];
    /** Torus tube radius. */
    tube?: number;
  };
  /** Optional mirrored copy on the opposite side (for paired organs). */
  mirrorAcrossX?: boolean;
}

// ---------------------------------------------------------------------------
// Palette
// ---------------------------------------------------------------------------

const BRAIN_COLOR = "#b8a898";
const HEART_COLOR = "#a83c3c";
const LUNG_COLOR = "#d49898";
const LIVER_COLOR = "#7a3a2a";
const STOMACH_COLOR = "#c89888";
const PANCREAS_COLOR = "#c8a888";
const SPLEEN_COLOR = "#7a3a4a";
const KIDNEY_COLOR = "#8a3a3a";
const INTESTINE_COLOR = "#c8a878";
const BLADDER_COLOR = "#d8c898";
const THYROID_COLOR = "#c88868";
const ADRENAL_COLOR = "#b87848";
const THYMUS_COLOR = "#c8a8a8";
const EYE_COLOR = "#4a5868";
const UTERUS_COLOR = "#b87888";
const SPINE_COLOR = "#ddd0c0";
const RIB_COLOR = "#ddd0c0";
const PELVIS_COLOR = "#ddd0c0";
const SKULL_COLOR = "#ddd0c0";

// ---------------------------------------------------------------------------
// Organ definitions
// ---------------------------------------------------------------------------

export const ORGANS: OrganDef[] = [
  // ---- Nervous ----------------------------------------------------------
  {
    id: "brain",
    label: "Brain",
    system: "nervous_system",
    group: "nervous",
    position: [0, 17, 0],
    color: BRAIN_COLOR,
    shape: "sphere",
    size: { r: 1.9 },
  },

  // ---- Cardiovascular ---------------------------------------------------
  {
    id: "heart",
    label: "Heart",
    system: "cardiovascular_system",
    group: "cardiovascular",
    position: [-0.8, 8.5, 0.2],
    color: HEART_COLOR,
    shape: "sphere",
    size: { r: 1.5 },
  },

  // ---- Respiratory ------------------------------------------------------
  {
    id: "lung_left",
    label: "Left lung",
    system: "respiratory_system",
    group: "respiratory",
    position: [1.9, 9.2, 0],
    color: LUNG_COLOR,
    shape: "capsule",
    size: { r: 1.2, length: 3.2 },
  },
  {
    id: "lung_right",
    label: "Right lung",
    system: "respiratory_system",
    group: "respiratory",
    position: [-1.9, 9.2, 0],
    color: LUNG_COLOR,
    shape: "capsule",
    size: { r: 1.2, length: 3.2 },
  },

  // ---- Digestive --------------------------------------------------------
  {
    id: "liver",
    label: "Liver",
    system: "digestive_system",
    group: "digestive",
    position: [-2.0, 3.2, 0.8],
    color: LIVER_COLOR,
    shape: "box",
    size: { box: [2.4, 1.2, 1.6] },
  },
  {
    id: "stomach",
    label: "Stomach",
    system: "digestive_system",
    group: "digestive",
    position: [1.8, 3.4, 0.4],
    color: STOMACH_COLOR,
    shape: "box",
    size: { box: [1.4, 1.3, 1.0] },
  },
  {
    id: "pancreas",
    label: "Pancreas",
    system: "digestive_system",
    group: "digestive",
    position: [0.2, 2.2, 0.6],
    color: PANCREAS_COLOR,
    shape: "box",
    size: { box: [2.2, 0.4, 0.5] },
  },
  {
    id: "intestine_large",
    label: "Large intestine",
    system: "digestive_system",
    group: "digestive",
    position: [0, -1.2, 0.2],
    rotation: [Math.PI / 2, 0, 0],
    color: INTESTINE_COLOR,
    shape: "torus",
    size: { r: 1.9, tube: 0.5 },
  },
  {
    id: "intestine_small",
    label: "Small intestine",
    system: "digestive_system",
    group: "digestive",
    position: [0, -1.2, 0.2],
    color: INTESTINE_COLOR,
    shape: "sphere",
    size: { r: 1.3 },
  },

  // ---- Renal ------------------------------------------------------------
  {
    id: "kidney_left",
    label: "Left kidney",
    system: "renal_system",
    group: "renal",
    position: [1.8, 1.2, -1.2],
    color: KIDNEY_COLOR,
    shape: "sphere",
    size: { r: 0.75 },
  },
  {
    id: "kidney_right",
    label: "Right kidney",
    system: "renal_system",
    group: "renal",
    position: [-1.8, 1.2, -1.2],
    color: KIDNEY_COLOR,
    shape: "sphere",
    size: { r: 0.75 },
  },
  {
    id: "bladder",
    label: "Bladder",
    system: "renal_system",
    group: "renal",
    position: [0, -4.8, 0.3],
    color: BLADDER_COLOR,
    shape: "sphere",
    size: { r: 0.9 },
  },

  // ---- Endocrine --------------------------------------------------------
  {
    id: "thyroid",
    label: "Thyroid",
    system: "endocrine_system",
    group: "endocrine",
    position: [0, 13.6, 0.4],
    color: THYROID_COLOR,
    shape: "sphere",
    size: { r: 0.5 },
  },
  {
    id: "adrenal_left",
    label: "Left adrenal gland",
    system: "endocrine_system",
    group: "endocrine",
    position: [1.8, 2.1, -1.2],
    color: ADRENAL_COLOR,
    shape: "sphere",
    size: { r: 0.35 },
  },
  {
    id: "adrenal_right",
    label: "Right adrenal gland",
    system: "endocrine_system",
    group: "endocrine",
    position: [-1.8, 2.1, -1.2],
    color: ADRENAL_COLOR,
    shape: "sphere",
    size: { r: 0.35 },
  },

  // ---- Immune -----------------------------------------------------------
  {
    id: "spleen",
    label: "Spleen",
    system: "immune_system",
    group: "immune",
    position: [2.6, 3.6, -1.0],
    color: SPLEEN_COLOR,
    shape: "box",
    size: { box: [0.9, 0.8, 0.9] },
  },
  {
    id: "thymus",
    label: "Thymus",
    system: "immune_system",
    group: "immune",
    position: [0, 9.8, 1.2],
    color: THYMUS_COLOR,
    shape: "box",
    size: { box: [1.0, 0.7, 0.5] },
  },

  // ---- Reproductive (simplified) ----------------------------------------
  {
    id: "uterus",
    label: "Uterus",
    system: "reproductive_system",
    group: "reproductive",
    position: [0, -4.0, 0.3],
    color: UTERUS_COLOR,
    shape: "box",
    size: { box: [0.8, 0.9, 0.6] },
  },

  // ---- Musculoskeletal --------------------------------------------------
  {
    id: "spine",
    label: "Spine",
    system: "musculoskeletal_system",
    group: "musculoskeletal",
    position: [0, 2, -1.6],
    color: SPINE_COLOR,
    shape: "capsule",
    size: { r: 0.35, length: 20 },
  },
  {
    id: "ribs",
    label: "Ribs",
    system: "musculoskeletal_system",
    group: "musculoskeletal",
    position: [0, 8.5, -0.3],
    rotation: [Math.PI / 2, 0, 0],
    color: RIB_COLOR,
    shape: "torus",
    size: { r: 2.6, tube: 0.18 },
  },
  {
    id: "pelvis",
    label: "Pelvis",
    system: "musculoskeletal_system",
    group: "musculoskeletal",
    position: [0, -3.4, -0.2],
    rotation: [Math.PI / 2, 0, 0],
    color: PELVIS_COLOR,
    shape: "torus",
    size: { r: 1.7, tube: 0.35 },
  },
  {
    id: "skull",
    label: "Skull",
    system: "musculoskeletal_system",
    group: "musculoskeletal",
    position: [0, 17.4, -0.2],
    color: SKULL_COLOR,
    shape: "sphere",
    size: { r: 2.15 },
  },

  // ---- Eyes -------------------------------------------------------------
  {
    id: "eye_left",
    label: "Left eye",
    system: "nervous_system",
    group: "nervous",
    position: [0.6, 16.8, 1.6],
    color: EYE_COLOR,
    shape: "sphere",
    size: { r: 0.32 },
  },
  {
    id: "eye_right",
    label: "Right eye",
    system: "nervous_system",
    group: "nervous",
    position: [-0.6, 16.8, 1.6],
    color: EYE_COLOR,
    shape: "sphere",
    size: { r: 0.32 },
  },
];

// ---------------------------------------------------------------------------
// Lookup
// ---------------------------------------------------------------------------

const BY_ID = new Map<string, OrganDef>();
for (const organ of ORGANS) {
  BY_ID.set(organ.id, organ);
}

export function getOrgan(id: string): OrganDef | undefined {
  return BY_ID.get(id);
}
