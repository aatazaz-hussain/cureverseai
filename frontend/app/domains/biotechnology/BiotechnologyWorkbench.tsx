"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import "./biotechnology-workbench.css";

type Mode =
  | "genomics"
  | "proteomics"
  | "cellular-biology"
  | "molecular-systems";

type RecordData = Record<string, string | string[] | Record<string, string | string[]>>;

const CONFIG = {
  genomics: {
    number: "01",
    title: "Genomics Intelligence",
    subtitle:
      "Resolve genes and genomic entities into structured molecular and biological research context.",
    placeholder: "Search genomic entity...",
    examples: ["TP53", "BRCA1", "EGFR"],
    visual: "dna",
  },
  proteomics: {
    number: "02",
    title: "Proteomics Intelligence",
    subtitle:
      "Explore proteins through molecular identity, function, domains, interactions and biological context.",
    placeholder: "Search protein...",
    examples: ["TP53", "BRCA1", "EGFR"],
    visual: "protein",
  },
  "cellular-biology": {
    number: "03",
    title: "Cellular Biology",
    subtitle:
      "Connect cellular processes with molecular participants, signaling and biological systems.",
    placeholder: "Search cellular process...",
    examples: ["Cell Cycle", "DNA Repair", "Cell Signaling"],
    visual: "cell",
  },
  "molecular-systems": {
    number: "04",
    title: "Molecular Systems",
    subtitle:
      "Map connected biological entities into a structured systems-level research context.",
    placeholder: "Search biological system...",
    examples: ["DNA Damage Response", "Growth Signaling", "Genome Stability"],
    visual: "network",
  },
} as const;

