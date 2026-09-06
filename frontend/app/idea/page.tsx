"use client";
import Footer from "@/components/Footer";

import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import "./idea.css";

const systemLayers = [
  {
    number: "01",
    title: "Biological Data Ingestion",
    short: "Real scientific sources",
    image: "/idea/dna-helix.png",
    text: "CureVerseAI begins with biological entities rather than generic text. The system can resolve genes and biological identifiers through Ensembl, connect proteins through UniProt mappings, and retrieve pathway and interaction context from Reactome. This gives the intelligence layer structured biological context before any downstream reasoning begins.",
    details: [
      "Gene symbols and identifiers are normalized before analysis.",
      "Ensembl provides gene-level identity and cross-references.",
      "UniProt mappings connect genes to protein records and reviewed entries.",
      "Reactome contributes pathway and biological process context.",
      "The resulting context becomes the foundation for downstream analysis."
    ]
  },
  {
    number: "02",
    title: "Entity Resolution",
    short: "One biological identity",
    image: "/idea/cellular-intelligence.png",
    text: "Scientific databases use different identifiers and naming conventions. CureVerseAI therefore resolves the same biological entity across sources instead of treating every record as an unrelated object. For a gene such as TP53, the system can connect the gene identity to its Ensembl record, canonical protein information and external evidence identifiers.",
    details: [
      "Gene symbols are resolved to stable Ensembl identifiers.",
      "Protein cross-references are collected from biological records.",
      "Reviewed UniProt entries are preferred when the organism and evidence support the selection.",
      "Identifiers remain traceable throughout the analysis.",
      "This prevents downstream evidence from being attached to the wrong biological target."
    ]
  },
  {
    number: "03",
    title: "Protein Intelligence",
    short: "Sequence → representation",
    image: "/idea/ai-foundation.png",
    text: "Once a canonical protein sequence is available, CureVerseAI can represent it with a pretrained protein language model. The current protein intelligence layer uses ESM2 to transform the sequence into a learned numerical representation. Instead of treating a protein as plain text, the system creates a machine-readable biological feature space.",
    details: [
      "Canonical protein sequences are retrieved from the biological context.",
      "ESM2 produces a 320-dimensional protein representation in the current implementation.",
      "The representation can be consumed by downstream multimodal analysis.",
      "The model provides learned sequence features rather than manually designed rules.",
      "Model output is kept distinguishable from externally sourced evidence."
    ]
  },
  {
    number: "04",
    title: "Molecular Intelligence",
    short: "SMILES → representation",
    image: "/idea/drug-development.png",
    text: "For molecule-aware workflows, CureVerseAI accepts molecular structures represented as SMILES. ChemBERTa is used to transform a molecule into a learned embedding. This creates a second biological modality that can be compared and combined with protein-level information.",
    details: [
      "A molecular structure can enter the system as a SMILES string.",
      "ChemBERTa produces a 768-dimensional molecular representation in the current implementation.",
      "The molecular representation remains separate from assay observations.",
      "The system can therefore distinguish what a model represents from what an experiment measured.",
      "This becomes useful for target–compound analysis and drug-development workflows."
    ]
  },
  {
    number: "05",
    title: "Cellular Intelligence",
    short: "Cell state → representation",
    image: "/idea/cellular-intelligence.png",
    text: "Biological behavior is not determined by a protein or molecule alone. Cellular context can change how a biological system behaves. CureVerseAI therefore includes a cellular feature pathway so that future analyses can incorporate structured cellular-state information alongside molecular and protein representations.",
    details: [
      "Cellular state can be represented as a dedicated modality.",
      "The current architecture exposes a cellular feature adapter.",
      "Cell features remain explicitly identified as cellular information.",
      "The architecture is designed to accommodate stronger cellular foundation models.",
      "This creates a path toward richer multimodal biological reasoning."
    ]
  },
  {
    number: "06",
    title: "Multimodal Feature Fusion",
    short: "Protein + molecule + cell",
    image: "/idea/evidence-network.png",
    text: "The multimodal layer brings active biological modalities into a common feature space. Protein, molecule and cellular representations are normalized and aligned before being combined into a unified representation. The purpose is not to manufacture a biological conclusion, but to give the intelligence engine a common numerical representation from which it can reason.",
    details: [
      "Each active modality is normalized before fusion.",
      "Different dimensionalities are aligned into a common feature space.",
      "The current fusion layer produces a 256-dimensional integrated representation.",
      "Available modalities are recorded so the analysis remains interpretable.",
      "Missing modalities do not silently become fabricated data."
    ]
  },
  {
    number: "07",
    title: "External Evidence Retrieval",
    short: "Open Targets + ChEMBL",
    image: "/idea/evidence-network.png",
    text: "Model representations alone are not enough for scientific interpretation. CureVerseAI therefore retrieves external evidence from dedicated scientific resources. Open Targets contributes disease-association context, while ChEMBL contributes experimentally observed compound and bioactivity relationships.",
    details: [
      "Open Targets provides target–disease association evidence.",
      "ChEMBL provides compound–target activity observations.",
      "Activity measurements such as IC50, EC50, Ki and Kd are preserved at the assay level.",
      "Experimental observations are not automatically converted into clinical effectiveness claims.",
      "External sources remain identifiable in the final evidence bundle."
    ]
  },
  {
    number: "08",
    title: "Evidence Reasoning",
    short: "What does the evidence actually support?",
    image: "/idea/tp53-network.png",
    text: "CureVerseAI separates evidence according to what kind of support it represents. Direct biological information, disease associations, experimental bioactivity, model-derived observations and contextual information are kept distinct. This prevents a model prediction from being presented as though it were an experimental result.",
    details: [
      "Direct biological evidence is separated from downstream interpretation.",
      "Disease association evidence remains linked to its external source.",
      "Experimental bioactivity remains assay-level evidence.",
      "Model-derived findings are explicitly identified as model-derived.",
      "Limitations are retained instead of being hidden behind a single confidence number."
    ]
  },
  {
    number: "09",
    title: "Integrated Biological Analysis",
    short: "From evidence to understanding",
    image: "/idea/final-ecosystem.png",
    text: "The final intelligence layer combines resolved biological context, multimodal representations and external evidence into one structured analysis. The result is not simply a database search and not simply a model prediction. It is a connected analytical view in which biological identity, model-derived features and experimental evidence can be inspected together.",
    details: [
      "The analysis engine orchestrates the biological services.",
      "Resolved entities provide the scientific backbone.",
      "Model outputs provide learned representations.",
      "External databases provide independent evidence.",
      "Evidence reasoning produces an interpretable summary with provenance and limitations."
    ]
  }
];

