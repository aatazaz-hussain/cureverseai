"use client";

type CharacterPose = "left" | "center" | "right";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./medicine.css";

const useCases = [
  {
    number: "01",
    title: "Clinical Profile",
    label: "PATIENT × BIOLOGY",
    description:
      "Connect clinical context with molecular and biological signals to build a structured patient-level interpretation.",
    href: "/domains/medicine/clinical-profile",
  },
  {
    number: "02",
    title: "Disease Intelligence",
    label: "DISEASE × EVIDENCE",
    description:
      "Explore disease mechanisms, biological associations, pathways and supporting evidence in one connected view.",
    href: "/domains/medicine/disease-intelligence",
  },
  {
    number: "03",
    title: "Treatment Context",
    label: "THERAPY × BIOLOGY",
    description:
      "Understand therapeutic context through targets, mechanisms, compounds and available scientific evidence.",
    href: "/domains/medicine/treatment-context",
  },
  {
    number: "04",
    title: "Variant Interpretation",
    label: "VARIANT × FUNCTION",
    description:
      "Move from a genetic variant toward functional, biological and disease-context evidence.",
    href: "/domains/medicine/variant-interpretation",
  },
];

const signals = [
  ["01", "PATIENT", "Clinical context becomes structured biological information."],
  ["02", "DISEASE", "Disease mechanisms connect with pathways and molecular systems."],
  ["03", "THERAPY", "Treatment context is interpreted through biological evidence."],
  ["04", "EVIDENCE", "Every conclusion remains connected to its underlying signals."],
];

