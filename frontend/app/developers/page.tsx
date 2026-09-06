"use client";

import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import "./developers.css";

const developers = [
  {
    number: "01",
    name: "Arooj Kanwal",
    image: "/team/girl-01.png",
    hometown: "Mianwali, Pakistan",
    role: "PROJECT MANAGER",
    secondaryRole: "DATABASE ADMINISTRATOR",
    discipline: "BS SOFTWARE ENGINEERING",
    focus: "PROJECT ARCHITECTURE · DATA SYSTEMS · COORDINATION",

    intro:
      "Arooj Kanwal is a seventh-semester BS Software Engineering student at Pir Mehr Ali Shah Arid Agriculture University, Rawalpindi, and a core member of the team behind CureVerseAI. Her contribution to the project sits at the intersection of technical organization, project direction and structured data management.",

    body:
      "As Project Manager, Arooj works across the development lifecycle to maintain alignment between the project's objectives, technical implementation and team responsibilities. Her role involves translating a complex system vision into an organized development structure, coordinating the work of different technical areas and maintaining a clear progression from requirements to implementation.",

    technical:
      "Her responsibilities extend deeply into the platform's data architecture. As Database Administrator, she contributes to the organization of biological entities, proteins, genes, variants, pathways, diseases, compounds, targets, assays, bioactivity records, evidence and analysis runs. This structured foundation allows CureVerseAI to treat biological information as connected data rather than isolated records.",

    philosophy:
      "For Arooj, effective software development is not only about writing functionality. It is about creating an environment in which information, people and technology remain organized enough for a complex system to evolve reliably.",

    tags: ["PROJECT MANAGEMENT", "DATABASE", "DATA ARCHITECTURE"],
  },

  {
    number: "02",
    name: "Aatazaz Hussain",
    image: "/team/boy.png",
    hometown: "Mianwali, Pakistan",
    role: "BACKEND DEVELOPER",
    secondaryRole: "AI DEVELOPER",
    discipline: "BS SOFTWARE ENGINEERING",
    focus: "AI ENGINEERING · BACKEND SYSTEMS · BIOLOGICAL INTELLIGENCE",

    intro:
      "Aatazaz Hussain is a seventh-semester BS Software Engineering student at Pir Mehr Ali Shah Arid Agriculture University, Rawalpindi. Within CureVerseAI, his work is centered on the computational core of the platform — connecting backend services, biological data infrastructure and artificial-intelligence workflows into one functioning system.",

    body:
      "His backend contribution focuses on the services that connect the user-facing platform with CureVerseAI's intelligence engine. He works on API communication, analysis orchestration and the computational pathways through which a biological question is transformed into structured analysis.",

    technical:
      "On the AI side, his work brings together pretrained biological models, protein representations, molecular representations, cellular information, multimodal feature fusion and evidence reasoning. CureVerseAI connects resources such as Ensembl, Reactome, UniProt, Open Targets and ChEMBL with model-derived representations so that biological analysis can combine computational intelligence with external evidence.",

    philosophy:
      "The objective is not simply to produce an AI-generated answer. The deeper engineering challenge is to construct the path behind that answer — identifying the biological entity, gathering context, applying appropriate models, retrieving evidence and separating evidence types before presenting an interpretable result.",

    tags: ["BACKEND", "AI ENGINEERING", "BIOLOGICAL INTELLIGENCE"],
  },

  {
    number: "03",
    name: "Umme Hani",
    image: "/team/girl-02.png",
    hometown: "Mianwali, Pakistan",
    role: "FRONTEND DEVELOPER",
    secondaryRole: "AI DEVELOPER",
    discipline: "BS SOFTWARE ENGINEERING",
    focus: "USER EXPERIENCE · FRONTEND SYSTEMS · AI INTERACTION",

    intro:
      "Umme Hani is a seventh-semester BS Software Engineering student at Pir Mehr Ali Shah Arid Agriculture University, Rawalpindi. Her role within CureVerseAI combines frontend engineering with artificial-intelligence development, focusing on the point where a complex computational system becomes a meaningful human experience.",

    body:
      "Her frontend work is responsible for shaping how CureVerseAI is experienced. This includes interface architecture, responsive layouts, interaction patterns, navigation and the visual presentation of biological information. The challenge is to communicate technically complex results without reducing the scientific character of the platform.",

    technical:
      "Alongside frontend development, Umme contributes to the AI layer of the project. Her work helps connect the intelligence produced by the underlying analysis pipeline with the interfaces through which users explore biological questions, evidence and results.",

    philosophy:
      "Her approach treats interface design as part of the intelligence system itself. A powerful model is only useful when its output can be understood, explored and connected to the user's original question. CureVerseAI therefore aims to make computational biology visible without making it unnecessarily complicated.",

    tags: ["FRONTEND", "AI DEVELOPMENT", "USER EXPERIENCE"],
  },
];

