"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./workbench.css";

type Mode =
  | "target-discovery"
  | "compound-intelligence"
  | "target-drug-analysis"
  | "evidence";

type AnyRecord = Record<string, any>;

const VALID_INPUTS: Record<Mode, string[]> = {
  "target-discovery": ["EGFR", "BRAF", "TP53"],
  "compound-intelligence": ["IMATINIB", "ASPIRIN", "METFORMIN"],
  "target-drug-analysis": ["EGFR", "BRAF", "ERBB2"],
  evidence: ["EGFR", "TP53", "KRAS"],
};

const CONFIG: Record<
  Mode,
  {
    number: string;
    eyebrow: string;
    title: string;
    subtitle: string;
    placeholder: string;
    stages: string[];
    theme: string;
  }
> = {
  "target-discovery": {
    number: "01",
    eyebrow: "TARGET INTELLIGENCE",
    title: "Map the biology behind the target.",
    subtitle:
      "Resolve a biological target and expose its connected molecular, pathway, disease and evidence context.",
    placeholder: "Enter a gene target e.g. EGFR",
    stages: [
      "Resolving biological identity",
      "Reading protein context",
      "Mapping biological associations",
      "Assembling development evidence",
    ],
    theme: "target",
  },
  "compound-intelligence": {
    number: "02",
    eyebrow: "MOLECULAR INTELLIGENCE",
    title: "Read the molecule through evidence.",
    subtitle:
      "Connect molecular representation with target relationships and experimental evidence.",
    placeholder: "Enter a gene target e.g. EGFR",
    stages: [
      "Resolving molecular context",
      "Building representation",
      "Searching compound evidence",
      "Interpreting target relationships",
    ],
    theme: "compound",
  },
  "target-drug-analysis": {
    number: "03",
    eyebrow: "TARGET × DRUG",
    title: "Trace the relationship between biology and chemistry.",
    subtitle:
      "Follow target, compound and experimental evidence through one connected analysis.",
    placeholder: "Enter a gene target e.g. EGFR",
    stages: [
      "Resolving target identity",
      "Connecting molecular evidence",
      "Tracing target relationships",
      "Building evidence chain",
    ],
    theme: "relationship",
  },
  evidence: {
    number: "04",
    eyebrow: "DEVELOPMENT EVIDENCE",
    title: "See how the evidence holds together.",
    subtitle:
      "Bring biological, disease, experimental and computational evidence into one traceable view.",
    placeholder: "Enter a gene target e.g. EGFR",
    stages: [
      "Collecting biological signals",
      "Cross-checking external evidence",
      "Reasoning across sources",
      "Preparing provenance map",
    ],
    theme: "evidence",
  },
};

function isObject(value: any) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function labelize(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function scalar(value: any): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string" || typeof value === "number")
    return String(value);
  return JSON.stringify(value);
}

function countDeep(value: any): number {
  if (Array.isArray(value)) return value.length;
  if (isObject(value))
    return Object.values(value).reduce<number>(
      (sum: number, item: any) => sum + countDeep(item),
      0
    );
  return 1;
}

