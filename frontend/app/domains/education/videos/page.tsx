"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./videos.css";

type Video = {
  id: number;
  category: string;
  title: string;
  description: string;
  channel: string;
  duration: string;
  youtube: string;
};

const videos: Video[] = [
  {
    id: 1,
    category: "VIRTUAL CELL",
    title: "The Virtual Cell",
    description:
      "Explore the emerging idea of using AI to model cells and understand complex biological systems.",
    channel: "Nature",
    duration: "SCIENCE",
    youtube: "https://www.youtube.com/results?search_query=Nature+virtual+cell+AI",
  },
  {
    id: 2,
    category: "CELL BIOLOGY",
    title: "The Inner Life of the Cell",
    description:
      "A visual journey through molecular processes and the remarkable machinery operating inside a living cell.",
    channel: "Harvard / XVIVO",
    duration: "CELL",
    youtube: "https://www.youtube.com/results?search_query=The+Inner+Life+of+the+Cell+Harvard+XVIVO",
  },
  {
    id: 3,
    category: "CELL BIOLOGY",
    title: "Molecular Machines",
    description:
      "See how molecular machines perform essential biological functions at microscopic scales.",
    channel: "HHMI BioInteractive",
    duration: "BIOLOGY",
    youtube: "https://www.youtube.com/results?search_query=HHMI+BioInteractive+molecular+machines",
  },
  {
    id: 4,
    category: "GENETICS",
    title: "DNA Structure and Replication",
    description:
      "Understand the molecular structure of DNA and how cells copy genetic information.",
    channel: "HHMI BioInteractive",
    duration: "GENETICS",
    youtube: "https://www.youtube.com/results?search_query=HHMI+BioInteractive+DNA+replication",
  },
  {
    id: 5,
    category: "GENETICS",
    title: "How CRISPR Works",
    description:
      "Learn the basic mechanism behind CRISPR gene editing and how guide RNA directs molecular targeting.",
    channel: "NIGMS / NIH",
    duration: "BIOTECH",
    youtube: "https://www.youtube.com/results?search_query=NIGMS+NIH+how+CRISPR+works",
  },
  {
    id: 6,
    category: "PROTEINS",
    title: "What Is a Protein?",
    description:
      "Understand amino acids, protein structure, folding, and why proteins are fundamental to life.",
    channel: "EMBL-EBI",
    duration: "PROTEINS",
    youtube: "https://www.youtube.com/results?search_query=EMBL-EBI+what+are+proteins",
  },
  {
    id: 7,
    category: "PROTEINS",
    title: "How AlphaFold Works",
    description:
      "Explore how artificial intelligence can predict protein structures and transform structural biology.",
    channel: "Google DeepMind",
    duration: "AI + BIO",
    youtube: "https://www.youtube.com/results?search_query=Google+DeepMind+AlphaFold+how+it+works",
  },
  {
    id: 8,
    category: "PROTEINS",
    title: "AlphaFold and the Protein Universe",
    description:
      "Discover how large-scale protein structure prediction is expanding our understanding of biology.",
    channel: "Google DeepMind",
    duration: "ALPHAFOLD",
    youtube: "https://www.youtube.com/results?search_query=Google+DeepMind+AlphaFold+protein+universe",
  },
  {
    id: 9,
    category: "AI + BIOLOGY",
    title: "AI for Science",
    description:
      "Explore how artificial intelligence is being applied to scientific discovery and biological research.",
    channel: "Google DeepMind",
    duration: "AI",
    youtube: "https://www.youtube.com/results?search_query=Google+DeepMind+AI+for+science+biology",
  },
  {
    id: 10,
    category: "SINGLE CELL",
    title: "Single-Cell Biology",
    description:
      "Learn how scientists use single-cell technologies to investigate the diversity and states of individual cells.",
    channel: "Nature",
    duration: "SINGLE CELL",
    youtube: "https://www.youtube.com/results?search_query=Nature+single+cell+biology",
  },
  {
    id: 11,
    category: "GENOMICS",
    title: "What Is Genomics?",
    description:
      "An introduction to genomes, sequencing, genetic variation, and the growing field of genomics.",
    channel: "NHGRI",
    duration: "GENOMICS",
    youtube: "https://www.youtube.com/results?search_query=NHGRI+what+is+genomics",
  },
  {
    id: 12,
    category: "GENETICS",
    title: "How Genes Work",
    description:
      "Understand how genes carry information and how cells use that information to make functional molecules.",
    channel: "TED-Ed",
    duration: "GENES",
    youtube: "https://www.youtube.com/results?search_query=TED-Ed+how+genes+work",
  },
  {
    id: 13,
    category: "CELL BIOLOGY",
    title: "How Cells Divide",
    description:
      "Explore the molecular events behind mitosis and how cells faithfully distribute their genetic material.",
    channel: "HHMI BioInteractive",
    duration: "MITOSIS",
    youtube: "https://www.youtube.com/results?search_query=HHMI+BioInteractive+mitosis+cell+division",
  },
  {
    id: 14,
    category: "PATHWAYS",
    title: "Cell Signaling",
    description:
      "Learn how cells communicate through molecular signals, receptors, pathways, and intracellular responses.",
    channel: "Nature",
    duration: "SIGNALING",
    youtube: "https://www.youtube.com/results?search_query=Nature+cell+signaling+biology",
  },
  {
    id: 15,
    category: "DRUG DEVELOPMENT",
    title: "How Drugs Find Their Targets",
    description:
      "Understand the relationship between biological targets, molecules, binding, and therapeutic discovery.",
    channel: "Nature",
    duration: "DRUG DISCOVERY",
    youtube: "https://www.youtube.com/results?search_query=Nature+drug+discovery+biological+targets",
  },
  {
    id: 16,
    category: "BIOTECHNOLOGY",
    title: "Synthetic Biology",
    description:
      "Explore how scientists engineer biological systems and build new functions from biological components.",
    channel: "Nature",
    duration: "SYNBIO",
    youtube: "https://www.youtube.com/results?search_query=Nature+synthetic+biology",
  },
  {
    id: 17,
    category: "MOLECULAR BIOLOGY",
    title: "From DNA to Protein",
    description:
      "Follow the flow of biological information from DNA through RNA to protein.",
    channel: "HHMI BioInteractive",
    duration: "MOLECULAR",
    youtube: "https://www.youtube.com/results?search_query=HHMI+BioInteractive+DNA+RNA+protein",
  },
  {
    id: 18,
    category: "BIOLOGY",
    title: "How Cells Communicate",
    description:
      "Discover the molecular language cells use to coordinate activities and respond to their environment.",
    channel: "TED-Ed",
    duration: "CELL SIGNALS",
    youtube: "https://www.youtube.com/results?search_query=TED-Ed+how+cells+communicate",
  },
  {
    id: 19,
    category: "AI + BIOLOGY",
    title: "Machine Learning in Biology",
    description:
      "See how machine learning is becoming a tool for analyzing biological data and discovering patterns.",
    channel: "Nature",
    duration: "ML",
    youtube: "https://www.youtube.com/results?search_query=Nature+machine+learning+biology",
  },
  {
    id: 20,
    category: "CUREVERSEAI",
    title: "Explore CureVerseAI Research",
    description:
      "Continue from video learning into live biological investigation across genes, proteins, variants, pathways, and evidence.",
    channel: "CureVerseAI",
    duration: "EXPLORE",
    youtube: "/domains/research",
  },
];

