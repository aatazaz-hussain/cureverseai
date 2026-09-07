"use client";

import { FormEvent, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./pathway-explorer.css";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

function cleanText(value: any): string {
  if (value === null || value === undefined) return "";

  if (typeof value === "string") {
    return value.replace(/<[^>]*>/g, "").trim();
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map(cleanText).filter(Boolean).join(", ");
  }

  if (typeof value === "object") {
    return cleanText(
      value.displayName ||
        value.name ||
        value.text ||
        value.label ||
        value.identifier ||
        value.id ||
        ""
    );
  }

  return String(value);
}

function uniqueById(entries: any[]) {
  const seen = new Set<string>();

  return entries.filter((entry) => {
    const id = String(entry.id || entry.name || "");

    if (!id || seen.has(id)) return false;

    seen.add(id);
    return true;
  });
}

export default function PathwayExplorerPage() {
  const [pathway, setPathway] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  async function investigate(event: FormEvent) {
    event.preventDefault();

    const clean = pathway.trim();

    if (!clean) {
      setError("Enter a pathway or biological term to investigate.");
      return;
    }

    setLoading(true);
    setSearched(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: "research",
          task: "pathway_exploration",
          input: {
            pathway: clean,
          },
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail?.message ||
            data?.detail ||
            data?.message ||
            "Pathway analysis failed."
        );
      }

      setResult(data);
    } catch (err: any) {
      setError(
        err?.message ||
          "Unable to connect to the CureVerseAI analysis engine."
      );
    } finally {
      setLoading(false);
    }
  }

  const analysis = result?.data || result?.analysis || result || {};

  /*
   * New enriched backend structure:
   *
   * data.result.result.pathways
   *
   * We also retain fallbacks so older responses do not break the page.
   */
  const enrichedResult =
    analysis?.result?.result ||
    analysis?.result ||
    analysis ||
    {};

  const enrichedPathways = Array.isArray(enrichedResult?.pathways)
    ? enrichedResult.pathways
    : [];

  const legacySearch =
    analysis?.result?.search_results ||
    analysis?.search_results ||
    {};

  const legacyGroups = Array.isArray(legacySearch?.results)
    ? legacySearch.results
    : [];

  const pathwayEntries = useMemo(() => {
    if (enrichedPathways.length) {
      const normalized = enrichedPathways.map((entry: any) => {
        const species = cleanText(entry?.species);

        return {
          id: cleanText(entry?.id) || "Unknown",
          name: cleanText(entry?.name) || "Biological pathway",
          species,
          description: cleanText(entry?.description),
          human: species.toLowerCase() === "homo sapiens",
          disease: Boolean(entry?.is_in_disease),
          inferred: Boolean(entry?.is_inferred),
          type: cleanText(entry?.type) || "Pathway",
          reviewStatus: cleanText(entry?.review_status),
          hasDiagram: Boolean(entry?.has_diagram),
          hasEHLD: Boolean(entry?.has_ehld),
          releaseDate: cleanText(entry?.release_date),
          matchedQuery: cleanText(entry?.matched_query),
          compartment: cleanText(entry?.compartment),
          literature: entry?.literature,
          crossReferences: entry?.cross_references,
          raw: entry?.raw || entry,
        };
      });

      return uniqueById(normalized);
    }

    const legacyEntries = legacyGroups.flatMap((group: any) =>
      Array.isArray(group?.entries)
        ? group.entries.map((entry: any) => ({
            ...entry,
            _groupType: group?.typeName || "",
          }))
        : []
    );

    return uniqueById(
      legacyEntries
        .filter((entry: any) => entry?.type === "Pathway")
        .map((entry: any) => {
          const species = cleanText(entry?.species);

          return {
            id: cleanText(
              entry?.stId || entry?.id || entry?.dbId
            ),
            name: cleanText(entry?.name) || "Biological pathway",
            species,
            description: cleanText(entry?.summation),
            human: species
              .toLowerCase()
              .includes("homo sapiens"),
            disease: Boolean(
              entry?.isDisease || entry?.disease
            ),
            inferred: Boolean(entry?.isInferred),
            type: cleanText(
              entry?.exactType || entry?.type
            ) || "Pathway",
            reviewStatus: "",
            hasDiagram: false,
            hasEHLD: false,
            releaseDate: "",
            matchedQuery: "",
            compartment: cleanText(
              entry?.compartmentNames
            ),
            raw: entry,
          };
        })
    );
  }, [enrichedPathways, legacyGroups]);

  const humanPathways = pathwayEntries.filter(
    (entry: any) => entry.human
  );

  const otherSpeciesPathways = pathwayEntries.filter(
    (entry: any) => !entry.human
  );

  const diseasePathways = pathwayEntries.filter(
    (entry: any) => entry.disease
  );

  const inferredPathways = pathwayEntries.filter(
    (entry: any) => entry.inferred
  );

  const sources = ["Reactome"];

  const topPathway =
    humanPathways[0] ||
    pathwayEntries[0] ||
    null;

  const expandedQueries = Array.isArray(
    enrichedResult?.expanded_queries
  )
    ? enrichedResult.expanded_queries
    : [];

  const reasoning =
    analysis?.evidence_reasoning?.evidence_summary ||
    analysis?.evidence_reasoning?.summary ||
    "Reactome pathway records were resolved from the investigated biological concept and enriched with pathway-level metadata.";

  const groupCounts = useMemo(() => {
    const counts: Record<string, number> = {};

    for (const group of legacyGroups) {
      const name = cleanText(
        group?.typeName ||
          group?.type ||
          "Other"
      );

      const count = Number(
        group?.entriesCount || 0
      );

      if (name) {
        counts[name] = count;
      }
    }

    return counts;
  }, [legacyGroups]);

  return (
    <main className="cv-pathway-page">
      <Navbar />

      {/* HERO */}
      <section className="cv-pathway-hero">
        <div className="cv-pathway-hero-glow" />

        <div className="cv-pathway-network">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <div className="cv-pathway-core" />
        </div>

        <div className="cv-pathway-hero-copy">
          <div className="cv-eyebrow">
            04 / RESEARCH INTELLIGENCE
          </div>

          <h1>
            Trace Biology Through Connected Pathways.
          </h1>

          <p>
            Explore biological pathways, connected entities,
            molecular relationships, and supporting evidence
            through the CureVerseAI research intelligence layer.
          </p>

          <div className="cv-pathway-metrics">
            <div>
              <strong>REACTOME</strong>
              <span>PATHWAY KNOWLEDGE</span>
            </div>

            <div>
              <strong>MULTI-SOURCE</strong>
              <span>BIOLOGICAL EVIDENCE</span>
            </div>

            <div>
              <strong>AI</strong>
              <span>REASONED CONTEXT</span>
            </div>
          </div>
        </div>
      </section>

      {/* SEARCH */}
      <section className="cv-pathway-investigate">
        <div className="cv-section-heading">
          <div className="cv-section-number">01</div>

          <div>
            <div className="cv-eyebrow">
              PATHWAY INVESTIGATION
            </div>

            <h2>Follow the biological network.</h2>

            <p>
              Enter a pathway, process, or biological term and
              let CureVerseAI resolve connected research
              context from Reactome.
            </p>
          </div>
        </div>

        <form
          className="cv-pathway-form"
          onSubmit={investigate}
        >
          <input
            value={pathway}
            onChange={(e) =>
              setPathway(e.target.value)
            }
            placeholder="e.g. Mitosis, DNA Repair, p53 signaling"
            aria-label="Pathway"
          />

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "ANALYZING..."
              : "EXPLORE PATHWAY"}
            <span>↗</span>
          </button>
        </form>

        {error && (
          <div className="cv-pathway-error">
            {error}
          </div>
        )}
      </section>

      {/* RESULTS */}
      <section className="cv-pathway-results">
        {!searched && (
          <div className="cv-pathway-ready">
            <div className="cv-ready-orbit">
              <div />
            </div>

            <div>
              <div className="cv-eyebrow">
                READY FOR INVESTIGATION
              </div>

              <h3>
                Enter a biological pathway to begin.
              </h3>

              <p>
                Pathway records, species context, connected
                biological entities, evidence, and reasoning
                will appear here.
              </p>
            </div>

            <div className="cv-ready-status">
              SYSTEM READY
            </div>
          </div>
        )}

        {loading && (
          <div className="cv-pathway-loading">
            <div className="cv-loading-spinner" />

            <div>
              <div className="cv-eyebrow">
                ANALYSIS RUNNING
              </div>

              <h3>
                Mapping biological connections...
              </h3>

              <p>
                Expanding the biological concept, resolving
                pathway candidates, and retrieving detailed
                Reactome records.
              </p>
            </div>
          </div>
        )}

        {!loading && result && (
          <>
            {/* RESULT BANNER */}
            <div className="cv-pathway-result-banner">
              <div>
                <div className="cv-eyebrow">
                  PATHWAY RESOLUTION
                </div>

                <h2>{pathway}</h2>

                {topPathway ? (
                  <p>
                    Primary result:{" "}
                    <strong>{topPathway.name}</strong>
                    {" · "}
                    <span>{topPathway.id}</span>
                    {" · "}
                    {topPathway.species ||
                      "Species not specified"}
                  </p>
                ) : (
                  <p>
                    No enriched pathway record was returned
                    for this investigation.
                  </p>
                )}
              </div>

              <div className="cv-result-status">
                ANALYSIS COMPLETE
              </div>
            </div>

            {/* STATS */}
            <div className="cv-pathway-stats">
              <div>
                <strong>
                  {pathwayEntries.length}
                </strong>
                <span>PATHWAY RECORDS</span>
              </div>

              <div>
                <strong>
                  {humanPathways.length}
                </strong>
                <span>HUMAN PATHWAYS</span>
              </div>

              <div>
                <strong>
                  {diseasePathways.length}
                </strong>
                <span>DISEASE PATHWAYS</span>
              </div>

              <div>
                <strong>
                  {sources.length}
                </strong>
                <span>EVIDENCE SOURCES</span>
              </div>
            </div>

            {/* CONCEPT EXPANSION */}
            {expandedQueries.length > 1 && (
              <div className="cv-pathway-intelligence">
                <div className="cv-intelligence-heading">
                  <div className="cv-card-label">
                    CONCEPT RESOLUTION
                  </div>

                  <h2>
                    The search was expanded intelligently.
                  </h2>

                  <p>
                    CureVerseAI searched related biological
                    terminology to avoid relying on a single
                    Reactome result page.
                  </p>
                </div>

                <div className="cv-connected-counts">
                  {expandedQueries.map(
                    (query: string, index: number) => (
                      <div key={`${query}-${index}`}>
                        <strong>
                          {String(index + 1).padStart(
                            2,
                            "0"
                          )}
                        </strong>

                        <span>
                          {query.toUpperCase()}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* CONNECTED BIOLOGY */}
            <div className="cv-pathway-intelligence">
              <div className="cv-intelligence-heading">
                <div className="cv-card-label">
                  CONNECTED BIOLOGY
                </div>

                <h2>
                  What surrounds the pathway.
                </h2>

                <p>
                  The investigation resolves biological
                  pathway records and their supporting
                  contextual metadata.
                </p>
              </div>

              <div className="cv-connected-counts">
                <div>
                  <strong>
                    {humanPathways.length}
                  </strong>
                  <span>HUMAN</span>
                </div>

                <div>
                  <strong>
                    {otherSpeciesPathways.length}
                  </strong>
                  <span>CROSS-SPECIES</span>
                </div>

                <div>
                  <strong>
                    {diseasePathways.length}
                  </strong>
                  <span>DISEASE</span>
                </div>

                <div>
                  <strong>
                    {inferredPathways.length}
                  </strong>
                  <span>INFERRED</span>
                </div>

                {Object.entries(groupCounts)
                  .slice(0, 3)
                  .map(
                    ([name, count]) => (
                      <div key={name}>
                        <strong>
                          {Number(
                            count
                          ).toLocaleString()}
                        </strong>
                        <span>
                          {name.toUpperCase()}
                        </span>
                      </div>
                    )
                  )}
              </div>
            </div>

            {/* MAIN GRID */}
            <div className="cv-pathway-grid">
              <article className="cv-pathway-card cv-main-pathways">
                <div className="cv-card-label">
                  {humanPathways.length
                    ? "HUMAN PATHWAY RECORDS"
                    : "PATHWAY RECORDS"}
                </div>

                <h3>
                  Biological pathways
                </h3>

                {humanPathways.length ? (
                  <div className="cv-entity-list">
                    {humanPathways.map(
                      (
                        entry: any,
                        index: number
                      ) => (
                        <div
                          className="cv-pathway-entry"
                          key={entry.id}
                        >
                          <span>
                            {String(
                              index + 1
                            ).padStart(
                              2,
                              "0"
                            )}
                          </span>

                          <div>
                            <strong>
                              {entry.name}
                            </strong>

                            <small>
                              {entry.id}
                              {entry.species
                                ? ` · ${entry.species}`
                                : ""}
                            </small>

                            {entry.description && (
                              <p>
                                {entry.description.length >
                                280
                                  ? `${entry.description.slice(
                                      0,
                                      280
                                    )}…`
                                  : entry.description}
                              </p>
                            )}

                            <div className="cv-pathway-tags">
                              {entry.reviewStatus && (
                                <em>
                                  {entry.reviewStatus.toUpperCase()}
                                </em>
                              )}

                              {entry.hasDiagram && (
                                <em>DIAGRAM</em>
                              )}

                              {entry.disease && (
                                <em>DISEASE</em>
                              )}

                              {entry.inferred && (
                                <em>INFERRED</em>
                              )}

                              {entry.matchedQuery && (
                                <em>
                                  VIA{" "}
                                  {entry.matchedQuery.toUpperCase()}
                                </em>
                              )}
                            </div>
                          </div>

                          <a
                            href={`https://reactome.org/content/detail/${encodeURIComponent(
                              entry.id
                            )}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`Open ${entry.name} in Reactome`}
                          >
                            ↗
                          </a>
                        </div>
                      )
                    )}

                    {otherSpeciesPathways.length >
                      0 && (
                      <div className="cv-species-summary">
                        <span>
                          CROSS-SPECIES CONTEXT
                        </span>

                        <strong>
                          {
                            otherSpeciesPathways.length
                          } additional records
                        </strong>

                        <small>
                          Non-human Reactome records are
                          retained as contextual biological
                          evidence rather than replacing the
                          human pathway results.
                        </small>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="cv-empty-result">
                    No human pathway records were returned.
                  </div>
                )}
              </article>

              {/* SIDE */}
              <div className="cv-pathway-side">
                <article className="cv-pathway-card">
                  <div className="cv-card-label">
                    EVIDENCE
                  </div>

                  <h3>
                    Research support
                  </h3>

                  <div className="cv-evidence-list">
                    {sources.map(
                      (
                        source: string,
                        index: number
                      ) => (
                        <div
                          key={source}
                        >
                          <span>
                            {String(
                              index + 1
                            ).padStart(
                              2,
                              "0"
                            )}
                          </span>

                          <strong>
                            {source}
                          </strong>
                        </div>
                      )
                    )}
                  </div>
                </article>

                <article className="cv-pathway-card cv-reasoning-card">
                  <div className="cv-card-label">
                    EVIDENCE REASONING
                  </div>

                  <h3>
                    What the evidence supports
                  </h3>

                  <p>
                    {reasoning}
                  </p>

                  <div className="cv-reasoning-source">
                    <span>
                      PRIMARY SOURCE
                    </span>

                    <strong>
                      Reactome
                    </strong>
                  </div>
                </article>
              </div>
            </div>

            {/* PRIMARY RECORD */}
            <article className="cv-pathway-card cv-featured-pathway">
              <div>
                <div className="cv-card-label">
                  PRIMARY BIOLOGICAL RECORD
                </div>

                <h3>
                  {topPathway?.name ||
                    pathway}
                </h3>

                <p>
                  {topPathway?.description ||
                    "No pathway description was returned by the source."}
                </p>
              </div>

              <div className="cv-featured-meta">
                <div>
                  <span>REACTOME ID</span>
                  <strong>
                    {topPathway?.id || "—"}
                  </strong>
                </div>

                <div>
                  <span>SPECIES</span>
                  <strong>
                    {topPathway?.species ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <span>TYPE</span>
                  <strong>
                    {topPathway?.type ||
                      "PATHWAY"}
                  </strong>
                </div>

                <div>
                  <span>DISEASE</span>
                  <strong>
                    {topPathway?.disease
                      ? "YES"
                      : "NO"}
                  </strong>
                </div>

                <div>
                  <span>REVIEW</span>
                  <strong>
                    {topPathway?.reviewStatus ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <span>DIAGRAM</span>
                  <strong>
                    {topPathway?.hasDiagram
                      ? "AVAILABLE"
                      : "—"}
                  </strong>
                </div>
              </div>

              {topPathway?.id && (
                <a
                  className="cv-reactome-link"
                  href={`https://reactome.org/content/detail/${encodeURIComponent(
                    topPathway.id
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  READ FULL REACTOME RECORD
                  <span>↗</span>
                </a>
              )}
            </article>

            {/* CROSS SPECIES */}
            {otherSpeciesPathways.length > 0 && (
              <article className="cv-pathway-card cv-species-card">
                <div className="cv-card-label">
                  CROSS-SPECIES CONTEXT
                </div>

                <h3>
                  Comparative biological records
                </h3>

                <div className="cv-entity-list">
                  {otherSpeciesPathways.map(
                    (entry: any) => (
                      <div
                        className="cv-pathway-entry"
                        key={entry.id}
                      >
                        <span>↳</span>

                        <div>
                          <strong>
                            {entry.name}
                          </strong>

                          <small>
                            {entry.id} ·{" "}
                            {entry.species}
                          </small>
                        </div>

                        <a
                          href={`https://reactome.org/content/detail/${encodeURIComponent(
                            entry.id
                          )}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Open ${entry.name} in Reactome`}
                        >
                          ↗
                        </a>
                      </div>
                    )
                  )}
                </div>
              </article>
            )}

            {/* RAW RECORD */}
            <article className="cv-pathway-card cv-raw-card">
              <div className="cv-card-label">
                ANALYSIS RECORD
              </div>

              <h3>
                Research intelligence output
              </h3>

              <pre>
                {JSON.stringify(
                  result,
                  null,
                  2
                )}
              </pre>
            </article>
          </>
        )}
      </section>

      <Footer />
    </main>
  );
}
