/**
 * CureVerseAI — Disease → Biological Impact
 * Scene constants.
 *
 * Pure data. No React, no Three.js imports. Imported by
 * layout.ts and the scene components.
 *
 * Design principles:
 *
 *   - Colors encode node TYPE, not importance.
 *   - Ring radius encodes TYPE, not score.
 *   - Angular position encodes index within type.
 *   - No numeric value is invented; nothing here pretends
 *     to be a "significance" scalar.
 */

import type { NodeType } from "../types";

// ---------------------------------------------------------------------------
// Node palette
// ---------------------------------------------------------------------------

/**
 * One color per node type. Chosen to be distinguishable
 * under the dark background and to feel scientific rather
 * than decorative.
 */
export const NODE_COLORS: Record<NodeType, string> = {
  disease:  "#e0525a", // red — the root
  system:   "#e9c58c", // warm amber — anatomical systems
  organ:    "#d4a875", // muted amber
  tissue:   "#a89878", // khaki
  cell:     "#7ac4b8", // teal — cellular
  gene:     "#7ba7e8", // blue — molecular
  protein:  "#5f8dd3", // deeper blue
  molecule: "#8b7fc4", // violet
  pathway:  "#c88fc4", // magenta — pathways
  mechanism:"#b8a4a4", // gray
  effect:   "#9c9c9c", // neutral gray
};

/** Fallback color when a node_type is somehow not in the palette. */
export const DEFAULT_NODE_COLOR = "#8a8a8a";

// ---------------------------------------------------------------------------
// Node geometry
// ---------------------------------------------------------------------------

/** Radius of the disease root node. */
export const DISEASE_NODE_RADIUS = 1.4;

/** Radius of every non-disease node. */
export const NODE_RADIUS = 0.55;

/** Scale applied on hover. */
export const HOVER_SCALE = 1.6;

/** Number of segments for the sphere geometry. Lower = cheaper. */
export const SPHERE_SEGMENTS = 16;

// ---------------------------------------------------------------------------
// Ring layout
// ---------------------------------------------------------------------------

/**
 * Radius of the ring (in scene units) for each node type.
 *
 * The disease sits at the origin. Every other type is
 * placed on a concentric ring at a fixed radius.
 *
 * Ordered from root outward: disease → systems → tissues
 * → cells → molecular → pathways. This matches the
 * walk order of the spec (Disease → Biological System →
 * Organ → Tissue → Cell → Molecular → Pathway).
 */
export const RING_RADII: Partial<Record<NodeType, number>> = {
  system:   6,
  organ:    12,
  tissue:   20,
  cell:     30,
  gene:     42,
  protein:  50,
  molecule: 58,
  pathway:  70,
};

/** Vertical offset per ring — subtle Z lift to add depth. */
export const RING_Y_OFFSETS: Partial<Record<NodeType, number>> = {
  system:   0,
  organ:    1.5,
  tissue:   3,
  cell:     4.5,
  gene:     6,
  protein:  6,
  molecule: 6,
  pathway:  7.5,
};

/**
 * Phase offset per ring so nodes on different rings do not
 * align radially. Prevents "spokes" of nodes when viewed
 * from above.
 */
export const RING_ANGULAR_OFFSETS: Partial<Record<NodeType, number>> = {
  system:   0,
  organ:    0.35,
  tissue:   0.9,
  cell:     1.6,
  gene:     2.3,
  protein:  2.3,
  molecule: 2.3,
  pathway:  3.1,
};

// ---------------------------------------------------------------------------
// Edge styling
// ---------------------------------------------------------------------------

/**
 * Line opacity keyed by evidence_level. Lower levels are
 * progressively more transparent — a visual encoding of
 * the honest evidence model, not a score.
 */
export const EVIDENCE_OPACITY: Record<string, number> = {
  direct:        0.55,
  experimental:  0.42,
  association:   0.28,
  computational: 0.18,
  contextual:    0.12,
  limited:       0.10,
  insufficient:  0.06,
};

/** Opacity used when an edge's evidence_level is not in the map. */
export const DEFAULT_EDGE_OPACITY = 0.15;

/** Opacity of an edge connected to the currently hovered node. */
export const HIGHLIGHT_EDGE_OPACITY = 0.9;

/** Opacity of everything not related to the hovered node. */
export const DIMMED_NODE_OPACITY = 0.2;
export const DIMMED_EDGE_OPACITY = 0.03;

