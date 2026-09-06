"use client";

import { useEffect, useRef, useState } from "react";

const domains = [
  {
    number: "01",
    title: "Research",
    subtitle: "Decode biological complexity",
    description:
      "Explore genes, proteins, pathways, variants and disease evidence through an integrated biological intelligence layer.",
    icon: "🧬",
  },
  {
    number: "02",
    title: "Drug Development",
    subtitle: "From target to evidence",
    description:
      "Connect biological targets, compounds, bioactivity and disease evidence to accelerate scientific discovery.",
    icon: "💊",
  },
  {
    number: "03",
    title: "Medicine",
    subtitle: "Translate biology into insight",
    description:
      "Turn complex biological evidence into understandable, evidence-backed scientific interpretation.",
    icon: "🩺",
  },
  {
    number: "04",
    title: "Biotechnology",
    subtitle: "Engineer the living world",
    description:
      "Explore biological systems, proteins, pathways and molecular relationships for biotechnology applications.",
    icon: "🔬",
  },
  {
    number: "05",
    title: "Education",
    subtitle: "Learn the science of life",
    description:
      "Make advanced biological knowledge accessible through intelligent, interactive learning experiences.",
    icon: "🎓",
  },
];

const stats = [
  ["01", "AI Domains", "05"],
  ["02", "Foundation Models", "02+"],
  ["03", "Evidence Sources", "04+"],
  ["04", "Biological Entities", "∞"],
];

function DeveloperCharacter({
  name,
  role,
  position,
  accent,
}: {
  name: string;
  role: string;
  position: string;
  accent: "red" | "gold";
}) {
  const accentClass = accent === "gold" ? "cv-gold" : "cv-red";

  return (
    <div
      className={`developer-character ${position}`}
      data-cursor-reactive="true"
    >
      <div className="character-glow" />
      <div className="character-head">
        <div className="character-hair" />
        <div className="character-face">
          <span className="eye eye-left" />
          <span className="eye eye-right" />
          <span className="smile" />
        </div>
      </div>

      <div className="character-body">
        <div className="character-neck" />
        <div className="character-shirt">
          <span className={accentClass}>CV</span>
        </div>
      </div>

      <div className="character-label">
        <span>{name}</span>
        <small>{role}</small>
      </div>
    </div>
  );
}

