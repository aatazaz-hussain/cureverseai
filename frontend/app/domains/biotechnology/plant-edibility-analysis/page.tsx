"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import "../biotechnology.css";
import "./plant-edibility.css";

type Assessment = {
  status: "Edible" | "Non-edible" | "Uncertain";
  title: string;
  description: string;
};

export default function PlantEdibilityAnalysisPage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [plantName, setPlantName] = useState("");
  const [error, setError] = useState("");
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  function handleFile(file?: File) {
    setError("");
    setAssessment(null);

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("Image size must be 10 MB or less.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setImage(reader.result);
        setFileName(file.name);
      }
    };
    reader.readAsDataURL(file);
  }

  function prepareAssessment() {
    setError("");
    setAssessment(null);

    if (!image && !plantName.trim()) {
      setError("Upload a plant image or enter a plant name to continue.");
      return;
    }

    setAssessment({
      status: "Uncertain",
      title: "Identification and evidence retrieval required",
      description:
        "No edibility conclusion has been made. The plant must first be identified and its edibility checked against reliable botanical and toxicity references. Do not consume a plant based on this page or an image alone.",
    });
  }

  return (
    <main className="plant-edibility-page">
      <Navbar />

      <section className="edibility-hero">
        <div className="edibility-orbit edibility-orbit-one" />
        <div className="edibility-orbit edibility-orbit-two" />

        <div className="edibility-hero-content">
          <Link
            href="/domains/biotechnology"
            className="edibility-back-link"
          >
            ← Biotechnology
          </Link>

          <span className="edibility-eyebrow">
            CUREVERSEAI · BOTANICAL SAFETY INTELLIGENCE
          </span>

          <h1>
            Plant <span>Edibility</span> Analysis
          </h1>

          <p className="edibility-hero-description">
            Investigate plant identity, documented edibility, and known
            toxicity evidence through a safety-first botanical workflow.
          </p>

          <div className="edibility-hero-points">
            <span>Plant identification</span>
            <span>Evidence-based assessment</span>
            <span>Toxicity awareness</span>
          </div>
        </div>
      </section>

      <section className="edibility-workspace">
        <div className="edibility-section-heading">
          <span className="edibility-section-kicker">INVESTIGATION WORKSPACE</span>
          <h2>Examine a Plant</h2>
          <p>
            Provide an image or plant name to prepare an edibility
            investigation.
          </p>
        </div>

        <div className="edibility-input-grid">
          <div className="edibility-panel edibility-upload-panel">
            <div className="edibility-panel-heading">
              <span className="edibility-step">01</span>
              <div>
                <h3>Upload Plant Image</h3>
                <p>Use a clear image showing leaves, flowers, or fruit.</p>
              </div>
            </div>

            <button
              type="button"
              className={`edibility-dropzone ${image ? "has-image" : ""}`}
              onClick={() => fileInput.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                handleFile(event.dataTransfer.files?.[0]);
              }}
            >
              {image ? (
                <>
                  <img src={image} alt="Selected plant preview" />
                  <span className="edibility-file-name">{fileName}</span>
                  <span className="edibility-change-image">
                    Click to change image
                  </span>
                </>
              ) : (
                <>
                  <span className="edibility-upload-icon">↑</span>
                  <strong>Choose a plant image</strong>
                  <span>or drag and drop it here</span>
                  <small>JPG, PNG, WEBP · Maximum 10 MB</small>
                </>
              )}
            </button>

            <input
              ref={fileInput}
              type="file"
              accept="image/*"
              hidden
              onChange={(event) => handleFile(event.target.files?.[0])}
            />
          </div>

          <div className="edibility-panel edibility-name-panel">
            <div className="edibility-panel-heading">
              <span className="edibility-step">02</span>
              <div>
                <h3>Plant Name</h3>
                <p>Already know the plant? Enter its name.</p>
              </div>
            </div>

            <label htmlFor="edibility-plant-name">Common or scientific name</label>
            <input
              id="edibility-plant-name"
              className="edibility-name-input"
              value={plantName}
              onChange={(event) => {
                setPlantName(event.target.value);
                setAssessment(null);
              }}
              placeholder="e.g. Ocimum tenuiflorum"
            />

            <div className="edibility-info-box">
              <span>i</span>
              <p>
                Common names can refer to different species. Scientific names
                help make evidence retrieval more precise.
              </p>
            </div>

            <button
              type="button"
              className="edibility-analyze-button"
              onClick={prepareAssessment}
            >
              Prepare Edibility Investigation <span>→</span>
            </button>

            {error && <p className="edibility-error">{error}</p>}
          </div>
        </div>

        {assessment && (
          <section className="edibility-result-panel" aria-live="polite">
            <div className="edibility-result-topline">
              <span>PRELIMINARY STATUS</span>
              <span className="edibility-status-badge">
                {assessment.status}
              </span>
            </div>
            <h3>{assessment.title}</h3>
            <p>{assessment.description}</p>
            <div className="edibility-result-next">
              <strong>Next step</strong>
              <span>
                Connect a plant-identification service and authoritative
                edibility and toxicity references before making an assessment.
              </span>
            </div>
          </section>
        )}
      </section>

      <section className="edibility-evidence-section">
        <div className="edibility-section-heading">
          <span className="edibility-section-kicker">ASSESSMENT FRAMEWORK</span>
          <h2>What the Investigation Will Examine</h2>
          <p>
            A reliable assessment needs more than visual similarity.
          </p>
        </div>

        <div className="edibility-evidence-grid">
          <article className="edibility-evidence-card">
            <span>01 / IDENTITY</span>
            <h3>Botanical Identification</h3>
            <p>
              Candidate species, scientific name, distinguishing features,
              and identification confidence where available.
            </p>
          </article>

          <article className="edibility-evidence-card">
            <span>02 / EDIBILITY</span>
            <h3>Documented Food Use</h3>
            <p>
              Reliable references describing whether a species or specific
              plant part has documented food use.
            </p>
          </article>

          <article className="edibility-evidence-card">
            <span>03 / TOXICITY</span>
            <h3>Known Hazards</h3>
            <p>
              Reported toxic compounds, hazardous plant parts, and documented
              risks when supported by reliable sources.
            </p>
          </article>

          <article className="edibility-evidence-card">
            <span>04 / EVIDENCE</span>
            <h3>Source Verification</h3>
            <p>
              Traceable references, uncertainty, and clear separation between
              documented facts and unresolved questions.
            </p>
          </article>
        </div>
      </section>

      <section className="edibility-safety-banner">
        <span className="edibility-safety-symbol">!</span>
        <div>
          <h3>Never use image analysis alone to decide whether to eat a plant.</h3>
          <p>
            Similar-looking species can have very different toxicity profiles.
            This tool is not a food-safety certification. Do not consume an
            unidentified plant or rely on an uncertain assessment.
          </p>
        </div>
      </section>

      <footer className="edibility-footer">
        <Link href="/domains/biotechnology">← Return to Biotechnology</Link>
        <span>CureVerseAI · Evidence before conclusions</span>
      </footer>
    </main>
  );
}
