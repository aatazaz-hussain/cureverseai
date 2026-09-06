"use client";
import Footer from "@/components/Footer";

import Navbar from "@/components/Navbar";

import { useEffect, useMemo, useState } from "react";

const domains = [
  {
    id: "research",
    number: "01",
    title: "Research",
    short: "Decode",
    description:
      "Explore genes, proteins, pathways, variants and biological evidence through an intelligent research layer.",
    color: "red",
  },
  {
    id: "drug_development",
    number: "02",
    title: "Drug Development",
    short: "Discover",
    description:
      "Connect targets, compounds, bioactivity and evidence to accelerate the path from biology to therapeutics.",
    color: "gold",
  },
  {
    id: "medicine",
    number: "03",
    title: "Medicine",
    short: "Understand",
    description:
      "Translate biological intelligence into clinically meaningful insights and decision support.",
    color: "cyan",
  },
  {
    id: "biotechnology",
    number: "04",
    title: "Biotechnology",
    short: "Engineer",
    description:
      "Turn biological knowledge into actionable biotechnology workflows and discoveries.",
    color: "violet",
  },
  {
    id: "education",
    number: "05",
    title: "Education",
    short: "Learn",
    description:
      "Make complex biological science easier to understand through intelligent exploration and guided learning.",
    color: "cream",
  },
];