const domains = [
  {
    number: "01",
    title: "Research",
    image: "/idea/dna-helix.png",
    intro: "Research begins with a biological question. CureVerseAI is designed to reduce the distance between that question and the biological context required to investigate it.",
    body: "Researchers can move from a gene or biological entity into connected information about proteins, pathways, variants, disease associations and experimental evidence. Instead of opening separate resources and manually rebuilding relationships, the platform provides a unified analytical workflow that keeps the underlying biological identity visible.",
    applications: [
      "Gene and protein exploration",
      "Pathway and biological-context analysis",
      "Variant and mutation investigation",
      "Evidence-backed biological hypothesis generation"
    ]
  },
  {
    number: "02",
    title: "Drug Development",
    image: "/idea/drug-development.png",
    intro: "Drug development requires connecting targets, molecules, experiments and disease context.",
    body: "CureVerseAI connects resolved biological targets with molecular representations and ChEMBL bioactivity observations, while Open Targets contributes disease-association context. The system preserves assay-level measurements so an IC50, EC50, Ki or Kd observation remains an experimental observation rather than being incorrectly transformed into a claim of therapeutic effectiveness.",
    applications: [
      "Target intelligence",
      "Compound–target evidence",
      "Bioactivity exploration",
      "Disease-associated target context"
    ]
  },
  {
    number: "03",
    title: "Medicine",
    image: "/idea/medicine.png",
    intro: "Medicine sits at the point where biological knowledge must become understandable and clinically meaningful.",
    body: "The CureVerseAI architecture provides a foundation for connecting molecular and biological information with structured medical understanding. The platform is designed to organize evidence and biological context rather than replacing professional medical judgment. Its role is to make complex biological relationships easier to inspect, explain and communicate.",
    applications: [
      "Biological context for medical questions",
      "Disease-oriented exploration",
      "Evidence organization",
      "Explainable biological learning"
    ]
  },
  {
    number: "04",
    title: "Biotechnology",
    image: "/idea/biotechnology.png",
    intro: "Biotechnology operates across genes, molecules, cells and engineered biological systems.",
    body: "CureVerseAI's multimodal architecture is designed for this cross-scale view. Biological entities can be connected with molecular structures, cellular representations and pathway context, creating an extensible foundation for biotechnology workflows involving biological engineering, target investigation and cellular systems.",
    applications: [
      "Gene and protein engineering context",
      "Molecular analysis",
      "Cellular-state exploration",
      "Biological system integration"
    ]
  },
  {
    number: "05",
    title: "Education",
    image: "/idea/education.png",
    intro: "Scientific knowledge becomes more powerful when complex concepts can be explored interactively.",
    body: "CureVerseAI extends its biological intelligence architecture toward education by turning biological relationships into structured explanations. Instead of presenting isolated definitions, an educational workflow can connect concepts across genes, proteins, molecules, cells, disease and evidence so that learners can understand how biological systems relate to one another.",
    applications: [
      "Concept-based biology exploration",
      "Interactive biological explanations",
      "Cross-scale learning",
      "Evidence-aware scientific education"
    ]
  }
];

