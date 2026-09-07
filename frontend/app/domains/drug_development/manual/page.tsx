"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./manual.css";

const workflows = [
  {
    number: "01",
    label: "TARGET DISCOVERY",
    title: "Identify the biological opportunity.",
    text: "Explore targets through biological function, disease relationships, pathways and supporting evidence.",
    href: "/domains/drug_development/target-discovery",
    image: "/research/research-character-left.png",
  },
  {
    number: "02",
    label: "COMPOUND INTELLIGENCE",
    title: "Understand the molecule.",
    text: "Investigate molecular identity, activity measurements and the biological context surrounding compounds.",
    href: "/domains/drug_development/compound-intelligence",
    image: "/research/research-character-center.png",
  },
  {
    number: "03",
    label: "TARGET × DRUG",
    title: "Connect biology with chemistry.",
    text: "Follow relationships between biological targets and compounds across the development landscape.",
    href: "/domains/drug_development/target-drug-analysis",
    image: "/research/research-character-right.png",
  },
  {
    number: "04",
    label: "DEVELOPMENT EVIDENCE",
    title: "Bring the evidence together.",
    text: "Read biological, disease and experimental signals as connected layers of development intelligence.",
    href: "/domains/drug_development/evidence",
    image: "/research/research-guide.png",
  },
];

const stages = [
  ["01", "TARGET", "Identify a biological target with development potential."],
  ["02", "MECHANISM", "Understand how the target participates in biology."],
  ["03", "COMPOUND", "Explore molecules connected to the target."],
  ["04", "ACTIVITY", "Interpret experimental activity measurements."],
  ["05", "DISEASE", "Connect the target to therapeutic disease context."],
  ["06", "EVIDENCE", "Bring the independent evidence layers together."],
];

const evidence = [
  ["BIOLOGICAL", "Target function, pathways and molecular context."],
  ["DISEASE", "Target–disease relationships and associations."],
  ["EXPERIMENTAL", "Observed molecular activity and assay records."],
  ["CHEMICAL", "Compound identity and target relationships."],
  ["COMPUTATIONAL", "Model-derived biological representations."],
];

const principles = [
  [
    "01",
    "Activity is evidence.",
    "Measurements such as IC50, EC50, Ki and Kd are experimental observations that require assay context.",
  ],
  [
    "02",
    "Association is not efficacy.",
    "A target–compound relationship does not by itself establish therapeutic effectiveness.",
  ],
  [
    "03",
    "Context changes interpretation.",
    "Target, disease, assay and biological context should remain visible when evaluating development signals.",
  ],
  [
    "04",
    "Evidence should remain traceable.",
    "Development intelligence is stronger when individual evidence layers and their sources remain inspectable.",
  ],
];