export default function DevelopersPage() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const sections = document.querySelectorAll("[data-developer]");

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = Number(
              (entry.target as HTMLElement).dataset.developer
            );

            if (!Number.isNaN(index)) {
              setActive(index);
            }

            entry.target.classList.add("is-visible");
          }
        });
      },
      {
        threshold: 0.25,
      }
    );

    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  return (
    <main className="developers-page">
      <Navbar />

      {/* HERO */}
      <section className="developers-hero">
        <div className="developers-hero-image" />

        <div className="developers-hero-grid" />

        <div className="developers-hero-content">
          <div className="developers-eyebrow">
            <span>THE PEOPLE</span>
            <i />
            <span>01 — CUREVERSEAI</span>
          </div>

          <div className="developers-hero-title">
            <span className="title-small">BEHIND THE</span>
            <h1>
              <span>INTELLIGENCE</span>
              <em>ENGINE.</em>
            </h1>
          </div>

          <p className="developers-hero-description">
            CureVerseAI is being developed by a team of seventh-semester
            Software Engineering students at Pir Mehr Ali Shah Arid
            Agriculture University, Rawalpindi — bringing together project
            management, data architecture, backend engineering, frontend
            systems and artificial intelligence.
          </p>

          <div className="developers-hero-meta">
            <div>
              <span>ACADEMIC PROGRAM</span>
              <strong>BS SOFTWARE ENGINEERING</strong>
            </div>

            <div>
              <span>SEMESTER</span>
              <strong>07 / SEVENTH</strong>
            </div>

            <div>
              <span>UNIVERSITY</span>
              <strong>PMAS-AAUR</strong>
            </div>

            <div>
              <span>LOCATION</span>
              <strong>RAWALPINDI</strong>
            </div>
          </div>
        </div>

        <div className="developers-hero-index">
          <span>SCROLL TO EXPLORE</span>
          <b>↓</b>
        </div>
      </section>

      {/* INTRODUCTION */}
      <section className="developers-introduction">
        <div className="section-number">02</div>

        <div className="introduction-heading">
          <span>THE TEAM</span>
          <h2>
            Engineering
            <br />
            <i>with purpose.</i>
          </h2>
        </div>

        <div className="introduction-copy">
          <p className="lead">
            CureVerseAI brings together three different technical
            perspectives around one shared objective: building a connected
            biological intelligence platform.
          </p>

          <p>
            The project is structured across multiple layers — from
            biological data and database architecture to artificial
            intelligence, backend services and the interfaces through which
            users interact with the system.
          </p>

          <p>
            Each member of the team contributes to a different part of this
            architecture. Together, these responsibilities form a development
            structure designed to move CureVerseAI from biological information
            toward usable, evidence-aware intelligence.
          </p>

          <div className="introduction-line">
            <span>DATA</span>
            <i />
            <span>MODELS</span>
            <i />
            <span>ENGINEERING</span>
            <i />
            <span>INTELLIGENCE</span>
          </div>
        </div>
      </section>

      {/* DEVELOPER SECTIONS */}
      <section className="developers-list">
        {developers.map((developer, index) => (
          <article
            key={developer.name}
            data-developer={index}
            className={`developer-section ${
              index === active ? "active-section" : ""
            }`}
          >
            <div className="developer-background-number">
              {developer.number}
            </div>

            <div className="developer-visual">
              <div className="visual-orbit orbit-one" />
              <div className="visual-orbit orbit-two" />
              <div className="visual-orbit orbit-three" />

              <div className="visual-crosshair">
                <span />
                <span />
              </div>

              <div className="developer-image-frame">
                <img
                  src={developer.image}
                  alt={developer.name}
                />
              </div>

              <div className="developer-visual-label">
                <span>CVAI / TEAM</span>
                <strong>{developer.number}</strong>
              </div>
            </div>

            <div className="developer-information">
              <div className="developer-topline">
                <span>{developer.number} / PROFILE</span>
                <span>{developer.hometown}</span>
              </div>

              <div className="developer-name-block">
                <span className="developer-name-kicker">
                  CORE CONTRIBUTOR
                </span>

                <h2>{developer.name}</h2>

                <div className="developer-role">
                  <strong>{developer.role}</strong>
                  <i>×</i>
                  <strong>{developer.secondaryRole}</strong>
                </div>
              </div>

              <div className="developer-divider" />

              <div className="developer-profile-grid">
                <div>
                  <span>DISCIPLINE</span>
                  <strong>{developer.discipline}</strong>
                </div>

                <div>
                  <span>PRIMARY FOCUS</span>
                  <strong>{developer.focus}</strong>
                </div>
              </div>

              <div className="developer-description">
                <p className="developer-intro">{developer.intro}</p>

                <p>{developer.body}</p>

                <div className="technical-panel">
                  <span>TECHNICAL CONTRIBUTION</span>
                  <p>{developer.technical}</p>
                </div>

                <div className="philosophy-panel">
                  <span>APPROACH</span>
                  <p>{developer.philosophy}</p>
                </div>
              </div>

              <div className="developer-tags">
                {developer.tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            </div>
          </article>
        ))}
      </section>

      {/* TEAM CLOSING */}
      <section className="developers-closing">
        <div className="closing-grid" />

        <div className="closing-content">
          <span className="closing-kicker">
            06 / THE MISSION CONTINUES
          </span>

          <h2>
            Different
            <br />
            <i>disciplines.</i>
            <br />
            One system.
          </h2>

          <p>
            CureVerseAI represents a collaborative engineering effort where
            project organization, structured data, artificial intelligence,
            backend infrastructure and frontend experience converge around a
            single biological intelligence platform.
          </p>

          <div className="closing-signature">
            <span>CUREVERSEAI</span>
            <i />
            <span>PMAS-AAUR · RAWALPINDI</span>
          </div>
        </div>
      </section>

      <footer className="developers-footer">
        <span>CUREVERSEAI</span>
        <span>BS SOFTWARE ENGINEERING · PMAS-AAUR</span>
        <span>2026</span>
      </footer>
    </main>
  );
}
