"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import "./biotechnology.css";

type CharacterPose = "left" | "center" | "right";

const characterMap: Record<CharacterPose, string> = {
  left: "/biotechnology/biotech-character-left.png",
  center: "/biotechnology/biotech-character-center.png",
  right: "/biotechnology/biotech-character-right.png",
};

export default function BiotechnologyPage() {
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

  const characterSrc = characterMap[pose];

  return (
    <main className="cv-biotechnology-page">
      <Navbar />

      {/* =========================================================
          SECTION 01 — HERO
      ========================================================= */}
      <section className="cv-biotechnology-hero">
        <div className="cv-biotechnology-grid" />

        <div className="cv-biotechnology-glow cv-biotechnology-glow-one" />
        <div className="cv-biotechnology-glow cv-biotechnology-glow-two" />

        <div className="cv-biotechnology-hero-copy">
          <div className="cv-biotechnology-kicker">
            <span>01</span>
            <i />
            <strong>BIOTECHNOLOGY INTELLIGENCE FLOW</strong>
          </div>

          <h1>
            Decode
            <br />
            <em>living matter.</em>
          </h1>

          <p>
            Explore biological materials from visible structure to anatomy,
            compounds, mechanisms, and potential biological relevance through
            connected scientific intelligence.
          </p>

          <div className="cv-biotechnology-hero-meta">
            <div>
              <strong>03</strong>
              <span>PLANT WORKFLOWS</span>
            </div>

            <div>
              <strong>AI</strong>
              <span>BIOLOGICAL INTELLIGENCE</span>
            </div>

            <div>
              <strong>∞</strong>
              <span>MATERIALS TO EXPLORE</span>
            </div>
          </div>

          <div className="cv-biotechnology-flow">
            <div className="cv-biotechnology-flow-heading">
              <span>BIOLOGICAL MATERIAL</span>
              <i />
              <strong>FROM MATTER TO MECHANISM</strong>
            </div>

            <div className="cv-biotechnology-flow-track">
              <div className="cv-biotechnology-flow-step">
                <span className="cv-biotechnology-flow-dot" />
                <strong>MATERIAL</strong>
                <p>Identify biology</p>
              </div>

              <i className="cv-biotechnology-flow-line" />

              <div className="cv-biotechnology-flow-step">
                <span className="cv-biotechnology-flow-dot" />
                <strong>ANATOMY</strong>
                <p>Explore structure</p>
              </div>

              <i className="cv-biotechnology-flow-line" />

              <div className="cv-biotechnology-flow-step">
                <span className="cv-biotechnology-flow-dot" />
                <strong>COMPOUNDS</strong>
                <p>Discover properties</p>
              </div>

              <i className="cv-biotechnology-flow-line" />

              <div className="cv-biotechnology-flow-step">
                <span className="cv-biotechnology-flow-dot" />
                <strong>MECHANISM</strong>
                <p>Connect biology</p>
              </div>
            </div>
          </div>

          <a
            href="#biotechnology-guide"
            className="cv-biotechnology-scroll"
          >
            EXPLORE BIOTECHNOLOGY
            <i>↓</i>
          </a>
        </div>

        <div className="cv-biotechnology-character">
          <div className="cv-biotechnology-character-aura" />

          <img
            src={characterSrc}
            alt="CureVerseAI biotechnology scientific guide"
            draggable={false}
          />

          <div className="cv-biotechnology-character-label">
            <i />
            BIOTECHNOLOGY / BIOLOGICAL INTELLIGENCE
          </div>
        </div>

        <div className="cv-biotechnology-side-data">
          <span>BIOLOGICAL MATERIAL</span>
          <i />
          <span>ANATOMY</span>
          <i />
          <span>COMPOUNDS</span>
        </div>

        <div className="cv-biotechnology-bottom-line">
          <span>CUREVERSEAI / BIOTECHNOLOGY</span>
          <span>OBSERVE — DECODE — DISCOVER</span>
        </div>
      </section>

      {/* =========================================================
          SECTION 02 — GUIDE
      ========================================================= */}
      <section
        className="biotechnology-guide-section"
        id="biotechnology-guide"
      >
        <div className="biotechnology-guide-inner">

          <div className="biotechnology-guide-copy">

            <div className="biotechnology-guide-eyebrow">
              <span>02</span>
              <i />
              <strong>UNDERSTANDING BIOLOGICAL MATTER</strong>
            </div>

            <h2>
              From material
              <br />
              <em>to biological insight.</em>
            </h2>

            <p className="biotechnology-guide-description">
              Biotechnology intelligence begins with the material itself.
              Instead of stopping at visual identification, CureVerseAI
              connects observable characteristics with biological structure,
              anatomical parts, compounds, properties, mechanisms, and
              potential applications.
            </p>

            <p className="biotechnology-guide-description secondary">
              Every investigation follows a connected biological chain —
              helping move from <strong>what we see</strong> to
              <strong> what it may contain</strong>, how those components may
              behave, and where the evidence leads next.
            </p>

            <a
              href="#biotechnology-workflows"
              className="biotechnology-guide-cta"
            >
              <span>EXPLORE BIOTECHNOLOGY WORKFLOWS</span>
              <b>↗</b>
            </a>

            <div className="biotechnology-guide-topics">

        <div className="biotechnology-guide-topic">
          <span className="biotechnology-guide-topic-icon">
            <b>AN</b>
          </span>
          <div>
            <strong>ANATOMY</strong>
            <p>Explore the biological structures and anatomical parts that make up living material.</p>
          </div>
        </div>

        <div className="biotechnology-guide-topic">
          <span className="biotechnology-guide-topic-icon">
            <b>CO</b>
          </span>
          <div>
            <strong>COMPOUNDS</strong>
            <p>Trace biological compounds and connect them with their properties and functions.</p>
          </div>
        </div>

        <div className="biotechnology-guide-topic">
          <span className="biotechnology-guide-topic-icon">
            <b>PR</b>
          </span>
          <div>
            <strong>PROPERTIES</strong>
            <p>Understand observable and biological properties through connected scientific evidence.</p>
          </div>
        </div>

        <div className="biotechnology-guide-topic">
          <span className="biotechnology-guide-topic-icon">
            <b>ME</b>
          </span>
          <div>
            <strong>MECHANISMS</strong>
            <p>Follow compounds and properties toward biological mechanisms and potential applications.</p>
          </div>
        </div>

      </div>

            <div className="biotechnology-guide-bottom-line">
              <span>MATERIAL</span>
              <i />
              <span>STRUCTURE</span>
              <i />
              <span>COMPOUND</span>
              <i />
              <span>MECHANISM</span>
              <i />
              <span>INSIGHT</span>
            </div>

          </div>

          <div className="biotechnology-guide-visual">
            <div className="biotechnology-guide-visual-frame">

              <div className="biotechnology-guide-image-wrap">
                <img
                  src="/biotechnology/biotechnology-guide.png"
                  alt="Biotechnology biological material intelligence"
                />
              </div>

              <div className="biotechnology-guide-scanline" />
              <div className="biotechnology-guide-grid-overlay" />

              <span className="biotechnology-guide-corner top-left" />
              <span className="biotechnology-guide-corner top-right" />
              <span className="biotechnology-guide-corner bottom-left" />
              <span className="biotechnology-guide-corner bottom-right" />

              <div className="biotechnology-guide-data data-one">
                MATERIAL IDENTIFIED
              </div>

              <div className="biotechnology-guide-data data-two">
                ANATOMY / COMPOUND
              </div>

              <div className="biotechnology-guide-data data-three">
                BIOLOGICAL INSIGHT
              </div>

              <div className="biotechnology-guide-visual-label">
                <i />
                BIOLOGICAL INTELLIGENCE / 02
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* =========================================================
          SECTION 03 — WORKFLOWS
      ========================================================= */}
      <section
        className="biotechnology-workflows-section"
        id="biotechnology-workflows"
      >
        <div className="biotechnology-workflows-atmosphere" />

        <div className="biotechnology-workflows-inner">
          <div className="biotechnology-workflows-header">
            <div className="biotechnology-workflows-eyebrow">
              <span>03</span>
              <i />
              <strong>BIOTECHNOLOGY WORKFLOWS</strong>
            </div>

            <div className="biotechnology-workflows-heading-row">
              <div>
                <h2>
                  Start with matter.
                  <br />
                  <em>Discover its biology.</em>
                </h2>
              </div>

              <p>
                Choose how you want to investigate a biological material.
                Each workflow follows a different scientific path — from
                understanding anatomical structure, to examining biological
                potential, to tracing compounds toward targets and pathways.
              </p>
            </div>
          </div>

          <div className="biotechnology-workflow-grid">
            {/* CARD 01 */}
            <a
              href="/domains/biotechnology/medicinal-plant-intelligence"
              className="biotechnology-workflow-card"
            >
              <div className="biotechnology-workflow-card-top">
                <span className="biotechnology-workflow-number">M→P</span>
                <div className="biotechnology-workflow-arrow">↗</div>
              </div>
              <div className="biotechnology-workflow-symbol">
                <div className="biotechnology-workflow-symbol-orbit" />
                <span>M→P</span>
              </div>
              <div className="biotechnology-workflow-content">
                <span className="biotechnology-workflow-kicker">
                  MEDICINAL PLANT INTELLIGENCE
                </span>
                <h3>
                  Discover
                  <br />
                  <em>medicinal plants.</em>
                </h3>
                <p>
                  Upload a plant image to explore candidate identification,
                  documented medicinal uses, known compounds, biological
                  activities, and supporting scientific evidence.
                </p>
              </div>
              <div className="biotechnology-workflow-path">
                IDENTIFY <i>→</i> COMPOUNDS <i>→</i> EVIDENCE
              </div>
            </a>

            {/* CARD 02 */}
            <a
              href="/domains/biotechnology/plant-edibility-analysis"
              className="biotechnology-workflow-card"
            >
              <div className="biotechnology-workflow-card-top">
                <span className="biotechnology-workflow-number">P→E</span>
                <div className="biotechnology-workflow-arrow">↗</div>
              </div>
              <div className="biotechnology-workflow-symbol">
                <div className="biotechnology-workflow-symbol-orbit" />
                <span>P→E</span>
              </div>
              <div className="biotechnology-workflow-content">
                <span className="biotechnology-workflow-kicker">
                  PLANT EDIBILITY ANALYSIS
                </span>
                <h3>
                  Explore
                  <br />
                  <em>plant edibility.</em>
                </h3>
                <p>
                  Investigate candidate plant identity and documented
                  edibility information. Uncertain or potentially toxic
                  plants are flagged instead of being declared safe to eat.
                </p>
              </div>
              <div className="biotechnology-workflow-path">
                IDENTIFY <i>→</i> CHECK <i>→</i> VERIFY
              </div>
            </a>

            {/* CARD 03 */}
            <a
              href="/domains/biotechnology/plant-lifebook"
              className="biotechnology-workflow-card"
            >
              <div className="biotechnology-workflow-card-top">
                <span className="biotechnology-workflow-number">P→B</span>
                <div className="biotechnology-workflow-arrow">↗</div>
              </div>
              <div className="biotechnology-workflow-symbol">
                <div className="biotechnology-workflow-symbol-orbit" />
                <span>P→B</span>
              </div>
              <div className="biotechnology-workflow-content">
                <span className="biotechnology-workflow-kicker">
                  PLANT LIFEBOOK
                </span>
                <h3>
                  Explore a plant's
                  <br />
                  <em>complete profile.</em>
                </h3>
                <p>
                  Build a structured botanical profile covering taxonomy,
                  morphology, habitat, distribution, ecological role,
                  known compounds, and available research.
                </p>
              </div>
              <div className="biotechnology-workflow-path">
                TAXONOMY <i>→</i> BIOLOGY <i>→</i> RESEARCH
              </div>
            </a>
          </div>

          <div className="biotechnology-workflows-bottom">
            <span>BIOLOGICAL MATERIAL</span>
            <i />
            <strong>COMPOUND</strong>
            <i />
            <strong>TARGET</strong>
            <i />
            <strong>PATHWAY</strong>
            <i />
            <span>MEDICINE / VIRTUAL CELL</span>
          </div>
        </div>
      </section>
    </main>
  );
}