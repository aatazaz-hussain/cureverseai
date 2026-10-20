"""
CureVerseAI — Medicine domain package.

This package contains all Medicine-domain logic, isolated from
the drug_development, research, and education packages.

Public surface (added incrementally across phases):

    app.medicine.simulation   — shared simulation contract and
                                the three Medicine workflows:
                                  virtual_disease_simulation
                                  treatment_simulation
                                  combination_treatment_simulation

Nothing in this package imports from app.drug_development,
app.research, or app.education at package-import time. Any
shared infrastructure (DiskCache, source clients) is imported
lazily by the specific modules that need it, so a failure in
one domain cannot break imports of another.
"""

__all__ = []