const evidenceTypes = [
  {
    number: "01",
    title: "Direct biological",
    text: "Information directly describing biological entities, identifiers, sequences, pathways or relationships."
  },
  {
    number: "02",
    title: "Disease association",
    text: "Externally sourced evidence connecting biological targets with diseases and phenotypes."
  },
  {
    number: "03",
    title: "Experimental",
    text: "Observed bioactivity and assay measurements retrieved from experimental scientific resources."
  },
  {
    number: "04",
    title: "Model-derived",
    text: "Features and findings generated by pretrained or computational intelligence layers."
  },
  {
    number: "05",
    title: "Contextual",
    text: "Supporting information that helps interpret an analysis without being treated as direct proof."
  }
];

const differentiators = [
  {
    title: "One biological identity across sources",
    text: "The system resolves and carries biological identity through the workflow instead of treating every external record as an isolated result."
  },
  {
    title: "Models connected to evidence",
    text: "Pretrained representations are placed beside external biological and experimental evidence rather than presented as a replacement for it."
  },
  {
    title: "Multimodal by architecture",
    text: "Protein, molecule and cellular modalities can contribute to one integrated representation while remaining individually traceable."
  },
  {
    title: "Evidence is not flattened",
    text: "The platform preserves the distinction between experimental observations, disease associations, direct biology and model-derived information."
  },
  {
    title: "Five domains, one intelligence layer",
    text: "Research, drug development, medicine, biotechnology and education share the same connected biological foundation."
  }
];

