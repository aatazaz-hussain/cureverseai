"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./drug-development.css";

const useCases = [
  {
    number: "01",
    label: "TARGET DISCOVERY",
    title: "Find the biology worth pursuing.",
    text: "Explore biological targets through disease relationships, pathway context and supporting evidence.",
    href: "/domains/drug_development/target-discovery",
  },
  {
    number: "02",
    label: "COMPOUND INTELLIGENCE",
    title: "Understand the molecule.",
    text: "Investigate compounds through molecular identity, activity signals and development context.",
    href: "/domains/drug_development/compound-intelligence",
  },
  {
    number: "03",
    label: "TARGET × DRUG",
    title: "Connect targets with compounds.",
    text: "Trace relationships between biological targets and molecules across the drug-development landscape.",
    href: "/domains/drug_development/target-drug-analysis",
  },
  {
    number: "04",
    label: "DEVELOPMENT EVIDENCE",
    title: "Bring the evidence together.",
    text: "Read biological, disease and experimental evidence as connected layers of a development decision.",
    href: "/domains/drug_development/evidence",
  },
];

const ecosystem = [
  ["RESEARCH", "Biological discovery"],
  ["DRUG DEVELOPMENT", "Target to compound"],
  ["MEDICINE", "Clinical understanding"],
  ["BIOTECHNOLOGY", "Engineering biology"],
  ["EDUCATION", "Scientific intelligence"],
];

