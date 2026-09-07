"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./articles.css";

type Article = {
  id: number;
  category: string;
  title: string;
  description: string;
  source: string;
  href: string;
  internal?: boolean;
};

const articles: Article[] = [
  {
    id: 1,
    category: "VIRTUAL CELL",
    title: "Can AI Build a Virtual Cell?",
    description:
      "How researchers are using artificial intelligence to model and predict cellular behavior.",
    source: "Nature",
    href: "https://www.nature.com/articles/d41586-025-02011-0",
  },
  {
    id: 2,
    category: "VIRTUAL CELL",
    title: "How to Build the Virtual Cell with AI",
    description:
      "A scientific perspective on priorities, opportunities, and the challenges of building AI virtual cells.",
    source: "Cell / PubMed",
    href: "https://pubmed.ncbi.nlm.nih.gov/39672099/",
  },
  {
    id: 3,
    category: "VIRTUAL CELL",
    title: "The Virtual Cell",
    description:
      "An overview of emerging AI-based computational models designed to represent cellular systems.",
    source: "Nature Methods",
    href: "https://www.nature.com/articles/s41592-025-02951-5",
  },
  {
    id: 4,
    category: "VIRTUAL CELL",
    title: "Grow AI Virtual Cells",
    description:
      "Why data, experimental feedback, and closed-loop learning matter for developing AI virtual cells.",
    source: "Cell Research",
    href: "https://www.nature.com/articles/s41422-025-01101-y",
  },
  {
    id: 5,
    category: "CELL AI",
    title: "Single-Cell Foundation Models",
    description:
      "How foundation models are being applied to single-cell biology, gene regulation, and perturbation analysis.",
    source: "Nature",
    href: "https://www.nature.com/articles/s12276-025-01547-5",
  },
  {
    id: 6,
    category: "CELL AI",
    title: "Towards Multimodal Foundation Models in Molecular Cell Biology",
    description:
      "How genomics, transcriptomics, proteomics, spatial data, and other modalities can be brought together.",
    source: "Nature",
    href: "https://www.nature.com/articles/s41586-025-08710-y",
  },
  {
    id: 7,
    category: "CELL AI",
    title: "scGPT: Foundation Models for Single-Cell Biology",
    description:
      "An introduction to generative pretrained models for genes, cells, perturbations, and multi-omics.",
    source: "Nature Methods",
    href: "https://www.nature.com/articles/s41592-024-02201-0",
  },
  {
    id: 8,
    category: "PROTEINS",
    title: "What Are Proteins and How Do We Know Their Structures?",
    description:
      "A clear introduction to proteins, amino acids, folding, structure, and biological function.",
    source: "EMBL-EBI",
    href: "https://www.ebi.ac.uk/training/online/courses/alphafold/an-introductory-guide-to-its-strengths-and-limitations/what-are-proteins-and-how-do-we-know-their-structures/",
  },
  {
    id: 9,
    category: "PROTEINS",
    title: "AlphaFold: Accelerating Breakthroughs in Biology",
    description:
      "Explore how AI-based protein structure prediction is changing structural biology and research.",
    source: "Google DeepMind",
    href: "https://deepmind.google/science/alphafold/",
  },
  {
    id: 10,
    category: "PROTEINS",
    title: "AlphaFold and the Protein Universe",
    description:
      "How large-scale protein structure prediction opened new possibilities for biological research.",
    source: "Google DeepMind",
    href: "https://deepmind.google/blog/alphafold-reveals-the-structure-of-the-protein-universe/",
  },
  {
    id: 11,
    category: "GENETICS",
    title: "What Is a Gene?",
    description:
      "A concise introduction to genes, inheritance, protein-coding information, and biological traits.",
    source: "NHGRI",
    href: "https://www.genome.gov/genetics-glossary/Gene",
  },
  {
    id: 12,
    category: "GENETICS",
    title: "What Is a Genome?",
    description:
      "Understand the complete DNA instruction set and how genomes are organized inside cells.",
    source: "NHGRI",
    href: "https://www.genome.gov/genetics-glossary/Genome",
  },
  {
    id: 13,
    category: "GENETICS",
    title: "Understanding DNA",
    description:
      "Explore DNA structure, bases, genetic information, and the molecular language of life.",
    source: "NHGRI",
    href: "https://www.genome.gov/genetics-glossary/Deoxyribonucleic-Acid-DNA",
  },
  {
    id: 14,
    category: "GENETICS",
    title: "The Genetic Code",
    description:
      "Learn how DNA sequences encode information that guides protein production.",
    source: "NHGRI",
    href: "https://www.genome.gov/genetics-glossary/Genetic-Code",
  },
  {
    id: 15,
    category: "PATHWAYS",
    title: "What Is Reactome?",
    description:
      "Learn how curated biological reactions and pathways organize knowledge about human biology.",
    source: "Reactome",
    href: "https://reactome.org/what-is-reactome/",
  },
  {
    id: 16,
    category: "PATHWAYS",
    title: "Exploring Biological Pathways",
    description:
      "Learn how pathway hierarchies, reactions, proteins, and molecular events are connected.",
    source: "Reactome",
    href: "https://reactome.org/userguide/pathway-browser",
  },
  {
    id: 17,
    category: "DRUG DEVELOPMENT",
    title: "Machine Learning in Preclinical Drug Discovery",
    description:
      "Explore how machine learning is being applied to hit discovery, mechanism analysis, and molecular optimization.",
    source: "Nature Chemical Biology",
    href: "https://www.nature.com/articles/s41589-024-01679-1",
  },
  {
    id: 18,
    category: "DRUG DEVELOPMENT",
    title: "What Is the Open Targets Platform?",
    description:
      "Understand how target-disease evidence can support systematic therapeutic target identification and prioritisation.",
    source: "Open Targets",
    href: "https://opentargets.org/",
  },
  {
    id: 19,
    category: "BIOTECHNOLOGY",
    title: "What Is CRISPR?",
    description:
      "An accessible introduction to CRISPR gene editing and how guide RNA directs Cas proteins to DNA.",
    source: "NIGMS",
    href: "https://www.nigms.nih.gov/biobeat/2024/10/what-is-crispr",
  },
  {
    id: 20,
    category: "CUREVERSEAI",
    title: "Explore CureVerseAI Research",
    description:
      "Investigate genes, proteins, variants, pathways, and biological evidence through the CureVerseAI Research domain.",
    source: "CureVerseAI",
    href: "/domains/research",
    internal: true,
  },
];