export default function Home() {
  const heroRef = useRef<HTMLElement | null>(null);
  const [cursor, setCursor] = useState({ x: 0, y: 0 });
  const [scrolled, setScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      const x = (event.clientX / window.innerWidth - 0.5) * 2;
      const y = (event.clientY / window.innerHeight - 0.5) * 2;

      setCursor({ x, y });
    };

    const handleScroll = () => {
      setScrolled(window.scrollY > 40);

      const heroHeight = Math.max(window.innerHeight * 1.35, 900);
      const progress = Math.min(
        Math.max(window.scrollY / heroHeight, 0),
        1
      );

      setScrollProgress(progress);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const goToDomains = () => {
    document.getElementById("domains")?.scrollIntoView({
      behavior: "smooth",
    });
  };

  return (
    <main className="cv-home">
      {/* =========================================================
          NAVIGATION
      ========================================================== */}
      <nav className={`cv-nav ${scrolled ? "cv-nav-scrolled" : ""}`}>
        <div className="cv-container cv-nav-inner">
          <a href="#" className="cv-brand">
            <span className="cv-brand-mark">CV</span>
            <span>
              CureVerse<span className="cv-red">AI</span>
            </span>
          </a>

          <div className="cv-nav-links">
            <a href="#domains">Domains</a>
            <a href="#intelligence">Intelligence</a>
            <a href="#developers">Developers</a>
            <a href="#about">About</a>
          </div>

          <a href="#domains" className="cv-nav-cta">
            Explore Platform
            <span>↗</span>
          </a>
        </div>
      </nav>

      {/* =========================================================
          CINEMATIC HERO / SCROLLATION STAGE
      ========================================================== */}
      <section ref={heroRef} className="cv-hero">
        <div className="hero-grid" />

        <div
          className="hero-cursor-light"
          style={{
            transform: `translate3d(${cursor.x * 70}px, ${cursor.y * 50}px, 0)`,
          }}
        />

        <div className="hero-orbit orbit-one" />
        <div className="hero-orbit orbit-two" />

        <span className="cv-particle p1" />
        <span className="cv-particle cv-particle-red p2" />
        <span className="cv-particle p3" />
        <span className="cv-particle cv-particle-red p4" />
        <span className="cv-particle p5" />

        {/* =====================================================
            SCROLLATION ENGINE

            This visual is intentionally procedural for now.
            Later it will be replaced by the AI-generated
            frame sequence without changing the hero structure.
        ====================================================== */}
        <div
          className="scrollation-stage"
          aria-hidden="true"
          style={{
            opacity: 0.42 + scrollProgress * 0.5,
            transform: `translate(-50%, -48%) scale(${
              0.82 + scrollProgress * 0.2
            }) rotate(${scrollProgress * 18}deg)`,
          }}
        >
          <div
            className="scrollation-ring ring-a"
            style={{
              transform: `rotate(${scrollProgress * 180}deg)`,
            }}
          />

          <div
            className="scrollation-ring ring-b"
            style={{
              transform: `rotate(${-scrollProgress * 240}deg)`,
            }}
          />

          <div
            className="scrollation-dna"
            style={{
              transform: `rotate(${18 + scrollProgress * 65}deg) scale(${
                0.82 + scrollProgress * 0.28
              })`,
            }}
          >
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="scrollation-core">
            <div
              className="core-cell"
              style={{
                transform: `scale(${0.88 + scrollProgress * 0.22})`,
              }}
            >
              <div
                className="core-nucleus"
                style={{
                  transform: `scale(${0.7 + scrollProgress * 0.45})`,
                }}
              />
            </div>
          </div>

          {/* Biological data particles */}
          <div
            className="scroll-data-orbit"
            style={{
              transform: `rotate(${scrollProgress * 300}deg)`,
            }}
          >
            {Array.from({ length: 12 }).map((_, index) => (
              <span
                key={index}
                className="scroll-data-node"
                style={{
                  transform: `rotate(${index * 30}deg) translateY(-245px)`,
                }}
              />
            ))}
          </div>

          <div className="scrollation-stage-label">
            <span>CV / BIOLOGICAL FIELD</span>
            <b>{Math.round(scrollProgress * 100)}%</b>
          </div>
        </div>

        <div className="cv-container hero-content">
          <div className="cv-eyebrow hero-eyebrow">
            <span className="cv-live-dot" />
            Biological Intelligence Engine / Online
          </div>

          <h1 className="cv-display hero-title">
            <span>UNDERSTAND</span>
            <span className="hero-title-offset">BIOLOGY.</span>
            <span className="hero-title-accent">DISCOVER WHAT&apos;S NEXT.</span>
          </h1>

          <p className="hero-description">
            CureVerseAI brings biological data, foundation models and scientific
            evidence together to help researchers, innovators, clinicians and
            learners explore the science of life.
          </p>

          <div className="hero-actions">
            <button
              className="cv-button cv-button-primary"
              onClick={goToDomains}
            >
              Enter CureVerseAI
              <span>→</span>
            </button>

            <a href="#intelligence" className="cv-button cv-button-secondary">
              Explore Intelligence
            </a>
          </div>
        </div>

        {/* =====================================================
            DEVELOPER TEAM
        ====================================================== */}
        <div
          className="developer-stage"
          style={{
            transform: `translate3d(${cursor.x * -10}px, ${
              cursor.y * -7
            }px, 0)`,
          }}
        >
          <img
            src="/team/cureverse-team.png"
            alt="CureVerseAI development team"
            className="developer-team-image"
          />
        </div>

        <div className="hero-bottom">
          <div>SCROLL TO ENTER THE VERSE</div>
          <div className="scroll-line">
            <span />
          </div>
          <div>01 / 08</div>
        </div>
      </section>

      {/* =========================================================
          INTRO
      ========================================================== */}
      <section id="about" className="cv-section cv-intro">
        <div className="cv-container intro-grid">
          <div>
            <div className="cv-eyebrow">01 / The Vision</div>
            <h2 className="cv-display section-title">
              THE LIVING
              <br />
              <span className="cv-red">DATA.</span>
            </h2>
          </div>

          <div className="intro-copy">
            <p className="large-copy">
              Biology is interconnected. CureVerseAI is built around that
              principle.
            </p>

            <p>
              Instead of treating genes, proteins, diseases, molecules and
              biological evidence as isolated pieces of information, the
              platform connects them into one intelligent scientific
              environment.
            </p>

            <div className="intro-line">
              <span />
              <small>DATA → MODELS → EVIDENCE → INSIGHT</small>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          DOMAINS
      ========================================================== */}
      <section id="domains" className="cv-section cv-domains">
        <div className="cv-container">
          <div className="section-heading">
            <div>
              <div className="cv-eyebrow">02 / Explore The Verse</div>
              <h2 className="cv-display section-title">
                FIVE WORLDS.
                <br />
                <span className="cv-red">ONE INTELLIGENCE.</span>
              </h2>
            </div>

            <p>
              Every domain gets its own scientific environment while sharing
              the same CureVerseAI intelligence layer.
            </p>
          </div>

          <div className="domain-grid">
            {domains.map((domain) => (
              <a
                href={`/domains/${domain.title.toLowerCase().replaceAll(" ", "-")}`}
                className="domain-card"
                key={domain.number}
              >
                <div className="domain-top">
                  <span>{domain.number}</span>
                  <span className="domain-arrow">↗</span>
                </div>

                <div className="domain-visual">
                  <div className="domain-orbit" />
                  <div className="domain-orbit orbit-small" />
                  <div className="domain-icon">{domain.icon}</div>
                </div>

                <div className="domain-info">
                  <div className="cv-eyebrow">{domain.subtitle}</div>
                  <h3>{domain.title}</h3>
                  <p>{domain.description}</p>
                </div>

                <div className="domain-enter">
                  Enter domain <span>→</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================================
          ANALYTICS / IMPACT
      ========================================================== */}
      <section id="intelligence" className="cv-section cv-impact">
        <div className="cv-container">
          <div className="cv-eyebrow">03 / Platform Intelligence</div>

          <div className="impact-heading">
            <h2 className="cv-display section-title">
              BUILT TO
              <br />
              <span className="cv-gold">CONNECT.</span>
            </h2>

            <p>
              A living view of the intelligence behind CureVerseAI. As the
              platform grows, this space can connect directly to real usage
              analytics.
            </p>
          </div>

          <div className="impact-stats">
            {stats.map(([number, label, value]) => (
              <div className="impact-stat" key={number}>
                <span className="stat-number">{number}</span>
                <div className="stat-value">{value}</div>
                <div className="stat-label">{label}</div>
                <div className="stat-line">
                  <span />
                </div>
              </div>
            ))}
          </div>

          <div className="analytics-visual">
            <div className="analytics-header">
              <span>CUREVERSEAI / ACTIVITY FIELD</span>
              <span className="cv-red">LIVE INTELLIGENCE</span>
            </div>

            <div className="analytics-field">
              <div className="analytics-grid" />

              {Array.from({ length: 16 }).map((_, index) => (
                <span
                  key={index}
                  className={`data-node node-${index + 1}`}
                />
              ))}

              <div className="analytics-core">
                <span>CV</span>
              </div>

              <div className="analytics-ring ring-1" />
              <div className="analytics-ring ring-2" />
              <div className="analytics-ring ring-3" />
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          TECHNOLOGY
      ========================================================== */}
      <section className="cv-section cv-technology">
        <div className="cv-container">
          <div className="cv-eyebrow">04 / Intelligence Architecture</div>

          <div className="tech-grid">
            <div>
              <h2 className="cv-display section-title">
                DATA
                <br />
                MEETS
                <br />
                <span className="cv-red">AI.</span>
              </h2>
            </div>

            <div className="tech-stack">
              <div className="tech-card">
                <span>01</span>
                <div>
                  <strong>Biological Knowledge</strong>
                  <p>
                    Genes, proteins, pathways, variants, diseases and
                    biological relationships.
                  </p>
                </div>
              </div>

              <div className="tech-card">
                <span>02</span>
                <div>
                  <strong>Foundation Models</strong>
                  <p>
                    Protein and molecular representation models transform
                    biological inputs into machine-readable intelligence.
                  </p>
                </div>
              </div>

              <div className="tech-card">
                <span>03</span>
                <div>
                  <strong>Evidence Reasoning</strong>
                  <p>
                    Multiple evidence sources are organized into transparent
                    scientific reasoning rather than unsupported answers.
                  </p>
                </div>
              </div>

              <div className="tech-card">
                <span>04</span>
                <div>
                  <strong>Unified Intelligence</strong>
                  <p>
                    One platform connects research, drug development,
                    medicine, biotechnology and education.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          DEVELOPERS
      ========================================================== */}
      <section id="developers" className="cv-section cv-developers">
        <div className="cv-container">
          <div className="cv-eyebrow">05 / The People</div>

          <div className="developers-heading">
            <h2 className="cv-display section-title">
              BUILT BY
              <br />
              <span className="cv-red">THREE MINDS.</span>
            </h2>

            <p>
              The people behind the idea, the engineering and the vision of
              CureVerseAI.
            </p>
          </div>

          <div className="team-placeholder">
            <div className="team-orbit" />
            <div className="team-orbit team-orbit-small" />

            <DeveloperCharacter
              name="Developer 01"
              role="AI / Biology"
              position="developer-left"
              accent="gold"
            />

            <DeveloperCharacter
              name="Developer 02"
              role="Research / AI"
              position="developer-center"
              accent="red"
            />

            <DeveloperCharacter
              name="Developer 03"
              role="Technology"
              position="developer-right"
              accent="gold"
            />
          </div>

          <div className="developer-link">
            <a href="/developers">
              Meet the full team <span>→</span>
            </a>
          </div>
        </div>
      </section>

      {/* =========================================================
          FINAL CTA
      ========================================================== */}
      <section className="cv-final">
        <div className="final-glow" />

        <div className="cv-container final-content">
          <div className="cv-eyebrow">CUREVERSEAI / BEGIN</div>

          <h2 className="cv-display final-title">
            ENTER THE
            <br />
            <span className="cv-red">VERSE.</span>
          </h2>

          <p>
            Explore the intersection of artificial intelligence and the
            science of life.
          </p>

          <button
            className="cv-button cv-button-primary"
            onClick={goToDomains}
          >
            Explore the five domains →
          </button>
        </div>
      </section>

      {/* =========================================================
          FOOTER
      ========================================================== */}
      <footer className="cv-footer">
        <div className="cv-container footer-inner">
          <div>
            <div className="cv-brand">
              <span className="cv-brand-mark">CV</span>
              CureVerse<span className="cv-red">AI</span>
            </div>
            <p>AI-powered biological intelligence.</p>
          </div>

          <div className="footer-links">
            <a href="#domains">Domains</a>
            <a href="#intelligence">Intelligence</a>
            <a href="/developers">Developers</a>
            <a href="/contact">Contact</a>
          </div>

          <div className="footer-copy">
            © {new Date().getFullYear()} CureVerseAI
          </div>
        </div>
      </footer>

      <style jsx>{`
        .cv-home {
          min-height: 100vh;
          background: var(--cv-bg);
          overflow: hidden;
        }

        /* NAV */

        .cv-nav {
          position: fixed;
          inset: 0 0 auto;
          z-index: 100;
          height: 78px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.07);
          transition: 400ms ease;
        }

        .cv-nav-scrolled {
          background: rgba(8, 10, 11, 0.78);
          backdrop-filter: blur(20px);
        }

        .cv-nav-inner {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .cv-brand {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 15px;
          font-weight: 600;
          letter-spacing: -0.04em;
        }

        .cv-brand-mark {
          width: 36px;
          height: 36px;
          display: grid;
          place-items: center;
          border: 1px solid rgba(255, 255, 255, 0.16);
          border-radius: 11px;
          font-size: 9px;
          letter-spacing: 0.08em;
        }

        .cv-nav-links {
          display: flex;
          align-items: center;
          gap: 31px;
          color: var(--cv-text-muted);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.14em;
        }

        .cv-nav-links a {
          transition: color 250ms ease;
        }

        .cv-nav-links a:hover {
          color: var(--cv-text);
        }

        .cv-nav-cta {
          display: flex;
          gap: 9px;
          align-items: center;
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.13em;
          color: var(--cv-text-soft);
        }

        .cv-nav-cta span {
          color: var(--cv-red);
          font-size: 14px;
        }

        /* HERO */

        .cv-hero {
          position: relative;
          min-height: 100vh;
          height: 980px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border-bottom: 1px solid var(--cv-border);
        }

        .hero-grid {
          position: absolute;
          inset: 0;
          opacity: 0.18;
          background-image:
            linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(
              90deg,
              rgba(255, 255, 255, 0.035) 1px,
              transparent 1px
            );
          background-size: 90px 90px;
          mask-image: radial-gradient(circle at center, black, transparent 76%);
        }

        .hero-cursor-light {
          position: absolute;
          width: 600px;
          height: 600px;
          left: calc(50% - 300px);
          top: calc(50% - 300px);
          border-radius: 50%;
          background: radial-gradient(
            circle,
            rgba(224, 82, 90, 0.1),
            transparent 65%
          );
          transition: transform 800ms cubic-bezier(0.22, 1, 0.36, 1);
          pointer-events: none;
        }

        .hero-orbit {
          position: absolute;
          width: 700px;
          height: 700px;
          border: 1px solid rgba(224, 82, 90, 0.1);
          border-radius: 50%;
          animation: orbit-spin 30s linear infinite;
        }

        .orbit-one {
          transform: rotate(25deg) scaleX(0.43);
        }

        .orbit-two {
          transform: rotate(-35deg) scaleX(0.28);
          border-color: rgba(233, 197, 140, 0.08);
          animation-duration: 42s;
          animation-direction: reverse;
        }

        @keyframes orbit-spin {
          from {
            rotate: 0deg;
          }
          to {
            rotate: 360deg;
          }
        }

        .scrollation-stage {
          position: absolute;
          width: 650px;
          height: 650px;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -48%);
          opacity: 0.55;
        }

        .scrollation-ring {
          position: absolute;
          inset: 12%;
          border: 1px solid rgba(224, 82, 90, 0.13);
          border-radius: 50%;
        }

        .ring-a {
          animation: ring-breathe 5s ease-in-out infinite;
        }

        .ring-b {
          inset: 25%;
          border-color: rgba(233, 197, 140, 0.11);
          animation: ring-breathe 4s ease-in-out infinite reverse;
        }

        @keyframes ring-breathe {
          0%,
          100% {
            scale: 0.96;
            opacity: 0.45;
          }
          50% {
            scale: 1.04;
            opacity: 1;
          }
        }

        .scrollation-core {
          position: absolute;
          inset: 31%;
          display: grid;
          place-items: center;
        }

        .core-cell {
          width: 100%;
          height: 100%;
          border: 1px solid rgba(224, 82, 90, 0.35);
          border-radius: 50%;
          background:
            radial-gradient(
              circle at 42% 38%,
              rgba(233, 197, 140, 0.2),
              transparent 25%
            ),
            radial-gradient(
              circle,
              rgba(224, 82, 90, 0.09),
              rgba(5, 7, 8, 0.9) 70%
            );
          box-shadow:
            inset 0 0 60px rgba(224, 82, 90, 0.08),
            0 0 100px rgba(224, 82, 90, 0.08);
          animation: cell-pulse 4s ease-in-out infinite;
        }

        .core-nucleus {
          position: absolute;
          width: 27%;
          aspect-ratio: 1;
          left: 36.5%;
          top: 36.5%;
          border-radius: 50%;
          background: rgba(224, 82, 90, 0.72);
          box-shadow: 0 0 45px rgba(224, 82, 90, 0.35);
        }

        @keyframes cell-pulse {
          0%,
          100% {
            scale: 0.96;
          }
          50% {
            scale: 1.03;
          }
        }

        .scrollation-dna {
          position: absolute;
          width: 110px;
          height: 400px;
          left: calc(50% - 55px);
          top: calc(50% - 200px);
          opacity: 0.45;
          transform: rotate(18deg);
          animation: dna-float 7s ease-in-out infinite;
        }

        .scrollation-dna::before,
        .scrollation-dna::after {
          content: "";
          position: absolute;
          top: 0;
          width: 3px;
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(
            to bottom,
            transparent,
            var(--cv-red),
            var(--cv-gold),
            var(--cv-red),
            transparent
          );
        }

        .scrollation-dna::before {
          left: 20px;
          transform: rotate(14deg);
        }

        .scrollation-dna::after {
          right: 20px;
          transform: rotate(-14deg);
        }

        .scrollation-dna span {
          position: absolute;
          left: 27px;
          width: 56px;
          height: 1px;
          background: rgba(233, 197, 140, 0.6);
          transform: rotate(var(--r));
        }

        .scrollation-dna span:nth-child(1) {
          top: 8%;
          --r: 8deg;
        }
        .scrollation-dna span:nth-child(2) {
          top: 21%;
          --r: -8deg;
        }
        .scrollation-dna span:nth-child(3) {
          top: 34%;
          --r: 8deg;
        }
        .scrollation-dna span:nth-child(4) {
          top: 47%;
          --r: -8deg;
        }
        .scrollation-dna span:nth-child(5) {
          top: 60%;
          --r: 8deg;
        }
        .scrollation-dna span:nth-child(6) {
          top: 73%;
          --r: -8deg;
        }
        .scrollation-dna span:nth-child(7) {
          top: 86%;
          --r: 8deg;
        }

        @keyframes dna-float {
          0%,
          100% {
            translate: 0 0;
          }
          50% {
            translate: 0 -18px;
          }
        }

        .scroll-data-orbit {
          position: absolute;
          inset: 50%;
          width: 1px;
          height: 1px;
          transition: transform 900ms cubic-bezier(0.22, 1, 0.36, 1);
        }

        .scroll-data-node {
          position: absolute;
          left: -3px;
          top: -3px;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--cv-red);
          box-shadow:
            0 0 12px rgba(224, 82, 90, 0.65),
            0 0 28px rgba(224, 82, 90, 0.18);
        }

        .scroll-data-node:nth-child(3n) {
          background: var(--cv-gold);
          box-shadow:
            0 0 12px rgba(233, 197, 140, 0.55),
            0 0 28px rgba(233, 197, 140, 0.15);
        }

        .scrollation-stage-label {
          position: absolute;
          left: 50%;
          bottom: 7%;
          translate: -50% 0;
          display: flex;
          align-items: center;
          gap: 13px;
          white-space: nowrap;
          color: rgba(238, 233, 225, 0.34);
          font-size: 7px;
          letter-spacing: 0.17em;
        }

        .scrollation-stage-label b {
          color: var(--cv-red);
          font-weight: 500;
        }

        .hero-content {
          position: relative;
          z-index: 10;
          text-align: center;
          margin-top: -40px;
        }

        .hero-eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 9px 13px;
          border: 1px solid rgba(255, 255, 255, 0.09);
          background: rgba(8, 10, 11, 0.48);
          backdrop-filter: blur(16px);
          border-radius: 999px;
        }

        .hero-title {
          max-width: 1100px;
          margin: 25px auto 0;
          font-size: clamp(52px, 8vw, 112px);
          position: relative;
        }

        .hero-title span {
          display: block;
        }

        .hero-title-offset {
          margin-left: 8vw;
          color: var(--cv-text);
        }

        .hero-title-accent {
          color: var(--cv-red);
          font-size: 0.72em;
          margin-top: 15px;
        }

        .hero-description {
          max-width: 620px;
          margin: 28px auto 0;
          color: var(--cv-text-soft);
          font-size: 13px;
          line-height: 1.8;
        }

        .hero-actions {
          display: flex;
          justify-content: center;
          gap: 10px;
          margin-top: 28px;
        }

        .developer-stage {
          position: absolute;
          z-index: 8;
          inset: auto 0 90px;
          height: 300px;
          pointer-events: none;
          transition: transform 900ms cubic-bezier(0.22, 1, 0.36, 1);
        }

        .developer-character {
          position: absolute;
          width: 150px;
          text-align: center;
          transition: transform 500ms cubic-bezier(0.22, 1, 0.36, 1);
        }

        .developer-character:hover {
          transform: translateY(-8px);
        }

        .developer-left {
          left: calc(50% - 285px);
        }

        .developer-center {
          left: calc(50% - 75px);
          scale: 1.08;
        }

        .developer-right {
          left: calc(50% + 135px);
        }

        .character-glow {
          position: absolute;
          width: 140px;
          height: 140px;
          left: 5px;
          top: 10px;
          border-radius: 50%;
          background: radial-gradient(
            circle,
            rgba(224, 82, 90, 0.13),
            transparent 68%
          );
          filter: blur(5px);
        }

        .character-head {
          position: relative;
          width: 85px;
          height: 92px;
          margin: auto;
          border-radius: 44% 44% 48% 48%;
          background: #c99474;
          border: 1px solid rgba(255, 255, 255, 0.12);
          box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
        }

        .character-hair {
          position: absolute;
          left: -2px;
          top: -5px;
          width: 89px;
          height: 43px;
          border-radius: 50px 50px 20px 20px;
          background: #171311;
        }

        .character-face {
          position: absolute;
          inset: 35px 14px 16px;
        }

        .eye {
          position: absolute;
          width: 6px;
          height: 4px;
          border-radius: 50%;
          background: #171311;
          transition: transform 350ms ease;
        }

        .eye-left {
          left: 12px;
        }

        .eye-right {
          right: 12px;
        }

        .smile {
          position: absolute;
          width: 19px;
          height: 8px;
          left: calc(50% - 9px);
          bottom: 2px;
          border-bottom: 1.5px solid #5e332a;
          border-radius: 0 0 20px 20px;
        }

        .character-body {
          position: relative;
          width: 118px;
          height: 105px;
          margin: -3px auto 0;
        }

        .character-neck {
          position: absolute;
          width: 28px;
          height: 22px;
          left: calc(50% - 14px);
          top: 0;
          background: #b87e62;
        }

        .character-shirt {
          position: absolute;
          inset: 14px 0 0;
          border-radius: 55px 55px 15px 15px;
          background: linear-gradient(145deg, #171b1d, #0e1112);
          border: 1px solid rgba(255, 255, 255, 0.1);
          display: grid;
          place-items: center;
          box-shadow: 0 25px 45px rgba(0, 0, 0, 0.35);
        }

        .character-shirt span {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
        }

        .character-label {
          display: grid;
          gap: 3px;
          margin-top: 5px;
        }

        .character-label span {
          font-size: 9px;
          color: var(--cv-text-soft);
        }

        .character-label small {
          color: var(--cv-text-muted);
          font-size: 7px;
          text-transform: uppercase;
          letter-spacing: 0.12em;
        }

        .hero-bottom {
          position: absolute;
          z-index: 20;
          left: 30px;
          right: 30px;
          bottom: 24px;
          display: grid;
          grid-template-columns: 1fr 180px 1fr;
          align-items: center;
          color: var(--cv-text-muted);
          font-size: 8px;
          letter-spacing: 0.18em;
        }

        .hero-bottom > :last-child {
          text-align: right;
        }

        .scroll-line {
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
          position: relative;
        }

        .scroll-line span {
          position: absolute;
          left: 0;
          top: -1px;
          width: 35%;
          height: 3px;
          background: var(--cv-red);
          animation: scroll-progress 2.4s ease-in-out infinite;
        }

        @keyframes scroll-progress {
          0% {
            left: 0;
          }
          50% {
            left: 65%;
          }
          100% {
            left: 0;
          }
        }

        /* SECTIONS */

        .cv-section {
          position: relative;
          padding: 150px 0;
          border-bottom: 1px solid var(--cv-border);
        }

        .section-title {
          font-size: clamp(54px, 7vw, 92px);
        }

        .intro-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 90px;
        }

        .intro-copy {
          padding-top: 38px;
        }

        .large-copy {
          margin: 0 0 30px;
          max-width: 560px;
          color: var(--cv-text);
          font-size: 27px;
          line-height: 1.35;
          letter-spacing: -0.04em;
        }

        .intro-copy > p:not(.large-copy) {
          max-width: 500px;
          color: var(--cv-text-muted);
          font-size: 13px;
          line-height: 1.9;
        }

        .intro-line {
          margin-top: 45px;
          display: flex;
          align-items: center;
          gap: 15px;
          color: var(--cv-text-muted);
          font-size: 8px;
          letter-spacing: 0.16em;
        }

        .intro-line span {
          width: 45px;
          height: 1px;
          background: var(--cv-red);
        }

        /* DOMAINS */

        .section-heading {
          display: flex;
          justify-content: space-between;
          align-items: end;
          gap: 60px;
          margin-bottom: 70px;
        }

        .section-heading > p {
          max-width: 360px;
          color: var(--cv-text-muted);
          font-size: 12px;
          line-height: 1.8;
        }

        .domain-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
        }

        .domain-card {
          position: relative;
          min-height: 540px;
          padding: 25px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border: 1px solid var(--cv-border);
          border-radius: var(--cv-radius-lg);
          background:
            radial-gradient(
              circle at 50% 35%,
              rgba(224, 82, 90, 0.075),
              transparent 35%
            ),
            #0d1112;
          transition:
            transform 450ms cubic-bezier(0.22, 1, 0.36, 1),
            border-color 450ms ease,
            box-shadow 450ms ease;
        }

        .domain-card:last-child {
          grid-column: 1 / -1;
        }

        .domain-card:hover {
          transform: translateY(-8px);
          border-color: var(--cv-border-red);
          box-shadow: 0 35px 90px rgba(0, 0, 0, 0.35);
        }

        .domain-top {
          display: flex;
          justify-content: space-between;
          color: var(--cv-text-muted);
          font-size: 9px;
          letter-spacing: 0.18em;
        }

        .domain-arrow {
          color: var(--cv-red);
          font-size: 18px;
        }

        .domain-visual {
          position: relative;
          height: 230px;
          display: grid;
          place-items: center;
        }

        .domain-orbit {
          position: absolute;
          width: 180px;
          height: 180px;
          border: 1px solid rgba(224, 82, 90, 0.17);
          border-radius: 50%;
          animation: domain-spin 16s linear infinite;
        }

        .domain-orbit::after {
          content: "";
          position: absolute;
          width: 5px;
          height: 5px;
          top: -3px;
          left: 50%;
          border-radius: 50%;
          background: var(--cv-red);
          box-shadow: 0 0 18px var(--cv-red);
        }

        .orbit-small {
          width: 125px;
          height: 125px;
          border-color: rgba(233, 197, 140, 0.16);
          animation-duration: 11s;
          animation-direction: reverse;
        }

        .domain-icon {
          position: relative;
          z-index: 2;
          width: 76px;
          height: 76px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background: rgba(16, 21, 23, 0.85);
          border: 1px solid rgba(255, 255, 255, 0.11);
          font-size: 28px;
          box-shadow: 0 0 50px rgba(224, 82, 90, 0.08);
        }

        @keyframes domain-spin {
          to {
            rotate: 360deg;
          }
        }

        .domain-info {
          position: relative;
          z-index: 2;
          margin-top: auto;
        }

        .domain-info h3 {
          margin: 8px 0 10px;
          font-size: 30px;
          letter-spacing: -0.05em;
        }

        .domain-info p {
          max-width: 500px;
          margin: 0;
          color: var(--cv-text-muted);
          font-size: 11px;
          line-height: 1.7;
        }

        .domain-enter {
          display: flex;
          justify-content: space-between;
          margin-top: 25px;
          padding-top: 15px;
          border-top: 1px solid var(--cv-border);
          color: var(--cv-text-soft);
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.13em;
        }

        .domain-enter span {
          color: var(--cv-red);
          font-size: 15px;
        }

        /* IMPACT */

        .cv-impact {
          background:
            radial-gradient(
              circle at 80% 30%,
              rgba(224, 82, 90, 0.055),
              transparent 30%
            ),
            var(--cv-bg);
        }

        .impact-heading {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 80px;
          align-items: end;
          margin-top: 30px;
        }

        .impact-heading p {
          max-width: 430px;
          color: var(--cv-text-muted);
          font-size: 12px;
          line-height: 1.8;
        }

        .impact-stats {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 10px;
          margin-top: 75px;
        }

        .impact-stat {
          min-height: 180px;
          padding: 20px;
          border: 1px solid var(--cv-border);
          border-radius: 18px;
          background: rgba(16, 21, 23, 0.5);
        }

        .stat-number {
          color: var(--cv-text-muted);
          font-size: 8px;
          letter-spacing: 0.16em;
        }

        .stat-value {
          margin-top: 30px;
          font-size: 44px;
          letter-spacing: -0.06em;
        }

        .stat-label {
          margin-top: 5px;
          color: var(--cv-text-muted);
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.13em;
        }

        .stat-line {
          position: relative;
          height: 1px;
          margin-top: 25px;
          background: var(--cv-border);
        }

        .stat-line span {
          display: block;
          width: 65%;
          height: 1px;
          background: var(--cv-red);
        }

        .analytics-visual {
          margin-top: 16px;
          border: 1px solid var(--cv-border);
          border-radius: 28px;
          overflow: hidden;
          background: #07090a;
        }

        .analytics-header {
          display: flex;
          justify-content: space-between;
          padding: 18px 20px;
          border-bottom: 1px solid var(--cv-border);
          color: var(--cv-text-muted);
          font-size: 8px;
          letter-spacing: 0.16em;
        }

        .analytics-field {
          position: relative;
          height: 430px;
          overflow: hidden;
        }

        .analytics-grid {
          position: absolute;
          inset: 0;
          opacity: 0.35;
          background-image:
            linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(
              90deg,
              rgba(255, 255, 255, 0.035) 1px,
              transparent 1px
            );
          background-size: 50px 50px;
        }

        .analytics-core {
          position: absolute;
          width: 100px;
          height: 100px;
          left: calc(50% - 50px);
          top: calc(50% - 50px);
          display: grid;
          place-items: center;
          border: 1px solid var(--cv-red);
          border-radius: 50%;
          color: var(--cv-red);
          box-shadow:
            0 0 45px rgba(224, 82, 90, 0.12),
            inset 0 0 30px rgba(224, 82, 90, 0.08);
          animation: core-breathe 4s ease-in-out infinite;
        }

        .analytics-core span {
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.1em;
        }

        @keyframes core-breathe {
          0%,
          100% {
            scale: 0.94;
          }
          50% {
            scale: 1.06;
          }
        }

        .analytics-ring {
          position: absolute;
          left: calc(50% - 125px);
          top: calc(50% - 125px);
          width: 250px;
          height: 250px;
          border: 1px solid rgba(224, 82, 90, 0.12);
          border-radius: 50%;
          animation: analytics-spin 18s linear infinite;
        }

        .ring-2 {
          width: 370px;
          height: 370px;
          left: calc(50% - 185px);
          top: calc(50% - 185px);
          border-color: rgba(233, 197, 140, 0.08);
          animation-duration: 27s;
          animation-direction: reverse;
        }

        .ring-3 {
          width: 500px;
          height: 500px;
          left: calc(50% - 250px);
          top: calc(50% - 250px);
          border-color: rgba(255, 255, 255, 0.05);
          animation-duration: 40s;
        }

        @keyframes analytics-spin {
          to {
            rotate: 360deg;
          }
        }

        .data-node {
          position: absolute;
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--cv-red);
          box-shadow: 0 0 15px rgba(224, 82, 90, 0.65);
          animation: node-pulse 2.5s ease-in-out infinite;
        }

        .node-1 {
          left: 17%;
          top: 28%;
        }
        .node-2 {
          left: 28%;
          top: 66%;
          animation-delay: -0.4s;
        }
        .node-3 {
          left: 41%;
          top: 18%;
          animation-delay: -0.7s;
        }
        .node-4 {
          left: 67%;
          top: 24%;
          animation-delay: -1.1s;
        }
        .node-5 {
          left: 79%;
          top: 58%;
          animation-delay: -1.6s;
        }
        .node-6 {
          left: 59%;
          top: 77%;
          animation-delay: -0.9s;
        }
        .node-7 {
          left: 22%;
          top: 47%;
          animation-delay: -0.2s;
        }
        .node-8 {
          left: 73%;
          top: 76%;
          animation-delay: -1.4s;
        }
        .node-9 {
          left: 84%;
          top: 34%;
          animation-delay: -0.6s;
        }
        .node-10 {
          left: 12%;
          top: 70%;
          animation-delay: -1.8s;
        }
        .node-11 {
          left: 50%;
          top: 11%;
          animation-delay: -1.3s;
        }
        .node-12 {
          left: 88%;
          top: 67%;
          animation-delay: -0.3s;
        }
        .node-13 {
          left: 34%;
          top: 85%;
          animation-delay: -1.2s;
        }
        .node-14 {
          left: 63%;
          top: 44%;
          animation-delay: -1.9s;
        }
        .node-15 {
          left: 47%;
          top: 90%;
          animation-delay: -0.5s;
        }
        .node-16 {
          left: 92%;
          top: 18%;
          animation-delay: -1.5s;
        }

        @keyframes node-pulse {
          0%,
          100% {
            scale: 0.6;
            opacity: 0.3;
          }
          50% {
            scale: 1.4;
            opacity: 1;
          }
        }

        /* TECHNOLOGY */

        .tech-grid {
          display: grid;
          grid-template-columns: 0.8fr 1.2fr;
          gap: 110px;
        }

        .tech-stack {
          border-top: 1px solid var(--cv-border);
        }

        .tech-card {
          display: grid;
          grid-template-columns: 45px 1fr;
          gap: 20px;
          padding: 28px 0;
          border-bottom: 1px solid var(--cv-border);
        }

        .tech-card > span {
          color: var(--cv-red);
          font-size: 8px;
          letter-spacing: 0.15em;
        }

        .tech-card strong {
          display: block;
          font-size: 17px;
          font-weight: 500;
        }

        .tech-card p {
          max-width: 500px;
          margin: 8px 0 0;
          color: var(--cv-text-muted);
          font-size: 11px;
          line-height: 1.7;
        }

        /* DEVELOPERS */

        .developers-heading {
          display: flex;
          justify-content: space-between;
          align-items: end;
          margin-top: 25px;
        }

        .developers-heading p {
          max-width: 330px;
          color: var(--cv-text-muted);
          font-size: 12px;
          line-height: 1.8;
        }

        .team-placeholder {
          position: relative;
          height: 500px;
          margin-top: 70px;
          overflow: hidden;
          border: 1px solid var(--cv-border);
          border-radius: 30px;
          background:
            radial-gradient(
              circle at 50% 50%,
              rgba(224, 82, 90, 0.08),
              transparent 35%
            ),
            #090c0d;
        }

        .team-placeholder .developer-stage {
          inset: 100px 0 auto;
        }

        .team-orbit {
          position: absolute;
          width: 500px;
          height: 500px;
          left: calc(50% - 250px);
          top: calc(50% - 250px);
          border: 1px solid rgba(224, 82, 90, 0.1);
          border-radius: 50%;
          animation: analytics-spin 30s linear infinite;
        }

        .team-orbit-small {
          width: 330px;
          height: 330px;
          left: calc(50% - 165px);
          top: calc(50% - 165px);
          border-color: rgba(233, 197, 140, 0.1);
          animation-direction: reverse;
        }

        .developer-link {
          display: flex;
          justify-content: center;
          margin-top: 28px;
        }

        .developer-link a {
          color: var(--cv-text-soft);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.14em;
        }

        .developer-link span {
          color: var(--cv-red);
          margin-left: 8px;
        }

        /* FINAL */

        .cv-final {
          position: relative;
          min-height: 720px;
          display: grid;
          place-items: center;
          overflow: hidden;
          text-align: center;
          border-bottom: 1px solid var(--cv-border);
        }

        .final-glow {
          position: absolute;
          width: 700px;
          height: 700px;
          left: calc(50% - 350px);
          top: calc(50% - 350px);
          border-radius: 50%;
          background: radial-gradient(
            circle,
            rgba(224, 82, 90, 0.11),
            transparent 65%
          );
        }

        .final-content {
          position: relative;
          z-index: 2;
        }

        .final-title {
          margin-top: 20px;
          font-size: clamp(70px, 10vw, 145px);
        }

        .final-content p {
          max-width: 500px;
          margin: 28px auto;
          color: var(--cv-text-muted);
          font-size: 13px;
          line-height: 1.8;
        }

        /* FOOTER */

        .cv-footer {
          padding: 45px 0;
        }

        .footer-inner {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          align-items: end;
          gap: 40px;
        }

        .cv-footer p {
          margin: 10px 0 0;
          color: var(--cv-text-muted);
          font-size: 9px;
        }

        .footer-links {
          display: flex;
          gap: 25px;
          color: var(--cv-text-muted);
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .footer-links a:hover {
          color: var(--cv-text);
        }

        .footer-copy {
          text-align: right;
          color: var(--cv-text-muted);
          font-size: 8px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        /* RESPONSIVE */

        @media (max-width: 900px) {
          .cv-nav-links {
            display: none;
          }

          .cv-hero {
            height: 900px;
          }

          .hero-title {
            font-size: clamp(48px, 11vw, 80px);
          }

          .developer-left {
            left: calc(50% - 220px);
          }

          .developer-right {
            left: calc(50% + 70px);
          }

          .intro-grid,
          .impact-heading,
          .tech-grid {
            grid-template-columns: 1fr;
            gap: 45px;
          }

          .domain-grid {
            grid-template-columns: 1fr;
          }

          .domain-card:last-child {
            grid-column: auto;
          }

          .impact-stats {
            grid-template-columns: 1fr 1fr;
          }

          .section-heading {
            display: block;
          }

          .section-heading > p {
            margin-top: 25px;
          }

          .developers-heading {
            display: block;
          }

          .developers-heading p {
            margin-top: 25px;
          }

          .footer-inner {
            grid-template-columns: 1fr;
            align-items: start;
          }

          .footer-copy {
            text-align: left;
          }
        }

        @media (max-width: 600px) {
          .cv-nav {
            height: 68px;
          }

          .cv-nav-cta {
            display: none;
          }

          .cv-hero {
            height: 820px;
            min-height: 820px;
          }

          .hero-content {
            margin-top: -100px;
          }

          .hero-title {
            font-size: 47px;
          }

          .hero-title-offset {
            margin-left: 0;
          }

          .hero-title-accent {
            font-size: 0.64em;
          }

          .hero-description {
            font-size: 11px;
            padding: 0 15px;
          }

          .hero-actions {
            flex-direction: column;
            align-items: center;
          }

          .scrollation-stage {
            width: 430px;
            height: 430px;
          }

          .developer-stage {
            bottom: 65px;
            height: 190px;
            scale: 0.7;
          }

          .developer-left {
            left: calc(50% - 185px);
          }

          .developer-center {
            left: calc(50% - 75px);
          }

          .developer-right {
            left: calc(50% + 35px);
          }

          .hero-bottom {
            left: 16px;
            right: 16px;
            grid-template-columns: 1fr 100px 1fr;
          }

          .cv-section {
            padding: 100px 0;
          }

          .section-title {
            font-size: 53px;
          }

          .domain-card {
            min-height: 500px;
          }

          .impact-stats {
            grid-template-columns: 1fr 1fr;
          }

          .stat-value {
            font-size: 35px;
          }

          .analytics-field {
            height: 300px;
          }

          .team-placeholder {
            height: 380px;
          }

          .team-placeholder .developer-stage {
            inset: 70px 0 auto;
          }

          .footer-links {
            flex-wrap: wrap;
          }
        }
      `}</style>
    </main>
  );
}