export default function DrugDevelopmentPage() {
  const [character, setCharacter] = useState<
    "left" | "center" | "right"
  >("center");

  return (
    <main className="cv-drug-page">
      <Navbar />

      <section
        className="cv-drug-hero"
        onMouseMove={(event) => {
          const x = event.clientX / window.innerWidth;

          if (x < 0.34) setCharacter("left");
          else if (x > 0.66) setCharacter("right");
          else setCharacter("center");
        }}
      >
        <div className="cv-drug-grid" />
        <div className="cv-drug-glow" />

        <div className="cv-drug-particles">
          {Array.from({ length: 22 }).map((_, i) => (
            <span key={i} style={{ "--i": i } as React.CSSProperties} />
          ))}
        </div>

        <div className="cv-drug-hero-copy">
          <div className="cv-eyebrow">01 / DRUG DEVELOPMENT</div>

          <h1>
            From biological
            <span>target to therapy.</span>
          </h1>

          <p>
            Connect target biology, molecular intelligence, disease
            context and experimental evidence across the drug-development
            journey.
          </p>

          <div className="cv-drug-hero-actions">
            <Link href="/domains/drug_development/manual">
              EXPLORE THE GUIDE <span>↗</span>
            </Link>

            <a href="#use-cases">
              EXPLORE USE CASES <span>↓</span>
            </a>
          </div>

          <div className="cv-drug-metrics">
            <div>
              <strong>04</strong>
              <span>WORKFLOWS</span>
            </div>
            <div>
              <strong>06</strong>
              <span>EVIDENCE LAYERS</span>
            </div>
            <div>
              <strong>∞</strong>
              <span>DEVELOPMENT PATHS</span>
            </div>
          </div>
        </div>

        <div className={`cv-drug-character cv-character-${character}`}>
          <div className="cv-character-halo" />

          <Image
            src={
              character === "left"
                ? "/research/research-character-left.png"
                : character === "right"
                  ? "/research/research-character-right.png"
                  : "/research/research-character-center.png"
            }
            alt="CureVerseAI drug development scientist"
            fill
            priority
            sizes="(max-width: 900px) 70vw, 45vw"
          />

          <div className="cv-character-scan" />
        </div>

        <div className="cv-drug-floating-card card-target">
          <span>TARGET</span>
          <strong>IDENTIFY</strong>
          <small>Biological signal</small>
        </div>

        <div className="cv-drug-floating-card card-compound">
          <span>COMPOUND</span>
          <strong>EVALUATE</strong>
          <small>Molecular activity</small>
        </div>

        <div className="cv-drug-floating-card card-evidence">
          <span>EVIDENCE</span>
          <strong>CONNECT</strong>
          <small>Development context</small>
        </div>
      </section>

      <section className="cv-drug-guide">
        <div className="cv-section-number">02</div>

        <div className="cv-drug-guide-grid">
          <div className="cv-drug-guide-image">
            <Image
              src="/research/research-guide.png"
              alt="Biological research visualization"
              fill
              sizes="(max-width: 900px) 100vw, 45vw"
            />
            <div className="cv-guide-image-overlay" />

            <div className="cv-guide-readout">
              <span>DEVELOPMENT ENGINE</span>
              <strong>TARGET → COMPOUND → EVIDENCE</strong>
            </div>
          </div>

          <div className="cv-drug-guide-copy">
            <div className="cv-eyebrow">DRUG DEVELOPMENT GUIDE</div>

            <h2>
              Understand the journey
              <span>before making the decision.</span>
            </h2>

            <p>
              Drug development is a connected biological problem. A
              promising molecule means little without understanding its
              target, mechanism, disease context and experimental evidence.
            </p>

            <p>
              CureVerseAI organizes these relationships into an
              investigation workflow designed to move from biological
              discovery toward development intelligence.
            </p>

            <Link href="/domains/drug_development/manual">
              READ THE DEVELOPMENT GUIDE <span>→</span>
            </Link>
          </div>
        </div>
      </section>

      <section id="use-cases" className="cv-drug-usecases">
        <div className="cv-section-number">03</div>

        <div className="cv-drug-heading">
          <div>
            <div className="cv-eyebrow">DEVELOPMENT WORKBENCH</div>

            <h2>
              Four routes
              <span>from biology to development.</span>
            </h2>
          </div>

          <p>
            Explore targets, compounds, relationships and evidence through
            focused drug-development workflows.
          </p>
        </div>

        <div className="cv-drug-usecase-grid">
          {useCases.map((item) => (
            <Link
              href={item.href}
              className="cv-drug-usecase-card"
              key={item.number}
            >
              <div className="cv-usecase-top">
                <span>{item.number}</span>
                <i>↗</i>
              </div>

              <div className="cv-usecase-line" />

              <div className="cv-usecase-label">{item.label}</div>

              <h3>{item.title}</h3>

              <p>{item.text}</p>

              <div className="cv-usecase-open">
                OPEN WORKBENCH
                <span>→</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="cv-drug-pipeline">
        <div className="cv-section-number">04</div>

        <div className="cv-drug-heading">
          <div>
            <div className="cv-eyebrow">THE DEVELOPMENT SYSTEM</div>

            <h2>
              One connected
              <span>development landscape.</span>
            </h2>
          </div>
        </div>

        <div className="cv-development-pipeline">
          {[
            ["01", "TARGET", "Find biological opportunity"],
            ["02", "MECHANISM", "Understand the biology"],
            ["03", "COMPOUND", "Explore molecular candidates"],
            ["04", "ACTIVITY", "Read experimental signals"],
            ["05", "DISEASE", "Connect therapeutic context"],
            ["06", "EVIDENCE", "Support development reasoning"],
          ].map(([number, title, text], index) => (
            <div className="cv-development-step" key={number}>
              <span>{number}</span>
              <div className="cv-development-dot" />
              <strong>{title}</strong>
              <p>{text}</p>

              {index < 5 && <i>→</i>}
            </div>
          ))}
        </div>
      </section>

      <section className="cv-drug-ecosystem">
        <div className="cv-section-number">05</div>

        <div className="cv-drug-ecosystem-heading">
          <div className="cv-eyebrow">CONNECTED CUREVERSEAI</div>

          <h2>
            Development does not
            <span>exist in isolation.</span>
          </h2>

          <p>
            Drug development sits between biological discovery, medicine,
            biotechnology and scientific education.
          </p>
        </div>

        <div className="cv-ecosystem-grid">
          {ecosystem.map(([name, description], index) => (
            <div
              className={`cv-ecosystem-card ${
                name === "DRUG DEVELOPMENT" ? "active" : ""
              }`}
              key={name}
            >
              <span>0{index + 1}</span>
              <strong>{name}</strong>
              <small>{description}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="cv-drug-final">
        <div className="cv-drug-final-glow" />

        <div className="cv-section-number">06</div>

        <div className="cv-drug-final-copy">
          <div className="cv-eyebrow">BEGIN DEVELOPMENT INTELLIGENCE</div>

          <h2>
            Discover the target.
            <span>Understand the molecule.</span>
          </h2>

          <p>
            Move from biological opportunity to evidence-informed
            development intelligence.
          </p>

          <div className="cv-drug-final-actions">
            <Link href="/domains/drug_development/target-discovery">
              TARGET DISCOVERY ↗
            </Link>

            <Link href="/domains/drug_development/compound-intelligence">
              COMPOUND INTELLIGENCE ↗
            </Link>

            <Link href="/domains/drug_development/target-drug-analysis">
              TARGET × DRUG ↗
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
