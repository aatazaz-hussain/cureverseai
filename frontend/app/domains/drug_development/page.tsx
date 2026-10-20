"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import "./drug-development.css";

type CharacterPose = "left" | "center" | "right";

const heroCharacters = {
  left: "/drug-development/drug-character-left.png",
  center: "/drug-development/drug-character-center.png",
  right: "/drug-development/drug-character-right.png",
};

export default function DrugDevelopmentPage() {
  const [pose, setPose] = useState<CharacterPose>("center");

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const x = event.clientX / window.innerWidth;

      if (x < 0.34) {
        setPose("left");
      } else if (x > 0.66) {
        setPose("right");
      } else {
        setPose("center");
      }
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const characterSrc = heroCharacters[pose];

  return (
    <main className="cv-drug-page">
      <Navbar />

      <section className="cv-drug-hero">
        {/* CELLULAR VIDEO BACKGROUND */}
        <div className="cv-drug-video-layer">
</div>

        {/* DARK CINEMATIC OVERLAY */}
        <div className="cv-drug-video-overlay" />

        {/* SCIENTIFIC GRID */}
        <div className="cv-drug-grid" />

        {/* AMBIENT GLOWS */}
        <div className="cv-drug-glow cv-drug-glow-one" />
        <div className="cv-drug-glow cv-drug-glow-two" />

        {/* HERO CONTENT */}
        <div className="cv-drug-hero-copy">
          <div className="cv-drug-kicker">
            <span>02</span>
            <i />
            DRUG DEVELOPMENT DOMAIN
          </div>

          <h1>
            Discover
            <br />
            <em>therapeutics.</em>
          </h1>

          <p>
            Connect disease biology, molecular mechanisms, therapeutic targets,
            compounds and scientific evidence to accelerate AI-assisted drug
            discovery.
          </p>

          <div className="cv-drug-hero-meta">
            <div>
              <strong>03</strong>
              <span>DISCOVERY WORKFLOWS</span>
            </div>

            <div>
              <strong>05</strong>
              <span>BIOLOGICAL LAYERS</span>
            </div>

            <div>
              <strong>01</strong>
              <span>CONNECTED SYSTEM</span>
            </div>
          </div>

          <div className="cv-drug-flow">
            <div className="cv-drug-flow-heading">
              <span>THERAPEUTIC DISCOVERY</span>
              <i />
              <strong>FROM DISEASE TO INTERVENTION</strong>
            </div>

            <div className="cv-drug-flow-track">
              <div className="cv-drug-flow-step">
                <span className="cv-drug-flow-dot" />
                <strong>DISEASE</strong>
                <p>Biological impact</p>
              </div>

              <div className="cv-drug-flow-line" />

              <div className="cv-drug-flow-step">
                <span className="cv-drug-flow-dot" />
                <strong>MECHANISM</strong>
                <p>Genes · Pathways</p>
              </div>

              <div className="cv-drug-flow-line" />

              <div className="cv-drug-flow-step">
                <span className="cv-drug-flow-dot" />
                <strong>TARGET</strong>
                <p>Therapeutic opportunity</p>
              </div>

              <div className="cv-drug-flow-line" />

              <div className="cv-drug-flow-step">
                <span className="cv-drug-flow-dot" />
                <strong>COMPOUND</strong>
                <p>Molecule · Intervention</p>
              </div>

              <div className="cv-drug-flow-line" />

              <div className="cv-drug-flow-step">
                <span className="cv-drug-flow-dot" />
                <strong>EVIDENCE</strong>
                <p>Traceable insight</p>
              </div>
            </div>
          </div>

          <a href="#drug-workflows" className="cv-drug-scroll">
            <span>EXPLORE DRUG DEVELOPMENT</span>
            <i>↓</i>
          </a>
        </div>

        {/* CHARACTER */}
        <div className={`cv-drug-character cv-drug-character-${pose}`}>
          <div className="cv-drug-character-aura" />

          <img
            src={characterSrc}
            alt="CureVerseAI Drug Development scientist"
            draggable={false}
          />

          <div className="cv-drug-character-label">
            <span>DRUG DISCOVERY INTELLIGENCE</span>
            <i />
          </div>
        </div>

        {/* SIDE DATA */}
        <div className="cv-drug-side-data">
          <span>DISEASE</span>
          <i />
          <span>MECHANISM</span>
          <i />
          <span>TARGET</span>
          <i />
          <span>COMPOUND</span>
          <i />
          <span>EVIDENCE</span>
        </div>

        {/* BOTTOM SYSTEM LINE */}
        <div className="cv-drug-bottom-line">
          <span>CUREVERSEAI / DRUG DEVELOPMENT</span>
          <span>SCROLL TO DISCOVER</span>
        </div>
      </section>

      {/* Workflow anchor for the next section */}
      {/* =====================================================
          SECTION 2 — DRUG DEVELOPMENT GUIDE
          ===================================================== */}
      <section className="drug-guide-section">
        <div className="drug-guide-bg-glow drug-guide-bg-glow-one" />
        <div className="drug-guide-bg-glow drug-guide-bg-glow-two" />

        <div className="drug-guide-inner">

          {/* LEFT CONTENT */}
          <div className="drug-guide-copy">

            <div className="drug-guide-eyebrow">
              <span>02</span>
              <i />
              <strong>THE DRUG DEVELOPMENT GUIDE</strong>
            </div>

            <h2>
              From disease biology
              <br />
              to <em>therapeutic opportunity.</em>
            </h2>

            <p className="drug-guide-description">
              Understand how CureVerseAI connects disease mechanisms,
              biological targets, compounds, interventions, and scientific
              evidence to support AI-assisted therapeutic discovery.
            </p>

            <p className="drug-guide-description secondary">
              Move from disease impact to mechanism, target, compound and
              evidence — following a connected biological path toward
              therapeutic hypothesis generation.
            </p>

            <a href="#drug-workflows" className="drug-guide-cta">
              <span>EXPLORE DISCOVERY WORKFLOWS</span>
              <b>↗</b>
            </a>

            <div className="drug-guide-topics">

              <div className="drug-guide-topic">
                <div className="drug-guide-topic-icon">
                  <span>D→B</span>
                </div>
                <div>
                  <strong>DISEASE IMPACT</strong>
                  <p>Organ, tissue &amp; cellular effects</p>
                </div>
              </div>

              <div className="drug-guide-topic">
                <div className="drug-guide-topic-icon">
                  <span>R→D</span>
                </div>
                <div>
                  <strong>REVERSE ENGINEERING</strong>
                  <p>Phenotype, genes &amp; pathways</p>
                </div>
              </div>

              <div className="drug-guide-topic">
                <div className="drug-guide-topic-icon">
                  <span>T→C</span>
                </div>
                <div>
                  <strong>THERAPEUTIC DISCOVERY</strong>
                  <p>Targets, compounds &amp; mechanisms</p>
                </div>
              </div>

              <div className="drug-guide-topic">
                <div className="drug-guide-topic-icon">
                  <span>EVI</span>
                </div>
                <div>
                  <strong>EVIDENCE INTELLIGENCE</strong>
                  <p>Biological &amp; pharmacological evidence</p>
                </div>
              </div>

            </div>

            <div className="drug-guide-bottom-line">
              <span>DISEASE / MECHANISM / TARGET / COMPOUND / EVIDENCE</span>
              <i />
            </div>

          </div>

          {/* RIGHT VISUAL */}
          <div className="drug-guide-visual">

            <div className="drug-guide-visual-frame">

              <div className="drug-guide-image-wrap">
                <img
                  src="/drug-development/hero-drug-discovery.png"
                  alt="Drug development therapeutic discovery visualization"
                  draggable={false}
                />
              </div>

              <div className="drug-guide-scanline" />

              <div className="drug-guide-data data-one">
                <span />
                <strong>DISEASE BIOLOGY</strong>
                <small>CONNECTED</small>
              </div>

              <div className="drug-guide-data data-two">
                <span />
                <strong>THERAPEUTIC TARGET</strong>
                <small>IDENTIFIED</small>
              </div>

              <div className="drug-guide-data data-three">
                <span />
                <strong>EVIDENCE</strong>
                <small>TRACEABLE</small>
              </div>

              <div className="drug-guide-corner corner-tl" />
              <div className="drug-guide-corner corner-tr" />
              <div className="drug-guide-corner corner-bl" />
              <div className="drug-guide-corner corner-br" />

              <div className="drug-guide-visual-label">
                <span>THERAPEUTIC DISCOVERY</span>
                <strong>02 / 05</strong>
              </div>

            </div>

            <div className="drug-guide-visual-caption">
              <span>DISEASE · TARGET · COMPOUND · EVIDENCE</span>
              <i />
              <strong>CUREVERSEAI</strong>
            </div>

          </div>

        </div>
      </section>

      {/* =====================================================
          SECTION 3 — DRUG DEVELOPMENT WORKFLOWS
          ===================================================== */}

      <section className="drug-workflows-section" id="drug-workflows">
        <div className="drug-workflows-atmosphere" />

        <div className="drug-workflows-inner">

          {/* HEADER */}
          <div className="drug-workflows-header">

            <div className="drug-workflows-eyebrow">
              <span>03</span>
              <i />
              <strong>DRUG DEVELOPMENT WORKFLOWS</strong>
            </div>

            <div className="drug-workflows-heading-row">

              <div>
                <h2>
                  Start with disease.
                  <br />
                  <em>Discover the biology.</em>
                </h2>
              </div>

              <p>
                Choose how you want to investigate a disease. Each workflow
                follows a different biological path — from understanding
                disease impact, to reverse-engineering mechanisms, to
                discovering potential therapeutic opportunities through
                connected evidence.
              </p>

            </div>

          </div>

          {/* WORKFLOW CARDS */}
          <div className="drug-workflow-grid">

            {/* 01 — DISEASE → BIOLOGICAL IMPACT */}
            <a
              href="/domains/drug_development/disease-impact"
              className="drug-workflow-card workflow-featured"
            >
              <div className="drug-workflow-top">
                <span className="drug-workflow-number">01</span>
                <span className="drug-workflow-arrow">↗</span>
              </div>

              <div className="drug-workflow-symbol">
                <span>D→B</span>
                <i />
              </div>

              <div className="drug-workflow-content">
                <span className="drug-workflow-kicker">
                  DISEASE BIOLOGY
                </span>

                <h3>Disease → Biological Impact</h3>

                <p>
                  Visualize how a disease affects the body by moving from
                  organ and tissue changes into cellular behavior and
                  molecular mechanisms.
                </p>
              </div>

              <div className="drug-workflow-footer">
                <span>DISEASE → CELL → MECHANISM</span>
                <b>EXPLORE</b>
              </div>
            </a>

            {/* 02 — REVERSE DISEASE ENGINEERING */}
            <a
              href="/domains/drug_development/reverse-disease-engineering"
              className="drug-workflow-card"
            >
              <div className="drug-workflow-top">
                <span className="drug-workflow-number">02</span>
                <span className="drug-workflow-arrow">↗</span>
              </div>

              <div className="drug-workflow-symbol">
                <span>R→M</span>
                <i />
              </div>

              <div className="drug-workflow-content">
                <span className="drug-workflow-kicker">
                  MECHANISM INVESTIGATION
                </span>

                <h3>Reverse Disease Engineering</h3>

                <p>
                  Work backward from disease phenotype through biological
                  mechanisms, genes, variants, pathways, and contributing
                  factors using evidence-weighted relationships.
                </p>
              </div>

              <div className="drug-workflow-footer">
                <span>PHENOTYPE → GENE → PATHWAY</span>
                <b>INVESTIGATE</b>
              </div>
            </a>

            {/* 03 — THERAPEUTIC DISCOVERY */}
            <a
              href="/domains/drug_development/therapeutic-discovery"
              className="drug-workflow-card"
            >
              <div className="drug-workflow-top">
                <span className="drug-workflow-number">03</span>
                <span className="drug-workflow-arrow">↗</span>
              </div>

              <div className="drug-workflow-symbol">
                <span>T→C</span>
                <i />
              </div>

              <div className="drug-workflow-content">
                <span className="drug-workflow-kicker">
                  THERAPEUTIC HYPOTHESIS
                </span>

                <h3>Therapeutic Discovery</h3>

                <p>
                  Connect disease mechanisms to potential targets,
                  compounds or interventions, downstream effects, and
                  supporting evidence for AI-assisted therapeutic
                  hypothesis generation.
                </p>
              </div>

              <div className="drug-workflow-footer">
                <span>MECHANISM → TARGET → COMPOUND</span>
                <b>DISCOVER</b>
              </div>
            </a>

          </div>

          {/* BOTTOM SYSTEM SIGNAL */}
          <div className="drug-workflows-bottom">
            <div>
              <span>DISEASE</span>
              <i />
              <span>MECHANISM</span>
              <i />
              <span>TARGET</span>
              <i />
              <strong>THERAPEUTIC OPPORTUNITY</strong>
            </div>

            <p>
              One connected discovery system. Three ways to investigate.
            </p>
          </div>

        </div>
      </section>

    </main>
  );
}