const categories = [
  "ALL",
  "VIRTUAL CELL",
  "CELL AI",
  "PROTEINS",
  "GENETICS",
  "PATHWAYS",
  "DRUG DEVELOPMENT",
  "BIOTECHNOLOGY",
  "CUREVERSEAI",
];

export default function EducationArticlesPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("ALL");

  const filteredArticles = useMemo(() => {
    const search = query.trim().toLowerCase();

    return articles.filter((article) => {
      const categoryMatch =
        category === "ALL" ||
        article.category === category;

      const searchMatch =
        !search ||
        article.title.toLowerCase().includes(search) ||
        article.description.toLowerCase().includes(search) ||
        article.category.toLowerCase().includes(search) ||
        article.source.toLowerCase().includes(search);

      return categoryMatch && searchMatch;
    });
  }, [query, category]);

  return (
    <main className="cv-articles-page">
      <Navbar />

      <section className="cv-articles-hero">
        <div className="cv-articles-grid-bg" />
        <div className="cv-articles-glow" />

        <div className="cv-articles-hero-inner">
          <div className="cv-eyebrow">
            01 / EDUCATION LIBRARY
          </div>

          <h1>
            Read the science.
            <br />
            <span>Understand the system.</span>
          </h1>

          <p>
            A curated learning library covering virtual cells,
            genes, proteins, pathways, artificial intelligence,
            drug discovery, biotechnology, and the science
            behind CureVerseAI.
          </p>

          <div className="cv-articles-stats">
            <div>
              <strong>20</strong>
              <span>CURATED READS</span>
            </div>

            <div>
              <strong>08</strong>
              <span>LEARNING AREAS</span>
            </div>

            <div>
              <strong>01</strong>
              <span>CONNECTED LIBRARY</span>
            </div>
          </div>
        </div>

        {/* ANIMATED SCIENTIFIC KNOWLEDGE ENGINE */}
        <div className="cv-articles-hero-visual">

          <div className="cv-hero-visual-glow" />

          <div className="cv-hero-orbit cv-hero-orbit-a" />
          <div className="cv-hero-orbit cv-hero-orbit-b" />
          <div className="cv-hero-orbit cv-hero-orbit-c" />

          <div className="cv-hero-core">
            <div className="cv-hero-core-inner">
              <span>AI</span>
            </div>
          </div>

          <div className="cv-hero-node cv-hero-node-a">
            <strong>DNA</strong>
            <span>GENETICS</span>
          </div>

          <div className="cv-hero-node cv-hero-node-b">
            <strong>PROTEIN</strong>
            <span>STRUCTURE</span>
          </div>

          <div className="cv-hero-node cv-hero-node-c">
            <strong>CELL</strong>
            <span>BIOLOGY</span>
          </div>

          <div className="cv-hero-node cv-hero-node-d">
            <strong>PATHWAY</strong>
            <span>SYSTEMS</span>
          </div>

          <div className="cv-hero-particle particle-a" />
          <div className="cv-hero-particle particle-b" />
          <div className="cv-hero-particle particle-c" />
          <div className="cv-hero-particle particle-d" />
          <div className="cv-hero-particle particle-e" />
          <div className="cv-hero-particle particle-f" />

          <div className="cv-hero-scan" />

          <div className="cv-hero-readout">
            <span>KNOWLEDGE ENGINE</span>
            <strong>ACTIVE</strong>
          </div>

        </div>
      </section>

      <section className="cv-articles-library">
        <div className="cv-articles-toolbar">
          <div>
            <div className="cv-eyebrow">
              LEARNING LIBRARY
            </div>

            <h2>
              Explore what interests you.
            </h2>
          </div>

          <div className="cv-article-count">
            {filteredArticles.length}
            <span> RESULTS</span>
          </div>
        </div>

        <div className="cv-articles-search">
          <span>⌕</span>

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search biology, virtual cells, proteins, AI..."
            aria-label="Search articles"
          />

          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
            >
              CLEAR
            </button>
          )}
        </div>

        <div className="cv-article-filters">
          {categories.map((item) => (
            <button
              key={item}
              type="button"
              className={
                category === item
                  ? "active"
                  : ""
              }
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>

        {filteredArticles.length > 0 ? (
          <div className="cv-articles-grid">
            {filteredArticles.map((article) => {
              const content = (
                <>
                  <div className="cv-article-top">
                    <span>
                      {String(article.id).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    <b>↗</b>
                  </div>

                  <div className="cv-article-content">
                    <div className="cv-article-category">
                      {article.category}
                    </div>

                    <h3>{article.title}</h3>

                    <p>
                      {article.description}
                    </p>
                  </div>

                  <div className="cv-article-footer">
                    <span>
                      {article.source}
                    </span>

                    <strong>
                      READ MORE ↗
                    </strong>
                  </div>

                  <div className="cv-article-scan" />
                </>
              );

              if (article.internal) {
                return (
                  <Link
                    href={article.href}
                    className="cv-article-card"
                    key={article.id}
                  >
                    {content}
                  </Link>
                );
              }

              return (
                <a
                  href={article.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cv-article-card"
                  key={article.id}
                >
                  {content}
                </a>
              );
            })}
          </div>
        ) : (
          <div className="cv-articles-empty">
            <span>NO MATCHES</span>
            <h3>
              Nothing matched your search.
            </h3>
            <p>
              Try another biological term or clear the
              category filter.
            </p>
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setCategory("ALL");
              }}
            >
              RESET LIBRARY
            </button>
          </div>
        )}
      </section>

      <section className="cv-articles-feature">
        <div className="cv-articles-feature-visual">
          <div className="cv-feature-orbit orbit-a" />
          <div className="cv-feature-orbit orbit-b" />
          <div className="cv-feature-core">
            <span />
            <span />
            <span />
          </div>
        </div>

        <div className="cv-articles-feature-copy">
          <div className="cv-eyebrow">
            START WITH THE BIG QUESTION
          </div>

          <h2>
            What would it take to
            <br />
            <span>build a virtual cell?</span>
          </h2>

          <p>
            The virtual cell sits at the intersection of
            biology, AI, multi-omics data, and computational
            modeling. Start there, then explore the genes,
            proteins, pathways, and technologies that make
            the idea possible.
          </p>

          <a
            href="https://www.nature.com/articles/d41586-025-02011-0"
            target="_blank"
            rel="noopener noreferrer"
            className="cv-feature-link"
          >
            EXPLORE THE VIRTUAL CELL
            <span>↗</span>
          </a>
        </div>
      </section>

      <Footer />
    </main>
  );
}
