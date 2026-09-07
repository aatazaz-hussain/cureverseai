"use client";

import { MouseEvent, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./education.css";

type HeroState = "left" | "center" | "right";

const heroCharacters = {
  left: "/research/research-character-left.png",
  center: "/research/research-character-center.png",
  right: "/research/research-character-right.png",
};

const learningCards = [
  {
    number: "01",
    eyebrow: "ARTICLE LEARNING",
    title: "Explore Biology Through Ideas.",
    description:
      "Read focused learning articles on virtual cells, genes, proteins, pathways, biological intelligence, and the technologies shaping modern life science.",
    href: "/domains/education/articles",
    tag: "READ & UNDERSTAND",
    icon: "↗",
  },
  {
    number: "02",
    eyebrow: "BOOKS & REFERENCES",
    title: "Go Deeper Into the Science.",
    description:
      "Discover curated books and references across molecular biology, genetics, systems biology, computational biology, drug development, and AI.",
    href: "/domains/education/books",
    tag: "EXPLORE REFERENCES",
    icon: "↗",
  },
  {
    number: "03",
    eyebrow: "VIDEO LEARNING",
    title: "See Biology in Motion.",
    description:
      "Learn through curated video collections covering virtual cells, biology, AI, CureVerseAI technologies, drug discovery, and biotechnology.",
    href: "/domains/education/videos",
    tag: "WATCH PLAYLISTS",
    icon: "▶",
  },
  {
    number: "04",
    eyebrow: "CUREVERSE CHAT",
    title: "Ask. Explore. Understand.",
    description:
      "Talk with the CureVerseAI learning assistant about biology, genes, proteins, pathways, cells, medicine, biotechnology, and the platform itself.",
    href: "/domains/education/chat",
    tag: "START LEARNING",
    icon: "✦",
  },
];

const domains = [
  {
    number: "01",
    title: "Research",
    text: "Investigate genes, proteins, variants, pathways, and biological evidence.",
    href: "/domains/research",
  },
  {
    number: "02",
    title: "Drug Development",
    text: "Explore the evidence connecting biological targets, compounds, and therapeutic research.",
    href: "/domains/drug-development",
  },
  {
    number: "03",
    title: "Medicine",
    text: "Connect biological intelligence with medical understanding and decision support.",
    href: "/domains/medicine",
  },
  {
    number: "04",
    title: "Biotechnology",
    text: "Understand biological systems, engineering approaches, and emerging technologies.",
    href: "/domains/biotechnology",
  },
  {
    number: "05",
    title: "Education",
    text: "Turn complex biological knowledge into something people can explore and understand.",
    href: "/domains/education",
  },
];

export default function EducationPage() {
  const [heroState, setHeroState] = useState<HeroState>("center");

  function handleHeroMove(event: MouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const ratio = x / rect.width;

    if (ratio < 0.34) {
      setHeroState("left");
    } else if (ratio > 0.66) {
      setHeroState("right");
    } else {
      setHeroState("center");
    }
  }

  return (
    <main className="cv-education-page">
      <Navbar />

      {/* HERO */}
      <section
        className={`cv-education-hero cv-hero-${heroState}`}
        onMouseMove={handleHeroMove}
        onMouseLeave={() => setHeroState("center")}
      >
        <div className="cv-education-hero-grid" />
        <div className="cv-education-glow cv-education-glow-a" />
        <div className="cv-education-glow cv-education-glow-b" />

        <div className="cv-education-hero-copy">
          <div className="cv-eyebrow">
            05 / EDUCATION INTELLIGENCE
          </div>

          <h1>
            Learn Biology.
            <br />
            <span>Understand Life.</span>
          </h1>

          <p>
            A learning environment built around the biology,
            technologies, and intelligence behind CureVerseAI.
            Explore ideas, follow scientific concepts, watch,
            read, and ask questions.
          </p>

          <div className="cv-education-hero-meta">
            <span>VIRTUAL CELL</span>
            <span>BIOLOGY</span>
            <span>AI</span>
            <span>KNOWLEDGE</span>
          </div>
        </div>

        <div className="cv-education-character-stage">
          <div className="cv-character-aura" />

          <img
            src={heroCharacters[heroState]}
            alt="CureVerseAI education scientist"
            className="cv-education-character"
          />

          <div className="cv-character-orbit cv-character-orbit-a" />
          <div className="cv-character-orbit cv-character-orbit-b" />

          <div className="cv-bio-node cv-bio-node-a">DNA</div>
          <div className="cv-bio-node cv-bio-node-b">CELL</div>
          <div className="cv-bio-node cv-bio-node-c">AI</div>
        </div>

        <div className="cv-education-hero-bottom">
          <div>
            <span>CURSOR INTERACTION</span>
            <strong>
              {heroState === "left"
                ? "EXPLORE LEFT"
                : heroState === "right"
                  ? "EXPLORE RIGHT"
                  : "EXPLORE"}
            </strong>
          </div>

          <div className="cv-cursor-line">
            <i />
          </div>

          <div className="cv-hero-index">
            <span>01</span>
            <span>03</span>
          </div>
        </div>
      </section>

      {/* LEARNING PATHWAYS */}
      <section className="cv-education-section cv-learning-section">
        <div className="cv-education-section-heading">
          <div className="cv-section-number">01</div>

          <div>
            <div className="cv-eyebrow">
              LEARNING PATHWAYS
            </div>

            <h2>
              Choose how you want
              <br />
              <span>to learn.</span>
            </h2>

            <p>
              Move from reading to watching to asking.
              CureVerseAI Education brings different ways
              of learning biological science into one
              connected environment.
            </p>
          </div>
        </div>

        <div className="cv-learning-grid">
          {learningCards.map((card) => (
            <Link
              href={card.href}
              className="cv-learning-card"
              key={card.number}
            >
              <div className="cv-learning-card-top">
                <span>{card.number}</span>
                <b>{card.icon}</b>
              </div>

              <div className="cv-card-scan" />

              <div className="cv-card-content">
                <div className="cv-card-label">
                  {card.eyebrow}
                </div>

                <h3>{card.title}</h3>

                <p>{card.description}</p>
              </div>

              <div className="cv-learning-card-footer">
                <span>{card.tag}</span>
                <strong>↗</strong>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* VIRTUAL CELL */}
      <section className="cv-education-section cv-virtual-cell-section">
        <div className="cv-virtual-cell-visual">
          <div className="cv-cell-ring cv-cell-ring-a" />
          <div className="cv-cell-ring cv-cell-ring-b" />
          <div className="cv-cell-ring cv-cell-ring-c" />

          <div className="cv-cell-core">
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="cv-cell-label cv-cell-label-a">
            GENES
          </div>

          <div className="cv-cell-label cv-cell-label-b">
            PROTEINS
          </div>

          <div className="cv-cell-label cv-cell-label-c">
            CELL STATE
          </div>
        </div>

        <div className="cv-virtual-cell-copy">
          <div className="cv-section-number">02</div>

          <div className="cv-eyebrow">
            THE VIRTUAL CELL
          </div>

          <h2>
            From biological
            <br />
            <span>systems to intelligence.</span>
          </h2>

          <p>
            The cell is where many of biology&apos;s most
            important stories come together. Genes encode
            information. Proteins perform functions.
            Pathways connect processes. Cellular states
            respond to change.
          </p>

          <p>
            Education is where we make these relationships
            understandable — before turning them into
            computational intelligence.
          </p>

          <Link
            href="/domains/education/articles"
            className="cv-text-link"
          >
            EXPLORE VIRTUAL CELL LEARNING
            <span>↗</span>
          </Link>
        </div>
      </section>

      {/* DOMAINS */}
      <section className="cv-education-section cv-domains-section">
        <div className="cv-education-section-heading">
          <div className="cv-section-number">03</div>

          <div>
            <div className="cv-eyebrow">
              THE CUREVERSEAI ECOSYSTEM
            </div>

            <h2>
              One platform.
              <br />
              <span>Five biological worlds.</span>
            </h2>

            <p>
              Education connects the knowledge layer to
              every domain of CureVerseAI.
            </p>
          </div>
        </div>

        <div className="cv-domain-grid">
          {domains.map((domain) => (
            <Link
              href={domain.href}
              className="cv-domain-card"
              key={domain.number}
            >
              <div className="cv-domain-number">
                {domain.number}
              </div>

              <div>
                <h3>{domain.title}</h3>
                <p>{domain.text}</p>
              </div>

              <span>↗</span>
            </Link>
          ))}
        </div>
      </section>

      {/* CLOSING */}
      <section className="cv-education-closing">
        <div className="cv-closing-grid" />

        <div className="cv-eyebrow">
          KNOWLEDGE / BIOLOGY / TOMORROW
        </div>

        <h2>
          Understand the science.
          <br />
          <span>Shape what comes next.</span>
        </h2>

        <p>
          CureVerseAI Education is where curiosity becomes
          biological understanding.
        </p>

        <Link
          href="/domains/education/chat"
          className="cv-closing-button"
        >
          ASK CUREVERSE AI
          <span>↗</span>
        </Link>
      </section>

      <Footer />
    </main>
  );
}
