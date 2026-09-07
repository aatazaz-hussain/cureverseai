"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./books.css";

type Book = {
  id: number;
  category: string;
  title: string;
  author: string;
  description: string;
  source: string;
  href: string;
};

const books: Book[] = [
  {
    id: 1,
    category: "BIOLOGY",
    title: "Biology 2e",
    author: "OpenStax",
    description:
      "A comprehensive introductory biology textbook covering cells, genetics, evolution, physiology, ecology, and the foundations of life science.",
    source: "OpenStax",
    href: "https://openstax.org/details/books/biology-2e/",
  },
  {
    id: 2,
    category: "GENETICS",
    title: "Understanding Genetics",
    author: "Genetic Alliance",
    description:
      "A practical guide covering genes, DNA, genomes, genetic disease, inheritance, genetic testing, and genetic counseling.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK132180/",
  },
  {
    id: 3,
    category: "GENOMICS",
    title: "An Introduction to Genomes",
    author: "NCBI Bookshelf",
    description:
      "A structured introduction to genomes, transcriptomes, proteomes, genome organization, and the methods used to study them.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK21130/",
  },
  {
    id: 4,
    category: "CELL BIOLOGY",
    title: "Molecular Biology of the Cell",
    author: "Alberts et al.",
    description:
      "A foundational molecular and cellular biology resource covering cells, genomes, genetic mechanisms, signaling, and cellular organization.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK21077/",
  },
  {
    id: 5,
    category: "MOLECULAR BIOLOGY",
    title: "The Cell: A Molecular Approach",
    author: "Geoffrey M. Cooper",
    description:
      "An accessible molecular view of cell structure, molecular mechanisms, genetic information, and cellular function.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK9839/",
  },
  {
    id: 6,
    category: "GENETICS",
    title: "Basic Genetic Mechanisms",
    author: "Alberts et al.",
    description:
      "A focused resource on DNA replication, repair, recombination, genome reading, protein synthesis, and gene regulation.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK21071/",
  },
  {
    id: 7,
    category: "GENE EXPRESSION",
    title: "How Cells Read the Genome",
    author: "Alberts et al.",
    description:
      "Explores transcription, RNA processing, translation, protein formation, and the flow of information from DNA to biological function.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK21050/",
  },
  {
    id: 8,
    category: "GENE REGULATION",
    title: "Control of Gene Expression",
    author: "Alberts et al.",
    description:
      "Introduces the mechanisms controlling when and where genes are expressed and how cellular specialization emerges.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK21057/",
  },
  {
    id: 9,
    category: "DNA",
    title: "The Structure and Function of DNA",
    author: "NCBI Bookshelf",
    description:
      "A focused biological resource exploring DNA structure, genetic information, molecular organization, and biological inheritance.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK26821/",
  },
  {
    id: 10,
    category: "GENETICS",
    title: "Genetic Twists of Fate",
    author: "Fields & Johnston",
    description:
      "A genetics resource connecting genes with disease, development, gene therapy, proteins, and stem-cell biology.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK559913/",
  },
  {
    id: 11,
    category: "GENOMICS",
    title: "Mapping and Sequencing the Human Genome",
    author: "National Research Council",
    description:
      "A foundational account of genome mapping, sequencing, genomic research, and the scientific implications of the Human Genome Project.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK218247/",
  },
  {
    id: 12,
    category: "GENOMICS",
    title: "Using Population Descriptors in Genetics and Genomics Research",
    author: "National Academies",
    description:
      "A modern framework for understanding population descriptors and their responsible use in human genetics and genomics research.",
    source: "National Academies / NCBI",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK589855/",
  },
  {
    id: 13,
    category: "PRECISION MEDICINE",
    title: "Improving Health Through Genomics",
    author: "National Academies",
    description:
      "Explores the potential of genomics across precision health care, including genomic medicine, sequencing, and health applications.",
    source: "National Academies / NCBI",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK592652/",
  },
  {
    id: 14,
    category: "SYSTEMS BIOLOGY",
    title: "Promise and Challenges in Systems Microbiology",
    author: "National Research Council",
    description:
      "Introduces systems approaches, modeling, tools, and emerging directions for understanding complex microbial systems.",
    source: "NCBI Bookshelf",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK215855/",
  },
  {
    id: 15,
    category: "GENOMICS",
    title: "Genes, Behavior, and the Social Environment",
    author: "National Academies",
    description:
      "Examines genetic influences, gene-environment interactions, genomic variation, and their relationship to health.",
    source: "National Academies / NCBI",
    href: "https://www.ncbi.nlm.nih.gov/books/NBK19932/",
  },
];

const categories = [
  "ALL",
  "BIOLOGY",
  "CELL BIOLOGY",
  "MOLECULAR BIOLOGY",
  "GENETICS",
  "GENOMICS",
  "GENE EXPRESSION",
  "GENE REGULATION",
  "DNA",
  "SYSTEMS BIOLOGY",
  "PRECISION MEDICINE",
];