export default function DrugDevelopmentManualPage() {
  const [activeWorkflow, setActiveWorkflow] = useState(0);

  return (
    <main className="cv-dd-manual">
      <Navbar />

      <section className="cv-dd-manual-hero">
        <div className="cv-dd-grid" />
        <div className="cv-dd-hero-glow" />

        <div className="cv-dd-particles">
          {Array.from({ length: 20 }).map((_, i) => (
            <span
              key={i}
              style={{ "--i": i } as React.CSSProperties}
            />
          ))}
        </div>

        <div className="cv-dd-hero-copy">
          <div className="cv-eyebrow">00 / DRUG DEVELOPMENT HANDBOOK</div>

          <h1>
            Follow the science
            <span>from target to therapy.</span>
          </h1>

          <p>
            Drug development is a connected biological investigation.
            Understand the target, trace the mechanism, evaluate the
            molecule and read the evidence before moving forward.
          </p>

          <div className="cv-dd-hero-actions">
            <Link href="/domains/drug_development/target-discovery">
              START TARGET DISCOVERY <span>↗</span>
            </Link>

            <a href="#journey">
              EXPLORE THE JOURNEY <span>↓</span>
            </a>
          </div>
        </div>

        <div className="cv-dd-hero-visual">
          <div className="cv-dd-orbit orbit-a" />
          <div className="cv-dd-orbit orbit-b" />
          <div className="cv-dd-orbit orbit-c" />

          <div className="cv-dd-core">
            <small>DEVELOPMENT</small>
            <strong>INTELLIGENCE</strong>
            <span>TARGET × COMPOUND × EVIDENCE</span>
          </div>

          <div className="cv-dd-node node-target">TARGET</div>
          <div className="cv-dd-node node-compound">COMPOUND</div>
          <div className="cv-dd-node node-activity">ACTIVITY</div>
          <div className="cv-dd-node node-evidence">EVIDENCE</div>
        </div>
      </section>

      <section className="cv-dd-intro">
        <div className="cv-section-number">01</div>

        <div className="cv-dd-intro-grid">
          <div>
            <div className="cv-eyebrow">THE DEVELOPMENT MINDSET</div>

            <h2>
              A drug candidate
              <span>starts with biology.</span>
            </h2>
          </div>

          <div>
            <p>
              Drug development connects biological targets with molecules,
              experimental measurements, disease context and evidence.
            </p>

            <p>
              CureVerseAI organizes these relationships into a connected
              investigation workflow so development questions can be
              explored from multiple scientific perspectives.
            </p>
          </div>
        </div>

        <div className="cv-dd-chain">
          {[
            "TARGET",
            "MECHANISM",
            "COMPOUND",
            "ACTIVITY",
            "DISEASE",
            "EVIDENCE",
          ].map((item, index) => (
            <div key={item}>
              <span>0{index + 1}</span>
              <strong>{item}</strong>
              {index < 5 && <i>→</i>}
            </div>
          ))}
        </div>
      </section>

      <section id="journey" className="cv-dd-journey">
        <div className="cv-section-number">02</div>

        <div className="cv-dd-heading">
          <div>
            <div className="cv-eyebrow">THE DEVELOPMENT JOURNEY</div>

            <h2>
              Six stages.
              <span>One connected system.</span>
            </h2>
          </div>

          <p>
            Each stage contributes a different layer of biological and
            experimental understanding to the development question.
          </p>
        </div>

        <div className="cv-dd-stage-grid">
          {stages.map(([number, title, text]) => (
            <article key={number} className="cv-dd-stage">
              <span>{number}</span>
              <div className="cv-dd-stage-line" />
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cv-dd-workflows">
        <div className="cv-section-number">03</div>

        <div className="cv-dd-heading">
          <div>
            <div className="cv-eyebrow">DEVELOPMENT WORKBENCH</div>

            <h2>
              Four ways
              <span>into the pipeline.</span>
            </h2>
          </div>
        </div>

        <div className="cv-dd-workflow-stage">
          <div className="cv-dd-workflow-tabs">
            {workflows.map((workflow, index) => (
              <button
                key={workflow.number}
                className={
                  activeWorkflow === index
                    ? "active"
                    : ""
                }
                onMouseEnter={() => setActiveWorkflow(index)}
                onClick={() => setActiveWorkflow(index)}
              >
                <span>{workflow.number}</span>
                <strong>{workflow.label}</strong>
                <i>↗</i>
              </button>
            ))}
          </div>

          <div className="cv-dd-workflow-feature">
            <div className="cv-dd-workflow-image">
              <Image
                src={workflows[activeWorkflow].image}
                alt={workflows[activeWorkflow].label}
                fill
                sizes="(max-width: 850px) 100vw, 45vw"
              />
              <div />
            </div>

            <div className="cv-dd-workflow-copy">
              <div className="cv-eyebrow">
                {workflows[activeWorkflow].label}
              </div>

              <h3>{workflows[activeWorkflow].title}</h3>

              <p>{workflows[activeWorkflow].text}</p>

              <Link href={workflows[activeWorkflow].href}>
                OPEN WORKBENCH <span>→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="cv-dd-evidence">
        <div className="cv-section-number">04</div>

        <div className="cv-dd-evidence-layout">
          <div>
            <div className="cv-eyebrow">DEVELOPMENT EVIDENCE</div>

            <h2>
              Build the picture
              <span>from multiple signals.</span>
            </h2>

            <p>
              A development decision should not depend on one isolated
              observation. Different evidence layers answer different
              scientific questions.
            </p>

            <div className="cv-dd-evidence-list">
              {evidence.map(([title, text], index) => (
                <div key={title}>
                  <span>0{index + 1}</span>
                  <div>
                    <strong>{title}</strong>
                    <p>{text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="cv-dd-evidence-visual">
            <div className="cv-dd-evidence-ring ring-one" />
            <div className="cv-dd-evidence-ring ring-two" />
            <div className="cv-dd-evidence-ring ring-three" />

            <div className="cv-dd-evidence-core">
              <small>EVIDENCE</small>
              <strong>LANDSCAPE</strong>
            </div>

            <div className="cv-dd-evidence-label label-a">
              BIOLOGY
            </div>
            <div className="cv-dd-evidence-label label-b">
              DISEASE
            </div>
            <div className="cv-dd-evidence-label label-c">
              ASSAY
            </div>
            <div className="cv-dd-evidence-label label-d">
              COMPOUND
            </div>
          </div>
        </div>
      </section>

      <section className="cv-dd-principles">
        <div className="cv-section-number">05</div>

        <div className="cv-dd-heading">
          <div>
            <div className="cv-eyebrow">SCIENTIFIC INTERPRETATION</div>

            <h2>
              Read the signal.
              <span>Respect the evidence.</span>
            </h2>
          </div>
        </div>

        <div className="cv-dd-principle-grid">
          {principles.map(([number, title, text]) => (
            <article key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cv-dd-example">
        <div className="cv-section-number">06</div>

        <div className="cv-dd-example-layout">
          <div>
            <div className="cv-eyebrow">EXAMPLE DEVELOPMENT QUESTION</div>

            <h2>
              Start with
              <span>EGFR.</span>
            </h2>

            <p>
              A target can connect biological function, disease context,
              molecular activity and development evidence.
            </p>
          </div>

          <div className="cv-dd-example-map">
            {[
              ["01", "EGFR", "TARGET"],
              ["02", "SIGNALING", "MECHANISM"],
              ["03", "COMPOUNDS", "MOLECULAR"],
              ["04", "ACTIVITY", "EXPERIMENT"],
              ["05", "DISEASE", "CONTEXT"],
              ["06", "EVIDENCE", "REASONING"],
            ].map(([number, value, label]) => (
              <div key={number}>
                <span>{number}</span>
                <strong>{value}</strong>
                <small>{label}</small>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="cv-dd-final">
        <div className="cv-dd-final-glow" />

        <div className="cv-section-number">07</div>

        <div className="cv-dd-final-copy">
          <div className="cv-eyebrow">
            BEGIN DRUG DEVELOPMENT INTELLIGENCE
          </div>

          <h2>
            Discover the target.
            <span>Trace the evidence.</span>
          </h2>

          <p>
            Move from biological opportunity toward a connected
            development landscape.
          </p>

          <div className="cv-dd-final-actions">
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
        </div>
      </section>

      <Footer />
    </main>
  );
}