// ---------------------------------------------------------------------------
// Canvas
// ---------------------------------------------------------------------------

/** Default camera position (x, y, z). */
export const CAMERA_POSITION: [number, number, number] = [0, 45, 110];

/** Default camera look-at target. */
export const CAMERA_TARGET: [number, number, number] = [0, 0, 0];

/** FOV in degrees. */
export const CAMERA_FOV = 50;

/** Background color of the Canvas — matches the page dark base. */
export const CANVAS_BACKGROUND = "#080a0b";

/** Fog near/far for a subtle depth gradient. */
export const FOG_NEAR = 80;
export const FOG_FAR = 260;

/** Damping factor for OrbitControls. Lower = more inertia. */
export const CONTROLS_DAMPING = 0.08;

/** Min/max zoom distance for OrbitControls. */
export const CONTROLS_MIN_DISTANCE = 15;
export const CONTROLS_MAX_DISTANCE = 220;

// ---------------------------------------------------------------------------
// Node types we render in Phase 14
// ---------------------------------------------------------------------------

/**
 * Which node types are shown. Every type the AI Engine can
 * emit that also has a ring radius defined.
 */
export const RENDERED_NODE_TYPES: NodeType[] = [
  "disease",
  "system",
  "organ",
  "tissue",
  "cell",
  "gene",
  "protein",
  "molecule",
  "pathway",
];

// ---------------------------------------------------------------------------
// Legend order
// ---------------------------------------------------------------------------

/**
 * Order in which types appear in the legend. Matches the
 * spec's walk order, plus disease at the top.
 */
export const LEGEND_ORDER: NodeType[] = [
  "disease",
  "system",
  "organ",
  "tissue",
  "cell",
  "gene",
  "protein",
  "molecule",
  "pathway",
];

// ---------------------------------------------------------------------------
// Phase 15 — Focus / multi-scale navigation
// ---------------------------------------------------------------------------

/**
 * A stage in the 8-stage navigation bar. Some stages map
 * to a single node type; others (MOLECULE) map to a set.
 * IMPACT is the special "overview" stage.
 */
export type FocusStage =
  | "DISEASE"
  | "SYSTEM"
  | "ORGAN"
  | "TISSUE"
  | "CELL"
  | "MOLECULE"
  | "PATHWAY"
  | "IMPACT";

/**
 * Stage order for the navigation bar. Matches spec §15.
 */
export const STAGE_ORDER: FocusStage[] = [
  "DISEASE",
  "SYSTEM",
  "ORGAN",
  "TISSUE",
  "CELL",
  "MOLECULE",
  "PATHWAY",
  "IMPACT",
];

/**
 * Which node types belong to each focus stage.
 *
 * DISEASE     : the root node only
 * MOLECULE    : gene + protein + molecule (three types, one scale)
 * IMPACT      : all types (overview)
 *
 * ORGAN is included even though the AI Engine does not
 * currently emit organ nodes; if it ever does, focus will
 * pick them up automatically.
 */
export const STAGE_TO_TYPES: Record<FocusStage, NodeType[]> = {
  DISEASE:   ["disease"],
  SYSTEM:    ["system"],
  ORGAN:     ["organ"],
  TISSUE:    ["tissue"],
  CELL:      ["cell"],
  MOLECULE:  ["gene", "protein", "molecule"],
  PATHWAY:   ["pathway"],
  IMPACT:    [
    "disease",
    "system",
    "organ",
    "tissue",
    "cell",
    "gene",
    "protein",
    "molecule",
    "pathway",
  ],
};

/**
 * Camera focus distance per stage, as a multiplier of the
 * ring radius. IMPACT uses the default wide position.
 *
 *   focusDistance = max(FOCUS_MIN_DISTANCE, radius * mult)
 *
 * The multiplier keeps bigger rings framed from farther out.
 */
export const STAGE_FOCUS_DISTANCE_MULT: Record<FocusStage, number> = {
  DISEASE:   2.2,
  SYSTEM:    3.2,
  ORGAN:     3.0,
  TISSUE:    3.0,
  CELL:      2.8,
  MOLECULE:  2.6,
  PATHWAY:   2.4,
  IMPACT:    0, // special: use default camera
};

/**
 * Minimum camera distance from origin during any focus.
 * Prevents the camera from flying inside the disease node.
 */
export const FOCUS_MIN_DISTANCE = 40;

/**
 * Vertical lift of the camera above the ring plane when
 * focused. Ratio of the horizontal distance. 0.5 means the
 * camera is halfway up.
 */