const DATA: Record<Mode, Record<string, RecordData>> = {
  genomics: {
    TP53: {
      entity_identity: {
        name: "TP53",
        entity_type: "Gene",
        gene_id: "ENSG00000141510",
        protein_id: "P04637",
        canonical_protein: "Cellular tumor antigen p53",
      },
      genomic_context: {
        organism: "Homo sapiens",
        gene_symbol: "TP53",
        molecular_role: "Tumor suppressor",
        research_domain: "Cancer biology",
      },
      biological_function: [
        "Regulation of cellular responses to stress",
        "Cell-cycle control",
        "DNA damage response",
        "Programmed cell death",
        "Genome stability",
      ],
      molecular_context: {
        protein_role: "Transcriptional regulator",
        cellular_context: "Primarily nuclear regulatory activity",
        research_focus: "Cellular stress and genome integrity",
      },
      biological_relationships: [
        "DNA damage response",
        "Cell-cycle regulation",
        "Apoptotic signaling",
        "Genome maintenance",
      ],
      research_context: {
        primary_area: "Molecular oncology",
        research_layers: [
          "Genomics",
          "Cancer biology",
          "Cellular regulation",
          "Genome stability",
        ],
      },
      record_status: "MATCHED — structured genomic research record",
    },

    BRCA1: {
      entity_identity: {
        name: "BRCA1",
        entity_type: "Gene",
        gene_id: "ENSG00000012048",
        protein_id: "P38398",
        canonical_protein: "BRCA1 DNA repair associated protein",
      },
      genomic_context: {
        organism: "Homo sapiens",
        gene_symbol: "BRCA1",
        molecular_role: "DNA repair and genome maintenance",
        research_domain: "Cancer genetics",
      },
      biological_function: [
        "DNA damage response",
        "DNA repair",
        "Genome maintenance",
        "Cellular checkpoint regulation",
      ],
      molecular_context: {
        protein_role: "DNA damage response-associated protein",
        cellular_context: "Cellular genome maintenance",
        research_focus: "DNA repair and genomic stability",
      },
      biological_relationships: [
        "DNA repair",
        "Genome stability",
        "DNA damage response",
        "Cellular checkpoint biology",
      ],
      research_context: {
        primary_area: "Cancer genetics",
        research_layers: [
          "Genomics",
          "DNA repair",
          "Genome maintenance",
          "Molecular oncology",
        ],
      },
      record_status: "MATCHED — structured genomic research record",
    },

    EGFR: {
      entity_identity: {
        name: "EGFR",
        entity_type: "Gene",
        gene_id: "ENSG00000146648",
        protein_id: "P00533",
        canonical_protein: "Epidermal growth factor receptor",
      },
      genomic_context: {
        organism: "Homo sapiens",
        gene_symbol: "EGFR",
        molecular_role: "Receptor tyrosine kinase",
        research_domain: "Cell signaling",
      },
      biological_function: [
        "Receptor-mediated signal transduction",
        "Cellular growth signaling",
        "Cell survival signaling",
        "Growth-factor response",
      ],
      molecular_context: {
        protein_role: "Transmembrane receptor tyrosine kinase",
        cellular_context: "Cell-surface receptor",
        research_focus: "Growth-factor and receptor signaling",
      },
      biological_relationships: [
        "Receptor signaling",
        "Cell proliferation",
        "Cell survival",
        "Targeted therapy research",
      ],
      research_context: {
        primary_area: "Molecular oncology",
        research_layers: [
          "Genomics",
          "Cell signaling",
          "Receptor biology",
          "Therapeutic research",
        ],
      },
      record_status: "MATCHED — structured genomic research record",
    },
  },

  proteomics: {
    TP53: {
      protein_identity: {
        name: "TP53 / p53",
        protein_id: "P04637",
        entity_type: "Protein",
        encoded_by: "TP53",
      },
      molecular_function: [
        "Transcriptional regulation",
        "Cell-cycle control",
        "DNA damage response",
        "Apoptotic signaling",
      ],
      biological_role: {
        primary_role: "Tumor suppressor",
        cellular_context: "Nuclear regulatory environment",
        research_domain: "Cancer biology",
      },
      protein_context: {
        molecular_layer: "Protein function",
        biological_layer: "Cellular regulation",
        systems_layer: "Genome integrity",
      },
      interaction_context: [
        "DNA damage response systems",
        "Cell-cycle regulatory systems",
        "Apoptotic pathways",
        "Genome maintenance",
      ],
      research_context: {
        focus: "Functional protein biology",
        applications: [
          "Protein function research",
          "Cancer biology",
          "Molecular regulation",
        ],
      },
      record_status: "MATCHED — structured proteomics research record",
    },

    BRCA1: {
      protein_identity: {
        name: "BRCA1",
        protein_id: "P38398",
        entity_type: "Protein",
        encoded_by: "BRCA1",
      },
      molecular_function: [
        "DNA damage response",
        "DNA repair",
        "Genome maintenance",
        "Regulatory protein interactions",
      ],
      biological_role: {
        primary_role: "DNA repair-associated protein",
        cellular_context: "Genome maintenance systems",
        research_domain: "Cancer genetics",
      },
      protein_context: {
        molecular_layer: "Protein function",
        biological_layer: "DNA repair",
        systems_layer: "Genome stability",
      },
      interaction_context: [
        "DNA repair machinery",
        "DNA damage response",
        "Genome maintenance",
        "Cellular checkpoint systems",
      ],
      research_context: {
        focus: "Functional protein biology",
        applications: [
          "DNA repair research",
          "Cancer genetics",
          "Protein interaction research",
        ],
      },
      record_status: "MATCHED — structured proteomics research record",
    },

    EGFR: {
      protein_identity: {
        name: "EGFR",
        protein_id: "P00533",
        entity_type: "Protein",
        encoded_by: "EGFR",
      },
      molecular_function: [
        "Receptor signaling",
        "Signal transduction",
        "Growth-factor response",
        "Cellular signaling regulation",
      ],
      biological_role: {
        primary_role: "Receptor tyrosine kinase",
        cellular_context: "Cell membrane",
        research_domain: "Cell signaling",
      },
      protein_context: {
        molecular_layer: "Receptor protein",
        biological_layer: "Signal transduction",
        systems_layer: "Growth signaling",
      },
      interaction_context: [
        "Growth-factor signaling",
        "Receptor activation",
        "Cell proliferation",
        "Therapeutic target research",
      ],
      research_context: {
        focus: "Protein signaling biology",
        applications: [
          "Receptor biology",
          "Molecular oncology",
          "Target research",
        ],
      },
      record_status: "MATCHED — structured proteomics research record",
    },
  },

  "cellular-biology": {
    "Cell Cycle": {
      cellular_identity: {
        process: "Cell Cycle",
        biological_level: "Cellular process",
        research_domain: "Cellular biology",
      },
      core_processes: [
        "Cell growth",
        "DNA replication",
        "Chromosome segregation",
        "Cell division",
      ],
      molecular_participants: [
        "Cell-cycle regulatory proteins",
        "DNA replication machinery",
        "Checkpoint regulators",
        "Chromosome segregation machinery",
      ],
      cellular_context: {
        primary_context: "Cellular proliferation",
        regulatory_context: "Checkpoint and progression control",
        systems_context: "Coordination of cellular growth and division",
      },
      signaling_context: [
        "Cell-cycle signaling",
        "DNA damage checkpoints",
        "Growth regulation",
      ],
      research_context: {
        focus: "Cellular proliferation and regulation",
        layers: [
          "Molecular regulation",
          "Cellular processes",
          "Genome integrity",
        ],
      },
      record_status: "MATCHED — structured cellular biology record",
    },

    "DNA Repair": {
      cellular_identity: {
        process: "DNA Repair",
        biological_level: "Cellular and molecular process",
        research_domain: "Genome maintenance",
      },
      core_processes: [
        "Damage recognition",
        "Repair pathway activation",
        "DNA restoration",
        "Genome integrity maintenance",
      ],
      molecular_participants: [
        "DNA repair proteins",
        "Damage-response regulators",
        "Checkpoint proteins",
        "Genome maintenance factors",
      ],
      cellular_context: {
        primary_context: "Response to DNA damage",
        regulatory_context: "Damage sensing and repair",
        systems_context: "Maintenance of genomic integrity",
      },
      signaling_context: [
        "DNA damage response",
        "Cellular checkpoint signaling",
        "Genome maintenance",
      ],
      research_context: {
        focus: "Genome stability",
        layers: [
          "DNA repair",
          "Cellular stress response",
          "Cancer biology",
        ],
      },
      record_status: "MATCHED — structured cellular biology record",
    },

    "Cell Signaling": {
      cellular_identity: {
        process: "Cell Signaling",
        biological_level: "Cellular communication",
        research_domain: "Cell biology",
      },
      core_processes: [
        "Signal reception",
        "Signal transduction",
        "Intracellular response",
        "Cellular adaptation",
      ],
      molecular_participants: [
        "Cell-surface receptors",
        "Signal transducers",
        "Protein kinases",
        "Transcriptional regulators",
      ],
      cellular_context: {
        primary_context: "Cellular communication",
        regulatory_context: "Extracellular-to-intracellular signaling",
        systems_context: "Coordination of cellular responses",
      },
      signaling_context: [
        "Receptor signaling",
        "Kinase signaling",
        "Transcriptional response",
      ],
      research_context: {
        focus: "Cellular communication and regulation",
        layers: [
          "Molecular signaling",
          "Cellular response",
          "Systems biology",
        ],
      },
      record_status: "MATCHED — structured cellular biology record",
    },
  },

  "molecular-systems": {
    "DNA Damage Response": {
      system_identity: {
        system: "DNA Damage Response",
        biological_level: "Molecular system",
        research_domain: "Genome stability",
      },
      system_components: [
        "DNA damage sensors",
        "Signal transducers",
        "Checkpoint regulators",
        "DNA repair machinery",
      ],
      relationships: [
        "Damage detection → signaling",
        "Signaling → checkpoint control",
        "Checkpoint control → repair",
        "Repair → genome restoration",
      ],
      system_architecture: {
        input: "DNA damage and cellular stress",
        processing: "Damage sensing and signaling",
        response: "Checkpoint activation and repair",
        outcome: "Maintenance of genome integrity",
      },
      biological_context: [
        "DNA repair",
        "Cell-cycle regulation",
        "Genome maintenance",
        "Cellular stress response",
      ],
      research_context: {
        focus: "Integrated genome stability research",
        layers: [
          "Genes",
          "Proteins",
          "Cellular processes",
          "Biological systems",
        ],
      },
      record_status: "MATCHED — structured molecular systems record",
    },

    "Growth Signaling": {
      system_identity: {
        system: "Growth Signaling",
        biological_level: "Molecular signaling system",
        research_domain: "Cell signaling",
      },
      system_components: [
        "Growth-factor signals",
        "Cell-surface receptors",
        "Signal transduction proteins",
        "Transcriptional regulators",
      ],
      relationships: [
        "Signal → receptor",
        "Receptor → intracellular signaling",
        "Signaling → cellular response",
        "Response → growth and survival processes",
      ],
      system_architecture: {
        input: "Extracellular growth signals",
        processing: "Receptor and intracellular signal transduction",
        response: "Cellular growth and survival programs",
        outcome: "Coordinated cellular response",
      },
      biological_context: [
        "Receptor biology",
        "Signal transduction",
        "Cell proliferation",
        "Cell survival",
      ],
      research_context: {
        focus: "Molecular signaling systems",
        layers: [
          "Receptors",
          "Proteins",
          "Pathways",
          "Cellular response",
        ],
      },
      record_status: "MATCHED — structured molecular systems record",
    },

    "Genome Stability": {
      system_identity: {
        system: "Genome Stability",
        biological_level: "Integrated biological system",
        research_domain: "Genomics and cell biology",
      },
      system_components: [
        "DNA repair mechanisms",
        "Damage response systems",
        "Cell-cycle checkpoints",
        "Chromosome maintenance mechanisms",
      ],
      relationships: [
        "DNA damage → damage response",
        "Damage response → checkpoint control",
        "Checkpoint control → repair",
        "Repair → genome maintenance",
      ],
      system_architecture: {
        input: "Genomic stress or DNA damage",
        processing: "Detection, signaling and repair",
        response: "Cellular protection and genome maintenance",
        outcome: "Preservation of genomic integrity",
      },
      biological_context: [
        "DNA repair",
        "Cell-cycle regulation",
        "Chromosome maintenance",
        "Cellular stress response",
      ],
      research_context: {
        focus: "Integrated genome maintenance",
        layers: [
          "Genomic information",
          "Protein machinery",
          "Cellular processes",
          "Systems biology",
        ],
      },
      record_status: "MATCHED — structured molecular systems record",
    },
  },
};

