"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./biotechnology.css";

type Pose = "left" | "center" | "right";

const areas = [
  {
    no: "01",
    title: "Genomics",
    text: "Explore genes, variants and genomic relationships to understand biological systems at molecular resolution.",
    href: "/domains/biotechnology/genomics",
  },
  {
    no: "02",
    title: "Proteomics",
    text: "Connect proteins with their functions, interactions and biological context across complex molecular systems.",
    href: "/domains/biotechnology/proteomics",
  },
  {
    no: "03",
    title: "Cellular Biology",
    text: "Study biological activity at the cellular level and connect molecular signals with cellular behaviour.",
    href: "/domains/biotechnology/cellular-biology",
  },
  {
    no: "04",
    title: "Molecular Systems",
    text: "Move beyond isolated entities by connecting genes, proteins, pathways, diseases and therapeutic context.",
    href: "/domains/biotechnology/molecular-systems",
  },
];

const workflow = [
  ["01", "BIOLOGICAL QUERY", "Define the biological entity or question."],
  ["02", "MOLECULAR ANALYSIS", "Resolve genes, proteins and molecular relationships."],
  ["03", "SYSTEM CONTEXT", "Connect individual signals to wider biological systems."],
  ["04", "RESEARCH INTELLIGENCE", "Bring the evidence together into an interpretable view."],
];

export default function BiotechnologyPage() {
  const [pose, setPose] = useState<Pose>("center");

  useEffect(() => {
    const move = (event: MouseEvent) => {
      const x = event.clientX / window.innerWidth;

      if (x < 0.34) setPose("left");
      else if (x > 0.66) setPose("right");
      else setPose("center");
    };

    window.addEventListener("mousemove", move);

    return () => window.removeEventListener("mousemove", move);
  }, []);

  const character =
    pose === "left"
      ? "/research/research-character-left.png"
      : pose === "right"
        ? "/research/research-character-right.png"
        : "/research/research-character-center.png";

  return (
    <div className="cv-bio-page">
      <Navbar />

      <main>
        <section className="cv-bio-hero">
          <div className="cv-bio-grid" />

          <div className="cv-bio-hero-inner">
            <div className="cv-bio-copy">
              <span className="cv-bio-index">04 / DOMAIN</span>

              <span className="cv-bio-eyebrow">
                BIOTECHNOLOGY INTELLIGENCE
              </span>

              <h1>
                Biology,
                <br />
                <em>decoded.</em>
              </h1>

              <p>
                Connect genes, proteins, cells and biological systems through
                one intelligent research environment built for modern
                biological discovery.
              </p>

              <div className="cv-bio-actions">
                <Link href="/domains/biotechnology/manual">
                  Explore Biotechnology
                </Link>

                <a href="#systems">
                  Discover the system ↓
                </a>
              </div>
            </div>

            <div className={`cv-bio-character cv-bio-character-${pose}`}>
              <div className="cv-bio-character-aura" />

              <img
                src={character}
                alt="CureVerseAI biotechnology researcher"
                draggable={false}
              />

              <div className="cv-bio-character-label">
                <span>BIOTECHNOLOGY INTELLIGENCE</span>
                <i />
              </div>
            </div>
          </div>

          <div className="cv-bio-scroll">
            <span>SCROLL TO EXPLORE</span>
            <i />
          </div>
        </section>

        <section className="cv-bio-intro" id="systems">
          <div className="cv-bio-section-number">01</div>

          <div className="cv-bio-intro-content">
            <span className="cv-bio-kicker">THE BIOLOGICAL SYSTEM</span>

            <h2>
              From individual signals
              <br />
              <em>to connected biology.</em>
            </h2>

            <p>
              Biology does not operate as isolated pieces. Genes influence
              proteins, proteins participate in pathways, pathways shape
              cellular behaviour, and those systems form the biological
              context behind disease and therapeutic research.
            </p>

            <div className="cv-bio-flow">
              <div>
                <b>GENES</b>
                <span>Genomic information</span>
              </div>

              <i>→</i>

              <div>
                <b>PROTEINS</b>
                <span>Molecular function</span>
              </div>

              <i>→</i>

              <div>
                <b>CELLS</b>
                <span>Cellular state</span>
              </div>

              <i>→</i>

              <div>
                <b>SYSTEMS</b>
                <span>Biological context</span>
              </div>
            </div>
          </div>
        </section>

        <section className="cv-bio-areas">
          <div className="cv-bio-section-head">
            <div>
              <span className="cv-bio-kicker">WHAT CURVERSEAI EXPLORES</span>
              <h2>Four layers of biological intelligence.</h2>
            </div>

            <p>
              A connected research perspective across molecular and cellular
              biology.
            </p>
          </div>

          <div className="cv-bio-area-grid">
            {areas.map((area) => (
              <Link
                key={area.no}
                href={area.href}
                className="cv-bio-area-card"
              >
                <span>{area.no}</span>
                <h3>{area.title}</h3>
                <p>{area.text}</p>
                <i>↗</i>
              </Link>
            ))}
          </div>
        </section>

        <section className="cv-bio-workflow">
          <div className="cv-bio-workflow-left">
            <span className="cv-bio-kicker">FROM SIGNAL TO SYSTEM</span>

            <h2>
              A research workflow
              <br />
              built around biology.
            </h2>

            <p>
              CureVerseAI transforms a biological question into a structured
              research journey — moving from entity resolution to molecular
              context and connected biological intelligence.
            </p>
          </div>

          <div className="cv-bio-workflow-right">
            {workflow.map(([no, title, text]) => (
              <div className="cv-bio-step" key={no}>
                <span>{no}</span>

                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>

                <b>+</b>
              </div>
            ))}
          </div>
        </section>

        <section className="cv-bio-intelligence">
          <div className="cv-bio-intelligence-inner">
            <div>
              <span className="cv-bio-kicker">SCIENTIFIC INTELLIGENCE</span>

              <h2>
                See the biology
                <br />
                <em>behind the signal.</em>
              </h2>
            </div>

            <div className="cv-bio-intelligence-grid">
              <div>
                <span>01</span>
                <strong>GENOMIC CONTEXT</strong>
                <p>Genes, variants and molecular identity.</p>
              </div>

              <div>
                <span>02</span>
                <strong>PROTEIN FUNCTION</strong>
                <p>Protein identity and biological function.</p>
              </div>

              <div>
                <span>03</span>
                <strong>CELLULAR STATE</strong>
                <p>Biological activity at the cellular level.</p>
              </div>

              <div>
                <span>04</span>
                <strong>RELATIONSHIPS</strong>
                <p>Connections between biological entities.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="cv-bio-cta">
          <span className="cv-bio-kicker">
            CURVERSEAI / BIOTECHNOLOGY
          </span>

          <h2>
            Explore biology
            <br />
            as a connected system.
          </h2>

          <Link href="/domains/biotechnology/manual">
            Enter Biotechnology →
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
