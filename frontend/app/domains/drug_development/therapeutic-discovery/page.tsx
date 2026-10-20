/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 *
 * The page shell for
 * /domains/drug_development/therapeutic-discovery.
 *
 * Assembles:
 *   - Navbar (shared)
 *   - Hero (breadcrumb + hero block)
 *   - InputRegion (disease input + advanced handoff + loading)
 *   - Results (dispatcher: error / unresolved / partial /
 *     no_candidates / resolved)
 *   - ScientificAvatar (bottom-left guide)
 *   - Footer (shared)
 *
 * CSS import order (later wins at equal specificity):
 *   1. therapeutic-discovery.css   (page scope)
 *   2. components/components.css   (component scope)
 *   3. components/graph/graph.css  (graph scope)
 */

"use client";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

import "./therapeutic-discovery.css";
import "./components/components.css";
import "./components/graph/graph.css";

import { TDProvider } from "./state";

import Hero from "./components/Hero";
import InputRegion from "./components/InputRegion";
import Results from "./components/Results";
import ScientificAvatar from "./components/ScientificAvatar";

export default function TherapeuticDiscoveryPage() {
  return (
    <TDProvider>
      <main className="cv-thedisc-page">
        <Navbar />

        <Hero />

        <InputRegion />

        <Results />

        <ScientificAvatar />

        <Footer />
      </main>
    </TDProvider>
  );
}