function Visual({ mode, loading }: { mode: Mode; loading: boolean }) {
  return (
    <div className={`bw-visual bw-${mode}`}>
      <div className="bw-orbit orbit-a" />
      <div className="bw-orbit orbit-b" />
      <div className="bw-core">
        {mode === "genomics" && <><i /><i /><i /><i /><b>DNA</b></>}
        {mode === "proteomics" && <><i /><i /><i /><i /><b>PROTEIN</b></>}
        {mode === "cellular-biology" && <><i /><i /><i /><i /><b>CELL</b></>}
        {mode === "molecular-systems" && <><i /><i /><i /><i /><b>SYSTEM</b></>}
      </div>
      {loading && (
        <div className="bw-scan">
          <span />
          ANALYZING BIOLOGICAL SYSTEM
        </div>
      )}
    </div>
  );
}

function DataSection({
  title,
  value,
}: {
  title: string;
  value: string | string[] | Record<string, string | string[]>;
}) {
  return (
    <section className="bw-data-section">
      <div className="bw-data-heading">
        <span>RESEARCH LAYER</span>
        <h3>{title.replaceAll("_", " ")}</h3>
      </div>

      <div className="bw-data-content">
        {Array.isArray(value) ? (
          <div className="bw-list">
            {value.map((item) => (
              <div key={item}>
                <i />
                <span>{item}</span>
              </div>
            ))}
          </div>
        ) : typeof value === "object" ? (
          <div className="bw-subgrid">
            {Object.entries(value).map(([key, item]) => (
              <div className="bw-subitem" key={key}>
                <small>{key.replaceAll("_", " ")}</small>
                {Array.isArray(item) ? (
                  <div className="bw-sublist">
                    {item.map((x) => <span key={x}>• {x}</span>)}
                  </div>
                ) : (
                  <strong>{item}</strong>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="bw-long-value">{value}</p>
        )}
      </div>
    </section>
  );
}

export default function BiotechnologyWorkbench({
  mode,
}: {
  mode: Mode;
}) {
  const config = CONFIG[mode];

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [result, setResult] = useState<RecordData | null>(null);

  useEffect(() => {
    setQuery("");
    setLoading(false);
    setSearched(false);
    setResult(null);
  }, [mode]);

  const search = (e: FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setResult(null);

    setTimeout(() => {
      const found = Object.keys(DATA[mode]).find(
        (key) => key.toLowerCase() === query.trim().toLowerCase()
      );

      setResult(found ? DATA[mode][found] : null);
      setLoading(false);
    }, 3400);
  };

  return (
    <main className="bw-page">
      <header className="bw-header">
        <Link href="/domains/biotechnology">← BIOTECHNOLOGY</Link>
        <span>{config.number} / BIOTECHNOLOGY WORKBENCH</span>
      </header>

      <section className="bw-hero">
        <div className="bw-copy">
          <span className="bw-eyebrow">
            BIOTECHNOLOGY / {config.number}
          </span>

          <h1>
            {config.title.split(" ")[0]}
            <br />
            <em>{config.title.split(" ").slice(1).join(" ")}</em>
          </h1>

          <p>{config.subtitle}</p>

          <form className="bw-search" onSubmit={search}>
            <span>⌕</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={config.placeholder}
              autoComplete="off"
            />
            <button disabled={!query.trim() || loading}>
              {loading ? "ANALYZING" : "SEARCH"}
            </button>
          </form>
        </div>

        <Visual mode={mode} loading={loading} />
      </section>

      {!searched && !loading && (
        <section className="bw-before">
          <span>RESEARCH WORKSPACE</span>
          <h2>Enter a biological query to begin.</h2>
          <p>
            The detailed research record will be resolved and rendered here
            after analysis.
          </p>
        </section>
      )}

      {searched && !loading && !result && (
        <section className="bw-not-found">
          <span>NOT FOUND</span>
          <h2>No matching biological record was found for this query.</h2>
        </section>
      )}

      {loading && (
        <section className="bw-processing">
          <div className="bw-processing-ring" />
          <span>PROCESSING BIOLOGICAL QUERY</span>
          <p>
            Resolving entity identity, molecular relationships and biological
            context...
          </p>
        </section>
      )}

      {result && !loading && (
        <section className="bw-result">
          <div className="bw-result-top">
            <div>
              <span>MATCHED RESEARCH RECORD</span>
              <h2>
                {String(
                  Object.values(result).find(
                    (x) =>
                      typeof x === "object" &&
                      !Array.isArray(x) &&
                      Object.keys(x).some((k) =>
                        ["name", "process", "system"].includes(k)
                      )
                  )
                ) !== "[object Object]"
                  ? "BIOLOGICAL RECORD"
                  : "BIOLOGICAL RECORD"}
              </h2>
            </div>

            <div className="bw-status">
              <i />
              MATCHED
            </div>
          </div>

          <div className="bw-result-intro">
            <span>STRUCTURED BIOLOGICAL INTELLIGENCE</span>
            <p>
              Research context resolved across molecular identity, biological
              relationships, system context and supporting research layers.
            </p>
          </div>

          <div className="bw-data">
            {Object.entries(result).map(([key, value]) => (
              <DataSection key={key} title={key} value={value} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
