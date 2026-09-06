export default function Footer() {
  return (
    <footer className="cv-footer">
      <div className="cv-footer-inner">

        <div className="cv-footer-intro">
          <a href="/" className="cv-footer-brand">
            <span className="cv-brand-mark">
              <i />
              <i />
            </span>

            <span>
              <strong>CureVerse</strong>
              <b>AI</b>
            </span>
          </a>

          <p>
            Biological intelligence at the intersection of science, AI and
            biology — turning complex biological signals into evidence-aware
            insight.
          </p>

          <span className="cv-footer-status">
            <i />
            SYSTEM ONLINE
          </span>
        </div>

        <div className="cv-footer-links">

          <div className="cv-footer-column">
            <small>PLATFORM</small>
            <a href="/#domains">Domains</a>
            <a href="/#intelligence">Intelligence</a>
            <a href="/idea">Vision</a>
            <a href="/contact">Start a Conversation</a>
          </div>

          <div className="cv-footer-column">
            <small>DOMAINS</small>
            <a href="/#domains">Research</a>
            <a href="/#domains">Drug Development</a>
            <a href="/#domains">Medicine</a>
            <a href="/#domains">Biotechnology</a>
            <a href="/#domains">Education</a>
          </div>

          <div className="cv-footer-column">
            <small>INTELLIGENCE</small>
            <span>Multimodal Intelligence</span>
            <span>Evidence Reasoning</span>
            <span>Biological Identity</span>
            <span>External Evidence</span>
            <span>Reasoned Insight</span>
          </div>

          <div className="cv-footer-column">
            <small>CONNECT</small>
            <a href="/developers">Developers</a>
            <a href="/contact">Contact</a>
            <a href="/contact">Research Collaboration</a>
            <a href="/contact">Technical Inquiry</a>
          </div>

        </div>
      </div>

      <div className="cv-footer-signal">
        <span>DATA</span>
        <i />
        <span>MODELS</span>
        <i />
        <span>EVIDENCE</span>
        <i />
        <span>REASONING</span>
        <i />
        <strong>INSIGHT</strong>
      </div>

      <div className="cv-footer-bottom">
        <span>SCIENCE FOR A HEALTHIER TOMORROW</span>
        <span>© {new Date().getFullYear()} CUREVERSEAI</span>
        <span>BUILDING THE BIOLOGICAL INTELLIGENCE LAYER</span>
      </div>

      <div className="cv-footer-wordmark">
        CUREVERSE<span>AI</span>
      </div>
    </footer>
  );
}
