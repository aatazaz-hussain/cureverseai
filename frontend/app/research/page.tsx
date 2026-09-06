"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import "./research.css";

type CharacterPose = "left" | "center" | "right";

export default function ResearchPage() {
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

  const characterSrc =
    pose === "left"
      ? "/research/research-character-left.png"
      : pose === "right"
        ? "/research/research-character-right.png"
        : "/research/research-character-center.png";

  return (
    <main className="cv-research-page">
      <Navbar />

      <section className="cv-research-hero">
        <div className="cv-research-grid" />
        <div className="cv-research-glow cv-research-glow-one" />
        <div className="cv-research-glow cv-research-glow-two" />

        <div className="cv-research-dna">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="cv-research-hero-copy">
          <div className="cv-research-kicker">
            <span>01</span>
            <i />
            RESEARCH DOMAIN
          </div>

          <h1>
            Investigate
            <br />
            <em>biology.</em>
          </h1>

          <p>
            Explore genes, proteins, variants, pathways and scientific evidence
            through one connected biological intelligence system.
          </p>

          <div className="cv-research-hero-meta">
            <div>
              <strong>05</strong>
              <span>RESEARCH WORKFLOWS</span>
            </div>

            <div>
              <strong>03</strong>
              <span>BIOLOGICAL MODALITIES</span>
            </div>

            <div>
              <strong>01</strong>
              <span>CONNECTED SYSTEM</span>
            </div>
          </div>

          <div className="cv-research-flow">
            <div className="cv-research-flow-heading">
              <span>RESEARCH INTELLIGENCE</span>
              <i />
              <strong>FROM QUESTION TO DISCOVERY</strong>
            </div>

            <div className="cv-research-flow-track">
              <div className="cv-research-flow-step">
                <span className="cv-research-flow-dot" />
                <strong>BIOLOGICAL INPUT</strong>
                <p>Gene · Protein · Variant</p>
              </div>

              <div className="cv-research-flow-line" />

              <div className="cv-research-flow-step">
                <span className="cv-research-flow-dot" />
                <strong>AI REPRESENTATION</strong>
                <p>Learned biological features</p>
              </div>

              <div className="cv-research-flow-line" />

              <div className="cv-research-flow-step">
                <span className="cv-research-flow-dot" />
                <strong>SCIENTIFIC EVIDENCE</strong>
                <p>Pathways · Disease · Experiments</p>
              </div>

              <div className="cv-research-flow-line" />

              <div className="cv-research-flow-step">
                <span className="cv-research-flow-dot" />
                <strong>REASONED INSIGHT</strong>
                <p>Connected, traceable research</p>
              </div>
            </div>
          </div>

          <a href="#research-manual" className="cv-research-scroll">
            <span>EXPLORE RESEARCH</span>
            <i>↓</i>
          </a>
        </div>

        <div className={`cv-research-character cv-research-character-${pose}`}>
          <div className="cv-research-character-aura" />

          <img
            src={characterSrc}
            alt="CureVerseAI research scientist"
            draggable={false}
          />

          <div className="cv-research-character-label">
            <span>RESEARCH INTELLIGENCE</span>
            <i />
          </div>
        </div>

        <div className="cv-research-side-data">
          <span>DATA</span>
          <i />
          <span>MODELS</span>
          <i />
          <span>EVIDENCE</span>
          <i />
          <span>INSIGHT</span>
        </div>

        <div className="cv-research-bottom-line">
          <span>CURVERSEAI / BIOLOGICAL INTELLIGENCE</span>
          <span>SCROLL TO INVESTIGATE</span>
        </div>
      </section>
      <section className="research-guide-section">
        <div className="research-guide-bg-glow research-guide-bg-glow-one" />
        <div className="research-guide-bg-glow research-guide-bg-glow-two" />

        <div className="research-guide-inner">
          {/* LEFT CONTENT */}
          <div className="research-guide-copy">
            <div className="research-guide-eyebrow">
              <span>02</span>
              <i />
              <strong>THE RESEARCH GUIDE</strong>
            </div>

            <h2>
              Understand the system
              <br />
              <em>before you investigate.</em>
            </h2>

            <p className="research-guide-description">
              Learn what CureVerseAI Research can investigate, how each workflow
              works, what biological data powers the results, and how to
              interpret the evidence returned by the system.
            </p>

            <p className="research-guide-description secondary">
              From genes and proteins to pathways, variants, and multi-source
              evidence — the guide gives you a clear path from question to
              biological insight.
            </p>

            <a href="/domains/research/manual" className="research-guide-cta">
              <span>EXPLORE THE RESEARCH GUIDE</span>
              <b>↗</b>
            </a>

            <div className="research-guide-topics">
              <div className="research-guide-topic">
                <div className="research-guide-topic-icon">
                  <span>DNA</span>
                </div>
                <div>
                  <strong>GENES</strong>
                  <p>Identity, function & variation</p>
                </div>
              </div>

              <div className="research-guide-topic">
                <div className="research-guide-topic-icon">
                  <span>PRO</span>
                </div>
                <div>
                  <strong>PROTEINS</strong>
                  <p>Structure & biological role</p>
                </div>
              </div>

              <div className="research-guide-topic">
                <div className="research-guide-topic-icon">
                  <span>PATH</span>
                </div>
                <div>
                  <strong>PATHWAYS</strong>
                  <p>Connected biological context</p>
                </div>
              </div>

              <div className="research-guide-topic">
                <div className="research-guide-topic-icon">
                  <span>EV</span>
                </div>
                <div>
                  <strong>EVIDENCE</strong>
                  <p>Sources behind the insight</p>
                </div>
              </div>
            </div>

            <div className="research-guide-bottom-line">
              <span>FROM DATA</span>
              <i />
              <span>TO DISCOVERY</span>
            </div>
          </div>

          {/* RIGHT VISUAL */}
          <div className="research-guide-visual">
            <div className="research-guide-visual-frame">
              <div className="research-guide-corner corner-tl" />
              <div className="research-guide-corner corner-tr" />
              <div className="research-guide-corner corner-bl" />
              <div className="research-guide-corner corner-br" />

              <div className="research-guide-image-wrap">
                <img
                  src="/research/research-guide.png"
                  alt="CureVerseAI biological research intelligence"
                />
              </div>

              <div className="research-guide-scanline" />

              <div className="research-guide-data data-one">
                <span />
                <strong>BIOLOGICAL DATA</strong>
                <small>CONNECTED</small>
              </div>

              <div className="research-guide-data data-two">
                <span />
                <strong>AI REPRESENTATION</strong>
                <small>ACTIVE</small>
              </div>

              <div className="research-guide-data data-three">
                <span />
                <strong>EVIDENCE</strong>
                <small>TRACEABLE</small>
              </div>

              <div className="research-guide-visual-label">
                <span>RESEARCH INTELLIGENCE</span>
                <strong>01 / 05</strong>
              </div>
            </div>

            <div className="research-guide-visual-caption">
              <span>EXPLORE · CONNECT · UNDERSTAND</span>
              <i />
              <strong>CUREVERSEAI</strong>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          SECTION 3 — RESEARCH WORKFLOWS
          ===================================================== */}

      <section className="research-workflows-section" id="research-workflows">
        <div className="research-workflows-atmosphere" />

        <div className="research-workflows-inner">
          <div className="research-workflows-header">
            <div className="research-workflows-eyebrow">
              <span>03</span>
              <i />
              <strong>RESEARCH WORKFLOWS</strong>
            </div>

            <div className="research-workflows-heading-row">
              <div>
                <h2>
                  Start with a question.
                  <br />
                  <em>Investigate the biology.</em>
                </h2>
              </div>

              <p>
                Choose how you want to investigate. Each workflow takes a
                biological question and turns it into a structured research
                workspace powered by connected biological data, AI
                representations, external evidence, and reasoning.
              </p>
            </div>
          </div>

          <div className="research-workflow-grid">
            {/* 01 — GENE EXPLORER */}

            <a
              href="/domains/research/gene-explorer"
              className="research-workflow-card workflow-featured"
            >
              <div className="research-workflow-top">
                <span className="research-workflow-number">01</span>
                <span className="research-workflow-arrow">↗</span>
              </div>

              <div className="research-workflow-symbol">
                <span>DNA</span>
                <i />
              </div>

              <div className="research-workflow-content">
                <span className="research-workflow-kicker">
                  BIOLOGICAL IDENTITY
                </span>

                <h3>Gene Explorer</h3>

                <p>
                  Start with a gene and uncover its biological identity, protein
                  relationship, pathways, variants, and connected context.
                </p>
              </div>

              <div className="research-workflow-footer">
                <span>GENE → CONTEXT</span>
                <b>INVESTIGATE</b>
              </div>
            </a>

            {/* 02 — PROTEIN EXPLORER */}

            <a
              href="/domains/research/protein-explorer"
              className="research-workflow-card"
            >
              <div className="research-workflow-top">
                <span className="research-workflow-number">02</span>
                <span className="research-workflow-arrow">↗</span>
              </div>

              <div className="research-workflow-symbol">
                <span>PRO</span>
                <i />
              </div>

              <div className="research-workflow-content">
                <span className="research-workflow-kicker">
                  PROTEIN INTELLIGENCE
                </span>

                <h3>Protein Explorer</h3>

                <p>
                  Explore a protein by identity or sequence and generate an
                  AI-based representation of its biological features.
                </p>
              </div>

              <div className="research-workflow-footer">
                <span>PROTEIN → FEATURES</span>
                <b>INVESTIGATE</b>
              </div>
            </a>

            {/* 03 — VARIANT INVESTIGATOR */}

            <a
              href="/domains/research/variant-investigator"
              className="research-workflow-card"
            >
              <div className="research-workflow-top">
                <span className="research-workflow-number">03</span>
                <span className="research-workflow-arrow">↗</span>
              </div>

              <div className="research-workflow-symbol">
                <span>VAR</span>
                <i />
              </div>

              <div className="research-workflow-content">
                <span className="research-workflow-kicker">
                  VARIANT CONTEXT
                </span>

                <h3>Variant Investigator</h3>

                <p>
                  Investigate a genetic variant in context and connect it with
                  biological information and available evidence.
                </p>
              </div>

              <div className="research-workflow-footer">
                <span>VARIANT → EVIDENCE</span>
                <b>INVESTIGATE</b>
              </div>
            </a>

            {/* 04 — PATHWAY EXPLORER */}

            <a
              href="/domains/research/pathway-explorer"
              className="research-workflow-card"
            >
              <div className="research-workflow-top">
                <span className="research-workflow-number">04</span>
                <span className="research-workflow-arrow">↗</span>
              </div>

              <div className="research-workflow-symbol">
                <span>PATH</span>
                <i />
              </div>

              <div className="research-workflow-content">
                <span className="research-workflow-kicker">
                  BIOLOGICAL NETWORK
                </span>

                <h3>Pathway Explorer</h3>

                <p>
                  Discover the biological pathways connected to a gene or
                  protein and understand relationships across the system.
                </p>
              </div>

              <div className="research-workflow-footer">
                <span>ENTITY → PATHWAY</span>
                <b>INVESTIGATE</b>
              </div>
            </a>

            {/* 05 — EVIDENCE RESEARCH */}

            <a
              href="/domains/research/evidence-research"
              className="research-workflow-card workflow-evidence"
            >
              <div className="research-workflow-top">
                <span className="research-workflow-number">05</span>
                <span className="research-workflow-arrow">↗</span>
              </div>

              <div className="research-workflow-symbol">
                <span>EV</span>
                <i />
              </div>

              <div className="research-workflow-content">
                <span className="research-workflow-kicker">
                  MULTI-SOURCE REASONING
                </span>

                <h3>Evidence Research</h3>

                <p>
                  Bring biological and experimental sources together to build a
                  connected, traceable evidence picture around a research
                  target.
                </p>
              </div>

              <div className="research-workflow-footer">
                <span>EVIDENCE → INSIGHT</span>
                <b>INVESTIGATE</b>
              </div>
            </a>
          </div>

          <div className="research-workflows-bottom">
            <div>
              <span>INPUT</span>
              <i />
              <span>REPRESENTATION</span>
              <i />
              <span>EVIDENCE</span>
              <i />
              <strong>INSIGHT</strong>
            </div>

            <p>One connected research system. Five ways to begin.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
