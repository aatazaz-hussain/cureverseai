"use client";

import { useRef, useState } from "react";

type PlantResult = {
  success: boolean;
  workflow: string;
  identification?: { method?: string; candidates?: Array<{ scientificName?: string; commonName?: string; confidence?: string; reasoning?: string }> };
  investigations?: Array<{
    candidate?: { scientificName?: string; commonName?: string; confidence?: string; reasoning?: string };
    taxonomy?: { available?: boolean; source?: string; sourceUrl?: string; record?: Record<string, unknown> };
    literature?: { available?: boolean; source?: string; sourceUrl?: string; totalResults?: number; records?: Array<{ title?: string; authors?: string; year?: string | number; doi?: string; pmid?: string; abstract?: string; url?: string }> };
  }>;
  assessment?: { medicinalUse?: { status?: string; reason?: string }; compounds?: { status?: string; reason?: string } };
  limitations?: string[];
};
import Navbar from "@/components/Navbar";
import "../biotechnology.css";
import "./medicinal-plant.css";

export default function MedicinalPlantIntelligencePage() {
  const [plantName, setPlantName] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [mode, setMode] = useState<"image" | "name">("image");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlantResult | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function chooseImage(file?: File) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setMessage("Please choose a valid image file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setMessage("Please choose an image smaller than 10 MB.");
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setImage(file);
    setPreview(URL.createObjectURL(file));
    setMessage("");
  }

  async function submitInvestigation() {
    if (loading) return;
    if (mode === "image" && !image) {
      setMessage("Upload a clear plant image to begin.");
      return;
    }
    if (mode === "name" && !plantName.trim()) {
      setMessage("Enter a plant name to begin.");
      return;
    }

    setLoading(true);
    setResult(null);
    setMessage("Investigating botanical records and scientific literature. This may take a little time.");

    try {
      const body = new FormData();
      body.append("mode", "medicinal");
      if (mode === "image" && image) body.append("image", image);
      if (mode === "name") body.append("plantName", plantName.trim());

      const response = await fetch("/api/biotechnology/plant", {
        method: "POST",
        body,
      });
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.error || "The investigation could not be completed.");
      }

      setResult(data as PlantResult);
      setMessage("Investigation completed. Review the sources and limitations below.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Request failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="cv-biotechnology-page mpi-page">
      <Navbar />

      <section className="mpi-hero">
        <div className="mpi-grid" />
        <div className="mpi-glow mpi-glow-one" />
        <div className="mpi-glow mpi-glow-two" />

        <div className="mpi-hero-inner">
          <div className="mpi-eyebrow">
            <span>01</span><i />
            <strong>BIOTECHNOLOGY / PLANT INTELLIGENCE</strong>
          </div>

          <h1>
            Plants hold
            <br />
            <em>stories untold.</em>
          </h1>

          <p className="mpi-intro">
            Investigate medicinal plants through botanical identification,
            documented traditional uses, known compounds, and scientific
            evidence — all in one connected workspace.
          </p>

          <div className="mpi-signals">
            <div><strong>01</strong><span>IDENTIFY</span></div>
            <i />
            <div><strong>02</strong><span>INVESTIGATE</span></div>
            <i />
            <div><strong>03</strong><span>VERIFY EVIDENCE</span></div>
          </div>

          <a href="#mpi-investigate" className="mpi-scroll">
            BEGIN INVESTIGATION <span>↓</span>
          </a>
        </div>

        <div className="mpi-orbit-art" aria-hidden="true">
          <div className="mpi-orbit mpi-orbit-a" />
          <div className="mpi-orbit mpi-orbit-b" />
          <div className="mpi-orbit mpi-orbit-c" />
          <div className="mpi-plant-mark">
            <span>✳</span>
            <i />
          </div>
          <div className="mpi-art-label">BOTANICAL INTELLIGENCE / 01</div>
        </div>

        <div className="mpi-hero-footer">
          <span>CUREVERSEAI / BIOTECHNOLOGY</span>
          <span>OBSERVE — IDENTIFY — INVESTIGATE</span>
        </div>
      </section>

      <section className="mpi-workspace" id="mpi-investigate">
        <div className="mpi-section-heading">
          <div className="mpi-eyebrow">
            <span>02</span><i />
            <strong>START YOUR INVESTIGATION</strong>
          </div>
          <h2>
            Begin with a plant.
            <br />
            <em>Follow the evidence.</em>
          </h2>
          <p>
            Upload a plant photograph or enter its name. The investigation
            workflow will connect botanical information with documented
            medicinal uses and available scientific literature.
          </p>
        </div>

        <div className="mpi-workspace-grid">
          <div className="mpi-panel mpi-input-panel">
            <div className="mpi-panel-top">
              <span>INVESTIGATION INPUT</span>
              <span className="mpi-status"><i /><span>READY</span></span>
            </div>

            <div className="mpi-tabs">
              <button
                type="button"
                className={mode === "image" ? "active" : ""}
                onClick={() => { setMode("image"); setMessage(""); }}
              >
                <span>01</span> Plant image
              </button>
              <button
                type="button"
                className={mode === "name" ? "active" : ""}
                onClick={() => { setMode("name"); setMessage(""); }}
              >
                <span>02</span> Plant name
              </button>
            </div>

            {mode === "image" ? (
              <button
                type="button"
                className={`mpi-dropzone ${preview ? "has-image" : ""}`}
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  chooseImage(e.dataTransfer.files?.[0]);
                }}
              >
                {preview ? (
                  <>
                    <img src={preview} alt="Selected plant preview" />
                    <span className="mpi-change-image">CHANGE IMAGE</span>
                  </>
                ) : (
                  <>
                    <span className="mpi-upload-symbol">↑</span>
                    <strong>Drop a plant image here</strong>
                    <span>or click to browse your files</span>
                    <small>JPG, PNG, WEBP · Maximum 10 MB</small>
                  </>
                )}
              </button>
            ) : (
              <div className="mpi-name-entry">
                <label htmlFor="mpi-plant-name">PLANT NAME</label>
                <input
                  id="mpi-plant-name"
                  value={plantName}
                  onChange={(e) => { setPlantName(e.target.value); setMessage(""); }}
                  placeholder="e.g. Azadirachta indica"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") submitInvestigation();
                  }}
                />
                <p>Common names and scientific names can be entered.</p>
              </div>
            )}

            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              hidden
              onChange={(e) => chooseImage(e.target.files?.[0])}
            />

            {message && <div className="mpi-message" role="status">{message}</div>}

            <button
              type="button"
              className="mpi-primary-button"
              onClick={submitInvestigation}
              disabled={loading}
            >
              {loading ? "INVESTIGATING..." : "RUN INVESTIGATION"} <span>{loading ? "…" : "↗"}</span>
            </button>

            <p className="mpi-input-note">
              Identification from an image may be uncertain. Verify candidate
              species before drawing conclusions about medicinal use.
            </p>
          </div>

          {result && (
            <section className="mpi-results" aria-live="polite">
              <div className="mpi-results-heading">
                <div className="mpi-eyebrow"><span>04</span><i /><strong>RETRIEVED FINDINGS</strong></div>
                <h2>Botanical records.<br /><em>Evidence to explore.</em></h2>
              </div>

              {(result.investigations || []).map((item, index) => {
                const tax = item.taxonomy?.record;
                const papers = item.literature?.records || [];
                const candidate = item.candidate;
                return (
                  <article className="mpi-result-card" key={`${candidate?.scientificName || "candidate"}-${index}`}>
                    <div className="mpi-panel-top">
                      <span>SPECIES CANDIDATE {String(index + 1).padStart(2, "0")}</span>
                      <span className="mpi-index">{candidate?.confidence || "UNVERIFIED"}</span>
                    </div>
                    <h3>{candidate?.scientificName || "Unresolved plant candidate"}</h3>
                    {candidate?.commonName && <p className="mpi-result-common">{candidate.commonName}</p>}
                    <p className="mpi-result-note">{candidate?.reasoning || "Candidate identity requires independent verification."}</p>

                    <h4>BOTANICAL TAXONOMY</h4>
                    {item.taxonomy?.available && tax ? (
                      <>
                        <dl className="mpi-taxonomy">
                          {["kingdom", "phylum", "class", "order", "family", "genus", "species", "taxonomicStatus", "rank"].map((key) =>
                            tax[key] != null ? (
                              <div key={key}><dt>{key.replace(/([A-Z])/g, " $1")}</dt><dd>{String(tax[key])}</dd></div>
                            ) : null
                          )}
                        </dl>
                        {item.taxonomy.sourceUrl && <a className="mpi-source-link" href={item.taxonomy.sourceUrl} target="_blank" rel="noreferrer">OPEN GBIF RECORD ↗</a>}
                      </>
                    ) : <p className="mpi-result-note">Taxonomy was unavailable for this candidate.</p>}

                    <h4>SCIENTIFIC LITERATURE {item.literature?.totalResults != null ? `· ${item.literature.totalResults.toLocaleString()} SEARCH RESULTS` : ""}</h4>
                    {papers.length ? (
                      <div className="mpi-paper-list">
                        {papers.slice(0, 8).map((paper, paperIndex) => (
                          <article className="mpi-paper" key={`${paper.doi || paper.pmid || paper.title}-${paperIndex}`}>
                            <h5>{paper.title || "Untitled research record"}</h5>
                            <p>{[paper.authors, paper.year].filter(Boolean).join(" · ")}</p>
                            {paper.abstract && <details><summary>Read available abstract</summary><p className="mpi-paper-abstract">{paper.abstract.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim()}</p></details>}
                            {paper.url && <a className="mpi-source-link" href={paper.url} target="_blank" rel="noreferrer">VIEW PUBLICATION ↗</a>}
                          </article>
                        ))}
                      </div>
                    ) : <p className="mpi-result-note">No literature records were returned.</p>}
                  </article>
                );
              })}

              <div className="mpi-result-card mpi-result-caution">
                <h3>Interpretation & limitations</h3>
                <p><strong>Medicinal efficacy:</strong> {result.assessment?.medicinalUse?.status || "Not established"}.</p>
                <p>{result.assessment?.medicinalUse?.reason || "Search results need individual critical appraisal; publication alone does not establish clinical benefit."}</p>
                <p><strong>Compounds:</strong> {result.assessment?.compounds?.status || "Not retrieved"}.</p>
                <p>Taxonomy and literature results do not confirm image identity, treatment effectiveness, dosage, or plant safety.</p>
                {!!result.limitations?.length && <ul>{result.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul>}
              </div>
            </section>
          )}

          <div className="mpi-panel mpi-evidence-panel">
            <div className="mpi-panel-top">
              <span>INVESTIGATION FRAMEWORK</span>
              <span className="mpi-index">03 / EVIDENCE</span>
            </div>

            <div className="mpi-evidence-list">
              <article className="mpi-evidence-item">
                <span className="mpi-evidence-number">01</span>
                <div>
                  <h3>Botanical identity</h3>
                  <p>Candidate species, scientific name, and taxonomy.</p>
                </div>
                <span className="mpi-arrow">↗</span>
              </article>
              <article className="mpi-evidence-item">
                <span className="mpi-evidence-number">02</span>
                <div>
                  <h3>Traditional medicinal use</h3>
                  <p>Documented traditional uses, clearly labelled as such.</p>
                </div>
                <span className="mpi-arrow">↗</span>
              </article>
              <article className="mpi-evidence-item">
                <span className="mpi-evidence-number">03</span>
                <div>
                  <h3>Known compounds</h3>
                  <p>Reported constituents and their available references.</p>
                </div>
                <span className="mpi-arrow">↗</span>
              </article>
              <article className="mpi-evidence-item">
                <span className="mpi-evidence-number">04</span>
                <div>
                  <h3>Scientific evidence</h3>
                  <p>Experimental findings distinguished from clinical evidence.</p>
                </div>
                <span className="mpi-arrow">↗</span>
              </article>
            </div>

            <div className="mpi-evidence-footer">
              <span><i /> EVIDENCE-FIRST APPROACH</span>
              <p>Traditional use is not proof of clinical effectiveness.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mpi-principles">
        <div className="mpi-principles-heading">
          <div className="mpi-eyebrow">
            <span>03</span><i />
            <strong>HOW TO READ THE FINDINGS</strong>
          </div>
          <h2>Different evidence.
            <br /><em>Different conclusions.</em>
          </h2>
        </div>

        <div className="mpi-principle-grid">
          <article className="mpi-principle-card">
            <span>01 / TRADITION</span>
            <h3>Traditional use</h3>
            <p>Records how a plant has historically been used, without treating tradition alone as proof of efficacy.</p>
          </article>
          <article className="mpi-principle-card">
            <span>02 / LABORATORY</span>
            <h3>Experimental activity</h3>
            <p>Reports laboratory or preclinical findings in their proper context, including study limitations.</p>
          </article>
          <article className="mpi-principle-card">
            <span>03 / CLINICAL</span>
            <h3>Clinical evidence</h3>
            <p>Separately identifies human clinical evidence where reliable sources are available.</p>
          </article>
        </div>

        <div className="mpi-safety-note">
          <span>!</span>
          <p>
            <strong>Scientific context matters.</strong> This tool is for
            research and educational exploration, not diagnosis, treatment
            recommendations, or confirmation that a plant is safe to consume.
          </p>
        </div>
      </section>

      <footer className="mpi-footer">
        <span>CUREVERSEAI / MEDICINAL PLANT INTELLIGENCE</span>
        <a href="/domains/biotechnology">← BACK TO BIOTECHNOLOGY</a>
      </footer>
    </main>
  );
}
