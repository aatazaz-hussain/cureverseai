"use client";

import { useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./gene-explorer.css";

type AnalysisResponse = {
  success?: boolean;
  data?: any;
  detail?: any;
};

function firstDefined(...values: any[]) {
  return values.find(
    (value) => value !== undefined && value !== null && value !== ""
  );
}

function cleanBiologicalName(value: any) {
  if (!value) return "";
  const text = String(value).trim();

  const sourceIndex = text.indexOf(" [Source:");
  if (sourceIndex !== -1) {
    return text.slice(0, sourceIndex).trim();
  }

  return text;
}

function geneSymbolFromRecord(value: any, fallback: string) {
  const raw = String(value || "").trim();

  if (!raw) return fallback;

  if (raw.includes(" [Source:")) {
    const prefix = raw.split(" [Source:")[0].trim();

    const known = prefix.match(/\b[A-Z0-9-]{2,12}\b$/);
    if (known) return known[0];

    return fallback;
  }

  return raw.length <= 15 ? raw : fallback;
}

function pretty(value: any, fallback = "Not available") {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number") return String(value);
  return JSON.stringify(value, null, 2);
}

export default function GeneExplorerPage() {
  const [gene, setGene] = useState("TP53");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  async function investigate() {
    const cleanGene = gene.trim();

    if (!cleanGene) {
      setError("Enter a gene symbol to begin the investigation.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/v1/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: "research",
          task: "gene_exploration",
          input: {
            gene: cleanGene,
          },
        }),
      });

      const payload: AnalysisResponse = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : payload.detail?.message || "The biological analysis failed."
        );
      }

      setResult(payload.data?.result || payload.data || payload);
    } catch (err: any) {
      setError(
        err?.message ||
          "Unable to connect to the CureVerseAI biological intelligence engine."
      );
    } finally {
      setLoading(false);
    }
  }

  const context = result?.biological_context || {};
  const geneRecord = context?.gene || {};

  const rawGeneName = firstDefined(
    geneRecord?.name,
    geneRecord?.display_name,
    result?.gene_name,
    result?.gene
  );

  const biologicalName = cleanBiologicalName(rawGeneName);
  const geneSymbol = geneSymbolFromRecord(
    result?.gene,
    gene,
  );

  const ensembl = firstDefined(
    geneRecord?.ensembl_id,
    geneRecord?.id,
    result?.ensembl_id,
    result?.uniprot_resolution?.ensembl_id
  );

  const transcript = firstDefined(
    geneRecord?.canonical_transcript,
    result?.canonical_transcript
  );

  const uniprotResolution = result?.uniprot_resolution || {};
  const uniprot = firstDefined(
    uniprotResolution?.selected_accession,
    uniprotResolution?.accession,
    result?.uniprot_accession
  );

  const proteinFeatures = result?.protein_features || {};
  const proteinDimension = firstDefined(
    proteinFeatures?.embedding_dimension,
    proteinFeatures?.features?.embedding_dimension
  );

  const proteinLength = firstDefined(
    proteinFeatures?.sequence_length,
    proteinFeatures?.features?.sequence_length
  );

  const reasoning = result?.evidence_reasoning || {};
  const evidenceSummary = reasoning?.evidence_summary || {};
  const evidenceComposition = reasoning?.evidence_composition || {};

  const openTargets = result?.open_targets_evidence || {};
  const chembl = result?.chembl_evidence || {};

  const pathways = useMemo(() => {
    const entities =
      context?.reactome_entities ||
      context?.pathways ||
      context?.reactome ||
      [];

    if (Array.isArray(entities)) return entities;
    return [];
  }, [context]);

  const diseases = useMemo(() => {
    const items =
      openTargets?.diseases ||
      openTargets?.associations ||
      openTargets?.disease_associations ||
      [];

    return Array.isArray(items) ? items : [];
  }, [openTargets]);

  const activities = useMemo(() => {
    const items =
      chembl?.relationships ||
      chembl?.activities ||
      chembl?.bioactivities ||
      [];

    return Array.isArray(items) ? items : [];
  }, [chembl]);

  return (
    <main className="gene-page">
      <Navbar />

      <section className="gene-hero">
        <div className="gene-hero-grid" />
        <div className="gene-orbit gene-orbit-one" />
        <div className="gene-orbit gene-orbit-two" />
        <div className="gene-glow gene-glow-one" />
        <div className="gene-glow gene-glow-two" />

        <div className="gene-hero-copy">
          <div className="gene-eyebrow">
            <span>01</span>
            <i />
            RESEARCH WORKSPACE
          </div>

          <h1>
            Gene
            <br />
            <em>Explorer.</em>
          </h1>

          <p>
            Start with a gene and follow its biological identity, protein
            representation, pathways, disease associations and experimental
            evidence through one connected system.
          </p>

          <div className="gene-hero-tags">
            <span>ENSEMBL</span>
            <span>UNIPROT</span>
            <span>REACTOME</span>
            <span>OPEN TARGETS</span>
            <span>CHEMBL</span>
          </div>
        </div>

        <div className="gene-visual">
          <div className="gene-visual-ring ring-a" />
          <div className="gene-visual-ring ring-b" />
          <div className="gene-visual-ring ring-c" />

          <div className="gene-core">
            <div className="gene-dna">
              {Array.from({ length: 12 }).map((_, index) => (
                <span key={index} style={{ "--i": index } as React.CSSProperties}>
                  <b />
                  <i />
                </span>
              ))}
            </div>
          </div>

          <div className="gene-node node-a">DNA</div>
          <div className="gene-node node-b">PRO</div>
          <div className="gene-node node-c">PATH</div>
          <div className="gene-node node-d">EV</div>
        </div>

        <div className="gene-hero-status">
          <span className="status-dot" />
          BIOLOGICAL INTELLIGENCE ONLINE
        </div>

        <div className="gene-hero-bottom">
          <span>GENE → CONTEXT → EVIDENCE → INSIGHT</span>
          <span>CURVERSEAI / 01</span>
        </div>
      </section>

      <section className="gene-workspace">
        <div className="gene-section-label">
          <span>02</span>
          <i />
          BEGIN INVESTIGATION
        </div>

        <div className="gene-workspace-layout">
          <div className="gene-form-panel">
            <div className="panel-index">01 / INPUT</div>

            <h2>
              What gene
              <br />
              <em>do you want to investigate?</em>
            </h2>

            <p>
              Enter a recognised gene symbol. CureVerseAI will connect
              biological identity with protein, pathway, disease and
              experimental evidence.
            </p>

            <label htmlFor="gene-input">GENE SYMBOL</label>

            <div className="gene-input-wrap">
              <span>⌬</span>
              <input
                id="gene-input"
                value={gene}
                onChange={(event) => setGene(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") investigate();
                }}
                placeholder="e.g. TP53"
                autoComplete="off"
              />
              <small>SYMBOL</small>
            </div>

            <button
              className={`investigate-button ${loading ? "is-loading" : ""}`}
              onClick={investigate}
              disabled={loading}
            >
              <span>
                {loading ? "INVESTIGATING BIOLOGY" : "INVESTIGATE GENE"}
              </span>
              <b>{loading ? "…" : "↗"}</b>
            </button>

            <div className="example-row">
              <span>TRY AN EXAMPLE</span>
              <button onClick={() => setGene("TP53")}>TP53</button>
              <button onClick={() => setGene("BRCA1")}>BRCA1</button>
              <button onClick={() => setGene("EGFR")}>EGFR</button>
            </div>
          </div>

          <div className="gene-pipeline-panel">
            <div className="panel-index">02 / PIPELINE</div>

            <h3>From identity to insight.</h3>

            <div className="pipeline">
              {[
                ["01", "BIOLOGICAL IDENTITY", "Ensembl"],
                ["02", "PROTEIN IDENTITY", "UniProt"],
                ["03", "BIOLOGICAL CONTEXT", "Reactome"],
                ["04", "DISEASE EVIDENCE", "Open Targets"],
                ["05", "EXPERIMENTAL EVIDENCE", "ChEMBL"],
                ["06", "AI REPRESENTATION", "ESM-2"],
                ["07", "EVIDENCE REASONING", "CureVerseAI"],
              ].map(([number, title, source]) => (
                <div className="pipeline-item" key={number}>
                  <span>{number}</span>
                  <div>
                    <strong>{title}</strong>
                    <small>{source}</small>
                  </div>
                  <i>→</i>
                </div>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="gene-error">
            <span>!</span>
            <div>
              <strong>INVESTIGATION COULD NOT COMPLETE</strong>
              <p>{error}</p>
            </div>
          </div>
        )}
      </section>

      {!result && !loading && (
        <section className="gene-empty">
          <div className="gene-empty-visual">
            <div />
            <span>⌬</span>
          </div>
          <p>WAITING FOR A BIOLOGICAL INPUT</p>
          <strong>Enter a gene above to open its biological profile.</strong>
        </section>
      )}

      {loading && (
        <section className="gene-loading">
          <div className="loading-core">
            <span />
            <span />
            <span />
          </div>
          <div>
            <span>CURVERSEAI INTELLIGENCE ENGINE</span>
            <h2>Tracing biological evidence<span>...</span></h2>
            <p>
              Connecting identity, protein representation, pathways and
              external evidence.
            </p>
          </div>
        </section>
      )}

      {result && !loading && (
        <section className="gene-results">
          <div className="results-header">
            <div>
              <div className="gene-section-label">
                <span>03</span>
                <i />
                INVESTIGATION RESULT
              </div>

              <h2>
                {geneSymbol || gene}
                <em>{biologicalName || "Biological profile"}</em>
              </h2>

              <p>
                A connected view assembled from biological databases,
                pretrained representations and evidence reasoning.
              </p>
            </div>

            <div className="result-live">
              <span />
              ANALYSIS COMPLETE
            </div>
          </div>

          <div className="identity-grid">
            <div className="identity-main result-card">
              <span className="card-kicker">BIOLOGICAL IDENTITY</span>
              <strong>{geneSymbol || gene}</strong>
              <p>
                {biologicalName
                  ? biologicalName
                  : "Gene investigated through the CureVerseAI biological layer."}
              </p>

              <div className="identity-lines">
                <div>
                  <small>ENSEMBL</small>
                  <b>{pretty(ensembl)}</b>
                </div>
                <div>
                  <small>CANONICAL TRANSCRIPT</small>
                  <b>{pretty(transcript)}</b>
                </div>
                <div>
                  <small>UNIPROT</small>
                  <b>{pretty(uniprot)}</b>
                </div>
              </div>
            </div>

            <div className="metric-card result-card">
              <span className="card-kicker">PROTEIN</span>
              <strong>{pretty(proteinLength, "—")}</strong>
              <small>AMINO ACIDS</small>
              <p>Canonical protein sequence represented by ESM-2.</p>
            </div>

            <div className="metric-card result-card">
              <span className="card-kicker">AI REPRESENTATION</span>
              <strong>{pretty(proteinDimension, "—")}</strong>
              <small>FEATURE DIMENSION</small>
              <p>Learned protein representation generated by the model layer.</p>
            </div>
          </div>

          <div className="results-columns">
            <div className="results-main-column">
              <section className="result-card context-card">
                <div className="card-heading">
                  <div>
                    <span className="card-kicker">BIOLOGICAL CONTEXT</span>
                    <h3>Where does this gene sit in biology?</h3>
                  </div>
                  <span className="card-number">04</span>
                </div>

                <div className="context-stats">
                  <div>
                    <strong>{pathways.length || context?.reactome_count || "—"}</strong>
                    <span>REACTOME ENTITIES</span>
                  </div>
                  <div>
                    <strong>
                      {context?.mutation_count ||
                        context?.mutations?.length ||
                        "—"}
                    </strong>
                    <span>VARIANTS / MUTATIONS</span>
                  </div>
                  <div>
                    <strong>{pathways.length ? "CONNECTED" : "AVAILABLE"}</strong>
                    <span>BIOLOGICAL CONTEXT</span>
                  </div>
                </div>

                {pathways.length > 0 ? (
                  <div className="entity-list">
                    {pathways.slice(0, 8).map((item: any, index: number) => (
                      <div key={index} className="entity-row">
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <div>
                          <strong>
                            {firstDefined(
                              item?.name,
                              item?.display_name,
                              item?.id,
                              "Biological entity"
                            )}
                          </strong>
                          <small>
                            {firstDefined(
                              item?.stId,
                              item?.stable_id,
                              item?.type,
                              "REACTOME"
                            )}
                          </small>
                        </div>
                        <i>↗</i>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-data">
                    Biological context is available in the returned research
                    record.
                  </div>
                )}
              </section>

              <section className="result-card evidence-card">
                <div className="card-heading">
                  <div>
                    <span className="card-kicker">EXTERNAL EVIDENCE</span>
                    <h3>What does the evidence show?</h3>
                  </div>
                  <span className="card-number">05</span>
                </div>

                <div className="evidence-source-grid">
                  <div>
                    <span>OPEN TARGETS</span>
                    <strong>
                      {firstDefined(
                        evidenceSummary?.disease_association,
                        evidenceSummary?.disease_associations,
                        diseases.length,
                        "AVAILABLE"
                      )}
                    </strong>
                    <p>Disease association evidence</p>
                  </div>

                  <div>
                    <span>CHEMBL</span>
                    <strong>
                      {firstDefined(
                        chembl?.summary?.total_relationships,
                        chembl?.total_relationships,
                        activities.length,
                        "AVAILABLE"
                      )}
                    </strong>
                    <p>Experimental bioactivity relationships</p>
                  </div>

                  <div>
                    <span>REACTOME</span>
                    <strong>{pathways.length || "CONNECTED"}</strong>
                    <p>Biological pathway context</p>
                  </div>
                </div>

                {diseases.length > 0 && (
                  <div className="evidence-mini-list">
                    <div className="mini-list-heading">
                      TOP DISEASE ASSOCIATIONS
                    </div>

                    {diseases.slice(0, 5).map((item: any, index: number) => (
                      <div key={index}>
                        <span>{index + 1}</span>
                        <strong>
                          {firstDefined(
                            item?.disease_name,
                            item?.name,
                            item?.disease?.name,
                            item?.id,
                            "Disease association"
                          )}
                        </strong>
                        <small>
                          {firstDefined(
                            item?.score,
                            item?.association_score,
                            "Evidence"
                          )}
                        </small>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>

            <aside className="results-side-column">
              <section className="result-card reasoning-card">
                <span className="card-kicker">06 / CUREVERSEAI REASONING</span>

                <div className="reasoning-orb">
                  <div />
                  <span>AI</span>
                </div>

                <h3>
                  Evidence
                  <br />
                  <em>connected.</em>
                </h3>

                <p>
                  CureVerseAI separates direct biological evidence, disease
                  associations, experimental observations, model-derived
                  signals and contextual information before forming an insight.
                </p>

                <div className="reasoning-level">
                  <small>EVIDENCE LEVEL</small>
                  <strong>
                    {firstDefined(
                      reasoning?.level,
                      evidenceComposition?.level,
                      reasoning?.classification,
                      "MULTI-SOURCE"
                    )}
                  </strong>
                </div>

                <div className="reasoning-bars">
                  {[
                    ["DIRECT", evidenceSummary?.direct],
                    ["DISEASE", evidenceSummary?.disease_association],
                    ["EXPERIMENTAL", evidenceSummary?.experimental_bioactivity],
                    ["MODEL", evidenceSummary?.model_derived],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <b>{pretty(value, "—")}</b>
                    </div>
                  ))}
                </div>
              </section>

              <section className="result-card provenance-card">
                <span className="card-kicker">07 / PROVENANCE</span>
                <h3>Trace the sources.</h3>

                {[
                  ["ENSEMBL", "Biological identity"],
                  ["UNIPROT", "Protein identity"],
                  ["REACTOME", "Pathway context"],
                  ["OPEN TARGETS", "Disease evidence"],
                  ["CHEMBL", "Experimental bioactivity"],
                  ["ESM-2", "Protein representation"],
                ].map(([source, description]) => (
                  <div className="source-row" key={source}>
                    <span />
                    <div>
                      <strong>{source}</strong>
                      <small>{description}</small>
                    </div>
                    <i>✓</i>
                  </div>
                ))}
              </section>
            </aside>
          </div>

          <section className="gene-insight">
            <div className="insight-mark">CV</div>
            <div>
              <span>08 / RESEARCH INSIGHT</span>
              <h2>
                Connected evidence
                <br />
                <em>creates context.</em>
              </h2>
              <p>
                {firstDefined(
                  reasoning?.summary,
                  reasoning?.insight,
                  reasoning?.findings?.[0]?.statement,
                  reasoning?.findings?.[0]?.description,
                  `The ${geneSymbol || gene} investigation connected biological identity with pathway context, disease associations, experimental evidence and model-derived representation. Review each evidence layer before drawing scientific conclusions.`
                )}
              </p>
            </div>
          </section>

          <details className="raw-analysis">
            <summary>
              <span>VIEW RAW ANALYSIS RECORD</span>
              <b>+</b>
            </summary>
            <pre>{pretty(result)}</pre>
          </details>
        </section>
      )}

      <Footer />
    </main>
  );
}