export default function EducationBooksPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("ALL");

  const filteredBooks = useMemo(() => {
    const search = query.trim().toLowerCase();

    return books.filter((book) => {
      const categoryMatch =
        category === "ALL" || book.category === category;

      const searchMatch =
        !search ||
        book.title.toLowerCase().includes(search) ||
        book.author.toLowerCase().includes(search) ||
        book.description.toLowerCase().includes(search) ||
        book.category.toLowerCase().includes(search) ||
        book.source.toLowerCase().includes(search);

      return categoryMatch && searchMatch;
    });
  }, [query, category]);

  return (
    <main className="cv-books-page">
      <Navbar />

      {/* HERO */}
      <section className="cv-books-hero">
        <div className="cv-books-grid-bg" />
        <div className="cv-books-glow" />

        <div className="cv-books-hero-inner">
          <div className="cv-eyebrow">
            02 / EDUCATION LIBRARY
          </div>

          <h1>
            Read deeper.
            <br />
            <span>Build your foundation.</span>
          </h1>

          <p>
            A curated collection of open and freely accessible
            scientific books covering biology, genetics,
            genomics, cells, molecular systems, and the
            foundations behind CureVerseAI.
          </p>

          <div className="cv-books-stats">
            <div>
              <strong>15</strong>
              <span>CURATED BOOKS</span>
            </div>

            <div>
              <strong>10</strong>
              <span>SCIENCE AREAS</span>
            </div>

            <div>
              <strong>PDF</strong>
              <span>OPEN ACCESS</span>
            </div>
          </div>
        </div>

        {/* BOOK KNOWLEDGE ENGINE */}
        <div className="cv-books-hero-visual">
          <div className="cv-book-aura" />

          <div className="cv-book-orbit cv-book-orbit-a" />
          <div className="cv-book-orbit cv-book-orbit-b" />
          <div className="cv-book-orbit cv-book-orbit-c" />

          <div className="cv-book-stack">
            <div className="cv-book-page page-back" />
            <div className="cv-book-page page-middle" />
            <div className="cv-book-page page-front">
              <div className="cv-book-page-top">
                <span>CV</span>
                <b>02</b>
              </div>

              <div className="cv-book-page-lines">
                <i />
                <i />
                <i />
                <i />
                <i />
              </div>

              <strong>KNOWLEDGE</strong>
              <small>BIOLOGY / GENOMICS</small>
            </div>
          </div>

          <div className="cv-book-node node-a">
            <strong>GENES</strong>
            <span>01</span>
          </div>

          <div className="cv-book-node node-b">
            <strong>CELL</strong>
            <span>02</span>
          </div>

          <div className="cv-book-node node-c">
            <strong>DNA</strong>
            <span>03</span>
          </div>

          <div className="cv-book-node node-d">
            <strong>AI</strong>
            <span>04</span>
          </div>

          <div className="cv-book-particle book-particle-a" />
          <div className="cv-book-particle book-particle-b" />
          <div className="cv-book-particle book-particle-c" />
          <div className="cv-book-particle book-particle-d" />

          <div className="cv-book-scan" />

          <div className="cv-book-status">
            <span>SCIENTIFIC LIBRARY</span>
            <strong>OPEN</strong>
          </div>
        </div>
      </section>

      {/* LIBRARY */}
      <section className="cv-books-library">
        <div className="cv-books-toolbar">
          <div>
            <div className="cv-eyebrow">
              BOOK COLLECTION
            </div>

            <h2>Explore the library.</h2>
          </div>

          <div className="cv-book-count">
            {filteredBooks.length}
            <span> BOOKS</span>
          </div>
        </div>

        <div className="cv-books-search">
          <span>⌕</span>

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search biology, genetics, genomics..."
            aria-label="Search books"
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

        <div className="cv-book-filters">
          {categories.map((item) => (
            <button
              key={item}
              type="button"
              className={category === item ? "active" : ""}
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>

        {filteredBooks.length > 0 ? (
          <div className="cv-books-grid">
            {filteredBooks.map((book) => (
              <a
                key={book.id}
                href={book.href}
                target="_blank"
                rel="noopener noreferrer"
                className="cv-book-card"
              >
                <div className="cv-book-card-top">
                  <span>
                    {String(book.id).padStart(2, "0")}
                  </span>

                  <b>PDF ↗</b>
                </div>

                <div className="cv-book-cover">
                  <div className="cv-mini-cover">
                    <span>CV</span>
                    <strong>{book.category}</strong>
                    <i />
                    <small>OPEN SCIENCE</small>
                  </div>
                </div>

                <div className="cv-book-card-content">
                  <div className="cv-book-category">
                    {book.category}
                  </div>

                  <h3>{book.title}</h3>

                  <div className="cv-book-author">
                    {book.author}
                  </div>

                  <p>{book.description}</p>
                </div>

                <div className="cv-book-card-footer">
                  <span>{book.source}</span>
                  <strong>OPEN PDF ↗</strong>
                </div>

                <div className="cv-book-scan" />
              </a>
            ))}
          </div>
        ) : (
          <div className="cv-books-empty">
            <span>NO MATCHES</span>

            <h3>
              Nothing matched your search.
            </h3>

            <p>
              Try another scientific topic or reset the
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

      {/* CLOSING */}
      <section className="cv-books-closing">
        <div className="cv-books-closing-grid" />

        <div className="cv-eyebrow">
          READ / CONNECT / UNDERSTAND
        </div>

        <h2>
          Knowledge becomes powerful
          <br />
          <span>when it connects.</span>
        </h2>

        <p>
          Build your foundation here, then take what you
          learn into the biological intelligence of CureVerseAI.
        </p>

        <Link
          href="/domains/research"
          className="cv-books-closing-button"
        >
          EXPLORE RESEARCH
          <span>↗</span>
        </Link>
      </section>

      <Footer />
    </main>
  );
}
