/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Hero.
 *
 * Breadcrumb + hero section. Static, presentational.
 *
 * Layout:
 *   - Breadcrumb strip (Drug Development → Reverse Disease Engineering)
 *   - Two-column hero
 *       left  : eyebrow, headline, description, CTA anchor
 *       right : corner-labeled image frame with scan line
 *
 * The hero image is reused from the existing
 * /public/drug-development/ folder. If a W02-specific
 * image is added later, swap the `HERO_IMAGE` constant.
 */

"use client";

const HERO_IMAGE = "/drug-development/disease-hero.png";

// ---------------------------------------------------------------------------
// Per-letter text — produces a cascade hover effect.
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
    <span className={`cv-revdis-per-letter ${className}`.trim()}>
      {letters.map((ch, i) => (
        <span
          key={i}
          className="cv-revdis-letter"
          style={{ ["--i" as string]: i }}
          aria-hidden="true"
        >
          {ch === " " ? "\u00A0" : ch}
        </span>
      ))}
    </span>
  );
}

export default function Hero() {
  return (
    <>
      <Breadcrumb />
      <section className="cv-revdis-hero">
        <div className="cv-revdis-hero-grid" />
        <div className="cv-revdis-hero-glow cv-revdis-hero-glow-one" />
        <div className="cv-revdis-hero-glow cv-revdis-hero-glow-two" />

        <div className="cv-revdis-hero-inner">
          <div className="cv-revdis-hero-copy">
            <div className="cv-revdis-hero-kicker">
              <span>02</span>
              <i />
              REVERSE DISEASE ENGINEERING
            </div>

            <h1 className="cv-revdis-hero-title">
              <PerLetterText text="Why does" />
              <br />
              <PerLetterText text="the disease" />{" "}
              <em>
                <PerLetterText text="happen?" />
              </em>
            </h1>

            <p className="cv-revdis-hero-sub">
              Enter a disease. CureVerseAI resolves it against
              biological sources, then reconstructs the chain of
              phenotypes, mechanisms, genes, and pathways that
              may explain it — every relationship grounded in
              evidence with its support classification made
              explicit.
            </p>

            <div className="cv-revdis-hero-meta">
              <div>
                <strong>4</strong>
                <span>INVESTIGATION LAYERS</span>
              </div>
              <div>
                <strong>6</strong>
                <span>EVIDENCE SOURCES</span>
              </div>
              <div>
                <strong>01</strong>
                <span>CONNECTED GRAPH</span>
              </div>
            </div>
          </div>

          <div className="cv-revdis-hero-visual">
            <div className="cv-revdis-hero-visual-frame">
              <img
                src={HERO_IMAGE}
                alt="Mechanistic investigation visualisation"
                draggable={false}
              />
              <div className="cv-revdis-hero-visual-scan" />
              <div className="cv-revdis-hero-visual-label">
                <span>MECHANISM INVESTIGATION</span>
                <strong>02 / 03</strong>
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
    <nav className="cv-revdis-breadcrumb" aria-label="Breadcrumb">
      <a href="/domains/drug_development">Drug Development</a>
      <i />
      <strong>Reverse Disease Engineering</strong>
    </nav>
  );
}
