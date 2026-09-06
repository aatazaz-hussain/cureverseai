export default function Navbar() {
  return (
    <header className="cv-nav">
      <a href="/" className="cv-brand">
        <span className="cv-brand-mark">
          <i />
          <i />
        </span>

        <span>
          <strong>CureVerse</strong>
          <b>AI</b>
        </span>
      </a>

      <nav className="cv-nav-links">
        <a href="/#domains">Domains</a>
        <a href="/#intelligence">Intelligence</a>
        <a href="/#team">Developers</a>
        <a href="/#about">About</a>
      </nav>

      <a href="/#domains" className="cv-nav-action">
        Explore Platform
        <span>↗</span>
      </a>
    </header>
  );
}