export default function Home() {
  const [cursor, setCursor] = useState({ x: 0, y: 0 });
  const [scroll, setScroll] = useState(0);
  const [activeDomain, setActiveDomain] = useState(0);
  const [teamFormation, setTeamFormation] = useState<
    "default" | "left" | "right"
  >("default");

  useEffect(() => {
    const handlePointer = (event: MouseEvent) => {
      const normalizedX =
        (event.clientX / window.innerWidth - 0.5) * 2;

      setCursor({
        x: normalizedX,
        y: (event.clientY / window.innerHeight - 0.5) * 2,
      });

      if (normalizedX < -0.22) {
        setTeamFormation("left");
      } else if (normalizedX > 0.22) {
        setTeamFormation("right");
      } else {
        setTeamFormation("default");
      }
    };

    const handleScroll = () => {
      const max =
        document.documentElement.scrollHeight - window.innerHeight;

      setScroll(max > 0 ? window.scrollY / max : 0);
    };

    window.addEventListener("mousemove", handlePointer);
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("mousemove", handlePointer);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const active = domains[activeDomain];

  const particles = useMemo(
    () =>
      Array.from({ length: 26 }, (_, index) => ({
        left: `${8 + ((index * 37) % 84)}%`,
        top: `${8 + ((index * 53) % 82)}%`,
        delay: `${(index % 7) * 0.6}s`,
        duration: `${5 + (index % 5)}s`,
      })),
    []
  );

  return (
    <main className="cv-site">
      {/* =====================================================
          NAVIGATION
      ====================================================== */}
      <Navbar />

      {/* =====================================================
          HERO / CINEMATIC OPENING
      ====================================================== */}
      <section
        className="cv-hero"
        style={
          {
            "--mouse-x": `${cursor.x}`,
            "--mouse-y": `${cursor.y}`,
          } as React.CSSProperties
        }
      >
        <div className="cv-hero-grid" />
        <div className="cv-hero-glow cv-glow-red" />
        <div className="cv-hero-glow cv-glow-cyan" />

        {particles.map((particle, index) => (
          <span
            key={index}
            className="cv-particle"
            style={{
              left: particle.left,
              top: particle.top,
              animationDelay: particle.delay,
              animationDuration: particle.duration,
            }}
          />
        ))}

        <div className="cv-hero-label">
          <span className="cv-live-dot" />
          BIOLOGICAL INTELLIGENCE / 01
        </div>

        <div className="cv-hero-copy">
          <p className="cv-eyebrow">
            SCIENCE × AI × BIOLOGY
          </p>

          <h1>
            <span>DISCOVER</span>
            <span className="cv-outline-word">WHAT&apos;S</span>
            <span>NEXT.</span>
          </h1>

          <p className="cv-hero-description">
            CureVerseAI brings biological data, foundation models and
            scientific evidence together — turning complex biology into
            intelligence you can explore.
          </p>

          <div className="cv-hero-actions">
            <a href="#domains" className="cv-button cv-button-primary">
              Enter the Verse
              <span>→</span>
            </a>

            <a href="#intelligence" className="cv-button cv-button-ghost">
              See Intelligence
            </a>
          </div>
        </div>

        {/* Biological core */}
        <div
          className="cv-bio-core"
          style={{
            transform: `translate3d(${cursor.x * -18}px, ${
              cursor.y * -14
            }px, 0)`,
          }}
        >
          <div className="cv-core-orbit orbit-one" />
          <div className="cv-core-orbit orbit-two" />
          <div className="cv-core-orbit orbit-three" />

          <div className="cv-core-dna">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="cv-core-nucleus">
            <small>CV</small>
            <strong>AI</strong>
          </div>
        </div>

        {/* Independent characters */}
        <div className={`cv-character-field formation-${teamFormation}`}>
          <img
            src="/team/girl-01.png"
            alt="CureVerseAI researcher"
            className="cv-character character-girl-one"
          />

          <img
            src="/team/boy.png"
            alt="CureVerseAI researcher"
            className="cv-character character-boy"
          />

          <img
            src="/team/girl-02.png"
            alt="CureVerseAI researcher"
            className="cv-character character-girl-two"
          />
        </div>

        <div className="cv-scroll-hint">
          <span>SCROLL TO ENTER THE VERSE</span>
          <i />
          <span>01 — 05</span>
        </div>
      </section>

      {/* =====================================================
          VISION
      ====================================================== */}
      <section id="about" className="cv-vision">
        <div className="cv-vision-noise" />

        <div className="cv-vision-orbit orbit-large" />
        <div className="cv-vision-orbit orbit-medium" />
        <div className="cv-vision-orbit orbit-small" />

        <div className="cv-vision-node node-red" />
        <div className="cv-vision-node node-gold" />
        <div className="cv-vision-node node-cyan" />

        <div className="cv-vision-dna" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="cv-vision-header">
          <span className="cv-section-index">02 / THE VISION</span>

          <span className="cv-vision-status">
            <i />
            BUILDING BIOLOGICAL INTELLIGENCE
          </span>
        </div>

        <div className="cv-vision-glass">
          <div className="cv-vision-content">
            <div className="cv-vision-title">
              <span className="vision-word vision-word-one">
                Biology,
              </span>

              <span className="vision-word vision-word-two">
                connected.
              </span>
            </div>

            <div className="cv-vision-copy">
              <p className="vision-reveal reveal-one">
                CureVerseAI is an AI-powered biological intelligence platform
                connecting real biological data, foundation models and
                scientific evidence.
              </p>

              <p className="vision-reveal reveal-two">
                It brings research, drug development, medicine, biotechnology
                and education into one connected system — helping people move
                from biological questions to meaningful understanding.
              </p>

              <div className="cv-vision-formula vision-reveal reveal-three">
                <span>DATA</span>
                <b>+</b>
                <span>MODELS</span>
                <b>+</b>
                <span>EVIDENCE</span>
                <b>→</b>
                <strong>INTELLIGENCE</strong>
              </div>

              <a href="/idea" className="cv-vision-link vision-reveal reveal-four">
                <span>Explore the vision</span>
                <strong>↗</strong>
              </a>
            </div>
          </div>

          <div className="cv-vision-panel-visual">
            <img
              src="/vision/cureverse-bio-visual.png"
              alt="CureVerseAI biological intelligence visualization"
              className="cv-bio-visual"
            />
          </div>
        </div>

        <div className="cv-vision-footer">
          <span>REAL DATA</span>
          <i />
          <span>FOUNDATION MODELS</span>
          <i />
          <span>SCIENTIFIC EVIDENCE</span>
        </div>
      </section>

      {/* =====================================================
          DOMAINS — CONSTELLATION, NOT CARDS
      ====================================================== */}
      <section id="domains" className="cv-domains">
        <div className="cv-section-heading">
          <div>
            <span className="cv-kicker">03 / FIVE WORLDS</span>
            <h2>
              One platform.
              <br />
              <span>Five ways into biology.</span>
            </h2>
          </div>

          <p>
            Choose a domain and enter a specialized intelligence environment
            built around the way you work.
          </p>
        </div>

        <div className="cv-domain-experience">
          <div className="cv-domain-list">
            {domains.map((domain, index) => (
              <button
                key={domain.id}
                className={`cv-domain-item ${
                  activeDomain === index ? "is-active" : ""
                }`}
                onMouseEnter={() => setActiveDomain(index)}
                onFocus={() => setActiveDomain(index)}
                type="button"
              >
                <span>{domain.number}</span>

                <strong>{domain.title}</strong>

                <small>{domain.short}</small>

                <i>↗</i>
              </button>
            ))}
          </div>

          <div className={`cv-domain-world world-${active.color}`}>
            <div className="cv-world-orbit">
              <span />
              <span />
              <span />
              <span />
            </div>

            <div className="cv-world-center">
              <small>{active.number} / DOMAIN</small>
              <h3>{active.title}</h3>
              <p>{active.description}</p>

              <a href={`/domains/${active.id}`}>
                Enter {active.title}
                <span>↗</span>
              </a>
            </div>

            <div className="cv-world-data data-one">
              BIOLOGICAL
              <b>INTELLIGENCE</b>
            </div>

            <div className="cv-world-data data-two">
              DATA
              <b>→ EVIDENCE</b>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          INTELLIGENCE
      ====================================================== */}
      <section id="intelligence" className="cv-intelligence">
        <div className="cv-intelligence-top">
          <span className="cv-kicker">04 / PLATFORM INTELLIGENCE</span>

          <h2>
            From biological
            <span>data</span>
            to understanding.
          </h2>

          <p>
            CureVerseAI connects biological databases, pretrained models,
            multimodal representations and external evidence into a single
            reasoning workflow — turning a biological question into a
            traceable, evidence-aware analysis.
          </p>
        </div>

        <div className="cv-intelligence-system">
          <div className="cv-intelligence-line line-one" />
          <div className="cv-intelligence-line line-two" />
          <div className="cv-intelligence-line line-three" />
          <div className="cv-intelligence-line line-four" />
          <div className="cv-intelligence-line line-five" />

          <div className="cv-intelligence-stage stage-data">
            <span className="stage-index">01</span>
            <small>BIOLOGICAL SOURCES</small>
            <div className="stage-items">
              <b>ENSEMBL</b>
              <b>REACTOME</b>
              <b>UNIPROT</b>
            </div>
            <p>Gene identity, canonical sequences, pathways and biological context.</p>
          </div>

          <div className="cv-intelligence-stage stage-context">
            <span className="stage-index">02</span>
            <small>IDENTITY &amp; CONTEXT</small>
            <div className="stage-core">
              <strong>GENE</strong>
              <span>→</span>
              <strong>PROTEIN</strong>
            </div>
            <p>Biological entities are resolved before intelligence is applied.</p>
          </div>

          <div className="cv-intelligence-stage stage-models">
            <span className="stage-index">03</span>
            <small>PRETRAINED MODELS</small>
            <div className="model-grid">
              <div>
                <strong>ESM-2</strong>
                <span>PROTEIN</span>
              </div>
              <div>
                <strong>ChemBERTa</strong>
                <span>MOLECULE</span>
              </div>
              <div>
                <strong>CELL</strong>
                <span>CELLULAR STATE</span>
              </div>
            </div>
            <p>Different biological modalities become machine-readable representations.</p>
          </div>

          <div className="cv-intelligence-stage stage-fusion">
            <span className="stage-index">04</span>
            <small>MULTIMODAL FUSION</small>
            <div className="fusion-orbit">
              <i />
              <i />
              <i />
              <strong>256D</strong>
            </div>
            <p>Protein, molecular and cellular signals are aligned into a unified feature representation.</p>
          </div>

          <div className="cv-intelligence-stage stage-evidence">
            <span className="stage-index">05</span>
            <small>EXTERNAL EVIDENCE</small>
            <div className="evidence-stack">
              <div>
                <strong>OPEN TARGETS</strong>
                <span>DISEASE ASSOCIATIONS</span>
              </div>
              <div>
                <strong>ChEMBL</strong>
                <span>EXPERIMENTAL BIOACTIVITY</span>
              </div>
            </div>
            <p>External evidence is retrieved separately from model-derived signals.</p>
          </div>

          <div className="cv-intelligence-stage stage-reasoning">
            <span className="stage-index">06</span>
            <small>EVIDENCE REASONING</small>
            <div className="reasoning-pills">
              <span>DIRECT</span>
              <span>DISEASE</span>
              <span>EXPERIMENTAL</span>
              <span>MODEL</span>
              <span>CONTEXT</span>
            </div>
            <p>Evidence types remain distinct so the system can explain what supports an insight.</p>
          </div>

          <div className="cv-intelligence-output">
            <span className="output-pulse" />
            <small>CUREVERSEAI</small>
            <strong>REASONED</strong>
            <strong>BIOLOGICAL</strong>
            <strong>INSIGHT</strong>
            <span className="output-caption">DATA + MODELS + EVIDENCE</span>
          </div>
        </div>

        <div className="cv-intelligence-facts">
          <div>
            <strong>05</strong>
            <span>BIOLOGICAL DOMAINS</span>
            <p>Research · Drug Development · Medicine · Biotechnology · Education</p>
          </div>
          <div>
            <strong>03</strong>
            <span>BIOLOGICAL MODALITIES</span>
            <p>Protein · Molecule · Cellular State</p>
          </div>
          <div>
            <strong>256D</strong>
            <span>FUSED REPRESENTATION</span>
            <p>Unified multimodal feature space</p>
          </div>
          <div>
            <strong>MULTI-SOURCE</strong>
            <span>EVIDENCE REASONING</span>
            <p>Direct · Disease · Experimental · Model · Context</p>
          </div>
        </div>

        <div className="cv-intelligence-note">
          <span>FOLLOW THE SIGNAL</span>
          <p>Biological identity → models → multimodal features → external evidence → reasoning → insight.</p>
        </div>
      </section>

      {/* =====================================================
          TEAM
      ====================================================== */}
      <section id="team" className="cv-team">
        <div className="cv-team-heading">
          <span className="cv-kicker">05 / THE PEOPLE</span>

          <h2>
            Three minds.
            <br />
            <span>One mission.</span>
          </h2>

          <p>
            Meet the people behind CureVerseAI.
          </p>
        </div>

        <div className="cv-team-stage">
          <div className="cv-team-glow" />

          <div className="cv-team-person person-one">
            <img src="/team/girl-01.png" alt="Arooj Kanwal" />
            <div className="cv-team-name">
              <span>01</span>
              <strong>Arooj Kanwal</strong>
            </div>
          </div>

          <div className="cv-team-person person-two">
            <img src="/team/boy.png" alt="Aatazaz Hussain" />
            <div className="cv-team-name">
              <span>02</span>
              <strong>Aatazaz Hussain</strong>
            </div>
          </div>

          <div className="cv-team-person person-three">
            <img src="/team/girl-02.png" alt="Umme Hani" />
            <div className="cv-team-name">
              <span>03</span>
              <strong>Umme Hani</strong>
            </div>
          </div>
        </div>

        <div className="cv-team-cta">
          <a href="/developers" className="cv-button cv-button-primary">
            Meet the Developers
            <span>↗</span>
          </a>
        </div>
      </section>

      {/* =====================================================
          FINAL CTA
      ====================================================== */}
      <section className="cv-final">
        <div className="cv-final-grid" />

        <span className="cv-kicker">THE CONVERSATION IS OPEN</span>

        <h2>
          Build what
          <br />
          <span>comes next.</span>
        </h2>

        <p>
          Have a research question, technical idea, collaboration opportunity,
          or simply want to understand CureVerseAI?
        </p>

        <a href="/contact" className="cv-button cv-button-primary cv-final-button">
          Start a Conversation
          <span>→</span>
        </a>

        <div className="cv-final-dna">
          <span />
          <span />
          <span />
          <span />
        </div>
      </section>

      <Footer />

      <div
        className="cv-progress"
        style={{ transform: `scaleX(${scroll})` }}
      />
    </main>
  );
}