const categories = [
  "ALL",
  "VIRTUAL CELL",
  "CELL BIOLOGY",
  "GENETICS",
  "GENOMICS",
  "PROTEINS",
  "AI + BIOLOGY",
  "SINGLE CELL",
  "PATHWAYS",
  "DRUG DEVELOPMENT",
  "BIOTECHNOLOGY",
  "MOLECULAR BIOLOGY",
  "BIOLOGY",
  "CUREVERSEAI",
];

export default function EducationVideosPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("ALL");

  const filteredVideos = useMemo(() => {
    const search = query.trim().toLowerCase();

    return videos.filter((video) => {
      const categoryMatch =
        category === "ALL" || video.category === category;

      const searchMatch =
        !search ||
        video.title.toLowerCase().includes(search) ||
        video.description.toLowerCase().includes(search) ||
        video.channel.toLowerCase().includes(search) ||
        video.category.toLowerCase().includes(search);

      return categoryMatch && searchMatch;
    });
  }, [query, category]);

  return (
    <main className="cv-videos-page">
      <Navbar />

      {/* HERO */}
      <section className="cv-videos-hero">
        <div className="cv-videos-grid-bg" />
        <div className="cv-videos-glow" />

        <div className="cv-videos-hero-inner">
          <div className="cv-eyebrow">
            03 / EDUCATION LIBRARY
          </div>

          <h1>
            See biology.
            <br />
            <span>Watch ideas come alive.</span>
          </h1>

          <p>
            Curated scientific videos covering cells, genes,
            proteins, genomics, artificial intelligence,
            biotechnology, drug development, and the ideas
            shaping modern life science.
          </p>

          <div className="cv-videos-stats">
            <div>
              <strong>20</strong>
              <span>CURATED VIDEOS</span>
            </div>

            <div>
              <strong>12</strong>
              <span>SCIENCE AREAS</span>
            </div>

            <div>
              <strong>YT</strong>
              <span>VIDEO LIBRARY</span>
            </div>
          </div>
        </div>

        {/* VIDEO KNOWLEDGE ENGINE */}
        <div className="cv-videos-hero-visual">

          <div className="cv-video-aura" />

          <div className="cv-video-orbit video-orbit-a" />
          <div className="cv-video-orbit video-orbit-b" />
          <div className="cv-video-orbit video-orbit-c" />

          <div className="cv-video-frame">
            <div className="cv-video-frame-top">
              <span>CV / 03</span>
              <b>● LIVE</b>
            </div>

            <div className="cv-video-screen">
              <div className="cv-video-dna">
                <i />
                <i />
                <i />
                <i />
                <i />
                <i />
              </div>

              <div className="cv-video-play">
                <span>▶</span>
              </div>

              <div className="cv-video-wave wave-a" />
              <div className="cv-video-wave wave-b" />
            </div>

            <div className="cv-video-frame-bottom">
              <span>BIOLOGY / AI / LIFE</span>
              <strong>PLAY</strong>
            </div>
          </div>

          <div className="cv-video-node video-node-a">
            <strong>CELL</strong>
            <span>01</span>
          </div>

          <div className="cv-video-node video-node-b">
            <strong>DNA</strong>
            <span>02</span>
          </div>

          <div className="cv-video-node video-node-c">
            <strong>AI</strong>
            <span>03</span>
          </div>

          <div className="cv-video-node video-node-d">
            <strong>PROTEIN</strong>
            <span>04</span>
          </div>

          <div className="cv-video-particle video-particle-a" />
          <div className="cv-video-particle video-particle-b" />
          <div className="cv-video-particle video-particle-c" />
          <div className="cv-video-particle video-particle-d" />

          <div className="cv-video-scan" />

          <div className="cv-video-status">
            <span>LEARNING STREAM</span>
            <strong>ACTIVE</strong>
          </div>
        </div>
      </section>

      {/* VIDEO LIBRARY */}
      <section className="cv-videos-library">
        <div className="cv-videos-toolbar">
          <div>
            <div className="cv-eyebrow">
              VIDEO LIBRARY
            </div>

            <h2>Watch. Explore. Understand.</h2>
          </div>

          <div className="cv-video-count">
            {filteredVideos.length}
            <span> VIDEOS</span>
          </div>
        </div>

        <div className="cv-videos-search">
          <span>⌕</span>

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search biology, cells, proteins, AI..."
            aria-label="Search videos"
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

        <div className="cv-video-filters">
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

        {filteredVideos.length > 0 ? (
          <div className="cv-videos-grid">
            {filteredVideos.map((video) => {
              const isInternal =
                video.youtube.startsWith("/");

              if (isInternal) {
                return (
                  <Link
                    key={video.id}
                    href={video.youtube}
                    className="cv-video-card"
                  >
                    <VideoCard video={video} />
                  </Link>
                );
              }

              return (
                <a
                  key={video.id}
                  href={video.youtube}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cv-video-card"
                >
                  <VideoCard video={video} />
                </a>
              );
            })}
          </div>
        ) : (
          <div className="cv-videos-empty">
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
      <section className="cv-videos-closing">
        <div className="cv-videos-closing-grid" />

        <div className="cv-eyebrow">
          WATCH / QUESTION / DISCOVER
        </div>

        <h2>
          Biology is easier to understand
          <br />
          <span>when you can see it.</span>
        </h2>

        <p>
          Start with a video, follow the concept, then take
          the question into CureVerseAI Research.
        </p>

        <Link
          href="/domains/research"
          className="cv-videos-closing-button"
        >
          EXPLORE RESEARCH
          <span>↗</span>
        </Link>
      </section>

      <Footer />
    </main>
  );
}

function VideoCard({ video }: { video: Video }) {
  return (
    <>
      <div className="cv-video-card-top">
        <span>
          {String(video.id).padStart(2, "0")}
        </span>

        <b>YOUTUBE ↗</b>
      </div>

      <div className="cv-video-thumbnail">
        <div className="cv-thumbnail-grid" />

        <div className="cv-thumbnail-orbit orbit-one" />
        <div className="cv-thumbnail-orbit orbit-two" />

        <div className="cv-thumbnail-core">
          <span>▶</span>
        </div>

        <div className="cv-thumbnail-label">
          {video.duration}
        </div>
      </div>

      <div className="cv-video-card-content">
        <div className="cv-video-category">
          {video.category}
        </div>

        <h3>{video.title}</h3>

        <p>{video.description}</p>
      </div>

      <div className="cv-video-card-footer">
        <span>{video.channel}</span>
        <strong>WATCH ↗</strong>
      </div>

      <div className="cv-video-card-scan" />
    </>
  );
}