export default function MedicinePage() {
  const [mouse, setMouse] = useState({ x: 50, y: 50 });
  const [pose, setPose] = useState<CharacterPose>("center");
  const [active, setActive] = useState(0);

  useEffect(() => {
    const move = (event: MouseEvent) => {
      const x = event.clientX / window.innerWidth;
      const y = event.clientY / window.innerHeight;

      setMouse({
        x: x * 100,
        y: y * 100,
      });

      if (x < 0.34) {
        setPose("left");
      } else if (x > 0.66) {
        setPose("right");
      } else {
        setPose("center");
      }
    };

    window.addEventListener("mousemove", move);
    return () => window.removeEventListener("mousemove", move);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % signals.length);
    }, 3200);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="cv-medicine-page">
      <Navbar />

      <main>
        {/* =====================================================
            HERO
        ===================================================== */}
        <section className="cv-med-hero">
          <div
            className="cv-med-cursor-glow"
            style={{
              left: `${mouse.x}%`,
              top: `${mouse.y}%`,
            }}
          />

          <div className="cv-med-grid" />

          <div className="cv-med-hero-copy">
            <div className="cv-med-index">03 / 05</div>

            <div className="cv-med-eyebrow">
              CUREVERSEAI / MEDICINE
            </div>

            <h1>
              Medicine,
              <br />
              <span>seen through biology.</span>
            </h1>

            <p>
              Connect clinical context, disease mechanisms, molecular
              information and therapeutic evidence inside one scientific
              intelligence layer.
            </p>

            <div className="cv-med-actions">
              <Link href="/domains/medicine/clinical-profile">
                EXPLORE MEDICAL INTELLIGENCE ↗
              </Link>

              <Link href="/domains/medicine/manual">
                READ THE MEDICINE MANUAL
              </Link>
            </div>
          </div>

          <div className="cv-med-hero-visual">
            <div
              className={`cv-med-character cv-med-character-${pose}`}
              style={{
                transform: `translate3d(
                  ${(mouse.x - 50) / 9}px,
                  ${(mouse.y - 50) / 14}px,
                  0
                )`,
              }}
            >
              <div className="cv-med-character-aura" />

              <img
                src={
                  pose === "left"
                    ? "/research/research-character-left.png"
                    : pose === "right"
                      ? "/research/research-character-right.png"
                      : "/research/research-character-center.png"
                }
                alt="CureVerseAI medical intelligence researcher"
                className="cv-med-character-image"
                draggable={false}
              />

              <div className="cv-med-character-label">
                <span>MEDICAL INTELLIGENCE</span>
                <i />
              </div>
            </div>

            <div className="cv-med-hud hud-a">
              <span>BIOMARKER</span>
              <b>ACTIVE</b>
            </div>

            <div className="cv-med-hud hud-b">
              <span>MOLECULAR CONTEXT</span>
              <b>CONNECTED</b>
            </div>

            <div className="cv-med-hud hud-c">
              <span>EVIDENCE</span>
              <b>TRACEABLE</b>
            </div>

            <div className="cv-med-crosshair" />
          </div>

          <div className="cv-med-hero-foot">
            <span>SCIENTIFIC MEDICINE INTELLIGENCE</span>
            <span>01 — 04</span>
          </div>
        </section>

        {/* =====================================================
            INTRO
        ===================================================== */}
        <section className="cv-med-intro">
          <div className="cv-med-section-no">01</div>

          <div className="cv-med-intro-title">
            <div className="cv-med-eyebrow">THE MEDICAL LAYER</div>

            <h2>
              Clinical questions
              <br />
              <span>begin with context.</span>
            </h2>
          </div>

          <div className="cv-med-intro-copy">
            <p>
              Medicine does not exist as an isolated dataset. A patient,
              disease, molecular target, treatment and genetic variant are
              connected parts of the same biological system.
            </p>

            <p>
              CureVerseAI brings these signals together so medical reasoning
              can move between clinical context and underlying biology without
              losing the evidence trail.
            </p>

            <div className="cv-med-rule">
              <span />
              <b>CONTEXT → BIOLOGY → EVIDENCE</b>
            </div>
          </div>
        </section>

        {/* =====================================================
            SIGNAL SYSTEM
        ===================================================== */}
        <section className="cv-med-signals">
          <div className="cv-med-section-header">
            <div>
              <span className="cv-med-eyebrow">CONNECTED SIGNALS</span>
              <h2>
                Four layers.
                <span> One medical picture.</span>
              </h2>
            </div>

            <div className="cv-med-live">
              <i />
              LIVE SYSTEM MAP
            </div>
          </div>

          <div className="cv-med-signal-layout">
            <div className="cv-med-signal-orbit">
              <div className="cv-med-orbit orbit-1" />
              <div className="cv-med-orbit orbit-2" />
              <div className="cv-med-orbit orbit-3" />

              <div className="cv-med-orbit-core">
                <span>CV</span>
                MEDICINE
              </div>

              {signals.map(([number, title], index) => (
                <button
                  key={title}
                  className={`cv-med-signal-dot dot-${index} ${
                    active === index ? "active" : ""
                  }`}
                  onClick={() => setActive(index)}
                >
                  {number}
                </button>
              ))}
            </div>

            <div className="cv-med-signal-copy">
              <div className="cv-med-signal-number">
                {signals[active][0]}
              </div>

              <div className="cv-med-eyebrow">
                {signals[active][1]}
              </div>

              <h3>
                {signals[active][2]}
              </h3>

              <div className="cv-med-signal-meter">
                <span />
              </div>

              <p>
                Move across medical evidence while retaining the biological
                context behind each signal.
              </p>
            </div>
          </div>
        </section>

        {/* =====================================================
            USE CASES
        ===================================================== */}
        <section className="cv-med-usecases">
          <div className="cv-med-section-header">
            <div>
              <span className="cv-med-eyebrow">MEDICAL WORKBENCH</span>
              <h2>
                From question
                <span> to interpretation.</span>
              </h2>
            </div>

            <div className="cv-med-section-tag">04 WORKFLOWS</div>
          </div>

          <div className="cv-med-usecase-grid">
            {useCases.map((item, index) => (
              <Link
                href={item.href}
                className="cv-med-usecase"
                key={item.number}
              >
                <div className="cv-med-usecase-top">
                  <span>{item.number}</span>
                  <em>{item.label}</em>
                </div>

                <div className="cv-med-usecase-art">
                  <div className={`med-art med-art-${index + 1}`}>
                    <i />
                    <i />
                    <i />
                    <b />
                  </div>
                </div>

                <h3>{item.title}</h3>

                <p>{item.description}</p>

                <div className="cv-med-usecase-bottom">
                  OPEN WORKFLOW <span>↗</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* =====================================================
            MEDICAL PIPELINE
        ===================================================== */}
        <section className="cv-med-pipeline">
          <div className="cv-med-section-no">04</div>

          <div className="cv-med-pipeline-title">
            <div className="cv-med-eyebrow">THE MEDICAL PIPELINE</div>
            <h2>
              Ask the question.
              <br />
              <span>Follow the biology.</span>
            </h2>
          </div>

          <div className="cv-med-pipeline-track">
            <div className="cv-med-pipeline-line">
              <i />
            </div>

            {[
              ["01", "QUESTION", "Clinical or biological question"],
              ["02", "CONTEXT", "Patient and disease context"],
              ["03", "BIOLOGY", "Genes, proteins and pathways"],
              ["04", "EVIDENCE", "Research and therapeutic evidence"],
              ["05", "INTERPRET", "Structured scientific view"],
            ].map(([number, title, description]) => (
              <article key={number}>
                <div className="cv-med-pipeline-dot">{number}</div>
                <small>{title}</small>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* =====================================================
            MANUAL CTA
        ===================================================== */}
        <section className="cv-med-manual">
          <div className="cv-med-manual-glow" />

          <div className="cv-med-eyebrow">MEDICINE MANUAL</div>

          <h2>
            A medical question
            <br />
            <span>deserves the whole picture.</span>
          </h2>

          <p>
            Learn how CureVerseAI connects patient context, disease biology,
            molecular information and evidence into one medical intelligence
            workflow.
          </p>

          <Link href="/domains/medicine/manual">
            OPEN MEDICINE MANUAL ↗
          </Link>
        </section>

        {/* =====================================================
            FINAL
        ===================================================== */}
        <section className="cv-med-final">
          <div>
            <span className="cv-med-eyebrow">CUREVERSEAI / MEDICINE</span>

            <h2>
              See medicine
              <br />
              <span>as a connected system.</span>
            </h2>
          </div>

          <Link href="/domains/medicine/clinical-profile">
            ENTER MEDICAL INTELLIGENCE ↗
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
