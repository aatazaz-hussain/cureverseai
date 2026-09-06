from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Gene(Base):
    __tablename__ = "genes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ensembl_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    organism: Mapped[str] = mapped_column(String(100), default="Homo sapiens")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    proteins: Mapped[list["Protein"]] = relationship(
        back_populates="gene",
        cascade="all, delete-orphan",
    )

    variants: Mapped[list["Variant"]] = relationship(
        back_populates="gene",
        cascade="all, delete-orphan",
    )


class Protein(Base):
    __tablename__ = "proteins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gene_id: Mapped[int] = mapped_column(ForeignKey("genes.id"), index=True)

    uniprot_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True
    )

    name: Mapped[Optional[str]] = mapped_column(String(255))
    sequence: Mapped[Optional[str]] = mapped_column(Text)
    sequence_length: Mapped[Optional[int]] = mapped_column(Integer)

    gene: Mapped["Gene"] = relationship(back_populates="proteins")


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gene_id: Mapped[int] = mapped_column(ForeignKey("genes.id"), index=True)

    variant_name: Mapped[str] = mapped_column(String(255), index=True)
    chromosome: Mapped[Optional[str]] = mapped_column(String(50))
    position: Mapped[Optional[int]] = mapped_column(Integer)
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    alternate: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )

    gene: Mapped["Gene"] = relationship(back_populates="variants")


class Pathway(Base):
    __tablename__ = "pathways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    pathway_id: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500))
    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    disease_id: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500))
    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Compound(Base):
    __tablename__ = "compounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    compound_id: Mapped[Optional[str]] = mapped_column(
        String(150),
        unique=True,
        index=True,
    )

    name: Mapped[Optional[str]] = mapped_column(String(500))
    smiles: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    target_id: Mapped[Optional[str]] = mapped_column(
        String(150),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500))
    target_type: Mapped[Optional[str]] = mapped_column(String(100))

    gene_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("genes.id"),
        index=True,
    )

    organism: Mapped[Optional[str]] = mapped_column(String(100))
    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Assay(Base):
    __tablename__ = "assays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    assay_id: Mapped[Optional[str]] = mapped_column(
        String(150),
        unique=True,
        index=True,
    )

    name: Mapped[Optional[str]] = mapped_column(String(500))
    assay_type: Mapped[Optional[str]] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Bioactivity(Base):
    __tablename__ = "bioactivities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    compound_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("compounds.id"),
        index=True,
    )

    target_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("targets.id"),
        index=True,
    )

    assay_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("assays.id"),
        index=True,
    )

    standard_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        index=True,
    )

    standard_value: Mapped[Optional[float]] = mapped_column(Float)
    standard_units: Mapped[Optional[str]] = mapped_column(String(50))

    pchembl_value: Mapped[Optional[float]] = mapped_column(Float)

    relation: Mapped[Optional[str]] = mapped_column(String(20))
    activity_comment: Mapped[Optional[str]] = mapped_column(Text)

    source: Mapped[Optional[str]] = mapped_column(String(100))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class DrugTargetRelationship(Base):
    __tablename__ = "drug_target_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    compound_id: Mapped[int] = mapped_column(
        ForeignKey("compounds.id"),
        index=True,
    )

    target_id: Mapped[int] = mapped_column(
        ForeignKey("targets.id"),
        index=True,
    )

    relationship_type: Mapped[str] = mapped_column(String(100))
    evidence_level: Mapped[Optional[str]] = mapped_column(String(100))

    source: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    identifiers: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    evidence_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        index=True,
    )

    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[str]] = mapped_column(String(150))

    description: Mapped[Optional[str]] = mapped_column(Text)

    evidence_level: Mapped[Optional[str]] = mapped_column(String(100))
    score: Mapped[Optional[float]] = mapped_column(Float)

    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    run_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    domain: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    analysis_type: Mapped[str] = mapped_column(String(150))

    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    result_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    name: Mapped[Optional[str]] = mapped_column(String(255))

    password_hash: Mapped[Optional[str]] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(100), index=True)

    description: Mapped[Optional[str]] = mapped_column(Text)

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id"),
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500))
    domain: Mapped[str] = mapped_column(String(100), index=True)

    report_type: Mapped[Optional[str]] = mapped_column(String(150))

    content: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
