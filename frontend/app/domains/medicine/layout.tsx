/**
 * CureVerseAI — Medicine domain
 * Domain root layout.
 *
 * Imports, in this order:
 *
 *   1. design.css  — tokens + primitives (must come first)
 *   2. medicine.css — landing page styles (existing)
 *   3. shared.css   — component baseline for workflows
 *
 * Next.js App Router only allows a page file to import CSS
 * from its own folder; shared CSS must come from a layout.
 * This layout is intentionally transparent.
 */

import type { ReactNode } from "react";

import "./_shared/design.css";
import "./medicine.css";
import "./_shared/shared.css";

export default function MedicineLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
