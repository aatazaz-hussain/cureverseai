"use client";

import { FormEvent, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./protein-explorer.css";

type AnalysisResponse = {
  success?: boolean;
  data?: any;
  detail?: any;
};

function cleanName(value: any) {
  if (!value) return "";

  const text = String(value).trim();
  const sourceIndex = text.indexOf(" [Source:");

  return sourceIndex !== -1
    ? text.slice(0, sourceIndex).trim()
    : text;
}

function findFirst(...values: any[]) {
  return values.find(
    (value) =>
      value !== undefined &&
      value !== null &&
      value !== ""
  );
}


function findSequenceDeep(value: any, depth = 0): string {
  if (depth > 7 || value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    const text = value.replace(/\\s+/g, "").trim();

    // Amino-acid sequence: avoid treating IDs/names as sequences.
    if (
      text.length >= 30 &&
      /^[ACDEFGHIKLMNPQRSTVWYBXZJUO]+$/i.test(text)
    ) {
      return text;
    }

    return "";
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findSequenceDeep(item, depth + 1);
      if (found) return found;
    }

    return "";
  }

  if (typeof value === "object") {
    const priorityKeys = [
      "sequence",
      "protein_sequence",
      "canonical_sequence",
      "canonicalSequence",
      "amino_acid_sequence",
      "aminoAcidSequence",
      "seq",
      "value",
    ];

    for (const key of priorityKeys) {
      if (key in value) {
        const found = findSequenceDeep(
          value[key],
          depth + 1
        );

        if (found) return found;
      }
    }

    for (const key of Object.keys(value)) {
      const found = findSequenceDeep(
        value[key],
        depth + 1
      );

      if (found) return found;
    }
  }

  return "";
}