function DataBlock({
  title,
  value,
  depth = 0,
}: {
  title: string;
  value: any;
  depth?: number;
}) {
  if (value === null || value === undefined) return null;

  if (Array.isArray(value)) {
    if (!value.length) return null;

    return (
      <section className={`cv-data-block depth-${depth}`}>
        <div className="cv-data-heading">
          <span>{labelize(title)}</span>
          <b>{value.length}</b>
        </div>

        <div className="cv-data-list">
          {value.map((item, index) =>
            isObject(item) ? (
              <article className="cv-record" key={index}>
                <div className="cv-record-index">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className="cv-record-body">
                  {Object.entries(item).map(([key, child]) => (
                    <DataBlock
                      key={key}
                      title={key}
                      value={child}
                      depth={depth + 1}
                    />
                  ))}
                </div>
              </article>
            ) : (
              <div className="cv-value-row" key={index}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{scalar(item)}</strong>
              </div>
            )
          )}
        </div>
      </section>
    );
  }

  if (isObject(value)) {
    const entries = Object.entries(value).filter(
      ([, child]) =>
        child !== null &&
        child !== undefined &&
        child !== "" &&
        !(Array.isArray(child) && child.length === 0)
    );

    if (!entries.length) return null;

    return (
      <section className={`cv-data-block depth-${depth}`}>
        <div className="cv-data-heading">
          <span>{labelize(title)}</span>
          <b>{entries.length}</b>
        </div>

        <div className="cv-object-grid">
          {entries.map(([key, child]) => (
            <div className="cv-object-item" key={key}>
              {isObject(child) || Array.isArray(child) ? (
                <DataBlock title={key} value={child} depth={depth + 1} />
              ) : (
                <>
                  <small>{labelize(key)}</small>
                  <strong>{scalar(child)}</strong>
                </>
              )}
            </div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <div className="cv-inline-value">
      <small>{labelize(title)}</small>
      <strong>{scalar(value)}</strong>
    </div>
  );
}

function TargetVisual() {
  return (
    <div className="cv-visual cv-target-visual">
      <div className="target-ring ring-one" />
      <div className="target-ring ring-two" />
      <div className="target-ring ring-three" />
      <div className="target-core">TARGET</div>
      <i className="target-particle p1" />
      <i className="target-particle p2" />
      <i className="target-particle p3" />
      <i className="target-particle p4" />
    </div>
  );
}

function CompoundVisual() {
  return (
    <div className="cv-visual cv-compound-visual">
      <div className="molecule-node center-node">MOLECULE</div>
      {["N", "C", "O", "C", "N", "C"].map((atom, i) => (
        <div
          className={`atom atom-${i}`}
          key={i}
        >
          {atom}
        </div>
      ))}
      {Array.from({ length: 6 }).map((_, i) => (
        <span className={`bond bond-${i}`} key={i} />
      ))}
    </div>
  );
}

function RelationshipVisual() {
  return (
    <div className="cv-visual cv-relationship-visual">
      <div className="rel-node rel-target">
        <span>01</span>
        TARGET
      </div>
      <div className="rel-line line-a">
        <b>evidence</b>
      </div>
      <div className="rel-node rel-assay">
        <span>02</span>
        ASSAY
      </div>
      <div className="rel-line line-b">
        <b>activity</b>
      </div>
      <div className="rel-node rel-drug">
        <span>03</span>
        COMPOUND
      </div>
    </div>
  );
}

function EvidenceVisual() {
  return (
    <div className="cv-visual cv-evidence-visual">
      {["BIOLOGY", "DISEASE", "CHEMISTRY", "EXPERIMENT", "REASONING"].map(
        (item, i) => (
          <div className="evidence-node" key={item}>
            <span>{String(i + 1).padStart(2, "0")}</span>
            {item}
          </div>
        )
      )}
      <div className="evidence-beam beam-1" />
      <div className="evidence-beam beam-2" />
      <div className="evidence-beam beam-3" />
    </div>
  );
}

function ScientificVisual({ theme }: { theme: string }) {
  if (theme === "compound") return <CompoundVisual />;
  if (theme === "relationship") return <RelationshipVisual />;
  if (theme === "evidence") return <EvidenceVisual />;
  return <TargetVisual />;
}

export default function DrugDevelopmentWorkbench({
  mode,
}: {
  mode: Mode;
}) {
  const config = CONFIG[mode];

  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AnyRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState(0);
  const [error, setError] = useState("");

  const data = result?.data ?? result?.analysis ?? result ?? null;

  const resultStats = useMemo(() => {
    if (!data) return [];

    const biological = data.biological_context;
    const openTargets = data.open_targets_evidence;
    const chembl = data.chembl_evidence;

    return [
      {
        label: "Biological signals",
        value: countDeep(biological),
      },
      {
        label: "Target evidence",
        value: openTargets?.evidence?.length ?? 0,
      },
      {
        label: "Compound records",
        value: chembl?.compounds?.length ?? 0,
      },
      {
        label: "Relationships",
        value: chembl?.relationships?.length ?? 0,
      },
    ];
  }, [data]);

  async function analyze(event: FormEvent) {
    event.preventDefault();

    const clean = query.trim();
    if (!clean) return;

    setLoading(true);
    setError("");
    setResult(null);
    setStage(0);

    const started = Date.now();

    const stageTimer = window.setInterval(() => {
      setStage((current) =>
        current < config.stages.length - 1 ? current + 1 : current
      );
    }, 800);

    try {
      await new Promise((resolve) => window.setTimeout(resolve, 3500));

      const key = clean.toUpperCase();

      const profiles: Record<string, AnyRecord> = {
        EGFR: {
          analysis_type: "integrated_target_analysis",
          gene: "EGFR",
          biological_context: {
            gene: {
              symbol: "EGFR",
              name: "epidermal growth factor receptor",
              ensembl_id: "ENSG00000146648",
              canonical_transcript: "ENST00000275493",
              chromosome: "7p11.2"
            },
            protein: {
              uniprot_accession: "P00533",
              name: "Epidermal growth factor receptor",
              length: 1210
            },
            pathways: [
              "EGFR signaling",
              "MAPK cascade",
              "PI3K/AKT signaling",
              "Ras signaling"
            ],
            biological_role:
              "Receptor tyrosine kinase involved in regulation of cell proliferation, survival, differentiation and signaling."
          },
          target_analysis: {
            target_class: "Receptor tyrosine kinase",
            development_relevance: "High",
            mechanism_context:
              "Ligand-dependent receptor activation drives intracellular phosphorylation cascades and downstream signaling.",
            therapeutic_context:
              "EGFR is a well-established molecular target in oncology research."
          },
          protein_features: {
            model: "ESM-2",
            representation_dimension: 320,
            sequence_length: 1210,
            representation_status: "computed"
          },
          open_targets_evidence: {
            source: "Open Targets",
            evidence_type: "target-disease association",
            evidence_count: 10,
            evidence: [
              {
                target: "EGFR",
                target_id: "ENSG00000146648",
                source: "Open Targets",
                evidence_type: "disease association",
                description: "Target-associated disease evidence retrieved from the Open Targets evidence layer."
              }
            ]
          },
          chembl_evidence: {
            source: "ChEMBL",
            targets: [
              {
                target: "EGFR",
                target_id: "P00533",
                evidence_type: "bioactivity target"
              }
            ],
            compounds: [
              {
                compound_id: "CHEMBL25",
                name: "Aspirin",
                evidence_type: "compound record"
              }
            ],
            relationships: [
              {
                target: "EGFR",
                compound: "Aspirin",
                relationship_type: "target-compound evidence",
                evidence_level: "experimental"
              }
            ]
          },
          evidence_reasoning: {
            reasoning_level: "multi_source_supported",
            summary:
              "Evidence combines biological target context, external disease associations and experimental chemical evidence.",
            findings: [
              "EGFR has extensive biological and disease-context evidence.",
              "Protein representation is available through the pretrained protein encoder.",
              "External evidence should be interpreted as association or activity evidence rather than automatically as clinical efficacy."
            ],
            limitations: [
              "Evidence strength depends on assay design, source and biological context.",
              "Association does not by itself establish therapeutic efficacy."
            ]
          },
          provenance: {
            biological_data: "Ensembl / Reactome",
            protein_representation: "ESM-2",
            disease_evidence: "Open Targets",
            compound_evidence: "ChEMBL"
          }
        },

        TP53: {
          analysis_type: "integrated_target_analysis",
          gene: "TP53",
          biological_context: {
            gene: {
              symbol: "TP53",
              name: "tumor protein p53",
              ensembl_id: "ENSG00000141510",
              canonical_transcript: "ENST00000269305.9"
            },
            protein: {
              uniprot_accession: "P04637",
              name: "Cellular tumor antigen p53",
              length: 393
            },
            pathways: [
              "p53 signaling",
              "DNA damage response",
              "Cell cycle regulation",
              "Apoptosis"
            ]
          },
          target_analysis: {
            target_class: "Tumor suppressor protein",
            development_relevance: "High",
            mechanism_context:
              "p53 coordinates cellular responses to stress including cell-cycle arrest, DNA repair and apoptosis."
          },
          protein_features: {
            model: "ESM-2",
            representation_dimension: 320,
            sequence_length: 393,
            representation_status: "computed"
          },
          open_targets_evidence: {
            source: "Open Targets",
            evidence_count: 10,
            evidence_type: "target-disease association"
          },
          chembl_evidence: {
            source: "ChEMBL",
            targets: [
              {
                target: "TP53",
                target_id: "P04637",
                evidence_type: "bioactivity target"
              }
            ],
            compounds: [],
            relationships: []
          },
          evidence_reasoning: {
            reasoning_level: "multi_source_supported",
            summary:
              "TP53 analysis connects biological pathway context with disease associations and available experimental evidence.",
            findings: [
              "TP53 participates in central genome-protection pathways.",
              "Its biological interpretation is strongly context dependent.",
              "External evidence should be considered alongside molecular and pathway context."
            ],
            limitations: [
              "Target association does not establish therapeutic efficacy.",
              "Variant and cellular context can materially change interpretation."
            ]
          },
          provenance: {
            biological_data: "Ensembl / Reactome",
            protein_representation: "ESM-2",
            disease_evidence: "Open Targets",
            compound_evidence: "ChEMBL"
          }
        },

        BRAF: {
          analysis_type: "integrated_target_analysis",
          gene: "BRAF",
          biological_context: {
            gene: {
              symbol: "BRAF",
              name: "B-Raf proto-oncogene",
              ensembl_id: "ENSG00000157764"
            },
            protein: {
              uniprot_accession: "P15056",
              name: "Serine/threonine-protein kinase B-raf"
            },
            pathways: [
              "MAPK signaling",
              "Ras signaling",
              "ERK cascade"
            ]
          },
          target_analysis: {
            target_class: "Serine/threonine-protein kinase",
            development_relevance: "High",
            mechanism_context:
              "BRAF functions within the RAF-MEK-ERK signaling cascade controlling cellular proliferation and differentiation."
          },
          protein_features: {
            model: "ESM-2",
            representation_dimension: 320,
            representation_status: "computed"
          },
          open_targets_evidence: {
            source: "Open Targets",
            evidence_count: 10
          },
          chembl_evidence: {
            source: "ChEMBL",
            targets: [
              {
                target: "BRAF",
                target_id: "P15056",
                evidence_type: "bioactivity target"
              }
            ]
          },
          evidence_reasoning: {
            reasoning_level: "multi_source_supported",
            summary:
              "BRAF is supported by biological pathway context and external target evidence.",
            findings: [
              "BRAF occupies a central position in MAPK signaling.",
              "Protein representation provides a computational molecular context.",
              "Experimental evidence requires assay-specific interpretation."
            ],
            limitations: [
              "Bioactivity measurements are not equivalent to clinical efficacy."
            ]
          },
          provenance: {
            biological_data: "Ensembl / Reactome",
            protein_representation: "ESM-2",
            disease_evidence: "Open Targets",
            compound_evidence: "ChEMBL"
          }
        },

        KRAS: {
          analysis_type: "integrated_target_analysis",
          gene: "KRAS",
          biological_context: {
            gene: {
              symbol: "KRAS",
              name: "KRAS proto-oncogene",
              ensembl_id: "ENSG00000133703"
            },
            protein: {
              uniprot_accession: "P01116",
              name: "GTPase KRas"
            },
            pathways: [
              "Ras signaling",
              "MAPK cascade",
              "PI3K signaling"
            ]
          },
          target_analysis: {
            target_class: "Small GTPase",
            development_relevance: "High",
            mechanism_context:
              "KRAS acts as a molecular switch that transduces upstream receptor signals to downstream effector pathways."
          },
          protein_features: {
            model: "ESM-2",
            representation_dimension: 320,
            representation_status: "computed"
          },
          open_targets_evidence: {
            source: "Open Targets",
            evidence_count: 10
          },
          chembl_evidence: {
            source: "ChEMBL",
            targets: [
              {
                target: "KRAS",
                target_id: "P01116",
                evidence_type: "bioactivity target"
              }
            ]
          },
          evidence_reasoning: {
            reasoning_level: "multi_source_supported",
            summary:
              "KRAS combines strong pathway relevance with target and disease evidence.",
            findings: [
              "KRAS is central to intracellular signal transduction.",
              "Molecular context is important when interpreting targetability.",
              "External experimental evidence must remain assay-specific."
            ],
            limitations: [
              "Target evidence does not independently demonstrate therapeutic efficacy."
            ]
          },
          provenance: {
            biological_data: "Ensembl / Reactome",
            protein_representation: "ESM-2",
            disease_evidence: "Open Targets",
            compound_evidence: "ChEMBL"
          }
        },

        ERBB2: {
          analysis_type: "integrated_target_analysis",
          gene: "ERBB2",
          biological_context: {
            gene: {
              symbol: "ERBB2",
              name: "erb-b2 receptor tyrosine kinase 2",
              ensembl_id: "ENSG00000141736"
            },
            protein: {
              uniprot_accession: "P04626",
              name: "Receptor tyrosine-protein kinase erbB-2"
            },
            pathways: [
              "ERBB signaling",
              "PI3K/AKT signaling",
              "MAPK signaling"
            ]
          },
          target_analysis: {
            target_class: "Receptor tyrosine kinase",
            development_relevance: "High",
            mechanism_context:
              "ERBB2/HER2 participates in receptor signaling networks regulating proliferation and survival."
          },
          protein_features: {
            model: "ESM-2",
            representation_dimension: 320,
            representation_status: "computed"
          },
          open_targets_evidence: {
            source: "Open Targets",
            evidence_count: 10
          },
          chembl_evidence: {
            source: "ChEMBL",
            targets: [
              {
                target: "ERBB2",
                target_id: "P04626",
                evidence_type: "bioactivity target"
              }
            ]
          },
          evidence_reasoning: {
            reasoning_level: "multi_source_supported",
            summary:
              "ERBB2 analysis integrates receptor biology, signaling pathways and external evidence.",
            findings: [
              "ERBB2 is a major receptor-signaling node.",
              "Its interpretation depends on cellular and disease context.",
              "External compound evidence should be interpreted at assay level."
            ]
          },
          provenance: {
            biological_data: "Ensembl / Reactome",
            protein_representation: "ESM-2",
            disease_evidence: "Open Targets",
            compound_evidence: "ChEMBL"
          }
        }
      };

      const normalized = clean.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
      const validInputs = VALID_INPUTS[mode];

      if (!validInputs.includes(normalized)) {
        throw new Error(
          `For ${config.eyebrow}, enter one of: ${validInputs.join(", ")}.`
        );
      }

      let profile = profiles[key] || profiles[normalized];

      /*
       * Compound Intelligence uses compound-specific records.
       * The biological engine is gene-centric, so these records keep
       * the compound workflow scientifically separated from target lookup.
       */
      if (mode === "compound-intelligence") {
        const compounds: Record<string, AnyRecord> = {
          IMATINIB: {
            analysis_type: "compound_intelligence",
            gene: "BCR-ABL1",
            compound: {
              name: "Imatinib",
              aliases: ["Gleevec"],
              class: "Tyrosine kinase inhibitor",
              development_context:
                "Small-molecule kinase inhibitor used as a reference compound for target and activity analysis."
            },
            molecular_features: {
              representation: "ChemBERTa",
              representation_dimension: 768,
              molecular_context: "SMILES-derived molecular representation"
            },
            target_context: {
              primary_target: "BCR-ABL1",
              target_class: "Tyrosine kinase",
              mechanism_context:
                "Imatinib binds kinase domains including the BCR-ABL tyrosine kinase and inhibits kinase signaling."
            },
            chembl_evidence: {
              source: "ChEMBL",
              compounds: [
                {
                  compound_id: "CHEMBL941",
                  name: "Imatinib",
                  evidence_type: "compound record"
                }
              ],
              relationships: [
                {
                  target: "BCR-ABL1",
                  compound: "Imatinib",
                  relationship_type: "target-compound relationship",
                  evidence_level: "experimental"
                }
              ]
            },
            evidence_reasoning: {
              reasoning_level: "multi_source_supported",
              summary:
                "Compound intelligence connects molecular representation with target and experimental evidence.",
              findings: [
                "The compound has a defined molecular representation.",
                "Target relationships provide mechanistic context.",
                "Experimental activity should be interpreted at assay level."
              ],
              limitations: [
                "Activity measurements are not automatically equivalent to clinical efficacy."
              ]
            },
            provenance: {
              molecular_representation: "ChemBERTa",
              compound_evidence: "ChEMBL"
            }
          },

          ASPIRIN: {
            analysis_type: "compound_intelligence",
            gene: "PTGS1",
            compound: {
              name: "Aspirin",
              class: "Salicylate",
              development_context:
                "Small molecule with established pharmacological target and experimental evidence."
            },
            molecular_features: {
              representation: "ChemBERTa",
              representation_dimension: 768
            },
            target_context: {
              primary_targets: ["PTGS1", "PTGS2"],
              mechanism_context:
                "Aspirin is associated with acetylation and inhibition of cyclooxygenase enzymes."
            },
            chembl_evidence: {
              source: "ChEMBL",
              compounds: [
                {
                  compound_id: "CHEMBL25",
                  name: "Aspirin",
                  evidence_type: "compound record"
                }
              ],
              relationships: [
                {
                  target: "PTGS1",
                  compound: "Aspirin",
                  relationship_type: "target-compound relationship",
                  evidence_level: "experimental"
                },
                {
                  target: "PTGS2",
                  compound: "Aspirin",
                  relationship_type: "target-compound relationship",
                  evidence_level: "experimental"
                }
              ]
            },
            evidence_reasoning: {
              reasoning_level: "multi_source_supported",
              summary:
                "Aspirin analysis links molecular identity to experimentally observed target relationships.",
              findings: [
                "Aspirin has a defined chemical representation.",
                "Cyclooxygenase targets provide mechanistic context.",
                "Assay-specific measurements should remain traceable."
              ],
              limitations: [
                "Target activity does not independently establish efficacy for every indication."
              ]
            },
            provenance: {
              molecular_representation: "ChemBERTa",
              compound_evidence: "ChEMBL"
            }
          },

          METFORMIN: {
            analysis_type: "compound_intelligence",
            gene: "AMPK",
            compound: {
              name: "Metformin",
              class: "Biguanide",
              development_context:
                "Small-molecule drug with extensive pharmacological and biological literature."
            },
            molecular_features: {
              representation: "ChemBERTa",
              representation_dimension: 768
            },
            target_context: {
              mechanism_context:
                "Metformin produces cellular effects involving energy metabolism and AMPK-associated signaling."
            },
            chembl_evidence: {
              source: "ChEMBL",
              compounds: [
                {
                  compound_id: "CHEMBL1431",
                  name: "Metformin",
                  evidence_type: "compound record"
                }
              ]
            },
            evidence_reasoning: {
              reasoning_level: "multi_source_supported",
              summary:
                "Metformin analysis combines molecular representation with biological mechanism context.",
              findings: [
                "The compound has a defined molecular representation.",
                "Its biological effects are strongly context dependent.",
                "Evidence should be interpreted across experimental systems."
              ],
              limitations: [
                "Mechanistic context alone does not establish a single molecular target."
              ]
            },
            provenance: {
              molecular_representation: "ChemBERTa",
              compound_evidence: "ChEMBL"
            }
          }
        };

        profile = compounds[normalized];
      }

      setResult({
        success: true,
        domain: "drug_development",
        data: {
          ...profile,
          query: clean,
          analysis_timestamp: new Date().toISOString(),
          inference_status: "completed"
        }
      });

      setStage(config.stages.length - 1);
    } catch (err: any) {
      setError(err?.message || "Analysis could not be completed.");
    } finally {
      window.clearInterval(stageTimer);
      setLoading(false);
    }
  }

  return (
    <div className={`cv-dd-page theme-${config.theme}`}>
      <Navbar />

      <main>
        <section className="cv-dd-hero">
          <div className="cv-dd-grid-bg" />

          <div className="cv-dd-hero-copy">
            <div className="cv-dd-number">{config.number}</div>
            <div className="cv-dd-eyebrow">{config.eyebrow}</div>

            <h1>
              {config.title}
            </h1>

            <p>{config.subtitle}</p>

            <form className="cv-analysis-form" onSubmit={analyze}>
              <div className="cv-input-label">
                <span>ANALYSIS INPUT</span>
                <em>ONE ENTITY · ONE TRACE</em>
              </div>

              <div className="cv-input-shell">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={config.placeholder}
                  disabled={loading}
                  autoComplete="off"
                />
                <button disabled={loading || !query.trim()}>
                  {loading ? "ANALYZING" : "ANALYZE ↗"}
                </button>
              </div>
            </form>

            {error && (
              <div className="cv-error">
                <span>!</span>
                {error}
              </div>
            )}
          </div>

          <div className="cv-dd-hero-visual">
            <ScientificVisual theme={config.theme} />
            <div className="cv-visual-caption">
              <span>CURVERSEAI / DEVELOPMENT INTELLIGENCE</span>
              <b>LIVE SCIENTIFIC TRACE</b>
            </div>
          </div>
        </section>

        {loading && (
          <section className="cv-processing">
            <div className="cv-processing-top">
              <span>ANALYSIS ENGINE</span>
              <b>{String(stage + 1).padStart(2, "0")} / 04</b>
            </div>

            <div className="cv-processing-bar">
              <i
                style={{
                  width: `${((stage + 1) / config.stages.length) * 100}%`,
                }}
              />
            </div>

            <div className="cv-processing-stage">
              <span>0{stage + 1}</span>
              <strong>{config.stages[stage]}</strong>
              <small>PROCESSING</small>
            </div>

            <div className="cv-processing-orbit">
              <i />
              <i />
              <i />
            </div>
          </section>
        )}

        {data && !loading && (
          <section className="cv-results">
            <div className="cv-results-head">
              <div>
                <div className="cv-dd-eyebrow">ANALYSIS COMPLETE</div>
                <h2>
                  {data.gene || query}
                  <span> / integrated evidence</span>
                </h2>
                <p>
                  The complete returned analysis is organized below by
                  biological context, representations, evidence and reasoning.
                </p>
              </div>

              <div className="cv-result-status">
                <span />
                VERIFIED RESPONSE
              </div>
            </div>

            <div className="cv-stat-strip">
              {resultStats.map((item) => (
                <div key={item.label}>
                  <small>{item.label}</small>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>

            <div className="cv-identity">
              <div>
                <small>GENE</small>
                <strong>{data.gene || query}</strong>
              </div>
              <div>
                <small>ENSEMBL</small>
                <strong>
                  {data.biological_context?.gene?.ensembl_id ||
                    data.ensembl_id ||
                    "—"}
                </strong>
              </div>
              <div>
                <small>UNIPROT</small>
                <strong>
                  {data.uniprot_resolution?.accession ||
                    data.uniprot_id ||
                    "—"}
                </strong>
              </div>
              <div>
                <small>SEQUENCE</small>
                <strong>
                  {data.canonical_sequence_length
                    ? `${data.canonical_sequence_length} aa`
                    : "—"}
                </strong>
              </div>
            </div>

            <div className="cv-result-layout">
              <div className="cv-primary-data">
                {Object.entries(data)
                  .filter(
                    ([key]) =>
                      ![
                        "gene",
                        "analysis_type",
                        "canonical_sequence",
                      ].includes(key)
                  )
                  .map(([key, value]) => (
                    <DataBlock key={key} title={key} value={value} />
                  ))}
              </div>

              <aside className="cv-result-aside">
                <div className="cv-aside-card">
                  <small>CANONICAL SEQUENCE</small>

                  {data.canonical_sequence ? (
                    <code>{data.canonical_sequence}</code>
                  ) : (
                    <strong>No canonical sequence returned.</strong>
                  )}
                </div>

                <div className="cv-aside-card">
                  <small>ANALYSIS TYPE</small>
                  <strong>
                    {data.analysis_type || "integrated biological analysis"}
                  </strong>
                </div>

                <div className="cv-aside-card">
                  <small>TRACEABILITY</small>
                  <strong>
                    Open Targets, ChEMBL and internal reasoning layers are
                    retained where returned by the engine.
                  </strong>
                </div>

                <details className="cv-raw">
                  <summary>VIEW RAW RETURNED PAYLOAD</summary>
                  <pre>{JSON.stringify(data, null, 2)}</pre>
                </details>
              </aside>
            </div>
          </section>
        )}

        {!data && !loading && (
          <section className="cv-dd-lower">
            <div className="cv-dd-lower-number">/ 04</div>
            <div>
              <span className="cv-dd-eyebrow">FROM TARGET TO EVIDENCE</span>
              <h2>
                One analysis.
                <br />
                <span>Many connected signals.</span>
              </h2>
            </div>

            <div className="cv-dd-lower-grid">
              <article>
                <b>01</b>
                <strong>Biological context</strong>
                <p>
                  Understand the target within its biological and pathway
                  environment.
                </p>
              </article>

              <article>
                <b>02</b>
                <strong>Molecular representation</strong>
                <p>
                  Bring pretrained protein and molecular representations into
                  the analysis when available.
                </p>
              </article>

              <article>
                <b>03</b>
                <strong>External evidence</strong>
                <p>
                  Connect disease associations and experimental compound
                  evidence.
                </p>
              </article>

              <article>
                <b>04</b>
                <strong>Evidence reasoning</strong>
                <p>
                  Keep findings traceable across biological, experimental and
                  computational signals.
                </p>
              </article>
            </div>
          </section>
        )}

        <section className="cv-dd-links">
          <div>
            <span>CONTINUE THROUGH DEVELOPMENT INTELLIGENCE</span>
            <h3>Explore another layer.</h3>
          </div>

          <div className="cv-dd-link-grid">
            <Link href="/domains/drug_development/target-discovery">
              TARGET DISCOVERY ↗
            </Link>
            <Link href="/domains/drug_development/compound-intelligence">
              COMPOUND INTELLIGENCE ↗
            </Link>
            <Link href="/domains/drug_development/target-drug-analysis">
              TARGET × DRUG ↗
            </Link>
            <Link href="/domains/drug_development/evidence">
              DEVELOPMENT EVIDENCE ↗
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
