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
            Explore genes, proteins, variants, pathways and scientific
            evidence through one connected biological intelligence system.
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

        <div
          className={`cv-research-character cv-research-character-${pose}`}
        >
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

      <section id="research-manual" className="cv-research-next">
        <div className="cv-research-next-kicker">
          <span>02</span>
          RESEARCH MANUAL
        </div>

        <h2>
          Start with a question.
          <br />
          <em>Follow the evidence.</em>
        </h2>

        <p>
          Learn how CureVerseAI turns a biological input into a connected,
          evidence-aware research result.
        </p>
      </section>
    </main>
  );
}
