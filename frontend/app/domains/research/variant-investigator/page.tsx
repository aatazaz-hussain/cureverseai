"use client";

import { FormEvent, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./variant-investigator.css";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AnyRecord = Record<string, any>;

function clean(value: any): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function first(...values: any[]): any {
  for (const value of values) {
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return "";
}

function formatName(value: any, fallback = "—"): string {
  const text = clean(value);
  if (!text) return fallback;

  const sourceIndex = text.indexOf(" [Source:");
  return sourceIndex >= 0
    ? text.slice(0, sourceIndex).trim()
    : text;
}

function parseVariant(variant: string) {
  const value = variant.trim().toUpperCase();

  const match = value.match(/^([A-Z])(\d+)([A-Z*])$/);

  if (!match) {
    return {
      reference: "",
      position: "",
      alternate: "",
      type: "Protein-level variant",
    };
  }

  const reference = match[1];
  const position = match[2];
  const alternate = match[3];

  let type = "Missense";

  if (alternate === "*") {
    type = "Nonsense";
  } else if (reference === alternate) {
    type = "Synonymous";
  }

  return {
    reference,
    position,
    alternate,
    type,
  };
}

function getEntities(result: AnyRecord) {
  const context = result?.biological_context || {};
  return (
    context?.reactome_entities ||
    context?.reactome ||
    result?.reactome_entities ||
    []
  );
}

function getSequence(result: AnyRecord): string {
  const candidates = [
    result?.canonical_sequence,
    result?.protein_features?.sequence,
    result?.protein_features?.protein_sequence,
    result?.integrated_features?.protein?.sequence,
    result?.integrated_features?.protein_features?.sequence,
  ];

  for (const candidate of candidates) {
    const value = clean(candidate).replace(/\s+/g, "");
    if (
      value.length >= 30 &&
      /^[ACDEFGHIKLMNPQRSTVWYBXZJUO]+$/i.test(value)
    ) {
      return value;
    }
  }

  return "";
}

function evidenceCount(result: AnyRecord): number {
  const reasoning = result?.evidence_reasoning || {};
  const sources = reasoning?.sources;

  if (Array.isArray(sources)) return sources.length;

  const evidence = result?.evidence;
  if (Array.isArray(evidence)) return evidence.length;

  return 0;
}

export default function VariantInvestigatorPage() {
  const [gene, setGene] = useState("");
  const [variant, setVariant] = useState("");
  const [submittedGene, setSubmittedGene] = useState("");
  const [submittedVariant, setSubmittedVariant] = useState("");

  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");

  const [result, setResult] = useState<AnyRecord | null>(null);
  const [error, setError] = useState("");

  const parsedVariant = useMemo(
    () => parseVariant(submittedVariant),
    [submittedVariant]
  );

  const analysis = result?.data?.analysis || {};
  const biologicalContext = analysis?.biological_context || {};
  const identity = biologicalContext?.gene || analysis?.gene || {};

  const entities = getEntities(analysis);
  const sequence = getSequence(analysis);

  const ensemblId = clean(
    first(
      identity?.ensembl_id,
      identity?.identifier,
      analysis?.ensembl_id
    )
  );

  const transcriptId = clean(
    first(
      result?.data?.canonical_transcript,
      analysis?.canonical_transcript?.id,
      analysis?.canonical_transcript,
      analysis?.transcript_id
    )
  );

  const apiEvidenceSources = Array.isArray(
    result?.data?.evidence_sources
  )
    ? result.data.evidence_sources
    : [];

  const apiEvidenceCount = Number(
    result?.data?.evidence_source_count || 0
  );

  const proteinName = formatName(
    first(
      identity?.name,
      analysis?.gene_name,
      analysis?.protein_name
    ),
    submittedGene || "Biological target"
  );

  const matchCount = Number(result?.data?.match_count || 0);

  const reasoning = analysis?.evidence_reasoning || {};

  const reasoningLevel = clean(
    first(
      reasoning?.composition?.level,
      reasoning?.evidence_summary?.level,
      reasoning?.level
    )
  );

  const sourceCount =
    apiEvidenceCount ||
    apiEvidenceSources.length ||
    evidenceCount(analysis);

  async function investigate(event: FormEvent) {
    event.preventDefault();

    const cleanGene = gene.trim().toUpperCase();
    const cleanVariant = variant.trim().toUpperCase();

    if (!cleanGene || !cleanVariant) {
      setError("Enter both a gene symbol and a protein-level variant.");
      setStatus("error");
      return;
    }

    setSubmittedGene(cleanGene);
    setSubmittedVariant(cleanVariant);
    setResult(null);
    setError("");
    setStatus("loading");

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/variants/analyze`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            gene: cleanGene,
            variant: cleanVariant,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail?.message ||
            data?.detail?.error ||
            data?.message ||
            "Variant analysis failed."
        );
      }

      setResult(data);
      setStatus("success");
    } catch (err: any) {
      setError(
        err?.message ||
          "Unable to complete the variant investigation."
      );
      setStatus("error");
    }
  }

  return (
    <main className="cv-variant-page">
      <Navbar />

      <section className="cv-variant-hero">
        <div className="cv-variant-hero-grid" />

        <div className="cv-variant-orbit cv-variant-orbit-a" />
        <div className="cv-variant-orbit cv-variant-orbit-b" />
        <div className="cv-variant-core">
          <span />
          <span />
          <span />
        </div>

        <div className="cv-variant-hero-copy">
          <div className="cv-eyebrow">
            <span>03</span>
            VARIANT INVESTIGATOR
          </div>

          <h1>
            Find the biological
            <br />
            meaning inside a{" "}
            <em>variant.</em>
          </h1>

          <p>
            Move from a protein-level change to its biological
            context, connected evidence, and reasoned interpretation.
          </p>

          <div className="cv-variant-metrics">
            <div>
              <strong>01</strong>
              <span>VARIANT</span>
            </div>
            <div>
              <strong>∞</strong>
              <span>CONTEXT</span>
            </div>
            <div>
              <strong>05</strong>
              <span>EVIDENCE LAYERS</span>
            </div>
          </div>
        </div>
      </section>

      <section className="cv-variant-investigate cv-section-reveal">
        <div className="cv-section-number">01 / INVESTIGATE</div>

        <div className="cv-section-heading">
          <h2>
            Give the system a <em>variant.</em>
          </h2>
          <p>
            Enter any gene symbol and protein-level variant. CureVerseAI
            resolves the biological identity and connects the investigation
            to the existing intelligence layer.
          </p>
        </div>

        <form
          className={`cv-variant-form ${
            status === "loading" ? "is-loading" : ""
          }`}
          onSubmit={investigate}
        >
          <label>
            <span>GENE</span>
            <input
              value={gene}
              onChange={(e) => setGene(e.target.value)}
              placeholder="TP53"
              autoComplete="off"
            />
          </label>

          <label>
            <span>VARIANT</span>
            <input
              value={variant}
              onChange={(e) => setVariant(e.target.value)}
              placeholder="R175H"
              autoComplete="off"
            />
          </label>

          <button type="submit" disabled={status === "loading"}>
            {status === "loading"
              ? "INVESTIGATING..."
              : "INVESTIGATE VARIANT"}
            <span>↗</span>
          </button>
        </form>

        {error && (
          <div className="cv-variant-error">
            <strong>ANALYSIS ERROR</strong>
            <span>{error}</span>
          </div>
        )}
      </section>

      {/* ALWAYS-PRESENT RESULT AREA */}
      <section className="cv-variant-results cv-section-reveal">
        <div className="cv-section-number">02 / RESULTS</div>

        {status === "idle" && (
          <div className="cv-variant-ready">
            <div className="cv-ready-pulse">
              <span />
            </div>

            <div>
              <span className="cv-result-kicker">
                READY FOR INVESTIGATION
              </span>
              <h2>
                Your biological result
                <br />
                will appear <em>here.</em>
              </h2>
              <p>
                Enter a gene and protein-level variant above. The
                investigation will resolve identity first, then connect
                biological context and evidence.
              </p>
            </div>

            <div className="cv-ready-stages">
              <span>IDENTITY</span>
              <span>CONTEXT</span>
              <span>EVIDENCE</span>
              <span>REASONING</span>
            </div>
          </div>
        )}

        {status === "loading" && (
          <div className="cv-variant-loading">
            <div className="cv-loading-header">
              <div>
                <span className="cv-result-kicker">
                  ANALYSIS IN PROGRESS
                </span>
                <h2>
                  Investigating{" "}
                  <em>
                    {submittedGene} {submittedVariant}
                  </em>
                </h2>
              </div>

              <div className="cv-loading-spinner" />
            </div>

            <div className="cv-analysis-pipeline">
              <div className="active">
                <span>01</span>
                <strong>IDENTITY</strong>
                <small>Resolving biological record</small>
              </div>

              <div className="active">
                <span>02</span>
                <strong>PROTEIN</strong>
                <small>Connecting canonical target</small>
              </div>

              <div className="active">
                <span>03</span>
                <strong>CONTEXT</strong>
                <small>Mapping biological entities</small>
              </div>

              <div className="active">
                <span>04</span>
                <strong>EVIDENCE</strong>
                <small>Collecting source layers</small>
              </div>

              <div className="active">
                <span>05</span>
                <strong>REASONING</strong>
                <small>Building evidence-aware view</small>
              </div>
            </div>
          </div>
        )}

        {status === "success" && result && (
          <div className="cv-variant-result-content">
            <div className="cv-result-banner">
              <div>
                <span className="cv-result-kicker">
                  INVESTIGATION COMPLETE
                </span>

                <h2>
                  {submittedGene}{" "}
                  <em>{submittedVariant}</em>
                </h2>

                <p>
                  Biological identity resolved. Connected evidence is
                  preserved separately from model-derived interpretation.
                </p>
              </div>

              <div className="cv-result-status">
                <span />
                RESOLVED
              </div>
            </div>

            <div className="cv-result-stats">
              <div>
                <strong>{matchCount}</strong>
                <span>DIRECT MATCHES</span>
              </div>

              <div>
                <strong>{entities.length || 0}</strong>
                <span>CONNECTED ENTITIES</span>
              </div>

              <div>
                <strong>{sourceCount || "—"}</strong>
                <span>EVIDENCE SOURCES</span>
              </div>

              <div>
                <strong>{sequence ? `${sequence.length}` : "—"}</strong>
                <span>AA SEQUENCE</span>
              </div>
            </div>

            <div className="cv-result-grid">
              <article className="cv-result-card cv-result-identity">
                <div className="cv-card-label">IDENTITY</div>

                <h3>
                  Variant <em>identity.</em>
                </h3>

                <div className="cv-identity-target">
                  <div className="cv-target-symbol">
                    {submittedGene.slice(0, 2)}
                  </div>

                  <div>
                    <strong>{proteinName}</strong>
                    <span>
                      {submittedGene} · {submittedVariant}
                    </span>
                  </div>
                </div>

                <div className="cv-data-row">
                  <span>VARIANT TYPE</span>
                  <strong>{parsedVariant.type}</strong>
                </div>

                <div className="cv-data-row">
                  <span>REFERENCE</span>
                  <strong>
                    {parsedVariant.reference || "—"}
                  </strong>
                </div>

                <div className="cv-data-row">
                  <span>POSITION</span>
                  <strong>
                    {parsedVariant.position || "—"}
                  </strong>
                </div>

                <div className="cv-data-row">
                  <span>ALTERNATE</span>
                  <strong>
                    {parsedVariant.alternate || "—"}
                  </strong>
                </div>
              </article>

              <article className="cv-result-card cv-result-context">
                <div className="cv-card-label">BIOLOGICAL CONTEXT</div>

                <h3>
                  Where does it <em>belong?</em>
                </h3>

                <div className="cv-context-list">
                  <div>
                    <span>ENSEMBL</span>
                    <strong>{ensemblId || "—"}</strong>
                  </div>

                  <div>
                    <span>CANONICAL TRANSCRIPT</span>
                    <strong>{transcriptId || "—"}</strong>
                  </div>

                  <div>
                    <span>SPECIES</span>
                    <strong>
                      {clean(
                        first(
                          identity?.species,
                          biologicalContext?.species,
                          "homo_sapiens"
                        )
                      )}
                    </strong>
                  </div>
                </div>

                <div
                  className={`cv-match-state ${
                    matchCount > 0 ? "matched" : "unmatched"
                  }`}
                >
                  <span>{matchCount > 0 ? "●" : "○"}</span>

                  <div>
                    <strong>
                      {matchCount > 0
                        ? "DIRECT MATCH FOUND"
                        : "NO DIRECT MATCH FOUND"}
                    </strong>

                    <p>
                      {matchCount > 0
                        ? "The requested variant appears in the currently connected biological records."
                        : "No exact source record was found. Gene-level biological context remains available and is kept distinct from direct variant evidence."}
                    </p>
                  </div>
                </div>
              </article>
            </div>

            <article className="cv-result-card cv-evidence-panel">
              <div className="cv-card-label">EVIDENCE</div>

              <div className="cv-evidence-heading">
                <div>
                  <h3>
                    Keep evidence <em>distinct.</em>
                  </h3>
                  <p>
                    CureVerseAI separates observations by their origin
                    instead of collapsing them into an unsupported
                    clinical conclusion.
                  </p>
                </div>

                <div className="cv-evidence-count">
                  <strong>05</strong>
                  <span>LAYERS</span>
                </div>
              </div>

              <div className="cv-evidence-grid">
                <div>
                  <span>01</span>
                  <strong>DIRECT BIOLOGY</strong>
                  <p>Ensembl · Reactome</p>
                </div>

                <div>
                  <span>02</span>
                  <strong>DISEASE</strong>
                  <p>Open Targets</p>
                </div>

                <div>
                  <span>03</span>
                  <strong>EXPERIMENTAL</strong>
                  <p>ChEMBL</p>
                </div>

                <div>
                  <span>04</span>
                  <strong>MODEL-DERIVED</strong>
                  <p>ESM-2 representation</p>
                </div>

                <div>
                  <span>05</span>
                  <strong>CONTEXTUAL</strong>
                  <p>Biological knowledge layer</p>
                </div>
              </div>
            </article>

            <article className="cv-reasoning-panel">
              <div className="cv-reasoning-mark">✦</div>

              <div className="cv-reasoning-content">
                <span> CUREVERSEAI / REASONED INSIGHT</span>

                <h3>
                  {reasoningLevel
                    ? reasoningLevel.replaceAll("_", " ")
                    : "evidence-aware interpretation"}
                </h3>

                <p>
                  {clean(
                    first(
                      reasoning?.evidence_summary?.text,
                      reasoning?.summary,
                      "The system keeps evidence layers separate and presents the available biological context without collapsing it into an unsupported clinical claim."
                    )
                  )}
                </p>
              </div>

              <div className="cv-reasoning-meta">
                <span>
                  SOURCES <strong>{sourceCount || "—"}</strong>
                </span>

                <span>
                  MATCHED RECORDS <strong>{matchCount}</strong>
                </span>
              </div>
            </article>

            {sequence && (
              <article className="cv-result-card cv-sequence-panel">
                <div className="cv-card-label">CANONICAL PROTEIN</div>

                <div className="cv-sequence-heading">
                  <div>
                    <h3>
                      Sequence <em>context.</em>
                    </h3>
                    <p>
                      Canonical amino-acid sequence resolved from the
                      connected biological identity layer.
                    </p>
                  </div>

                  <strong>{sequence.length} AA</strong>
                </div>

                <div className="cv-sequence-box">
                  {sequence.match(/.{1,60}/g)?.map(
                    (chunk: string, index: number) => (
                      <div key={`${chunk}-${index}`}>
                        <span>
                          {String(index * 60 + 1).padStart(4, "0")}
                        </span>
                        <code>{chunk}</code>
                      </div>
                    )
                  )}
                </div>
              </article>
            )}
          </div>
        )}
      </section>

      <section className="cv-variant-principles cv-section-reveal">
        <div className="cv-section-number">03 / WHY IT MATTERS</div>

        <div className="cv-section-heading">
          <h2>
            A variant is not just a <em>label.</em>
          </h2>
        </div>

        <div className="cv-principle-grid">
          <article>
            <span>IDENTITY</span>
            <strong>Resolve the biological record first.</strong>
            <p>
              Establish the gene, canonical transcript, protein and
              source identity before interpretation.
            </p>
          </article>

          <article>
            <span>CONTEXT</span>
            <strong>Connect the change to biology.</strong>
            <p>
              Preserve pathways, biological entities and surrounding
              context instead of treating a variant in isolation.
            </p>
          </article>

          <article>
            <span>EVIDENCE</span>
            <strong>Preserve where observations come from.</strong>
            <p>
              Distinguish direct records, disease associations,
              experimental observations and model-derived features.
            </p>
          </article>

          <article>
            <span>REASONING</span>
            <strong>Show what is supported.</strong>
            <p>
              Evidence-aware reasoning should expose uncertainty
              rather than invent clinical certainty.
            </p>
          </article>
        </div>
      </section>

      <Footer />
    </main>
  );
}
