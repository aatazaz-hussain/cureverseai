"use client";

import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const isHome = pathname === "/";
  const isDevelopers = pathname === "/developers";
  const isIdea = pathname === "/idea";

  const navItems = [];

  if (!isHome) {
    navItems.push({
      label: "Home",
      href: "/",
    });
  }

  navItems.push({
    label: "Domains",
    href: "/#domains",
  });

  navItems.push({
    label: "Intelligence",
    href: "/#intelligence",
  });

  if (isHome || isIdea) {
    navItems.push({
      label: "Developers",
      href: "/developers",
    });
  }

  if (isHome || isDevelopers) {
    navItems.push({
      label: "About",
      href: "/idea",
    });
  }

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
        {navItems.map((item) => (
          <a key={item.label} href={item.href}>
            {item.label}
          </a>
        ))}
      </nav>

      <a href="/#domains" className="cv-nav-action">
        Explore Platform
        <span>↗</span>
      </a>
    </header>
  );
}
