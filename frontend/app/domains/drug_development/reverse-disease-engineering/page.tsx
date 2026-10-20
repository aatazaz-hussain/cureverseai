/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 *
 * The page shell for /domains/drug_development/reverse-disease-engineering.
 *
 * Assembles:
 *   - Navbar (shared)
 *   - Hero (breadcrumb + hero block)
 *   - InputRegion (disease input + ChEMBL toggle + loading)
 *   - Results (dispatcher: error / unresolved / partial / resolved)
 *   - Footer (shared)
 *
 * Every real behaviour lives in a component or in the
 * Context. This file only composes and mounts.
 *
 * CSS import order:
 *   1. reverse-disease-engineering.css  (page scope)
 *   2. components/components.css        (component scope)
 *   3. components/graph/graph.css       (graph scope)
 *
 * Later imports win at equal specificity, so the page
 * rules come first and the tightest scopes come last.
 */

"use client";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

import "./reverse-disease-engineering.css";
import "./components/components.css";
import "./components/graph/graph.css";

import { RDEProvider } from "./state";

import Hero from "./components/Hero";
import InputRegion from "./components/InputRegion";
import Results from "./components/Results";
import ScientificAvatar from "./components/ScientificAvatar";

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ReverseDiseaseEngineeringPage() {
  return (
    <RDEProvider>
      <main className="cv-revdis-page">
        <Navbar />

        <Hero />

        <InputRegion />

        <Results />

        <ScientificAvatar />

        <Footer />
      </main>
    </RDEProvider>
  );
}
