/**
 * CureVerseAI — Disease → Biological Impact
 * Bubble journey data transform.
 *
 * Builds the journey tree from a BiologicalImpactResult.
 *
 * Hierarchy:
 *   System -> Tissue -> Cell -> Molecule -> (graph)
 *
 * The AI Engine's impact graph is hub-and-spoke: every
 * node type connects directly to the disease node, not
 * to each other. There are no system->tissue or
 * tissue->cell edges. The journey therefore imposes the
 * hierarchy by node type, filtering the disease's direct
 * connections at each tier.
 *
 * Every bubble corresponds to a real ImpactNode. No
 * fabrications, no synthetic categories.
 *
 * Caps:
 *   MAX_TISSUES   = 10
 *   MAX_CELLS     = 10
 *   MAX_MOLECULES = 8
 *
 * The cap keeps each level to a readable number of
 * siblings. Without it, every tissue would have the same
 * cells as children and the journey would feel identical
 * regardless of which tissue you clicked.
 */

import type {
  BiologicalImpactResult,
  ImpactNode,
  NodeType,
} from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_TISSUES = 10;
const MAX_CELLS = 10;
const MAX_MOLECULES = 8;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Bubble {
  /** Original node id, or synthetic id for terminal bubbles. */
  id: string;
  /** Display label. */
  label: string;
  /** Node type (determines color). */
  type: NodeType;
  /** Number of children — used for bubble size at parent level. */
  childCount: number;
  /** Direct children in the journey hierarchy. */
  children: Bubble[];
  /** True when clicking this bubble opens the graph. */
  opensGraph: boolean;
  /** Original node, for reference. */
  source?: ImpactNode;
}

// ---------------------------------------------------------------------------
// Node lookups
// ---------------------------------------------------------------------------

function nodesOfType(
  result: BiologicalImpactResult,
  type: NodeType,
): ImpactNode[] {
  return (result.nodes ?? []).filter(
    (n) => n.node_type === type,
  );
}

/**
 * Sort nodes by a meaningful weight, descending.
 *
 * Preference order:
 *   1. metadata.supporting_gene_count (higher first)
 *   2. metadata.hpo_annotation_count (higher first)
 *   3. name (alphabetical, for determinism)
 */
function sortByWeight(nodes: ImpactNode[]): ImpactNode[] {
  return [...nodes].sort((a, b) => {
    const aMd = a.metadata ?? {};
    const bMd = b.metadata ?? {};

    const aSgc = Number(
      (aMd as Record<string, unknown>).supporting_gene_count ?? 0,
    );
    const bSgc = Number(
      (bMd as Record<string, unknown>).supporting_gene_count ?? 0,
    );
    if (aSgc !== bSgc) return bSgc - aSgc;

    const aHpo = Number(
      (aMd as Record<string, unknown>).hpo_annotation_count ?? 0,
    );
    const bHpo = Number(
      (bMd as Record<string, unknown>).hpo_annotation_count ?? 0,
    );
    if (aHpo !== bHpo) return bHpo - aHpo;

    return (a.name ?? "").localeCompare(b.name ?? "");
  });
}

// ---------------------------------------------------------------------------
// Bubble construction
// ---------------------------------------------------------------------------

function makeBubble(
  node: ImpactNode,
  childCount: number,
  children: Bubble[] = [],
  opensGraph = false,
): Bubble {
  return {
    id: node.node_id,
    label: node.name,
    type: node.node_type,
    childCount,
    children,
    opensGraph,
    source: node,
  };
}

// ---------------------------------------------------------------------------
// Tree builder (tiered, not graph-walked)
// ---------------------------------------------------------------------------

/**
 * Build a tiered journey tree rooted at the given system.
 *
 * Every level uses the disease's direct connections of
 * the appropriate type. The hierarchy is imposed by
 * type order, not by graph edges.
 */
function buildTieredTree(
  system: ImpactNode,
  result: BiologicalImpactResult,
): Bubble {
  // ---- Level 4: molecules (genes + proteins) --------------

  const genes = nodesOfType(result, "gene");
  const proteins = nodesOfType(result, "protein");

  // Interleave genes and proteins for a mixed molecule level.
  const moleculesRaw: ImpactNode[] = [];
  const maxMol = Math.max(genes.length, proteins.length);
  for (let i = 0; i < maxMol; i++) {
    if (i < genes.length) moleculesRaw.push(genes[i]);
    if (i < proteins.length) moleculesRaw.push(proteins[i]);
  }

  const molecules = sortByWeight(moleculesRaw).slice(
    0,
    MAX_MOLECULES,
  );

  const moleculeBubbles = molecules.map((m) =>
    makeBubble(m, 0, [], true),
  );

  // ---- Level 3: cells -------------------------------------

  const cells = sortByWeight(
    nodesOfType(result, "cell"),
  ).slice(0, MAX_CELLS);

  const cellBubbles = cells.map((c) =>
    makeBubble(c, moleculeBubbles.length, moleculeBubbles),
  );

  // ---- Level 2: tissues -----------------------------------

  const tissues = sortByWeight(
    nodesOfType(result, "tissue"),
  ).slice(0, MAX_TISSUES);

  const tissueBubbles = tissues.map((t) =>
    makeBubble(t, cellBubbles.length, cellBubbles),
  );

  // ---- Level 1: root system -------------------------------

  return makeBubble(
    system,
    tissueBubbles.length,
    tissueBubbles,
  );
}

// ---------------------------------------------------------------------------
// Root selection
// ---------------------------------------------------------------------------

/**
 * Choose the "most affected" system to be the root of
 * the journey.
 *
 * Heuristic: the system node whose metadata carries the
 * highest hpo_annotation_count (Monarch's per-system
 * phenotype count). Falls back to the first system in the
 * result if no count is available.
 *
 * For Asthma this picks "respiratory". For Alzheimer's it
 * picks "nervous_system". For Type 2 diabetes it picks
 * "metabolism_homeostasis" or similar.
 */
export function pickRootSystem(
  result: BiologicalImpactResult,
): ImpactNode | null {
  const systems = nodesOfType(result, "system");
  if (systems.length === 0) return null;

  let best = systems[0];
  let bestCount = -1;

  for (const s of systems) {
    const md = s.metadata ?? {};
    const count = Number(
      (md as Record<string, unknown>)
        .hpo_annotation_count ?? 0,
    );
    if (count > bestCount) {
      bestCount = count;
      best = s;
    }
  }

  return best;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Build the journey for a result. Returns the root bubble,
 * or null if the result has no systems.
 */
export function buildJourney(
  result: BiologicalImpactResult,
): Bubble | null {
  const root = pickRootSystem(result);
  if (!root) return null;

  return buildTieredTree(root, result);
}

/**
 * Find the path from the root bubble down to a bubble
 * with the given id. Returns an empty array if the id is
 * not found.
 */
export function findPath(
  root: Bubble,
  targetId: string,
): Bubble[] {
  if (root.id === targetId) return [root];

  for (const child of root.children) {
    const sub = findPath(child, targetId);
    if (sub.length > 0) {
      return [root, ...sub];
    }
  }

  return [];
}
