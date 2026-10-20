"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow hero.
 *
 * Two-column layout:
 *   - Left: breadcrumb, kicker (numbered disc), h1 with italic
 *     accent, subtitle, optional status chip.
 *   - Right: framed square visual with ambient scan overlay
 *     and a corner label.
 *
 * This is the language used by the drug_development workflow
 * pages. The image is presented inside a bordered frame with a
 * scan animation, not as a full-bleed background.
 */

import Link from "next/link";
import type { ReactNode } from "react";

interface Props {
  kicker: string;
  kickerNumber?: string;
  title: string;
  titleEm?: string;
  subtitle: string;
  heroImage: string;
  heroAlt: string;
  visualLabel?: string;
  visualStage?: string;
  accent?: "cyan" | "gold" | "red";
  statusChip?: ReactNode;
  breadcrumbLabel?: string;
}

export default function Hero({
  kicker,
  kickerNumber = "01",
  title,
  titleEm,
  subtitle,
  heroImage,
  heroAlt,
  visualLabel = "MEDICINE SIMULATION",
  visualStage = "01 / 03",
  accent = "red",
  statusChip,
  breadcrumbLabel,
}: Props) {
  return (
    <>
      <div className="cv-medicine-wf-breadcrumb">
        <Link href="/domains/medicine">Medicine</Link>
        <i />
        <strong>{breadcrumbLabel ?? kicker}</strong>
      </div>

      <section className={`cv-medicine-wf-hero cv-medicine-wf-hero--${accent}`}>
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-one" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-two" />

        <div className="cv-medicine-wf-hero-inner">
          <div className="cv-medicine-wf-hero-copy">
            <div className="cv-medicine-wf-hero-kicker">
              <span>{kickerNumber}</span>
              <i />
              {kicker}
            </div>

            <h1>
              {title}
              {titleEm ? (
                <>
                  <br />
                  <em>{titleEm}</em>
                </>
              ) : null}
            </h1>

            <p className="cv-medicine-wf-hero-sub">{subtitle}</p>

            {statusChip ? (
              <div className="cv-medicine-wf-hero-status">{statusChip}</div>
            ) : null}
          </div>

          <div className="cv-medicine-wf-hero-visual">
            <div className="cv-medicine-wf-hero-visual-frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={heroImage} alt={heroAlt} draggable={false} />
              <div className="cv-medicine-wf-hero-visual-scan" />
              <div className="cv-medicine-wf-hero-visual-label">
                <span>{visualLabel}</span>
                <strong>{visualStage}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
