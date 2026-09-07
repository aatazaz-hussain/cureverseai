"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./workbench.css";

type Mode =
  | "clinical-profile"
  | "disease-intelligence"
  | "treatment-context"
  | "variant-interpretation";

type ResearchData = {
  [key: string]: string | ResearchData | string[];
};

type Config = {
  eyebrow: string;
  title: string;
  subtitle: string;
  placeholder: string;
  examples: string[];
  description: string;
  investigates: string[];
  pipeline: string[];
  questions: string[];
};

const CONFIG: Record<Mode, Config> = {
  "clinical-profile": {
    eyebrow: "MEDICINE / CLINICAL PROFILE",
    title: "Clinical Profile",
    subtitle:
      "Resolve a biological entity into a structured molecular and clinical research context.",
    placeholder: "Search gene or biological entity...",
    examples: ["TP53", "BRCA1", "EGFR"],
    description:
      "Clinical Profile organizes the biological identity of a selected gene into a structured research context covering molecular identity, biological function, cellular role and evidence-oriented interpretation.",
    investigates: [
      "Gene identity and canonical molecular record",
      "Protein and molecular characteristics",
      "Biological and cellular function",
      "Research and evidence context",
    ],
    pipeline: [
      "Entity resolution",
      "Molecular characterization",
      "Functional context",
      "Evidence context",
    ],
    questions: [
      "What biological entity is being investigated?",
      "What molecular functions are associated with it?",
      "What cellular processes does it participate in?",
      "What research context surrounds the entity?",
    ],
  },

  "disease-intelligence": {
    eyebrow: "MEDICINE / DISEASE INTELLIGENCE",
    title: "Disease Intelligence",
    subtitle:
      "Build a structured biological view of disease from molecular context to research relationships.",
    placeholder: "Search disease...",
    examples: ["Breast Cancer", "Lung Cancer", "Colorectal Cancer"],
    description:
      "Disease Intelligence organizes a disease query into biological context, connected systems, research domains and evidence-oriented research layers.",
    investigates: [
      "Disease biological context",
      "Molecular and cellular systems",
      "Research domains",
      "Disease-related evidence context",
    ],
    pipeline: [
      "Disease resolution",
      "Biological context",
      "Connected systems",
      "Research intelligence",
    ],
    questions: [
      "What biological context defines the disease?",
      "Which molecular systems are relevant?",
      "What research domains surround the disease?",
      "What evidence context should be considered?",
    ],
  },

  "treatment-context": {
    eyebrow: "MEDICINE / TREATMENT CONTEXT",
    title: "Treatment Context",
    subtitle:
      "Connect a therapeutic entity with its targets, biological relationships and research context.",
    placeholder: "Search treatment...",
    examples: ["Imatinib", "Pembrolizumab", "Trastuzumab"],
    description:
      "Treatment Context structures a therapy query around therapeutic class, molecular targets, biological relationships and evidence-oriented research layers.",
    investigates: [
      "Therapeutic identity and class",
      "Known molecular targets",
      "Biological relationships",
      "Treatment research context",
    ],
    pipeline: [
      "Treatment resolution",
      "Target identification",
      "Biological relationship",
      "Evidence context",
    ],
    questions: [
      "What type of treatment is being investigated?",
      "Which biological targets are relevant?",
      "How does the treatment relate to biological systems?",
      "What research context surrounds the therapy?",
    ],
  },

  "variant-interpretation": {
    eyebrow: "MEDICINE / VARIANT INTERPRETATION",
    title: "Variant Interpretation",
    subtitle:
      "Resolve a molecular variant into structured genomic and biological interpretation context.",
    placeholder: "Search variant...",
    examples: ["TP53 R175H", "BRCA1 C61G", "EGFR L858R"],
    description:
      "Variant Interpretation organizes a variant query around gene identity, molecular change, interpretation layers and biological context.",
    investigates: [
      "Variant and gene identity",
      "Molecular variant type",
      "Interpretation layers",
      "Biological and evidence context",
    ],
    pipeline: [
      "Variant resolution",
      "Molecular characterization",
      "Interpretation layers",
      "Evidence context",
    ],
    questions: [
      "Which gene contains the variant?",
      "What molecular change is being represented?",
      "Which interpretation layers are relevant?",
      "What biological context surrounds the variant?",
    ],
  },
};

