"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import "./manual.css";

const tools = [
  {
    number: "01",
    label: "GENE EXPLORER",
    title: "Start with the gene.",
    text: "Resolve biological identity, transcripts, identifiers and connected evidence before moving deeper into the system.",
    href: "/domains/research/gene-explorer",
    image: "/research/research-character-left.png",
  },
  {
    number: "02",
    label: "PROTEIN EXPLORER",
    title: "Move into the protein.",
    text: "Follow canonical protein identity and sequence into a machine-readable representation with ESM-2.",
    href: "/domains/research/protein-explorer",
    image: "/research/research-character-center.png",
  },
  {
    number: "03",
    label: "VARIANT INVESTIGATOR",
    title: "Investigate variation.",
    text: "Explore variant records, connected biological entities and the evidence surrounding a genetic change.",
    href: "/domains/research/variant-investigator",
    image: "/research/research-character-right.png",
  },
  {
    number: "04",
    label: "PATHWAY EXPLORER",
    title: "Trace the biology.",
    text: "Search biological processes and pathways through connected Reactome records, reactions and molecular entities.",
    href: "/domains/research/pathway-explorer",
    image: "/research/research-guide.png",
  },
  {
    number: "05",
    label: "EVIDENCE RESEARCH",
    title: "Read the evidence.",
    text: "Bring direct biological, disease, experimental, model-derived and contextual evidence into one reasoning layer.",
    href: "/domains/research/evidence-research",
    image: "/research/research-character-center.png",
  },
];

const sources = [
  {
    code: "ENS",
    name: "Ensembl",
    role: "Genes · transcripts · identifiers",
  },
  {
    code: "UNI",
    name: "UniProt",
    role: "Proteins · canonical sequences",
  },
  {
    code: "RHE",
    name: "Reactome",
    role: "Pathways · reactions · complexes",
  },
  {
    code: "OT",
    name: "Open Targets",
    role: "Targets · disease associations",
  },
  {
    code: "CHE",
    name: "ChEMBL",
    role: "Experimental bioactivity",
  },
  {
    code: "ESM",
    name: "ESM-2",
    role: "Protein representation",
  },
];

const principles = [
  ["01", "Evidence ≠ Prediction", "Observed evidence and computational outputs must never be treated as the same thing."],
  ["02", "Association ≠ Causation", "A biological association does not automatically establish a causal mechanism."],
  ["03", "Model ≠ Experiment", "An embedding or model representation is useful computational information, not experimental proof."],
  ["04", "Missing ≠ Negative", "The absence of a retrieved record does not prove that a biological relationship does not exist."],
];

