/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Hero.
 *
 * Breadcrumb + hero block. Static, presentational.
 */

"use client";

const HERO_IMAGE = "/drug-development/medicine.png";

// ---------------------------------------------------------------------------
// Per-letter text
// ---------------------------------------------------------------------------

function PerLetterText({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) {
  const letters = Array.from(text);
  return (
    <span
      className={`cv-thedisc-per-letter ${className}`.trim()}
    >
      {letters.map((ch, i) => (
        <span
          key={i}
          className="cv-thedisc-letter"
          style={{ ["--i" as string]: i }}
          aria-hidden="true"
        >
          {ch === " " ? "\u00A0" : ch}
        </span>
      ))}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Hero
// ---------------------------------------------------------------------------

export default function Hero() {
  return (
    <>
      <Breadcrumb />
      <section className="cv-thedisc-hero">
        <div className="cv-thedisc-hero-grid" />
        <div className="cv-thedisc-hero-glow cv-thedisc-hero-glow-one" />
        <div className="cv-thedisc-hero-glow cv-thedisc-hero-glow-two" />

        <div className="cv-thedisc-hero-inner">
          <div className="cv-thedisc-hero-copy">
            <div className="cv-thedisc-hero-kicker">
              <span>03</span>
              <i />
              THERAPEUTIC DISCOVERY
            </div>

            <h1 className="cv-thedisc-hero-title">
              <PerLetterText text="Find an" />
              <br />
              <PerLetterText text="intervention." />
            </h1>

            <p className="cv-thedisc-hero-sub">
              Connect a disease or a mechanism from Workflow 02
              to the targets and compounds that might change it.
              Every compound is drawn from real experimental
              records. Every link in the mechanism-of-action
              chain is labeled with how strongly it is
              supported.
            </p>

            <div className="cv-thedisc-hero-meta">
              <div>
                <strong>3</strong>
                <span>INVESTIGATION LAYERS</span>
              </div>
              <div>
                <strong>5</strong>
                <span>EVIDENCE SOURCES</span>
              </div>
              <div>
                <strong>01</strong>
                <span>CONNECTED GRAPH</span>
              </div>
            </div>
          </div>

          <div className="cv-thedisc-hero-visual">
            <div className="cv-thedisc-hero-visual-frame">
              <img
                src={HERO_IMAGE}
                alt="Therapeutic intervention visualisation"
                draggable={false}
              />
              <div className="cv-thedisc-hero-visual-scan" />
              <div className="cv-thedisc-hero-visual-label">
                <span>THERAPEUTIC HYPOTHESIS</span>
                <strong>03 / 03</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

// ---------------------------------------------------------------------------
// Breadcrumb
// ---------------------------------------------------------------------------

function Breadcrumb() {
  return (
    <nav
      className="cv-thedisc-breadcrumb"
      aria-label="Breadcrumb"
    >
      <a href="/domains/drug_development">Drug Development</a>
      <i />
      <strong>Therapeutic Discovery</strong>
    </nav>
  );
}