const DATA: Record<Mode, Record<string, ResearchData>> = {
  "clinical-profile": {
    TP53: {
      entity: "TP53",
      record_type: "Gene / Protein Research Record",
      gene_id: "ENSG00000141510",
      canonical_protein: "P04637",
      protein_length: "393 amino acids",
      biological_role: "Tumor suppressor protein",
      primary_function:
        "Regulates cellular responses to stress and contributes to control of cell-cycle progression, DNA damage responses and programmed cell death.",
      cellular_functions: [
        "Cell-cycle regulation",
        "DNA damage response",
        "Apoptotic signaling",
        "Genome stability",
      ],
      molecular_context: {
        gene: "TP53",
        protein: "Cellular tumor antigen p53",
        localization: "Nuclear regulatory context",
        molecular_role: "Transcriptional regulator",
      },
      research_context: {
        domain: "Cancer biology",
        focus: [
          "Tumor suppressor biology",
          "Genomic stability",
          "Cellular stress response",
          "Cancer-associated molecular alterations",
        ],
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured biological record resolved for TP53.",
        note:
          "This workspace presents structured research context rather than a clinical diagnosis or treatment recommendation.",
      },
    },

    BRCA1: {
      entity: "BRCA1",
      record_type: "Gene / Protein Research Record",
      gene_id: "ENSG00000012048",
      canonical_protein: "P38398",
      biological_role: "DNA repair and genome maintenance",
      primary_function:
        "Participates in cellular mechanisms involved in DNA damage response and maintenance of genomic integrity.",
      cellular_functions: [
        "DNA repair",
        "DNA damage response",
        "Genome maintenance",
        "Cellular checkpoint regulation",
      ],
      molecular_context: {
        gene: "BRCA1",
        protein: "Breast cancer type 1 susceptibility protein",
        molecular_role: "DNA damage response-associated protein",
      },
      research_context: {
        domain: "Cancer genetics",
        focus: [
          "DNA repair biology",
          "Genomic stability",
          "Inherited cancer genetics",
          "Molecular oncology",
        ],
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured biological record resolved for BRCA1.",
        note:
          "This workspace presents research context and does not independently determine clinical significance.",
      },
    },

    EGFR: {
      entity: "EGFR",
      record_type: "Gene / Protein Research Record",
      gene_id: "ENSG00000146648",
      canonical_protein: "P00533",
      biological_role: "Receptor tyrosine kinase",
      primary_function:
        "Acts as a cell-surface receptor involved in signaling processes that regulate cellular growth, survival and other biological responses.",
      cellular_functions: [
        "Receptor signaling",
        "Cellular growth signaling",
        "Cell survival signaling",
        "Signal transduction",
      ],
      molecular_context: {
        gene: "EGFR",
        protein: "Epidermal growth factor receptor",
        molecular_role: "Transmembrane receptor tyrosine kinase",
        localization: "Cell membrane",
      },
      research_context: {
        domain: "Molecular oncology",
        focus: [
          "Growth-factor signaling",
          "Cancer biology",
          "Receptor signaling",
          "Targeted therapy research",
        ],
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured biological record resolved for EGFR.",
        note:
          "This workspace is designed for research interpretation and is not a clinical decision system.",
      },
    },
  },

  "disease-intelligence": {
    "Breast Cancer": {
      entity: "Breast Cancer",
      record_type: "Disease Research Record",
      biological_context: {
        system: "Breast tissue and associated cellular systems",
        research_context:
          "Disease research can involve genomic, molecular, cellular and tissue-level investigation.",
        biological_layers: [
          "Genomic alterations",
          "Cellular signaling",
          "Tumor microenvironment",
          "Disease progression biology",
        ],
      },
      research_domains: [
        "Cancer genomics",
        "Molecular oncology",
        "Tumor biology",
        "Therapeutic research",
      ],
      connected_systems: [
        "Genomic regulation",
        "Cell signaling",
        "Cell proliferation",
        "Tumor microenvironment",
      ],
      intelligence_layers: {
        molecular: "Genes, proteins and molecular alterations",
        cellular: "Cellular behavior and signaling systems",
        systems: "Connected biological processes and disease context",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured disease research context resolved for Breast Cancer.",
        note:
          "The workspace organizes research context and does not provide patient-specific diagnosis.",
      },
    },

    "Lung Cancer": {
      entity: "Lung Cancer",
      record_type: "Disease Research Record",
      biological_context: {
        system: "Pulmonary tissue and associated cellular systems",
        research_context:
          "Research may examine genomic alterations, cellular signaling, tissue biology and disease progression.",
        biological_layers: [
          "Genomic alterations",
          "Growth signaling",
          "Cellular state",
          "Tumor microenvironment",
        ],
      },
      research_domains: [
        "Cancer genomics",
        "Molecular pathology",
        "Cell signaling",
        "Therapeutic research",
      ],
      connected_systems: [
        "Receptor signaling",
        "Cell proliferation",
        "DNA damage response",
        "Tumor microenvironment",
      ],
      intelligence_layers: {
        molecular: "Molecular alterations and signaling components",
        cellular: "Cellular processes associated with disease biology",
        systems: "Integrated biological disease context",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured disease research context resolved for Lung Cancer.",
        note:
          "The workspace does not substitute for clinical diagnosis or medical advice.",
      },
    },

    "Colorectal Cancer": {
      entity: "Colorectal Cancer",
      record_type: "Disease Research Record",
      biological_context: {
        system: "Colorectal tissue and associated cellular systems",
        research_context:
          "Disease research can integrate genomic, cellular, signaling and tissue-level biological information.",
        biological_layers: [
          "Genomic alterations",
          "Cell-cycle regulation",
          "Cell signaling",
          "Tumor microenvironment",
        ],
      },
      research_domains: [
        "Cancer genetics",
        "Molecular oncology",
        "Tumor biology",
        "Therapeutic research",
      ],
      connected_systems: [
        "Cell-cycle control",
        "DNA repair",
        "Growth signaling",
        "Cellular differentiation",
      ],
      intelligence_layers: {
        molecular: "Molecular and genomic disease context",
        cellular: "Cellular processes relevant to disease biology",
        systems: "Connected biological systems",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured disease research context resolved for Colorectal Cancer.",
        note:
          "This is a research-oriented biological context, not patient-specific medical advice.",
      },
    },
  },

  "treatment-context": {
    Imatinib: {
      entity: "Imatinib",
      record_type: "Treatment Research Record",
      therapeutic_class: "Tyrosine kinase inhibitor",
      therapeutic_context:
        "A targeted therapy studied in contexts involving specific kinase signaling pathways.",
      targets: [
        "BCR-ABL1",
        "KIT",
        "PDGFRA",
      ],
      biological_relationship: {
        primary_relationship:
          "Treatment interacts with selected protein kinase targets.",
        molecular_context:
          "Target engagement can alter kinase-mediated cellular signaling.",
        research_context:
          "Used as a research example for connecting treatment entities with molecular targets.",
      },
      research_layers: [
        "Drug identity",
        "Target relationships",
        "Kinase signaling",
        "Therapeutic research",
      ],
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured treatment context resolved for Imatinib.",
        note:
          "The workspace does not determine whether a treatment is appropriate for an individual patient.",
      },
    },

    Pembrolizumab: {
      entity: "Pembrolizumab",
      record_type: "Treatment Research Record",
      therapeutic_class: "Monoclonal antibody / immune checkpoint inhibitor",
      therapeutic_context:
        "An immunotherapy research entity associated with immune checkpoint biology.",
      targets: [
        "PD-1",
      ],
      biological_relationship: {
        primary_relationship:
          "The treatment is associated with immune checkpoint signaling through PD-1.",
        molecular_context:
          "Checkpoint biology connects treatment research with immune-cell signaling and tumor-immune interactions.",
        research_context:
          "Used as a research example for connecting therapy with immune biological context.",
      },
      research_layers: [
        "Treatment identity",
        "Immune checkpoint biology",
        "Target relationship",
        "Therapeutic research",
      ],
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured treatment context resolved for Pembrolizumab.",
        note:
          "No patient-specific treatment recommendation is generated.",
      },
    },

    Trastuzumab: {
      entity: "Trastuzumab",
      record_type: "Treatment Research Record",
      therapeutic_class: "Monoclonal antibody",
      therapeutic_context:
        "A targeted biological therapy associated with HER2/ERBB2 receptor biology.",
      targets: [
        "ERBB2 / HER2",
      ],
      biological_relationship: {
        primary_relationship:
          "The treatment is connected to HER2/ERBB2 receptor biology.",
        molecular_context:
          "Target-directed interaction connects therapy research with receptor signaling.",
        research_context:
          "Used as a research example for treatment-target relationship analysis.",
      },
      research_layers: [
        "Treatment identity",
        "Target receptor",
        "Receptor signaling",
        "Therapeutic research",
      ],
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured treatment context resolved for Trastuzumab.",
        note:
          "This workspace is for structured research context rather than individualized treatment decisions.",
      },
    },
  },

  "variant-interpretation": {
    "TP53 R175H": {
      entity: "TP53 R175H",
      record_type: "Variant Research Record",
      gene: "TP53",
      variant: "R175H",
      variant_type: "Missense substitution",
      molecular_context: {
        reference_gene: "TP53",
        amino_acid_change: "Arginine → Histidine",
        position: "175",
        protein: "p53",
      },
      interpretation_layers: [
        "Variant identity",
        "Protein-level consequence",
        "Gene biological context",
        "Research evidence context",
      ],
      biological_question:
        "How does a specific sequence-level change relate to the biological context of the affected protein?",
      interpretation_context: {
        genomic: "Variant represented at the sequence level",
        protein: "Amino-acid substitution in the encoded protein",
        biological: "Interpretation should be considered within TP53 biology",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured variant record resolved for TP53 R175H.",
        note:
          "This record is not presented as an independent clinical classification.",
      },
    },

    "BRCA1 C61G": {
      entity: "BRCA1 C61G",
      record_type: "Variant Research Record",
      gene: "BRCA1",
      variant: "C61G",
      variant_type: "Missense substitution",
      molecular_context: {
        reference_gene: "BRCA1",
        amino_acid_change: "Cysteine → Glycine",
        position: "61",
        protein: "BRCA1",
      },
      interpretation_layers: [
        "Variant identity",
        "Protein-level consequence",
        "BRCA1 molecular context",
        "Research evidence context",
      ],
      biological_question:
        "How should a sequence-level change be interpreted in the molecular context of BRCA1?",
      interpretation_context: {
        genomic: "Specific sequence-level variant",
        protein: "Amino-acid substitution",
        biological: "Interpretation should be considered within BRCA1 DNA-repair biology",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured variant record resolved for BRCA1 C61G.",
        note:
          "The workspace does not independently establish clinical pathogenicity.",
      },
    },

    "EGFR L858R": {
      entity: "EGFR L858R",
      record_type: "Variant Research Record",
      gene: "EGFR",
      variant: "L858R",
      variant_type: "Missense substitution",
      molecular_context: {
        reference_gene: "EGFR",
        amino_acid_change: "Leucine → Arginine",
        position: "858",
        protein: "Epidermal growth factor receptor",
      },
      interpretation_layers: [
        "Variant identity",
        "Protein-level consequence",
        "EGFR signaling context",
        "Research evidence context",
      ],
      biological_question:
        "How does the molecular change relate to EGFR protein and signaling biology?",
      interpretation_context: {
        genomic: "Specific sequence-level variant",
        protein: "Amino-acid substitution at residue 858",
        biological: "Interpretation should be considered within EGFR signaling biology",
      },
      evidence_context: {
        record_status: "MATCHED",
        interpretation:
          "Structured variant record resolved for EGFR L858R.",
        note:
          "This research view does not independently determine treatment or clinical significance.",
      },
    },
  },
};