export default function ResearchManualPage() {
  const [activeTool, setActiveTool] = useState(0);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 120);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <main className={`cv-manual-page ${scrolled ? "is-scrolled" : ""}`}>
      <section className="cv-manual-hero">
        <div className="cv-manual-hero-grid" />

        <div className="cv-manual-particles">
          {Array.from({ length: 18 }).map((_, i) => (
            <span key={i} style={{ "--i": i } as React.CSSProperties} />
          ))}
        </div>

        <div className="cv-manual-orbit orbit-one" />
        <div className="cv-manual-orbit orbit-two" />
        <div className="cv-manual-orbit orbit-three" />

        <div className="cv-manual-hero-copy">
          <div className="cv-eyebrow">00 / RESEARCH INTELLIGENCE HANDBOOK</div>

          <h1>
            Understand biology
            <span>before you investigate it.</span>
          </h1>

          <p>
            CureVerseAI Research connects genes, proteins, variants,
            pathways and evidence into a continuous biological investigation
            workflow.
          </p>

          <div className="cv-manual-hero-actions">
            <Link href="/domains/research/gene-explorer">
              START AN INVESTIGATION <span>↗</span>
            </Link>
            <a href="#workflow">EXPLORE THE SYSTEM <span>↓</span></a>
          </div>
        </div>

        <div className="cv-manual-hero-visual">
          <div className="cv-visual-ring ring-a" />
          <div className="cv-visual-ring ring-b" />
          <div className="cv-visual-core">
            <div className="cv-core-label">BIOLOGICAL</div>
            <strong>INTELLIGENCE</strong>
            <small>RESEARCH ENGINE</small>
          </div>

          <div className="cv-node node-gene">GENE</div>
          <div className="cv-node node-protein">PROTEIN</div>
          <div className="cv-node node-pathway">PATHWAY</div>
          <div className="cv-node node-evidence">EVIDENCE</div>
        </div>
      </section>

      <section className="cv-manual-intro cv-reveal">
        <div className="cv-section-number">01</div>

        <div className="cv-intro-layout">
          <div>
            <div className="cv-eyebrow">THE RESEARCH MINDSET</div>
            <h2>
              Biology is not
              <span>a single record.</span>
            </h2>
          </div>

          <div className="cv-intro-copy">
            <p>
              A gene can lead to a protein. A protein can participate in
              pathways. A variant can alter a biological context. Evidence
              can come from several independent sources.
            </p>

            <p>
              CureVerseAI brings these layers together so an investigation
              can move from identity to biological context and evidence
              without losing the distinction between what is observed and
              what is computationally derived.
            </p>
          </div>
        </div>

        <div className="cv-chain">
          {["GENE", "PROTEIN", "VARIANT", "PATHWAY", "EVIDENCE"].map(
            (item, index) => (
              <div className="cv-chain-item" key={item}>
                <span>0{index + 1}</span>
                <strong>{item}</strong>
                {index < 4 && <i>→</i>}
              </div>
            )
          )}
        </div>
      </section>

      <section id="workflow" className="cv-manual-workflow cv-reveal">
        <div className="cv-section-number">02</div>

        <div className="cv-section-heading">
          <div className="cv-eyebrow">HOW THE SYSTEM WORKS</div>
          <h2>
            From question
            <span>to evidence.</span>
          </h2>
          <p>
            Every investigation follows a connected biological reasoning
            path rather than treating each data source as an isolated result.
          </p>
        </div>

        <div className="cv-workflow">
          {[
            ["01", "USER QUESTION", "Define the biological entity or process you want to investigate."],
            ["02", "SOURCE RESOLUTION", "Resolve identity across authoritative biological resources."],
            ["03", "MULTI-SOURCE EVIDENCE", "Connect pathway, disease and experimental observations."],
            ["04", "AI REPRESENTATION", "Generate computational representations from biological inputs."],
            ["05", "EVIDENCE REASONING", "Separate direct, experimental, disease, model and contextual evidence."],
            ["06", "INTERPRETABLE RESULT", "Present the connected investigation in a form a researcher can inspect."],
          ].map(([number, title, text]) => (
            <div className="cv-workflow-card" key={number}>
              <span>{number}</span>
              <div className="cv-workflow-line" />
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cv-manual-tools cv-reveal">
        <div className="cv-section-number">03</div>

        <div className="cv-section-heading">
          <div className="cv-eyebrow">RESEARCH WORKBENCH</div>
          <h2>
            Five ways
            <span>into biology.</span>
          </h2>
        </div>

        <div className="cv-tool-stage">
          <div className="cv-tool-list">
            {tools.map((tool, index) => (
              <button
                className={`cv-tool-tab ${activeTool === index ? "active" : ""}`}
                key={tool.number}
                onMouseEnter={() => setActiveTool(index)}
                onClick={() => setActiveTool(index)}
              >
                <span>{tool.number}</span>
                <strong>{tool.label}</strong>
                <i>↗</i>
              </button>
            ))}
          </div>

          <div className="cv-tool-feature">
            <div className="cv-tool-image">
              <Image
                src={tools[activeTool].image}
                alt={tools[activeTool].label}
                fill
                sizes="(max-width: 900px) 100vw, 45vw"
              />
              <div className="cv-tool-image-overlay" />
            </div>

            <div className="cv-tool-feature-copy">
              <div className="cv-eyebrow">{tools[activeTool].label}</div>
              <h3>{tools[activeTool].title}</h3>
              <p>{tools[activeTool].text}</p>

              <Link href={tools[activeTool].href}>
                OPEN WORKBENCH <span>→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="cv-manual-sources cv-reveal">
        <div className="cv-section-number">04</div>

        <div className="cv-source-heading">
          <div>
            <div className="cv-eyebrow">CONNECTED KNOWLEDGE</div>
            <h2>
              Built across
              <span>biological sources.</span>
            </h2>
          </div>

          <p>
            CureVerseAI does not depend on a single biological database.
            Different sources contribute different layers of evidence.
          </p>
        </div>

        <div className="cv-source-grid">
          {sources.map((source) => (
            <div className="cv-source-card" key={source.code}>
              <div className="cv-source-code">{source.code}</div>
              <div>
                <h3>{source.name}</h3>
                <p>{source.role}</p>
              </div>
              <span>↗</span>
            </div>
          ))}
        </div>
      </section>

      <section className="cv-manual-evidence cv-reveal">
        <div className="cv-section-number">05</div>

        <div className="cv-evidence-layout">
          <div className="cv-evidence-copy">
            <div className="cv-eyebrow">EVIDENCE REASONING</div>
            <h2>
              Not all
              <span>evidence is equal.</span>
            </h2>

            <p>
              CureVerseAI keeps different evidence classes visible instead
              of collapsing them into a single unexplained score.
            </p>

            <div className="cv-evidence-stack">
              {[
                ["01", "DIRECT BIOLOGY"],
                ["02", "DISEASE ASSOCIATION"],
                ["03", "EXPERIMENTAL"],
                ["04", "MODEL-DERIVED"],
                ["05", "CONTEXTUAL"],
              ].map(([number, label]) => (
                <div key={number}>
                  <span>{number}</span>
                  <strong>{label}</strong>
                  <i>+</i>
                </div>
              ))}
            </div>
          </div>

          <div className="cv-evidence-visual">
            <div className="cv-evidence-orbit orbit-one" />
            <div className="cv-evidence-orbit orbit-two" />
            <div className="cv-evidence-orbit orbit-three" />
            <div className="cv-evidence-center">
              <small>EVIDENCE</small>
              <strong>REASONING</strong>
            </div>

            <div className="cv-evidence-pulse pulse-one">BIOLOGY</div>
            <div className="cv-evidence-pulse pulse-two">DISEASE</div>
            <div className="cv-evidence-pulse pulse-three">EXPERIMENT</div>
            <div className="cv-evidence-pulse pulse-four">MODEL</div>
          </div>
        </div>
      </section>

      <section className="cv-manual-principles cv-reveal">
        <div className="cv-section-number">06</div>

        <div className="cv-section-heading">
          <div className="cv-eyebrow">SCIENTIFIC PRINCIPLES</div>
          <h2>
            Interpret the result.
            <span>Do not overclaim it.</span>
          </h2>
        </div>

        <div className="cv-principle-grid">
          {principles.map(([number, title, text]) => (
            <article key={number} className="cv-principle-card">
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cv-manual-example cv-reveal">
        <div className="cv-section-number">07</div>

        <div className="cv-example-layout">
          <div>
            <div className="cv-eyebrow">EXAMPLE INVESTIGATION</div>
            <h2>
              Follow
              <span>TP53.</span>
            </h2>
            <p>
              A single biological target can travel through multiple
              connected evidence layers.
            </p>
          </div>

          <div className="cv-example-pipeline">
            {[
              ["TP53", "GENE"],
              ["ENSG00000141510", "ENSEMBL"],
              ["P04637", "UNIPROT"],
              ["393 AA", "PROTEIN"],
              ["REACTOME", "PATHWAYS"],
              ["OPEN TARGETS", "DISEASE"],
              ["CHEMBL", "BIOACTIVITY"],
              ["ESM-2", "REPRESENTATION"],
            ].map(([value, label], index) => (
              <div className="cv-example-node" key={value}>
                <span>0{index + 1}</span>
                <strong>{value}</strong>
                <small>{label}</small>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="cv-manual-final">
        <div className="cv-final-glow" />

        <div className="cv-section-number">08</div>

        <div className="cv-final-copy">
          <div className="cv-eyebrow">BEGIN YOUR INVESTIGATION</div>
          <h2>
            Biology is
            <span>connected.</span>
          </h2>
          <p>
            Start with one question. Follow the evidence. Explore the system.
          </p>

          <div className="cv-final-actions">
            <Link href="/domains/research/gene-explorer">
              GENE EXPLORER ↗
            </Link>
            <Link href="/domains/research/protein-explorer">
              PROTEIN EXPLORER ↗
            </Link>
            <Link href="/domains/research/variant-investigator">
              VARIANT INVESTIGATOR ↗
            </Link>
            <Link href="/domains/research/pathway-explorer">
              PATHWAY EXPLORER ↗
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
