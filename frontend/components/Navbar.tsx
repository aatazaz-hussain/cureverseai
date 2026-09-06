"use client";

import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const isHome = pathname === "/";

  const developersLabel = pathname === "/developers" ? "Home" : "Developers";
  const developersHref = pathname === "/developers" ? "/" : "/developers";

  const aboutLabel = pathname === "/idea" ? "Home" : "About";
  const aboutHref = pathname === "/idea" ? "/" : "/idea";

  return (
    <header className="cv-nav cv-nav-sticky">
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
        {!isHome && <a href="/">Home</a>}

        <a href="/#domains">Domains</a>
        <a href="/#intelligence">Intelligence</a>

        <a href={developersHref}>{developersLabel}</a>
        <a href={aboutHref}>{aboutLabel}</a>
      </nav>

      <a href="/#domains" className="cv-nav-action">
        Explore Platform
        <span>↗</span>
      </a>
    </header>
  );
}