function normalize(value: string) {
  return value.trim().toLowerCase();
}

function findRecord(mode: Mode, query: string) {
  const records = DATA[mode];
  const key = Object.keys(records).find(
    (item) => normalize(item) === normalize(query)
  );

  return key ? records[key] : null;
}

function DataBlock({
  label,
  value,
  depth = 0,
}: {
  label: string;
  value: unknown;
  depth?: number;
}) {
  if (Array.isArray(value)) {
    return (
      <div className={`med-data-block med-depth-${depth}`}>
        <div className="med-data-label">{label}</div>

        <div className="med-data-array">
          {value.map((item, index) => (
            <div className="med-data-array-item" key={`${label}-${index}`}>
              <span>•</span>
              <p>{String(item)}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (value && typeof value === "object") {
    return (
      <div className={`med-data-block med-depth-${depth}`}>
        <div className="med-data-label">{label}</div>

        <div className="med-data-children">
          {Object.entries(value as ResearchData).map(([childLabel, childValue]) => (
            <DataBlock
              key={childLabel}
              label={childLabel}
              value={childValue}
              depth={depth + 1}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`med-data-row med-depth-${depth}`}>
      <span>{label}</span>
      <strong>{String(value)}</strong>
    </div>
  );
}

function ScientificVisual({ mode, processing }: { mode: Mode; processing: boolean }) {
  return (
    <div className={`med-scientific-visual med-visual-${mode}`}>
      <div className="med-visual-grid" />

      {mode === "clinical-profile" && (
        <>
          <div className="med-patient-core">
            <div className="med-patient-head" />
            <div className="med-patient-body" />
          </div>
          <div className="med-biomarker med-biomarker-1">GENE</div>
          <div className="med-biomarker med-biomarker-2">PROTEIN</div>
          <div className="med-biomarker med-biomarker-3">CELL</div>
        </>
      )}

      {mode === "disease-intelligence" && (
        <div className="med-disease-network">
          <i className="node node-center">DISEASE</i>
          <i className="node node-1">GENE</i>
          <i className="node node-2">CELL</i>
          <i className="node node-3">PATHWAY</i>
          <i className="node node-4">SYSTEM</i>
          <span className="network-line line-1" />
          <span className="network-line line-2" />
          <span className="network-line line-3" />
          <span className="network-line line-4" />
        </div>
      )}

      {mode === "treatment-context" && (
        <div className="med-treatment-flow">
          <div className="treatment-node">DRUG</div>
          <span />
          <div className="treatment-node">TARGET</div>
          <span />
          <div className="treatment-node">PATHWAY</div>
        </div>
      )}

      {mode === "variant-interpretation" && (
        <div className="med-dna">
          <div className="dna-strand dna-left" />
          <div className="dna-strand dna-right" />
          <div className="dna-mark">VARIANT</div>
        </div>
      )}

      {processing && (
        <div className="med-processing-overlay">
          <div className="med-processing-ring" />
          <span>ANALYZING BIOLOGICAL CONTEXT</span>
          <small>Resolving research layers...</small>
        </div>
      )}
    </div>
  );
}

function WorkspaceOverview({ config }: { config: Config }) {
  return (
    <section className="med-workspace-overview">
      <div className="med-overview-intro">
        <span>MEDICINE RESEARCH WORKSPACE</span>
        <h2>
          From biological query
          <br />
          to structured research context.
        </h2>
        <p>{config.description}</p>
      </div>

      <div className="med-overview-columns">
        <div>
          <label>WHAT THIS WORKSPACE INVESTIGATES</label>

          <ul className="med-overview-list">
            {config.investigates.map((item) => (
              <li key={item}>
                <i />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <label>RESEARCH PIPELINE</label>

          <div className="med-pipeline">
            {config.pipeline.map((item, index) => (
              <div key={item}>
                <span>0{index + 1}</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="med-research-questions">
        <label>QUESTIONS THIS WORKSPACE HELPS STRUCTURE</label>

        <div>
          {config.questions.map((question, index) => (
            <article key={question}>
              <span>0{index + 1}</span>
              <p>{question}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function MedicineWorkbench({ mode }: { mode: Mode }) {
  const config = CONFIG[mode];

  const [query, setQuery] = useState("");
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ResearchData | null>(null);
  const [searched, setSearched] = useState(false);

  const matchedRecord = useMemo(
    () => findRecord(mode, query),
    [mode, query]
  );

  useEffect(() => {
    setQuery("");
    setResult(null);
    setSearched(false);
    setProcessing(false);
  }, [mode]);

  const runSearch = (event: FormEvent) => {
    event.preventDefault();

    if (!query.trim()) return;

    setSearched(true);
    setResult(null);
    setProcessing(true);

    window.setTimeout(() => {
      setProcessing(false);
      setResult(matchedRecord);
    }, 3400);
  };

  return (
    <div className="med-workbench-page">
      <Navbar />

      <main>
        <section className="med-workbench-hero">
          <div className="med-hero-noise" />

          <div className="med-workbench-inner">
            <div className="med-workbench-copy">
              <span className="med-workbench-eyebrow">
                {config.eyebrow}
              </span>

              <h1>{config.title}</h1>

              <p>{config.subtitle}</p>

              <div className="med-search-wrap">
                <form onSubmit={runSearch}>
                  <div className="med-search-icon">⌕</div>

                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={config.placeholder}
                    autoComplete="off"
                  />

                  <button type="submit" disabled={processing || !query.trim()}>
                    {processing ? "ANALYZING..." : "SEARCH"}
                  </button>
                </form>

                <div className="med-search-hint">
                  <span>SEARCH THE RESEARCH RECORD</span>
                  <span>EXACT ENTITY MATCH</span>
                </div>
              </div>
            </div>

            <ScientificVisual mode={mode} processing={processing} />
          </div>
        </section>

        <WorkspaceOverview config={config} />

        <section className="med-results-section">
          {!searched && !processing && (
            <div className="med-empty-state">
              <span>RESEARCH RECORD</span>
              <h2>Search to reveal the biological record.</h2>
              <p>
                Enter a supported research entity above. Detailed structured
                information will appear here only after the search is executed.
              </p>
            </div>
          )}

          {processing && (
            <div className="med-loading-state">
              <div className="med-loader">
                <span />
                <span />
                <span />
              </div>

              <span>PROCESSING RESEARCH QUERY</span>

              <p>
                Resolving entity identity, molecular context and research
                layers...
              </p>
            </div>
          )}

          {searched && !processing && !result && (
            <div className="med-not-found">
              <span>NOT FOUND</span>
              <h2>No matching biological record was found for this query.</h2>
              <p>
                Search using an exact supported research entity for this
                workspace.
              </p>
            </div>
          )}

          {result && !processing && (
            <div className="med-result">
              <div className="med-result-header">
                <div>
                  <span>MATCHED RESEARCH RECORD</span>
                  <h2>{String(result.entity)}</h2>
                </div>

                <div className="med-result-status">
                  <i />
                  MATCHED
                </div>
              </div>

              <div className="med-result-body">
                {Object.entries(result).map(([label, value]) => (
                  <DataBlock key={label} label={label} value={value} />
                ))}
              </div>
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
}