export const FOCUS_HEIGHT_RATIO = 0.55;

/**
 * Non-focused rings dim to this opacity. Applied to both
 * node emissive intensity and material opacity.
 */
export const FOCUSED_NODE_OPACITY = 1.0;
export const UNFOCUSED_NODE_OPACITY = 0.25;

/**
 * When focused, only edges touching the focused rings are
 * shown. This multiplier is applied on top of the
 * evidence-level opacity.
 */
export const FOCUSED_EDGE_MULTIPLIER = 1.0;
export const UNFOCUSED_EDGE_MULTIPLIER = 0.0; // hidden

/**
 * Camera transition duration, distance-scaled (MS-I).
 */
export const CAMERA_TRANSITION_MIN_MS = 500;
export const CAMERA_TRANSITION_MAX_MS = 1800;
export const CAMERA_TRANSITION_SCALE = 4; // ms per scene unit

/**
 * Label sizing and offset.
 */
export const LABEL_OFFSET_Y = 0.9; // scene units above node center
export const LABEL_MAX_PER_RING = 40; // hard cap to prevent DOM explosion

/**
 * Dynamic radius tuning (MS-L).
 *
 * radius_for(type) = max(base, base + (count - SOFT_COUNT) * STEP)
 * then rounded up to be at least PREV_RADIUS + MIN_RING_GAP.
 */
export const RING_SOFT_COUNT = 8;
export const RING_COUNT_STEP = 0.4;
export const MIN_RING_GAP = 8;

/**
 * Global edge opacity multiplier for the overview/IMPACT
 * state. Reduces the "sunburst" so nodes remain the
 * primary visual.
 */
export const IMPACT_EDGE_DAMPING = 0.28;

// ---------------------------------------------------------------------------
// Phase 15.5 — Human body + organs
// ---------------------------------------------------------------------------

/**
 * Body shell opacity. Very low so organs inside are
 * visible through the skin.
 */
export const BODY_SHELL_OPACITY = 0.08;
export const BODY_SHELL_COLOR = "#c4a882";

/**
 * Skeleton opacity when rendered behind organs.
 */
export const BODY_SKELETON_OPACITY = 0.18;
export const BODY_SKELETON_COLOR = "#ddd0c0";

/**
 * Organ rendering.
 *
 * Baseline (no focus): dim but visible.
 * Highlighted (organ is part of the affected system): full opacity + emissive glow.
 * Dimmed (a system is focused but this organ is not in it): very low.
 */
export const ORGAN_BASE_OPACITY = 0.32;
export const ORGAN_HIGHLIGHT_OPACITY = 1.0;
export const ORGAN_DIMMED_OPACITY = 0.08;

export const ORGAN_BASE_EMISSIVE = 0.05;
export const ORGAN_HIGHLIGHT_EMISSIVE = 1.1;

/**
 * Pulse animation applied to highlighted organs.
 * In seconds.
 */
export const ORGAN_PULSE_PERIOD_S = 2.4;

/**
 * Body scale — how large the body is in scene units.
 * Kept separate from graph so the body occupies its own
 * vertical scale.
 */
export const BODY_HEIGHT = 40;
export const BODY_CENTER_Y = 0;

/**
 * Camera positions for each body stage.
 */
export const BODY_CAMERA_POSITION: [number, number, number] = [
  0, 8, 62,
];
export const BODY_CAMERA_LOOKAT: [number, number, number] = [
  0, 0, 0,
];

/**
 * Organ highlight color for the "affected" state — a warm
 * red-orange that reads as "active" against the neutral
 * anatomical palette.
 */
export const ORGAN_HIGHLIGHT_COLOR = "#e0525a";

/**
 * X-axis offset of the human body from the origin.
 * The abstract graph stays at the origin; the body sits
 * to the left so both are visible without overlapping.
 */
export const BODY_OFFSET_X = -35;

/**
 * Camera positions for the body-oriented stages
 * (DISEASE, SYSTEM). These are computed relative to
 * BODY_OFFSET_X.
 */
export const BODY_STAGE_CAMERA: Record<string, [number, number, number]> = {
  DISEASE: [BODY_OFFSET_X, 5, 55],
  SYSTEM: [BODY_OFFSET_X, 5, 42],
};

/**
 * Look-at target for body-oriented stages.
 */
export const BODY_STAGE_LOOKAT: [number, number, number] = [
  BODY_OFFSET_X,
  0,
  0,
];
