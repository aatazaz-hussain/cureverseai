"use client";
import Footer from "@/components/Footer";

import Navbar from "../../components/Navbar";
import "./contact.css";

const inquiryTypes = [
  "Research Collaboration",
  "Technical Inquiry",
  "Project Discussion",
  "Academic Collaboration",
  "General Inquiry",
];

export default function ContactPage() {
  return (
    <main className="contact-page">
      <Navbar />

      {/* HERO */}
      <section className="contact-hero">
        <div className="contact-hero-grid" />

        <div className="contact-hero-glow" />

        <div className="contact-hero-content">
          <div className="contact-kicker">
            <span>07 / CONNECTION</span>
            <i />
            <span>CUREVERSEAI</span>
          </div>

          <h1>
            Let&apos;s build
            <br />
            <em>what comes next.</em>
          </h1>

          <p>
            CureVerseAI is designed around collaboration — connecting
            biological data, artificial intelligence, evidence and people.
            Whether the conversation begins with a research question,
            technical idea or collaboration opportunity, this is where it
            starts.
          </p>

          <div className="contact-hero-signal">
            <span className="signal-dot" />
            <span>OPEN FOR RESEARCH · TECHNICAL · ACADEMIC DISCUSSION</span>
          </div>
        </div>

        <div className="contact-hero-mark">
          <span>CV</span>
          <small>AI</small>
        </div>
      </section>

      {/* CONTACT SYSTEM */}
      <section className="contact-system">
        <div className="contact-system-header">
          <div>
            <span className="contact-section-number">01</span>
            <span className="contact-section-label">
              COMMUNICATION CHANNEL
            </span>
          </div>

          <p>
            Tell us what you are exploring. The conversation can be about
            biology, AI, software engineering, research or the future
            direction of CureVerseAI.
          </p>
        </div>

        <div className="contact-grid">

          {/* LEFT — CHANNELS */}
          <aside className="contact-channels">

            <div className="channel-intro">
              <span>DIRECT CHANNELS</span>
              <h2>
                Choose your
                <br />
                <i>entry point.</i>
              </h2>
            </div>

            <a
              href="mailto:cureverseai@gmail.com"
              className="contact-channel"
            >
              <div className="channel-icon">@</div>

              <div>
                <span>EMAIL</span>
                <strong>cureverseai@gmail.com</strong>
                <small>For research and project communication</small>
              </div>

              <b>↗</b>
            </a>

            <a
              href="https://www.linkedin.com/"
              target="_blank"
              rel="noreferrer"
              className="contact-channel"
            >
              <div className="channel-icon">in</div>

              <div>
                <span>NETWORK</span>
                <strong>LinkedIn</strong>
                <small>Connect with the development team</small>
              </div>

              <b>↗</b>
            </a>

            <div className="contact-channel contact-channel-static">
              <div className="channel-icon">01</div>

              <div>
                <span>PROJECT</span>
                <strong>CureVerseAI</strong>
                <small>
                  Biological Intelligence · AI · Software Engineering
                </small>
              </div>
            </div>

            <div className="contact-status">
              <span className="status-light" />
              <div>
                <strong>CONNECTION STATUS</strong>
                <small>Available for meaningful discussion</small>
              </div>
            </div>
          </aside>

          {/* RIGHT — FORM */}
          <div className="contact-form-shell">

            <div className="form-topline">
              <span>02 / START A CONVERSATION</span>
              <span>CVAI / CONTACT</span>
            </div>

            <div className="form-heading">
              <h2>
                What are you
                <br />
                <span>working on?</span>
              </h2>

              <p>
                Give us enough context to understand the direction of the
                conversation. Short or detailed — both are welcome.
              </p>
            </div>

            <form
              className="contact-form"
              onSubmit={async (e) => {
                e.preventDefault();

                const form = e.currentTarget;
                const formData = new FormData(form);

                const payload = {
                  name: String(formData.get("name") || ""),
                  email: String(formData.get("email") || ""),
                  conversation_type: String(formData.get("type") || ""),
                  message: String(formData.get("message") || ""),
                };

                const button = form.querySelector("button[type=\"submit\"]");
                const buttonText = button?.querySelector("span");

                if (button instanceof HTMLButtonElement) {
                  button.disabled = true;
                }

                if (buttonText) {
                  buttonText.textContent = "TRANSMITTING...";
                }

                try {
                  const response = await fetch(
                    "http://localhost:8000/api/v1/contact",
                    {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify(payload),
                    }
                  );

                  const result = await response.json();

                  if (!response.ok) {
                    throw new Error(
                      result?.detail?.message ||
                      result?.detail ||
                      "Unable to send your message."
                    );
                  }

                  form.reset();

                  if (buttonText) {
                    buttonText.textContent = "MESSAGE RECEIVED ✓";
                  }

                  setTimeout(() => {
                    if (buttonText) {
                      buttonText.textContent = "TRANSMIT MESSAGE";
                    }
                  }, 3000);
                } catch (error) {
                  console.error("Contact submission failed:", error);

                  if (buttonText) {
                    buttonText.textContent = "TRANSMISSION FAILED";
                  }

                  setTimeout(() => {
                    if (buttonText) {
                      buttonText.textContent = "TRANSMIT MESSAGE";
                    }
                  }, 3000);
                } finally {
                  if (button instanceof HTMLButtonElement) {
                    button.disabled = false;
                  }
                }
              }}
            >
              <div className="form-row">
                <label>
                  <span>YOUR NAME</span>
                  <input
                    type="text"
                    name="name"
                    placeholder="Enter your name"
                    required
                  />
                </label>

                <label>
                  <span>EMAIL ADDRESS</span>
                  <input
                    type="email"
                    name="email"
                    placeholder="you@example.com"
                    required
                  />
                </label>
              </div>

              <label>
                <span>CONVERSATION TYPE</span>

                <select name="type" defaultValue="">
                  <option value="" disabled>
                    Select an entry point
                  </option>

                  {inquiryTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>YOUR MESSAGE</span>

                <textarea
                  name="message"
                  rows={7}
                  placeholder="Describe the idea, question, research direction or collaboration you have in mind..."
                  required
                />
              </label>

              <div className="form-bottom">
                <div>
                  <span>DATA HANDLING</span>
                  <small>
                    Your information is used only to respond to this
                    conversation.
                  </small>
                </div>

                <button type="submit">
                  <span>TRANSMIT MESSAGE</span>
                  <b>↗</b>
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* WHY CONTACT */}
      <section className="contact-purpose">

        <div className="purpose-header">
          <span>03 / WHY CONNECT</span>

          <h2>
            Some questions
            <br />
            <i>need more than a form.</i>
          </h2>
        </div>

        <div className="purpose-grid">

          <article>
            <span>01</span>
            <h3>RESEARCH</h3>
            <p>
              Discuss biological questions, computational research
              directions, datasets, biological targets and opportunities to
              explore new research workflows with CureVerseAI.
            </p>
          </article>

          <article>
            <span>02</span>
            <h3>TECHNOLOGY</h3>
            <p>
              Explore the engineering behind the platform — biological data
              infrastructure, AI models, multimodal representations,
              evidence retrieval and intelligent analysis systems.
            </p>
          </article>

          <article>
            <span>03</span>
            <h3>COLLABORATION</h3>
            <p>
              If you are building something at the intersection of biology,
              medicine, biotechnology, education or artificial intelligence,
              start a conversation with the team.
            </p>
          </article>

          <article>
            <span>04</span>
            <h3>ACADEMIA</h3>
            <p>
              CureVerseAI is being developed as a software engineering
              project at PMAS-Arid Agriculture University, Rawalpindi, with
              an interest in meaningful academic and technical exchange.
            </p>
          </article>

        </div>
      </section>

      {/* FINAL */}
      <section className="contact-final">

        <div className="contact-final-orbit orbit-a" />
        <div className="contact-final-orbit orbit-b" />

        <div className="contact-final-content">
          <span>04 / CUREVERSEAI</span>

          <h2>
            Biology is
            <br />
            <i>connected.</i>
          </h2>

          <p>
            And meaningful innovation is connected too — people, ideas,
            evidence, engineering and the questions that bring them together.
          </p>

          <div className="contact-final-line">
            <span>DATA</span>
            <i />
            <span>MODELS</span>
            <i />
            <span>EVIDENCE</span>
            <i />
            <span>PEOPLE</span>
          </div>
        </div>
      </section>
      <Footer />
    </main>
  );
}