export default function IdeaPage() {
  const [activeLayer, setActiveLayer] = useState(0);
  const [activeDomain, setActiveDomain] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const max =
        document.documentElement.scrollHeight - window.innerHeight;

      setScrollProgress(max > 0 ? window.scrollY / max : 0);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const layer = systemLayers[activeLayer];
  const domain = domains[activeDomain];

  return (
    <main className="cv-idea-page">
      <div
        className="cv-idea-progress"
        style={{ transform: `scaleX(${scrollProgress})` }}
      />

      <Navbar />

      {/* =====================================================
          01 — EXECUTIVE OVERVIEW
      ====================================================== */}
      <section className="cv-idea-book-section cv-idea-overview">
        <div className="cv-idea-book-label">
          <span>01</span>
          EXECUTIVE OVERVIEW
        </div>

        <div className="cv-idea-book-grid">
          <div>
            <h1>
              Biological intelligence
              <em>needs connection.</em>
            </h1>

            <p className="cv-idea-lead">
              CureVerseAI is an AI-powered biological intelligence platform
              designed to connect real biological data, foundation models and
              scientific evidence into one connected analytical system.
            </p>
          </div>

          <div className="cv-idea-overview-visual cv-idea-image-frame">
            <img
              src="/idea/hero-cell.png"
              alt="Biological intelligence visualization"
              className="cv-idea-main-image"
            />
            <span className="cv-idea-image-orbit orbit-a" />
            <span className="cv-idea-image-orbit orbit-b" />
          </div>
        </div>

        <div className="cv-idea-overview-text">
          <p>
            <strong>The problem is fragmentation.</strong> Biological
            information exists across databases, models, scientific papers,
            experimental resources and specialized workflows.
          </p>

          <p>
            <strong>The opportunity is connection.</strong> CureVerseAI brings
            those layers into one architecture where biological identity,
            learned representations and evidence can travel together.
          </p>

          <p>
            <strong>The goal is understanding.</strong> The platform is built
            to help users move from a biological question toward a structured,
            evidence-aware analytical view.
          </p>
        </div>
      </section>

      {/* =====================================================
          02 — THE PROBLEM
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>02</span>
              THE PROBLEM
            </div>
            <h2>
              Biology is rich.
              <br />
              The workflow is <em>fragmented.</em>
            </h2>
          </div>

          <p>
            A biological question rarely belongs to one database or one
            model. A researcher may need gene identity from one resource,
            protein information from another, pathways from another and
            experimental evidence from yet another system.
          </p>
        </div>

        <div className="cv-idea-problem-map">
          <div className="cv-idea-problem-source">
            <span>SCIENTIFIC INPUTS</span>
            <strong>Genes</strong>
            <strong>Proteins</strong>
            <strong>Pathways</strong>
            <strong>Diseases</strong>
            <strong>Compounds</strong>
            <strong>Experiments</strong>
          </div>

          <div className="cv-idea-problem-chaos">
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <strong>
              DIFFERENT SOURCES
              <br />
              DIFFERENT IDENTITIES
              <br />
              DIFFERENT EVIDENCE
            </strong>
          </div>

          <div className="cv-idea-problem-result">
            <small>WITHOUT CONNECTION</small>
            <strong>?</strong>
            <span>MANUAL SYNTHESIS</span>
          </div>
        </div>

        <div className="cv-idea-two-column-text">
          <div>
            <h3>Information is not intelligence</h3>
            <p>
              Searching for a gene and receiving thousands of records does not
              automatically answer a biological question. The difficult part is
              understanding how those records relate to one another, which
              evidence is experimental, which information is model-derived,
              and what conclusions the available evidence can actually support.
            </p>
          </div>

          <div>
            <h3>Models are not the whole answer</h3>
            <p>
              A foundation model can create a powerful representation of a
              protein or molecule, but scientific reasoning also requires
              external biological context and experimental evidence. CureVerseAI
              is designed around that combination rather than treating model
              output as the final truth.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          03 — HOW THE SYSTEM WORKS
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>03</span>
              HOW THE SYSTEM WORKS
            </div>

            <h2>
              From biological question
              <br />
              to <em>connected intelligence.</em>
            </h2>
          </div>

          <p>
            CureVerseAI is organized as a layered intelligence pipeline. Each
            layer has a specific responsibility, and the output of one layer
            becomes structured input for the next.
          </p>
        </div>

        <div className="cv-idea-system-layout">
          <div className="cv-idea-system-nav">
            {systemLayers.map((item, index) => (
              <button
                key={item.number}
                className={index === activeLayer ? "active" : ""}
                onClick={() => setActiveLayer(index)}
              >
                <span>{item.number}</span>
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.short}</small>
                </div>
              </button>
            ))}
          </div>

          <div className="cv-idea-system-reading">
            <div className="cv-idea-system-image cv-idea-image-frame">
              <img
                src={layer.image}
                alt={layer.title}
                className="cv-idea-section-image"
              />
              <div className="cv-idea-image-scan" />
            </div>

            <div className="cv-idea-system-copy">
              <span>{layer.number} / SYSTEM LAYER</span>

              <h3>{layer.title}</h3>

              <p className="cv-idea-system-main">
                {layer.text}
              </p>

              <div className="cv-idea-detail-list">
                {layer.details.map((detail) => (
                  <div key={detail}>
                    <i />
                    <p>{detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="cv-idea-pipeline-summary">
          <span>THE COMPLETE FLOW</span>

          <div>
            <strong>QUESTION</strong>
            <b>→</b>
            <strong>IDENTITY</strong>
            <b>→</b>
            <strong>CONTEXT</strong>
            <b>→</b>
            <strong>MODELS</strong>
            <b>→</b>
            <strong>EVIDENCE</strong>
            <b>→</b>
            <strong>REASONING</strong>
            <b>→</b>
            <strong>INSIGHT</strong>
          </div>
        </div>
      </section>

      {/* =====================================================
          04 — MULTIMODAL INTELLIGENCE
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>04</span>
              MULTIMODAL INTELLIGENCE
            </div>

            <h2>
              Biology exists at
              <br />
              <em>multiple scales.</em>
            </h2>
          </div>

          <p>
            A protein sequence, a molecule and a cellular state describe
            different aspects of biology. CureVerseAI treats them as separate
            modalities that can contribute to a shared representation.
          </p>
        </div>

        <div className="cv-idea-modalities">
          <article className="cv-idea-image-card">
            <div className="modality-visual">
              <img
                src="/idea/dna-helix.png"
                alt="Protein and genomic visualization"
              />
            </div>
            <span>MODALITY 01</span>
            <h3>Protein / Sequence</h3>
            <p>
              Biological sequences are represented through a pretrained protein
              language model, allowing sequence-level information to enter the
              integrated feature space.
            </p>
          </article>

          <article className="cv-idea-image-card">
            <div className="modality-visual">
              <img
                src="/idea/ai-foundation.png"
                alt="AI biological intelligence visualization"
              />
            </div>
            <span>MODALITY 02</span>
            <h3>Molecule / Structure</h3>
            <p>
              Molecular structures represented as SMILES can be transformed
              into learned molecular features through the ChemBERTa model.
            </p>
          </article>

          <article className="cv-idea-image-card">
            <div className="modality-visual">
              <img
                src="/idea/cellular-intelligence.png"
                alt="Cellular intelligence visualization"
              />
            </div>
            <span>MODALITY 03</span>
            <h3>Cell / State</h3>
            <p>
              Cellular information provides a system-level context that can be
              incorporated alongside protein and molecular representations.
            </p>
          </article>
        </div>

        <div className="cv-idea-fusion">
          <span>FEATURE FUSION</span>
          <div>
            <strong>PROTEIN</strong>
            <b>+</b>
            <strong>MOLECULE</strong>
            <b>+</b>
            <strong>CELL</strong>
            <b>→</b>
            <strong>INTEGRATED BIOLOGICAL REPRESENTATION</strong>
          </div>
          <p>
            The current fusion layer normalizes active modalities, aligns them
            into a common space and produces a 256-dimensional integrated
            representation. This representation is a computational feature
            space — it is not itself a clinical conclusion.
          </p>
        </div>
      </section>

      {/* =====================================================
          05 — TP53 CASE STUDY
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>05</span>
              REAL SYSTEM EXAMPLE
            </div>

            <h2>
              TP53 through
              <br />
              the <em>CureVerseAI pipeline.</em>
            </h2>
          </div>

          <p>
            TP53 demonstrates how the platform can move from a simple gene
            symbol into a connected biological analysis involving identity,
            protein information, disease associations, compounds and
            experimental bioactivity.
          </p>
        </div>

        <div className="cv-idea-tp53-feature">
          <div className="cv-idea-tp53-image cv-idea-image-frame">
            <img
              src="/idea/tp53-network.png"
              alt="TP53 connected biological network"
            />
            <div className="cv-idea-image-vignette" />
          </div>

          <div className="cv-idea-tp53-copy">
            <span>CASE STUDY / TP53</span>

            <h3>One question becomes a connected evidence graph.</h3>

            <p>
              The system resolves TP53 to its Ensembl identity
              <strong> ENSG00000141510</strong>, retrieves its canonical
              protein context, resolves the reviewed UniProt entry
              <strong> P04637</strong>, and connects the biological target with
              external drug-development evidence.
            </p>

            <p>
              In the integrated analysis, the target resolves to the ChEMBL
              target <strong>CHEMBL4096</strong>. The evidence layer can then
              retrieve experimental relationships while Open Targets supplies
              disease-association context.
            </p>

            <p>
              The important point is not simply the number of records returned.
              The system keeps track of <strong>where each finding came from</strong>
              and what type of evidence it represents.
            </p>
          </div>
        </div>

        <div className="cv-idea-data-strip">
          <div>
            <span>ENSEMBL</span>
            <strong>ENSG00000141510</strong>
          </div>

          <div>
            <span>UNIPROT</span>
            <strong>P04637</strong>
          </div>

          <div>
            <span>CHEMBL TARGET</span>
            <strong>CHEMBL4096</strong>
          </div>

          <div>
            <span>PROTEIN</span>
            <strong>393 aa</strong>
          </div>
        </div>

        <div className="cv-idea-reading-note">
          <span>WHY THIS MATTERS</span>
          <p>
            A single biological question can therefore travel through
            identifier resolution, protein representation, disease evidence,
            compound relationships and evidence reasoning without losing the
            identity of the underlying target.
          </p>
        </div>
      </section>

      {/* =====================================================
          06 — EVIDENCE
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>06</span>
              EVIDENCE & TRUST
            </div>

            <h2>
              Not every signal
              <br />
              means the <em>same thing.</em>
            </h2>
          </div>

          <p>
            Scientific intelligence becomes more trustworthy when different
            evidence types remain distinguishable. CureVerseAI therefore
            classifies evidence instead of collapsing everything into one
            unexplained score.
          </p>
        </div>

        <div className="cv-idea-evidence-visual cv-idea-image-frame">
          <img
            src="/idea/evidence-network.png"
            alt="Connected scientific evidence network"
          />
        </div>

        <div className="cv-idea-evidence-grid">
          {evidenceTypes.map((item) => (
            <article key={item.number}>
              <span>{item.number}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>

        <div className="cv-idea-trust-note">
          <strong>
            Evidence reasoning is a core part of the intelligence layer —
            not an afterthought.
          </strong>

          <p>
            For example, a ChEMBL IC50 observation can tell us that a compound
            was measured in a particular assay context. It should not
            automatically be rewritten as “this drug works.” CureVerseAI keeps
            the observation connected to its source and evidence type, allowing
            the final analysis to communicate both what is known and what
            remains uncertain.
          </p>
        </div>
      </section>

      {/* =====================================================
          07 — FIVE DOMAINS
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>07</span>
              FIVE DOMAINS
            </div>

            <h2>
              One intelligence layer.
              <br />
              <em>Five biological worlds.</em>
            </h2>
          </div>

          <p>
            CureVerseAI is not designed around one narrow biological workflow.
            The same connected intelligence foundation can support research,
            drug development, medicine, biotechnology and education.
          </p>
        </div>

        <div className="cv-idea-domain-book">
          <div className="cv-idea-domain-nav">
            {domains.map((item, index) => (
              <button
                key={item.number}
                className={index === activeDomain ? "active" : ""}
                onClick={() => setActiveDomain(index)}
              >
                <span>{item.number}</span>
                <strong>{item.title}</strong>
              </button>
            ))}
          </div>

          <div className="cv-idea-domain-reading">
            <div className="cv-idea-domain-image cv-idea-image-frame">
              <img
                src={domain.image}
                alt={domain.title}
              />
            </div>

            <div className="cv-idea-domain-copy">
              <span>{domain.number} / DOMAIN</span>

              <h3>{domain.title}</h3>

              <p className="domain-intro">{domain.intro}</p>

              <p>{domain.body}</p>

              <div className="cv-idea-application-list">
                {domain.applications.map((application) => (
                  <div key={application}>
                    <i />
                    <span>{application}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          08 — BIOTECH / CELLULAR
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>08</span>
              BIOLOGICAL SCALE
            </div>

            <h2>
              From molecules
              <br />
              to <em>living systems.</em>
            </h2>
          </div>

          <p>
            Biological understanding changes as the scale changes. The
            platform's architecture is intentionally extensible so that
            molecular and sequence-level intelligence can eventually connect
            with richer cellular and system-level representations.
          </p>
        </div>

        <div className="cv-idea-scale-feature">
          <div className="cv-idea-scale-image cv-idea-image-frame">
            <img
              src="/idea/biotechnology.png"
              alt="Biotechnology and molecular engineering visualization"
            />
          </div>

          <div className="cv-idea-scale-copy">
            <span>CONNECTED BIOLOGY</span>

            <h3>
              A gene is not isolated from the system around it.
            </h3>

            <p>
              Genes participate in proteins. Proteins participate in pathways.
              Molecules interact with biological targets. Cellular states
              influence behavior. Diseases emerge from complex biological
              systems. A useful intelligence platform therefore needs an
              architecture that can move across these levels rather than
              stopping at one representation.
            </p>

            <p>
              CureVerseAI's multimodal design provides that foundation by
              allowing different biological representations to coexist inside
              one analytical workflow.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          09 — MEDICINE + EDUCATION
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>09</span>
              HUMAN UNDERSTANDING
            </div>

            <h2>
              Intelligence should
              <br />
              <em>explain biology.</em>
            </h2>
          </div>

          <p>
            The same biological infrastructure can support both professional
            exploration and learning. The difference is not the underlying
            biology; it is how that biology is presented to the user.
          </p>
        </div>

        <div className="cv-idea-human-grid">
          <article className="cv-idea-human-card">
            <div className="cv-idea-human-image cv-idea-image-frame">
              <img src="/idea/medicine.png" alt="Medical biology visualization" />
            </div>

            <div>
              <span>MEDICINE</span>
              <h3>Turn biological complexity into structured context.</h3>
              <p>
                Medical workflows can benefit from organized biological
                information that connects disease context, molecular
                relationships and evidence without pretending that an AI
                analysis replaces professional clinical judgment.
              </p>
            </div>
          </article>

          <article className="cv-idea-human-card">
            <div className="cv-idea-human-image cv-idea-image-frame">
              <img src="/idea/education.png" alt="Biology education visualization" />
            </div>

            <div>
              <span>EDUCATION</span>
              <h3>Turn isolated facts into connected understanding.</h3>
              <p>
                Students can learn biology through relationships: how genes
                connect to proteins, how proteins participate in pathways, how
                molecules interact with targets, and how evidence supports
                scientific conclusions.
              </p>
            </div>
          </article>
        </div>
      </section>

      {/* =====================================================
          10 — WHY DIFFERENT
      ====================================================== */}
      <section className="cv-idea-book-section">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>10</span>
              WHY CUREVERSEAI
            </div>

            <h2>
              More than a model.
              <br />
              More than a <em>database.</em>
            </h2>
          </div>

          <p>
            CureVerseAI's distinction is architectural. It connects scientific
            data, pretrained representations and evidence reasoning into one
            workflow instead of making the user choose between disconnected
            tools.
          </p>
        </div>

        <div className="cv-idea-difference-book">
          {differentiators.map((item, index) => (
            <article key={item.title}>
              <span>0{index + 1}</span>

              <div>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </div>
            </article>
          ))}
        </div>

        <div className="cv-idea-comparison">
          <div>
            <span>TRADITIONAL FRAGMENTATION</span>
            <p>
              Search database → copy identifier → open another resource →
              search again → inspect model → manually compare evidence →
              construct conclusion.
            </p>
          </div>

          <strong>VS</strong>

          <div>
            <span>CUREVERSEAI</span>
            <p>
              Biological question → resolve identity → gather context →
              generate multimodal features → retrieve evidence → reason over
              evidence → produce connected analysis.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          11 — FINAL ECOSYSTEM
      ====================================================== */}
      <section className="cv-idea-book-section cv-idea-final-ecosystem">
        <div className="cv-idea-heading-row">
          <div>
            <div className="cv-idea-book-label">
              <span>11</span>
              THE BIGGER VISION
            </div>

            <h2>
              A connected
              <br />
              <em>biological intelligence layer.</em>
            </h2>
          </div>

          <p>
            CureVerseAI is designed as an extensible foundation. New biological
            sources, stronger foundation models, richer cellular representations
            and additional reasoning capabilities can be connected without
            abandoning the underlying architecture.
          </p>
        </div>

        <div className="cv-idea-final-image cv-idea-image-frame">
          <img
            src="/idea/final-ecosystem.png"
            alt="Connected biological intelligence ecosystem"
          />

          <div className="cv-idea-final-image-caption">
            <span>DATA</span>
            <i />
            <span>MODELS</span>
            <i />
            <span>EVIDENCE</span>
            <i />
            <span>REASONING</span>
            <i />
            <span>UNDERSTANDING</span>
          </div>
        </div>

        <div className="cv-idea-final-text">
          <p>
            The long-term vision is not to create another isolated AI tool.
            It is to create an intelligence layer where biological information
            can move across scales, models can contribute learned
            representations, scientific evidence remains traceable, and users
            can understand how an analysis was constructed.
          </p>

          <p>
            That is the core idea behind CureVerseAI:
            <strong> connect biology before trying to predict it.</strong>
          </p>
        </div>
      </section>

      {/* =====================================================
          FINAL
      ====================================================== */}
      <section className="cv-idea-final-book">
        <span>THE CUREVERSEAI VISION</span>

        <h2>
          Biology,
          <br />
          <em>connected.</em>
        </h2>

        <p>
          From research to drug development, medicine, biotechnology and
          education — one connected intelligence architecture for understanding
          the biological world.
        </p>

        <a href="/">
          RETURN TO PLATFORM
          <strong>↗</strong>
        </a>
      </section>
      <Footer />
    </main>
  );
}
