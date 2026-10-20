"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import "./medicine.css";

type CharacterPose = "left" | "center" | "right";

const heroCharacters = {
  left: "/medicine/medicine-character-left.png",
  center: "/medicine/medicine-character-center.png",
  right: "/medicine/medicine-character-right.png",
};

export default function MedicinePage() {
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
    <main className="cv-medicine-page">
      <Navbar />

      {/* =========================================================
          HERO
          ========================================================= */}

      <section className="cv-medicine-hero">
        <div className="cv-medicine-grid" />

        <div className="cv-medicine-glow cv-medicine-glow-one" />
        <div className="cv-medicine-glow cv-medicine-glow-two" />

        <div className="cv-medicine-hero-copy">

          <div className="cv-medicine-kicker">
            <span>01</span>
            <i />
            <strong>MEDICINE SIMULATION FLOW</strong>
          </div>

          <h1>
            Simulate
            <br />
            <em>biology.</em>
          </h1>

          <p>
            Explore how diseases alter biological systems, how interventions
            may change cellular behavior, and how treatment combinations can be
            compared through evidence-aware virtual simulation.
          </p>

          <div className="cv-medicine-hero-meta">
            <div>
              <strong>03</strong>
              <span>SIMULATION WORKFLOWS</span>
            </div>

            <div>
              <strong>AI</strong>
              <span>BIOLOGICAL MODELING</span>
            </div>

            <div>
              <strong>∞</strong>
              <span>SCENARIOS TO EXPLORE</span>
            </div>
          </div>

          <div className="cv-medicine-flow">

            <div className="cv-medicine-flow-heading">
              <span>VIRTUAL CELL</span>
              <i />
              <strong>FROM DISEASE TO RESPONSE</strong>
            </div>

            <div className="cv-medicine-flow-track">

              <div className="cv-medicine-flow-step">
                <span className="cv-medicine-flow-dot" />
                <strong>DISEASE</strong>
                <p>Model condition</p>
              </div>

              <i className="cv-medicine-flow-line" />

              <div className="cv-medicine-flow-step">
                <span className="cv-medicine-flow-dot" />
                <strong>VIRTUAL CELL</strong>
                <p>Simulate biology</p>
              </div>

              <i className="cv-medicine-flow-line" />

              <div className="cv-medicine-flow-step">
                <span className="cv-medicine-flow-dot" />
                <strong>TREATMENT</strong>
                <p>Model intervention</p>
              </div>

              <i className="cv-medicine-flow-line" />

              <div className="cv-medicine-flow-step">
                <span className="cv-medicine-flow-dot" />
                <strong>RESPONSE</strong>
                <p>Compare outcomes</p>
              </div>

            </div>
          </div>

          <a href="#medicine-guide" className="cv-medicine-scroll">
            EXPLORE MEDICINE
            <i>↓</i>
          </a>

        </div>

        <div className="cv-medicine-character">
          <div className="cv-medicine-character-aura" />

          <img
            src={characterSrc}
            alt="Medicine scientific guide"
            draggable={false}
          />

          <div className="cv-medicine-character-label">
            <i />
            MEDICINE / SIMULATION
          </div>
        </div>

        <div className="cv-medicine-side-data">
          <span>VIRTUAL BIOLOGY</span>
          <i />
          <span>SIMULATION</span>
          <i />
          <span>RESPONSE</span>
        </div>

        <div className="cv-medicine-bottom-line">
          <span>CUREVERSEAI / MEDICINE</span>
          <span>SIMULATE — UNDERSTAND — EXPLORE</span>
        </div>

      </section>

      {/* =========================================================
          SECTION 2 — MEDICINE GUIDE
          ========================================================= */}

      <section className="medicine-guide-section" id="medicine-guide">
        <div className="medicine-guide-bg-glow medicine-guide-bg-glow-one" />
        <div className="medicine-guide-bg-glow medicine-guide-bg-glow-two" />

        <div className="medicine-guide-inner">

          <div className="medicine-guide-copy">

            <div className="medicine-guide-eyebrow">
              <span>02</span>
              <i />
              <strong>THE MEDICINE GUIDE</strong>
            </div>

            <h2>
              From biology
              <br />
              to <em>simulation.</em>
            </h2>

            <p className="medicine-guide-description">
              Medicine uses AI-powered virtual biological models to explore
              how disease states alter cells and tissues, how interventions
              may influence biological mechanisms, and how different
              treatment strategies compare.
            </p>

            <p className="medicine-guide-description secondary">
              Instead of treating biology as a static record, CureVerseAI
              turns connected evidence into an interactive simulation space
              for investigating possible biological responses.
            </p>

            <a href="#medicine-workflows" className="medicine-guide-cta">
              <span>EXPLORE SIMULATION</span>
              <b>↗</b>
            </a>

            <div className="medicine-guide-topics">

              <div className="medicine-guide-topic">
                <div className="medicine-guide-topic-icon">
                  <span>D</span>
                </div>
                <div>
                  <strong>DISEASE MODELS</strong>
                  <p>Explore altered biological states.</p>
                </div>
              </div>

              <div className="medicine-guide-topic">
                <div className="medicine-guide-topic-icon">
                  <span>T</span>
                </div>
                <div>
                  <strong>TREATMENT</strong>
                  <p>Model intervention responses.</p>
                </div>
              </div>

              <div className="medicine-guide-topic">
                <div className="medicine-guide-topic-icon">
                  <span>C</span>
                </div>
                <div>
                  <strong>COMBINATIONS</strong>
                  <p>Compare treatment strategies.</p>
                </div>
              </div>

              <div className="medicine-guide-topic">
                <div className="medicine-guide-topic-icon">
                  <span>E</span>
                </div>
                <div>
                  <strong>EVIDENCE</strong>
                  <p>Connect simulation to biology.</p>
                </div>
              </div>

            </div>

            <div className="medicine-guide-bottom-line">
              <span>BIOLOGY</span>
              <i />
              <span>MODEL</span>
              <i />
              <strong>SIMULATED RESPONSE</strong>
            </div>

          </div>

          <div className="medicine-guide-visual">

            <div className="medicine-guide-visual-frame">

              <div className="medicine-guide-image-wrap">
                <img
                  src="/medicine/medicine-guide.png"
                  alt="Virtual biological simulation"
                />
              </div>

              <div className="medicine-guide-scanline" />

              <div className="medicine-guide-corner corner-tl" />
              <div className="medicine-guide-corner corner-tr" />
              <div className="medicine-guide-corner corner-bl" />
              <div className="medicine-guide-corner corner-br" />

              <div className="medicine-guide-data data-one">
                <span />
                <strong>VIRTUAL CELL</strong>
                <small>MODEL</small>
              </div>

              <div className="medicine-guide-data data-two">
                <span />
                <strong>BIOLOGICAL STATE</strong>
                <small>SIMULATED</small>
              </div>

              <div className="medicine-guide-data data-three">
                <span />
                <strong>TREATMENT RESPONSE</strong>
                <small>EXPLORE</small>
              </div>

              <div className="medicine-guide-visual-label">
                <span>MEDICINE</span>
                <strong>VIRTUAL BIOLOGICAL MODEL</strong>
              </div>

            </div>

            <div className="medicine-guide-visual-caption">
              <i />
              <span>SIMULATION SPACE</span>
              <strong>CUREVERSEAI</strong>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================
          SECTION 3 — MEDICINE WORKFLOWS
          ========================================================= */}

      <section className="medicine-workflows-section" id="medicine-workflows">
        <div className="medicine-workflows-atmosphere" />

        <div className="medicine-workflows-inner">

          <div className="medicine-workflows-header">

            <div className="medicine-workflows-eyebrow">
              <span>03</span>
              <i />
              <strong>MEDICINE WORKFLOWS</strong>
            </div>

            <div className="medicine-workflows-heading-row">

              <div>
                <h2>
                  Model the disease.
                  <br />
                  <em>Simulate the response.</em>
                </h2>
              </div>

              <p>
                Choose how you want to explore a biological scenario. Each
                workflow uses simulation to investigate disease states,
                treatment responses, or combinations of interventions.
              </p>

            </div>

          </div>

          <div className="medicine-workflow-grid">

            <a
              href="/domains/medicine/disease-simulation"
              className="medicine-workflow-card workflow-featured"
            >
              <div className="medicine-workflow-top">
                <span className="medicine-workflow-number">01</span>
                <span className="medicine-workflow-arrow">↗</span>
              </div>

              <div className="medicine-workflow-symbol">
                <span>D→C</span>
                <i />
              </div>

              <div className="medicine-workflow-content">
                <span className="medicine-workflow-kicker">
                  VIRTUAL DISEASE MODEL
                </span>

                <h3>Virtual Disease Simulation</h3>

                <p>
                  Start from a healthy cellular state, apply a disease
                  condition, and visualize how biological structure and
                  behavior change inside the virtual model.
                </p>
              </div>

              <div className="medicine-workflow-footer">
                <span>HEALTHY → DISEASE → CELL</span>
                <b>SIMULATE</b>
              </div>
            </a>

            <a
              href="/domains/medicine/treatment-simulation"
              className="medicine-workflow-card"
            >
              <div className="medicine-workflow-top">
                <span className="medicine-workflow-number">02</span>
                <span className="medicine-workflow-arrow">↗</span>
              </div>

              <div className="medicine-workflow-symbol">
                <span>T→R</span>
                <i />
              </div>

              <div className="medicine-workflow-content">
                <span className="medicine-workflow-kicker">
                  INTERVENTION MODEL
                </span>

                <h3>Treatment Simulation</h3>

                <p>
                  Apply a medicine or intervention to a modeled disease state
                  and visualize target pathways, cellular effects, and the
                  resulting simulated response.
                </p>
              </div>

              <div className="medicine-workflow-footer">
                <span>DISEASE → TARGET → RESPONSE</span>
                <b>MODEL</b>
              </div>
            </a>

            <a
              href="/domains/medicine/combination-treatment"
              className="medicine-workflow-card"
            >
              <div className="medicine-workflow-top">
                <span className="medicine-workflow-number">03</span>
                <span className="medicine-workflow-arrow">↗</span>
              </div>

              <div className="medicine-workflow-symbol">
                <span>T1+T2</span>
                <i />
              </div>

              <div className="medicine-workflow-content">
                <span className="medicine-workflow-kicker">
                  COMBINATION SIMULATION
                </span>

                <h3>Combination Treatment Simulator</h3>

                <p>
                  Compare T1, T2, and T1+T2 inside a virtual biological model
                  to explore differences in modeled pathways and cellular
                  responses using connected evidence.
                </p>
              </div>

              <div className="medicine-workflow-footer">
                <span>T1 → T2 → T1+T2</span>
                <b>COMPARE</b>
              </div>
            </a>

          </div>

          <div className="medicine-workflows-bottom">
            <div>
              <span>DISEASE</span>
              <i />
              <span>VIRTUAL CELL</span>
              <i />
              <span>TREATMENT</span>
              <i />
              <strong>SIMULATED RESPONSE</strong>
            </div>

            <p>
              One biological model. Three ways to simulate.
            </p>
          </div>

        </div>
      </section>

    </main>
  );
}