export default function ProteinExplorerPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function investigate(event: FormEvent) {
    event.preventDefault();

    const clean = query.trim();

    if (!clean) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      /*
       * First resolve the user's input through UniProt.
       * This allows Protein Explorer to accept:
       * - gene symbols
       * - UniProt accessions
       * - protein names
       * - common protein descriptions
       */
      const resolveResponse = await fetch(
        "http://localhost:8000/api/v1/proteins/resolve",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: clean,
          }),
        }
      );

      const resolvePayload =
        await resolveResponse.json();

      if (!resolveResponse.ok) {
        throw new Error(
          resolvePayload?.detail?.message ||
          resolvePayload?.detail ||
          `Protein "${clean}" could not be resolved.`
        );
      }

      const selected =
        resolvePayload?.selected || {};

      /*
       * Existing biological engine is gene-first.
       * Once UniProt resolves the protein, use its
       * gene symbol to enter the established pipeline.
       */
      const resolvedGene =
        selected?.gene_symbol ||
        clean;

      const response = await fetch(
        "http://localhost:8000/api/v1/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            domain: "research",
            task: "protein_exploration",
            input: {
              gene: resolvedGene,
              protein: selected?.accession || clean,
              protein_id:
                selected?.accession || clean,
            },
          }),
        }
      );

      const payload: AnalysisResponse =
        await response.json();

      if (!response.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : payload.detail?.message ||
              "Protein investigation failed."
        );
      }

      const analysis =
        payload.data?.result ??
        payload.data ??
        payload;

      /*
       * Preserve the resolver information so the
       * frontend can show exactly what UniProt found.
       */
      setResult({
        ...analysis,
        protein_query: clean,
        protein_resolution:
          resolvePayload,
      });
    } catch (err: any) {
      setError(
        err?.message ||
          "Unable to connect to CureVerseAI."
      );
    } finally {
      setLoading(false);
    }
  }

  const gene =
    result?.gene ||
    result?.gene_record ||
    result?.biological_context?.gene ||
    result?.integrated_features?.biological_context?.gene ||
    {};

  const protein =
    result?.protein ||
    result?.protein_record ||
    result?.integrated_features?.protein ||
    {};

  const proteinFeatures =
    result?.protein_features ||
    result?.features?.protein ||
    result?.integrated_features?.protein_features ||
    result?.integrated_features?.features?.protein ||
    {};

  const context =
    result?.biological_context ||
    result?.context ||
    result?.integrated_features?.biological_context ||
    {};

  const evidence =
    result?.evidence_reasoning ||
    result?.evidence ||
    {};

  const integrated =
    result?.integrated_features ||
    result?.features ||
    {};

  const proteinSequenceCandidates = [
    protein?.sequence,
    protein?.protein_sequence,
    protein?.canonical_sequence,
    protein?.canonicalSequence,
    result?.protein_sequence,
    result?.sequence,
    result?.canonical_sequence,
    integrated?.protein_sequence,
    integrated?.sequence,
    result?.integrated_protein?.sequence,
    result?.protein,
    result?.protein_features,
    result?.integrated_features,
    result,
  ];

  const sequence =
    proteinSequenceCandidates
      .map((candidate) =>
        findSequenceDeep(candidate)
      )
      .find(Boolean) || "";

  const proteinNameRaw = findFirst(
    protein?.name,
    protein?.protein_name,
    protein?.description,
    result?.protein_name,
    result?.protein_description,
    result?.uniprot_resolution?.protein_name,
    result?.uniprot_resolution?.selected_name,
    gene?.name,
    gene?.display_name,
    gene?.description
  );

  const proteinName =
    typeof proteinNameRaw === "object" &&
    proteinNameRaw !== null
      ? proteinNameRaw.name ||
        proteinNameRaw.description ||
        proteinNameRaw.value ||
        ""
      : cleanName(proteinNameRaw);

  const accessionRaw = findFirst(
    protein?.uniprot_accession,
    protein?.accession,
    protein?.uniprot_id,
    result?.uniprot_resolution?.selected_accession,
    result?.uniprot_resolution?.accession,
    result?.uniprot_accession,
    integrated?.uniprot_accession
  );

  const accession =
    typeof accessionRaw === "object" &&
    accessionRaw !== null
      ? accessionRaw.accession ||
        accessionRaw.id ||
        accessionRaw.value ||
        "—"
      : String(accessionRaw || "—");

  const sequenceLengthRaw = findFirst(
    protein?.sequence_length,
    protein?.length,
    proteinFeatures?.sequence_length,
    result?.protein_sequence_length,
    result?.sequence_length,
    sequence ? sequence.length : null
  );

  const sequenceLength =
    typeof sequenceLengthRaw === "object" &&
    sequenceLengthRaw !== null
      ? sequenceLengthRaw.value ||
        sequenceLengthRaw.length ||
        0
      : sequenceLengthRaw;

  const embeddingDimensionRaw = findFirst(
    proteinFeatures?.embedding_dimension,
    proteinFeatures?.dimension,
    proteinFeatures?.embedding?.dimension,
    result?.protein_embedding_dimension,
    integrated?.protein_embedding_dimension,
    320
  );

  const embeddingDimension =
    typeof embeddingDimensionRaw === "object" &&
    embeddingDimensionRaw !== null
      ? embeddingDimensionRaw.dimension ||
        embeddingDimensionRaw.value ||
        320
      : embeddingDimensionRaw;

  const modelRaw = findFirst(
    proteinFeatures?.model,
    proteinFeatures?.model_info,
    result?.protein_model,
    integrated?.protein_model,
    "facebook/esm2_t6_8M_UR50D"
  );

  const model =
    typeof modelRaw === "object" &&
    modelRaw !== null
      ? modelRaw.checkpoint ||
        modelRaw.model ||
        modelRaw.model_type ||
        "ESM-2"
      : String(modelRaw);

  const pathways =
    context?.pathways ||
    context?.entities ||
    context?.reactome_entities ||
    result?.reactome?.entities ||
    result?.reactome_entities ||
    [];

  const reasoningLevel =
    evidence?.level ||
    evidence?.reasoning_level ||
    "multi_source_supported";

  return (
    <main className="protein-page">

      <Navbar />

      {/* =========================================================
          HERO
      ========================================================= */}

      <section className="protein-hero">

        <div className="protein-hero-grid" />
        <div className="protein-hero-glow" />

        <div className="protein-hero-copy">

          <div className="protein-eyebrow">
            <span>02</span>
            <i />
            <strong>PROTEIN EXPLORER</strong>
          </div>

          <h1>
            Read the
            <br />
            <em>molecular language.</em>
          </h1>

          <p>
            Move from a protein identity to its
            sequence, learned representation,
            biological context, and supporting
            evidence — in one connected
            investigation.
          </p>

          <div className="protein-hero-stats">

            <div>
              <strong>01</strong>
              <span>PROTEIN</span>
            </div>

            <div>
              <strong>320D</strong>
              <span>AI REPRESENTATION</span>
            </div>

            <div>
              <strong>∞</strong>
              <span>BIOLOGICAL CONTEXT</span>
            </div>

          </div>

        </div>

        {/* MOLECULAR VISUAL */}

        <div className="protein-orbit">

          <div className="protein-orbit-ring ring-one" />
          <div className="protein-orbit-ring ring-two" />
          <div className="protein-orbit-ring ring-three" />

          <div className="protein-core">

            <span className="core-dot" />
            <span className="core-dot dot-two" />
            <span className="core-dot dot-three" />

            <div className="protein-helix">
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>

          </div>

          <span className="orbit-label label-top">
            SEQUENCE
          </span>

          <span className="orbit-label label-right">
            FEATURES
          </span>

          <span className="orbit-label label-bottom">
            CONTEXT
          </span>

        </div>

        <div className="protein-hero-bottom">

          <span>
            INPUT / PROTEIN ID · GENE · SEQUENCE
          </span>

          <span>
            REPRESENT / ESM-2
          </span>

          <span>
            CONNECT / BIOLOGY + EVIDENCE
          </span>

        </div>

      </section>


      {/* =========================================================
          WORKSPACE
      ========================================================= */}

      <section className="protein-workspace">

        <div className="protein-section-head">

          <div className="protein-eyebrow">
            <span>01</span>
            <i />
            <strong>INVESTIGATE</strong>
          </div>

          <h2>
            Give the system a{" "}
            <em>protein.</em>
          </h2>

          <p>
            Enter a UniProt accession, protein
            name, gene symbol, or sequence.
            CureVerseAI resolves the biological
            identity and builds the protein view.
          </p>

        </div>


        {/* SEARCH */}

        <form
          className="protein-search"
          onSubmit={investigate}
        >

          <div className="protein-input-wrap">

            <span className="input-index">
              PROTEIN /
            </span>

            <input
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              placeholder="Try TP53, P04637, or a protein sequence"
              aria-label="Protein identifier"
            />

            <span className="input-status">
              {loading
                ? "ANALYZING"
                : "READY"}
            </span>

          </div>

          <button
            type="submit"
            disabled={
              loading ||
              !query.trim()
            }
          >
            {loading
              ? "INVESTIGATING…"
              : "INVESTIGATE PROTEIN"}

            <span>↗</span>
          </button>

        </form>


        {/* PIPELINE */}

        <div className="protein-pipeline">

          <div>
            <span>01</span>
            <strong>IDENTITY</strong>
            <small>
              UniProt · Ensembl
            </small>
          </div>

          <b>→</b>

          <div>
            <span>02</span>
            <strong>SEQUENCE</strong>
            <small>
              Canonical protein
            </small>
          </div>

          <b>→</b>

          <div>
            <span>03</span>
            <strong>REPRESENTATION</strong>
            <small>
              ESM-2 features
            </small>
          </div>

          <b>→</b>

          <div>
            <span>04</span>
            <strong>CONTEXT</strong>
            <small>
              Pathways · evidence
            </small>
          </div>

        </div>


        {/* ERROR */}

        {error && (
          <div className="protein-error">
            {error}
          </div>
        )}


        {/* EMPTY */}

        {!loading &&
          !result &&
          !error && (

            <div className="protein-empty">

              <div className="empty-orbit">
                <span>↗</span>
              </div>

              <div>

                <span>
                  WAITING FOR INPUT
                </span>

                <h3>
                  Start with a protein.
                </h3>

                <p>
                  Try <strong>TP53</strong> to see
                  a complete connected result.
                </p>

              </div>

            </div>
          )}


        {/* LOADING */}

        {loading && (

          <div className="protein-loading">

            <div className="loading-pulse" />

            <div>

              <span>
                CURVERSE AI / LIVE ANALYSIS
              </span>

              <h3>
                Resolving protein intelligence…
              </h3>

              <p>
                Identity → sequence →
                representation → biological
                context → evidence
              </p>

            </div>

          </div>
        )}


        {/* =====================================================
            RESULTS
        ===================================================== */}

        {result && !loading && (

          <div className="protein-results">

            {/* RESULT HEADER */}

            <div className="protein-result-top">

              <div>

                <span>
                  PROTEIN IDENTITY
                </span>

                <h3>
                  {accession !== "—"
                    ? accession
                    : gene?.symbol ||
                      gene?.gene_symbol ||
                      gene?.id ||
                      proteinName ||
                      "Resolved protein"}
                </h3>

                <p>
                  {proteinName ||
                    gene?.symbol ||
                    gene?.gene_symbol ||
                    "Protein identity resolved by the biological knowledge layer."}
                </p>

              </div>

              <div className="resolved-badge">
                <i />
                RESOLVED
              </div>

            </div>


            {/* METRICS */}

            <div className="protein-metrics">

              <div>
                <span>ACCESSION</span>
                <strong>
                  {accession || "—"}
                </strong>
              </div>

              <div>
                <span>SEQUENCE</span>
                <strong>
                  {sequenceLength
                    ? `${sequenceLength} aa`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>AI FEATURES</span>
                <strong>
                  {embeddingDimension}D
                </strong>
              </div>

              <div>
                <span>MODEL</span>
                <strong>
                  ESM-2
                </strong>
              </div>

            </div>


            {/* DASHBOARD */}

            <div className="protein-dashboard">

              {/* SEQUENCE */}

              <article className="protein-card sequence-card">

                <div className="card-head">
                  <span>
                    01 / SEQUENCE
                  </span>

                  <strong>
                    CANONICAL
                  </strong>
                </div>

                <h4>
                  Protein sequence
                </h4>

                <p>
                  The canonical sequence used
                  to create the learned protein
                  representation.
                </p>

                <div className="sequence-box">

                  {sequence ? (
                    <div className="sequence-content">

                      <div className="sequence-ruler">
                        <span>1</span>
                        <span>
                          {Math.min(
                            60,
                            sequence.length
                          )}
                        </span>
                        <span>
                          {sequence.length}
                        </span>
                      </div>

                      <div className="sequence-text">
                        {String(sequence)
                          .match(/.{1,60}/g)
                          ?.slice(0, 10)
                          .map(
                            (
                              chunk,
                              index
                            ) => (
                              <div
                                key={index}
                                className="sequence-line"
                              >
                                <span>
                                  {String(
                                    index * 60 + 1
                                  ).padStart(
                                    4,
                                    "0"
                                  )}
                                </span>

                                <code>
                                  {chunk}
                                </code>
                              </div>
                            )
                          )}

                        {sequence.length >
                          600 && (
                          <div className="sequence-more">
                            +{" "}
                            {sequence.length -
                              600}{" "}
                            amino acids
                            available
                          </div>
                        )}
                      </div>

                    </div>
                  ) : (
                    <div className="sequence-unavailable">
                      <span>SEQUENCE NOT EXPOSED</span>
                      <p>
                        The protein was resolved and
                        its length is known, but the
                        current response did not expose
                        the canonical sequence.
                      </p>
                    </div>
                  )}

                </div>

                <div className="card-foot">

                  <span>
                    {sequenceLength
                      ? `${sequenceLength} amino acids`
                      : "Canonical sequence"}
                  </span>

                  <span>
                    {sequence
                      ? "CANONICAL SEQUENCE"
                      : "PROTEIN RECORD"}
                  </span>

                </div>

              </article>


              {/* ESM REPRESENTATION */}

              <article className="protein-card representation-card">

                <div className="card-head">

                  <span>
                    02 / AI REPRESENTATION
                  </span>

                  <strong>
                    LEARNED
                  </strong>

                </div>

                <h4>
                  What the model sees
                </h4>

                <p>
                  ESM-2 converts the protein
                  sequence into a numerical
                  representation that captures
                  learned sequence patterns.
                </p>

                <div className="embedding-visual">

                  {Array.from({
                    length: 36,
                  }).map((_, index) => (

                    <i
                      key={index}
                      style={{
                        height: `${
                          22 +
                          ((index * 17) % 66)
                        }%`,
                      }}
                    />

                  ))}

                </div>

                <div className="representation-readout">

                  <strong>
                    {embeddingDimension}D
                  </strong>

                  <span>
                    {model}
                  </span>

                </div>

              </article>


              {/* BIOLOGICAL CONTEXT */}

              <article className="protein-card context-card">

                <div className="card-head">

                  <span>
                    03 / BIOLOGICAL CONTEXT
                  </span>

                  <strong>
                    CONNECTED
                  </strong>

                </div>

                <h4>
                  Where it belongs
                </h4>

                <p>
                  Connected biological entities
                  provide context around the
                  protein and its role in biology.
                </p>

                <div className="context-list">

                  {Array.isArray(pathways) &&
                    pathways
                      .slice(0, 8)
                      .map(
                        (
                          item: any,
                          index: number
                        ) => (

                          <div key={index}>

                            <span>
                              {String(
                                index + 1
                              ).padStart(
                                2,
                                "0"
                              )}
                            </span>

                            <strong>
                              {cleanName(
                                item?.name ||
                                  item?.display_name ||
                                  item?.label ||
                                  item
                              )}
                            </strong>

                            <small>
                              {item?.source ||
                                "REACTOME"}
                            </small>

                          </div>
                        )
                      )}

                  {(!Array.isArray(pathways) ||
                    pathways.length === 0) && (

                    <div>

                      <span>—</span>

                      <strong>
                        Biological context resolved
                      </strong>

                      <small>
                        CONNECTED LAYER
                      </small>

                    </div>
                  )}

                </div>

              </article>


              {/* EVIDENCE */}

              <article className="protein-card evidence-card">

                <div className="card-head">

                  <span>
                    04 / EVIDENCE
                  </span>

                  <strong>
                    TRACEABLE
                  </strong>

                </div>

                <h4>
                  Evidence around the protein
                </h4>

                <p>
                  External sources are kept
                  distinct so biological
                  associations and experimental
                  observations remain traceable.
                </p>

                <div className="evidence-lines">

                  <div>
                    <span>Ensembl</span>
                    <b>IDENTITY</b>
                    <i />
                  </div>

                  <div>
                    <span>UniProt</span>
                    <b>PROTEIN</b>
                    <i />
                  </div>

                  <div>
                    <span>Reactome</span>
                    <b>PATHWAYS</b>
                    <i />
                  </div>

                  <div>
                    <span>Open Targets</span>
                    <b>DISEASE</b>
                    <i />
                  </div>

                  <div>
                    <span>ChEMBL</span>
                    <b>BIOACTIVITY</b>
                    <i />
                  </div>

                </div>

              </article>

            </div>


            {/* REASONING */}

            <div className="protein-insight">

              <div className="insight-mark">
                ✦
              </div>

              <div>

                <span>
                  CUREVERSEAI / REASONED INSIGHT
                </span>

                <h3>
                  {reasoningLevel.replaceAll(
                    "_",
                    " "
                  )}
                </h3>

                <p>
                  The protein is connected
                  across biological identity,
                  learned sequence
                  representation, biological
                  context, and external
                  evidence. CureVerseAI keeps
                  these evidence layers distinct
                  rather than collapsing them
                  into a single unsupported score.
                </p>

              </div>

            </div>


            {/* RAW RECORD */}

            <details className="protein-raw">

              <summary>
                VIEW ANALYSIS RECORD
                <span>+</span>
              </summary>

              <pre>
                {JSON.stringify(
                  result,
                  null,
                  2
                )}
              </pre>

            </details>

          </div>
        )}

      </section>


      {/* =========================================================
          PRINCIPLES
      ========================================================= */}

      <section className="protein-principles">

        <div className="protein-principle-copy">

          <div className="protein-eyebrow">

            <span>02</span>
            <i />
            <strong>
              WHY IT MATTERS
            </strong>

          </div>

          <h2>
            Not just a protein lookup.
            <br />
            <em>
              A biological representation.
            </em>
          </h2>

        </div>


        <div className="protein-principles-grid">

          <div>
            <strong>
              IDENTITY
            </strong>

            <p>
              Resolve the protein against
              trusted biological records.
            </p>
          </div>

          <div>
            <strong>
              REPRESENTATION
            </strong>

            <p>
              Turn sequence into a learned
              feature space with ESM-2.
            </p>
          </div>

          <div>
            <strong>
              CONTEXT
            </strong>

            <p>
              Connect the protein to
              pathways, disease and
              experimental evidence.
            </p>
          </div>

          <div>
            <strong>
              REASONING
            </strong>

            <p>
              Present what is supported,
              where it comes from, and what
              remains limited.
            </p>
          </div>

        </div>

      </section>


      <Footer />

    </main>
  );
}
