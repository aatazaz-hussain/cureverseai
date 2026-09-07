"use client";

import { FormEvent, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

type Status = "idle" | "processing" | "success" | "not-found" | "error";

type AnyRecord = Record<string, any>;

type EvidenceResult = {
  success?: boolean;
  data?: {
    result?: AnyRecord;
  };
};

const API_BASE =
  process.env.NEXT_PUBLIC_CUREVERSEAI_API_URL ||
  "http://localhost:8000";

const stages = [
  ["01", "BIOLOGY"],
  ["02", "DISEASE"],
  ["03", "EXPERIMENT"],
  ["04", "EVIDENCE"],
  ["05", "REASONING"],
];

function pretty(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function safeArray(value: unknown): AnyRecord[] {
  return Array.isArray(value) ? value : [];
}

function EvidenceVisual({ processing }: { processing: boolean }) {
  return (
    <div className={`evr-visual ${processing ? "is-processing" : ""}`}>
      <div className="evr-visual-grid" />

      <div className="evr-ring evr-ring-a" />
      <div className="evr-ring evr-ring-b" />
      <div className="evr-ring evr-ring-c" />

      <div className="evr-line evr-line-a" />
      <div className="evr-line evr-line-b" />
      <div className="evr-line evr-line-c" />
      <div className="evr-line evr-line-d" />

      <div className="evr-node evr-node-a">
        <span />
        BIOLOGY
      </div>

      <div className="evr-node evr-node-b">
        <span />
        DISEASE
      </div>

      <div className="evr-node evr-node-c">
        <span />
        ACTIVITY
      </div>

      <div className="evr-node evr-node-d">
        <span />
        SOURCES
      </div>

      <div className="evr-core">
        <small>EVIDENCE</small>
        <strong>ENGINE</strong>
        <i />
        <span>CONNECTED BIOLOGY</span>
      </div>

      <div className="evr-scan" />
    </div>
  );
}

function Metric({
  number,
  label,
  detail,
}: {
  number: string | number;
  label: string;
  detail: string;
}) {
  return (
    <div className="evr-metric">
      <strong>{number}</strong>
      <span>{label}</span>
      <small>{detail}</small>
    </div>
  );
}

function SourceCard({
  number,
  title,
  source,
  count,
  description,
}: {
  number: string;
  title: string;
  source: string;
  count: number;
  description: string;
}) {
  return (
    <article className="evr-source-card">
      <div className="evr-source-top">
        <span>{number}</span>
        <b>{source}</b>
        <i>↗</i>
      </div>

      <h3>{title}</h3>

      <div className="evr-source-count">
        <strong>{count}</strong>
        <span>records connected</span>
      </div>

      <p>{description}</p>
    </article>
  );
}

export default function EvidenceResearchPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<EvidenceResult | null>(null);
  const [error, setError] = useState("");

  const evidence = result?.data?.result;

  const openTargets = evidence?.open_targets_evidence || {};
  const chembl = evidence?.chembl_evidence || {};

  const openTargetEvidence = safeArray(openTargets.evidence);
  const chemblRelationships = safeArray(chembl.relationships);
  const chemblCompounds = safeArray(chembl.compounds);
  const chemblTargets = safeArray(chembl.targets);

  const openTargetSummary =
    (openTargets.summary || {}) as AnyRecord;

  const openTargetProvenance =
    (openTargets.provenance || {}) as AnyRecord;

  const chemblSummary =
    (chembl.summary || {}) as AnyRecord;

  const chemblProvenance =
    (chembl.provenance || {}) as AnyRecord;

  const diseaseEntries = useMemo(() => {
    return openTargetEvidence
      .map((item) => {
        const metadata = item.metadata || {};

        return {
          disease:
            metadata.disease_name ||
            item.disease_name ||
            item.disease ||
            "Disease association",
          score:
            metadata.association_score ??
            item.association_score ??
            null,
          source: item.source || "Open Targets",
          description: item.description || "",
        };
      })
      .slice(0, 8);
  }, [openTargetEvidence]);

  const totalEvidence =
    openTargetEvidence.length +
    chemblRelationships.length +
    chemblCompounds.length +
    chemblTargets.length;

  async function runResearch(event: FormEvent) {
    event.preventDefault();

    const gene = query.trim();

    if (!gene) return;

    setStatus("processing");
    setResult(null);
    setError("");

    try {
      /*
       * Keep the processing state visible long enough to make the
       * evidence synthesis feel deliberate and scientific.
       */
      const minimumDelay = new Promise((resolve) =>
        window.setTimeout(resolve, 3400),
      );

      const request = fetch(`${API_BASE}/api/v1/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: "research",
          task: "evidence_research",
          input: {
            gene,
          },
        }),
      });

      const [response] = await Promise.all([request, minimumDelay]);

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(
          payload?.detail?.message ||
            payload?.detail ||
            "Evidence research failed.",
        );
      }

      const returned = payload as EvidenceResult;
      const biologicalResult = returned?.data?.result;

      if (!biologicalResult?.gene) {
        setStatus("not-found");
        setResult(null);
        return;
      }

      setResult(returned);
      setStatus("success");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete evidence research.",
      );
      setStatus("error");
    }
  }

  return (
    <main className="evr-page">
      <Navbar />

      <section className="evr-hero">
        <div className="evr-hero-grid" />
        <div className="evr-hero-glow" />

        <div className="evr-hero-copy">
          <div className="evr-eyebrow">
            <span>05</span>
            <i />
            RESEARCH INTELLIGENCE
          </div>

          <h1>
            Evidence
            <br />
            <em>connected.</em>
          </h1>

          <p>
            Follow biological evidence across target identity, disease
            associations, experimental activity, external sources and
            evidence-aware reasoning.
          </p>

          <div className="evr-hero-meta">
            {stages.slice(0, 3).map(([number, label]) => (
              <div key={number}>
                <strong>{number}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        <EvidenceVisual processing={status === "processing"} />
      </section>

      <section className="evr-workbench">
        <div className="evr-section-number">01</div>

        <div className="evr-workbench-heading">
          <div>
            <div className="evr-eyebrow">INVESTIGATION WORKBENCH</div>
            <h2>
              Ask the biological
              <span>question.</span>
            </h2>
          </div>

          <p>
            Resolve a biological target and trace the evidence connected to
            it across the CureVerseAI intelligence layer.
          </p>
        </div>

        <form className="evr-search" onSubmit={runResearch}>
          <div className="evr-search-index">
            <span>01</span>
            <small>TARGET</small>
          </div>

          <div className="evr-search-field">
            <label>GENE / BIOLOGICAL ENTITY</label>

            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Enter biological target"
              autoComplete="off"
              spellCheck={false}
            />
          </div>

          <button type="submit" disabled={status === "processing"}>
            {status === "processing" ? (
              <>
                <i />
                ANALYZING
              </>
            ) : (
              <>
                INVESTIGATE
                <span>→</span>
              </>
            )}
          </button>
        </form>
      </section>

      {status === "processing" && (
        <section className="evr-processing">
          <EvidenceVisual processing />

          <div className="evr-processing-copy">
            <div className="evr-eyebrow">
              <span>LIVE</span>
              <i />
              EVIDENCE SYNTHESIS
            </div>

            <h2>
              Connecting
              <span>biological evidence.</span>
            </h2>

            <div className="evr-processing-steps">
              {stages.map(([number, label], index) => (
                <div key={number}>
                  <span>{number}</span>
                  <strong>{label}</strong>
                  <i className={index < 3 ? "active" : ""} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {status === "not-found" && (
        <section className="evr-not-found">
          <span>NO BIOLOGICAL RECORD</span>
          <h2>
            NOT FOUND — No matching biological record was found for this
            query.
          </h2>
        </section>
      )}

      {status === "error" && (
        <section className="evr-error">
          <span>ANALYSIS ERROR</span>
          <h2>{error}</h2>
        </section>
      )}

      {status === "success" && evidence && (
        <>
          <section className="evr-result">
            <div className="evr-section-number">02</div>

            <div className="evr-result-heading">
              <div>
                <div className="evr-eyebrow">
                  EVIDENCE CONNECTED BIOLOGY
                </div>

                <h2>
                  {String(evidence.gene).toUpperCase()}
                  <span>research record.</span>
                </h2>
              </div>

              <div className="evr-result-status">
                <i />
                CONNECTED
              </div>
            </div>

            <div className="evr-metrics">
              <Metric
                number={totalEvidence}
                label="TOTAL EVIDENCE"
                detail="Connected records"
              />

              <Metric
                number={openTargetEvidence.length}
                label="DISEASE EVIDENCE"
                detail="Open Targets"
              />

              <Metric
                number={chemblRelationships.length}
                label="ACTIVITY"
                detail="ChEMBL relationships"
              />

              <Metric
                number={chemblCompounds.length}
                label="COMPOUNDS"
                detail="Connected molecules"
              />

              <Metric
                number={chemblTargets.length}
                label="TARGETS"
                detail="Validated targets"
              />
            </div>
          </section>

          <section className="evr-landscape">
            <div className="evr-section-number">03</div>

            <div className="evr-section-heading">
              <div>
                <div className="evr-eyebrow">EVIDENCE LANDSCAPE</div>
                <h2>
                  One target.
                  <span>Multiple evidence layers.</span>
                </h2>
              </div>

              <p>
                Different evidence layers answer different biological
                questions. CureVerseAI keeps those signals connected rather
                than collapsing them into one unexplained score.
              </p>
            </div>

            <div className="evr-landscape-grid">
              <SourceCard
                number="01"
                source="OPEN TARGETS"
                title="Disease association"
                count={openTargetEvidence.length}
                description="Target–disease associations retrieved through the connected Open Targets evidence layer."
              />

              <SourceCard
                number="02"
                source="CHEMBL"
                title="Experimental activity"
                count={chemblRelationships.length}
                description="Experimental activity relationships connected to the biological target."
              />

              <SourceCard
                number="03"
                source="CHEMBL"
                title="Compound context"
                count={chemblCompounds.length}
                description="Compounds represented in the connected experimental evidence structure."
              />

              <SourceCard
                number="04"
                source="BIOLOGY"
                title="Target context"
                count={chemblTargets.length}
                description="Validated target records connected to the evidence investigation."
              />
            </div>
          </section>

          <section className="evr-diseases">
            <div className="evr-section-number">04</div>

            <div className="evr-section-heading">
              <div>
                <div className="evr-eyebrow">CONNECTED DISEASE EVIDENCE</div>
                <h2>
                  What the target
                  <span>is associated with.</span>
                </h2>
              </div>
            </div>

            <div className="evr-disease-grid">
              {diseaseEntries.length ? (
                diseaseEntries.map((entry, index) => (
                  <article className="evr-disease-card" key={`${entry.disease}-${index}`}>
                    <div className="evr-disease-number">
                      {String(index + 1).padStart(2, "0")}
                    </div>

                    <div>
                      <span>{entry.source}</span>
                      <h3>{entry.disease}</h3>

                      {entry.description && (
                        <p>{entry.description}</p>
                      )}
                    </div>

                    <div className="evr-disease-score">
                      <small>ASSOCIATION</small>
                      <strong>
                        {entry.score !== null
                          ? Number(entry.score).toFixed(3)
                          : "—"}
                      </strong>
                    </div>
                  </article>
                ))
              ) : (
                <div className="evr-empty">
                  No disease association records were returned.
                </div>
              )}
            </div>
          </section>

          <section className="evr-provenance">
            <div className="evr-section-number">05</div>

            <div className="evr-section-heading">
              <div>
                <div className="evr-eyebrow">SOURCE INTELLIGENCE</div>
                <h2>
                  Evidence with
                  <span>provenance.</span>
                </h2>
              </div>

              <p>
                Inspect where the connected evidence came from and how much
                information was retrieved by each source layer.
              </p>
            </div>

            <div className="evr-provenance-grid">
              <article>
                <span>01 / OPEN TARGETS</span>
                <h3>Disease intelligence</h3>

                <div>
                  <small>TARGET ID</small>
                  <strong>
                    {openTargetProvenance?.open_targets?.target_id ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <small>TOTAL ASSOCIATIONS</small>
                  <strong>
                    {openTargetProvenance?.open_targets
                      ?.total_associations ?? "—"}
                  </strong>
                </div>

                <div>
                  <small>RETRIEVED ROWS</small>
                  <strong>
                    {openTargetProvenance?.open_targets
                      ?.retrieved_rows ?? openTargetEvidence.length}
                  </strong>
                </div>
              </article>

              <article>
                <span>02 / CHEMBL</span>
                <h3>Experimental bioactivity</h3>

                <div>
                  <small>ACTIVITY RECORDS</small>
                  <strong>
                    {chemblSummary?.activities ??
                      chemblSummary?.activity_count ??
                      chemblRelationships.length}
                  </strong>
                </div>

                <div>
                  <small>COMPOUNDS</small>
                  <strong>
                    {chemblCompounds.length}
                  </strong>
                </div>

                <div>
                  <small>TARGETS</small>
                  <strong>
                    {chemblTargets.length}
                  </strong>
                </div>
              </article>
            </div>
          </section>

          <section className="evr-records">
            <div className="evr-section-number">06</div>

            <div className="evr-section-heading">
              <div>
                <div className="evr-eyebrow">RESEARCH RECORDS</div>
                <h2>
                  Inspect the
                  <span>evidence structure.</span>
                </h2>
              </div>
            </div>

            <div className="evr-record-grid">
              <article className="evr-record-card">
                <div className="evr-record-heading">
                  <span>01</span>
                  <div>
                    <small>OPEN TARGETS</small>
                    <strong>DISEASE ASSOCIATION</strong>
                  </div>
                  <i>↗</i>
                </div>

                {openTargetEvidence.slice(0, 6).map((item, index) => (
                  <div className="evr-record-row" key={index}>
                    <span>{String(index + 1).padStart(2, "0")}</span>

                    <div>
                      <strong>
                        {item.metadata?.disease_name ||
                          item.disease_name ||
                          "Disease association"}
                      </strong>

                      <small>
                        {item.description ||
                          "Target–disease association"}
                      </small>
                    </div>

                    <b>
                      {item.metadata?.association_score !==
                      undefined
                        ? Number(
                            item.metadata.association_score,
                          ).toFixed(3)
                        : "—"}
                    </b>
                  </div>
                ))}
              </article>

              <article className="evr-record-card">
                <div className="evr-record-heading">
                  <span>02</span>
                  <div>
                    <small>CHEMBL</small>
                    <strong>EXPERIMENTAL ACTIVITY</strong>
                  </div>
                  <i>↗</i>
                </div>

                {chemblRelationships.slice(0, 8).map((item, index) => (
                  <div className="evr-record-row" key={index}>
                    <span>{String(index + 1).padStart(2, "0")}</span>

                    <div>
                      <strong>
                        {item.compound ||
                          item.compound_name ||
                          item.assay ||
                          "Activity relationship"}
                      </strong>

                      <small>
                        {pretty(
                          item.activity_type ||
                            item.standard_type ||
                            item.relationship ||
                            "Experimental evidence",
                        )}
                      </small>
                    </div>

                    <b>
                      {item.standard_value ??
                        item.value ??
                        "—"}
                    </b>
                  </div>
                ))}

                {!chemblRelationships.length && (
                  <div className="evr-empty">
                    No experimental activity relationships were returned.
                  </div>
                )}
              </article>
            </div>

            <details className="evr-raw">
              <summary>
                <span>07 / COMPLETE ANALYSIS RECORD</span>
                <strong>VIEW STRUCTURED OUTPUT +</strong>
              </summary>

              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          </section>
        </>
      )}

      <Footer />
    </main>
  );
}
