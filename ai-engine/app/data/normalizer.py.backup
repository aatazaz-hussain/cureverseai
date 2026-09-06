import re

from app.data.schemas import (
    BiologicalEntity,
    GeneRecord,
    MutationRecord,
)


def clean_reactome_text(value):
    if value is None:
        return None

    value = re.sub(r"<[^>]+>", "", str(value))
    return value.strip()


def normalize_ensembl_gene(data: dict) -> GeneRecord:
    return GeneRecord(
        symbol=data.get("display_name", ""),
        ensembl_id=data.get("id"),
        name=data.get("description"),
        species=data.get("species"),
        biotype=data.get("biotype"),
        chromosome=data.get("seq_region_name"),
        start=data.get("start"),
        end=data.get("end"),
        strand=data.get("strand"),
        assembly=data.get("assembly_name"),
        canonical_transcript=data.get("canonical_transcript"),
        description=data.get("description"),
    )


def normalize_reactome_entity(data: dict) -> BiologicalEntity:
    raw_name = data.get("displayName") or data.get("name") or ""

    return BiologicalEntity(
        identifier=str(
            data.get("stId")
            or data.get("dbId")
            or data.get("identifier")
            or ""
        ),
        name=clean_reactome_text(raw_name),
        entity_type=data.get("type", "Unknown"),
        source="Reactome",
        species=data.get("species"),
        compartment=clean_reactome_text(
            data.get("compartments")
        ),
        metadata={
            "reactome_name": clean_reactome_text(
                data.get("name")
            ),
            "schema_class": data.get("schemaClass"),
        },
    )


def extract_reactome_entities(data: dict):
    entities = []

    for group in data.get("results", []):
        group_type = group.get("typeName", "Unknown")

        for entry in group.get("entries", []):
            entity = normalize_reactome_entity(entry)

            if entity.entity_type == "Unknown":
                entity.entity_type = group_type

            entities.append(entity)

    return entities


def extract_mutations(entities):
    mutations = []

    # Common protein-level HGVS-like forms:
    # K351R
    # K351N
    # Q5*
    # N210Hfs*5
    # L299Afs*6
    # D259Qfs*3
    variant_pattern = re.compile(
        r"\b("
        r"[A-Z]\d+[A-Z*]"
        r"|"
        r"[A-Z]\d+[A-Z]fs\*\d+"
        r")\b"
    )

    for entity in entities:
        name = entity.name or ""

        if not name.upper().startswith("TP53"):
            continue

        match = variant_pattern.search(name)

        if not match:
            continue

        mutations.append(
            MutationRecord(
                gene="TP53",
                variant=match.group(1),
                identifier=entity.identifier,
                source=entity.source,
                species=entity.species,
                compartment=entity.compartment,
                metadata=entity.metadata,
            )
        )

    return mutations
