"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import "../biotechnology.css";
import "./plant-lifebook.css";

export default function PlantLifeBookPage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [plantName, setPlantName] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
  const [prepared, setPrepared] = useState(false);

  function handleImage(file?: File) {
    setError("");
    setPrepared(false);

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

  function prepareProfile() {
    setError("");
    setPrepared(false);

    if (!plantName.trim() && !image) {
      setError("Enter a plant name or upload a plant image first.");
      return;
    }

    setPrepared(true);
  }

  const sections = [
    {
      number: "01",
      label: "IDENTITY",
      title: "Taxonomy & Classification",
      description:
        "Scientific name, common names, botanical family, genus, species, and classification references.",
    },
    {
      number: "02",
      label: "MORPHOLOGY",
      title: "Physical Characteristics",
      description:
        "Documented leaf structure, flowers, fruit, stems, growth form, and other distinguishing features.",
    },
    {
      number: "03",
      label: "ECOLOGY",
      title: "Habitat & Distribution",
      description:
        "Reported native range, geographic distribution, habitat preferences, and ecological relationships.",
    },
    {
      number: "04",
      label: "CHEMISTRY",
      title: "Known Plant Compounds",
      description:
        "Reported chemical constituents and links to established compound databases where available.",
    },
    {
      number: "05",
      label: "BIOLOGY",
      title: "Biological Characteristics",
      description:
        "Growth patterns, life cycle, reproduction, adaptations, and documented biological properties.",
    },
    {
      number: "06",
      label: "RESEARCH",
      title: "Scientific Literature",
      description:
        "Traceable publications and research records, with findings distinguished from hypotheses.",
    },
  ];

  return (
    <main className="plb-page">
      <Navbar />

      <section className="plb-hero">
        <div className="plb-grid" aria-hidden="true" />
        <div className="plb-glow plb-glow-one" aria-hidden="true" />
        <div className="plb-glow plb-glow-two" aria-hidden="true" />

        <div className="plb-hero-inner">
          <Link href="/domains/biotechnology" className="plb-back-link">
            ← Biotechnology
          </Link>

          <div className="plb-eyebrow">
            <i />
            CUREVERSEAI <span> / </span> BOTANICAL KNOWLEDGE SYSTEM
          </div>

          <h1>
            Plant
            <br />
            <em>LifeBook.</em>
          </h1>

          <p className="plb-intro">
            Explore the biological identity of a plant through a structured
            botanical profile connecting taxonomy, morphology, ecology,
            chemical constituents, and scientific research.
          </p>

          <div className="plb-signals">
            <div>
              <strong>01</strong>
              <span>IDENTIFY</span>
            </div>
            <i />
            <div>
              <strong>02</strong>
              <span>EXPLORE</span>
            </div>
            <i />
            <div>
              <strong>03</strong>
              <span>VERIFY</span>
            </div>
          </div>

          <a className="plb-scroll" href="#plb-workspace">
            EXPLORE A PLANT <span>↓</span>
          </a>
        </div>

        <div className="plb-orbit-art" aria-hidden="true">
          <div className="plb-orbit plb-orbit-a" />
          <div className="plb-orbit plb-orbit-b" />
          <div className="plb-orbit plb-orbit-c" />
          <div className="plb-plant-mark">
            <span>✳</span>
            <i />
          </div>
          <span className="plb-art-label">BOTANICAL RECORD / 001</span>
        </div>

        <div className="plb-hero-footer">
          <span>BOTANICAL INTELLIGENCE</span>
          <span>KNOWLEDGE · EVIDENCE · DISCOVERY</span>
        </div>
      </section>

      <section className="plb-workspace" id="plb-workspace">
        <div className="plb-section-heading">
          <div className="plb-eyebrow">
            <i /> BEGIN YOUR INVESTIGATION
          </div>
          <h2>
            Open a plant <em>record.</em>
          </h2>
          <p>
            Search for a known plant or provide an image to begin preparing
            its botanical profile.
          </p>
        </div>

        <div className="plb-search-grid">
          <div className="plb-panel">
            <div className="plb-panel-top">
              <span>01 / PLANT LOOKUP</span>
              <span className="plb-status"><i /> NAME SEARCH</span>
            </div>

            <label htmlFor="plb-plant-name">COMMON OR SCIENTIFIC NAME</label>
            <input
              id="plb-plant-name"
              value={plantName}
              onChange={(event) => {
                setPlantName(event.target.value);
                setPrepared(false);
              }}
              placeholder="e.g. Azadirachta indica"
            />

            <p className="plb-input-note">
              A scientific name can help distinguish between species that
              share a common name.
            </p>
          </div>

          <div className="plb-panel">
            <div className="plb-panel-top">
              <span>02 / IMAGE REFERENCE</span>
              <span className="plb-status"><i /> OPTIONAL</span>
            </div>

            <button
              type="button"
              className={`plb-dropzone ${image ? "has-image" : ""}`}
              onClick={() => fileInput.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                handleImage(event.dataTransfer.files?.[0]);
              }}
            >
              {image ? (
                <>
                  <img src={image} alt="Uploaded plant reference" />
                  <span className="plb-change-image">
                    {fileName} · Click to change
                  </span>
                </>
              ) : (
                <>
                  <span className="plb-upload-symbol">↑</span>
                  <strong>Add a plant photograph</strong>
                  <span>Choose an image or drag it here</span>
                  <small>JPG · PNG · WEBP / MAX 10 MB</small>
                </>
              )}
            </button>

            <input
              ref={fileInput}
              type="file"
              accept="image/*"
              hidden
              onChange={(event) => handleImage(event.target.files?.[0])}
            />
          </div>
        </div>

        {error && <p className="plb-error">{error}</p>}

        <button
          type="button"
          className="plb-primary-button"
          onClick={prepareProfile}
        >
          PREPARE BOTANICAL PROFILE <span>↗</span>
        </button>

        {prepared && (
          <div className="plb-message" aria-live="polite">
            <strong>Profile request prepared.</strong>
            <p>
              {plantName.trim()
                ? `Plant query: ${plantName.trim()}.`
                : "An image reference has been selected."}{" "}
              External botanical database retrieval and image identification
              are not connected yet. No botanical facts have been inferred
              from the input.
            </p>
          </div>
        )}
      </section>

      <section className="plb-profile-section">
        <div className="plb-section-heading">
          <div className="plb-eyebrow">
            <i /> BOTANICAL PROFILE STRUCTURE
          </div>
          <h2>
            One plant. <em>Many dimensions.</em>
          </h2>
          <p>
            Each section is designed to be populated from established
            botanical databases and traceable scientific sources.
          </p>
        </div>

        <div className="plb-profile-grid">
          {sections.map((section) => (
            <article className="plb-profile-card" key={section.number}>
              <div className="plb-card-top">
                <span>{section.number}</span>
                <span>{section.label}</span>
              </div>
              <h3>{section.title}</h3>
              <p>{section.description}</p>
              <span className="plb-card-mark">↗</span>
            </article>
          ))}
        </div>
      </section>

      <section className="plb-source-note">
        <span>i</span>
        <div>
          <strong>Evidence is part of the profile.</strong>
          <p>
            Botanical records can vary in completeness and certainty.
            Scientific names, reported traits, compound records, and research
            findings should retain their source references. An image match
            alone does not establish a definitive species identification.
          </p>
        </div>
      </section>

      <footer className="plb-footer">
        <Link href="/domains/biotechnology">← Return to Biotechnology</Link>
        <span>CUREVERSEAI · BOTANICAL KNOWLEDGE SYSTEM</span>
      </footer>
    </main>
  );
}
