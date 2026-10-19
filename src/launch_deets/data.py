"""Load and validate the synthetic, source-linked archive."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ROOT


REQUIRED_RECORD_COLUMNS = {
    "record_id", "launch_id", "entity_id", "event_type", "occurred_at", "severity",
    "status", "summary", "source_id", "revision", "synthetic",
}
ALLOWED_RELATIONSHIPS = {
    "LAUNCH_HAS_COMPONENT", "COMPONENT_INVOLVED_IN_INCIDENT",
    "INCIDENT_ADDRESSED_BY_ACTION", "DOCUMENT_SUPPORTS_ENTITY",
}


@dataclass(frozen=True)
class Archive:
    records: pd.DataFrame
    relationships: pd.DataFrame
    golden: pd.DataFrame
    guardrails: pd.DataFrame
    documents: list[dict[str, Any]]


def _front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    _, header, body = text.split("---", 2)
    metadata: dict[str, str] = {}
    for line in header.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata, body.strip()


def load_archive(root: Path = ROOT) -> Archive:
    from langchain_community.document_loaders import TextLoader

    data = root / "data"
    docs = []
    for path in sorted((data / "documents").glob("*.md")):
        document = TextLoader(str(path), encoding="utf-8").load()[0]
        metadata, body = _front_matter(document.page_content)
        docs.append({"path": path, "metadata": metadata, "text": body})
    return Archive(
        records=pd.read_csv(data / "records.csv", keep_default_na=False),
        relationships=pd.read_csv(data / "relationships.csv", keep_default_na=False),
        golden=pd.read_csv(data / "golden_questions.csv", keep_default_na=False),
        guardrails=pd.read_csv(data / "guardrail_cases.csv", keep_default_na=False),
        documents=docs,
    )


def validate_archive(archive: Archive) -> list[str]:
    errors: list[str] = []
    r = archive.records
    missing = sorted(REQUIRED_RECORD_COLUMNS - set(r.columns))
    if missing:
        errors.append(f"records.csv missing columns: {missing}")
    if r.record_id.duplicated().any():
        errors.append("records.csv contains duplicate record_id values")
    if not r.synthetic.astype(str).str.lower().eq("true").all():
        errors.append("Every record must be marked synthetic=true")
    record_ids = set(r.record_id)
    doc_ids = {d["metadata"].get("document_id", "") for d in archive.documents}
    if len(doc_ids - {""}) != len(archive.documents):
        errors.append("Markdown document_id values are missing or duplicated")
    if len(archive.relationships):
        if not archive.relationships.relationship.isin(ALLOWED_RELATIONSHIPS).all():
            errors.append("relationships.csv contains an unknown relationship type")
        if archive.relationships.evidence_id.eq("").any():
            errors.append("Every graph edge must have an evidence_id")
        dangling = set(archive.relationships.evidence_id) - record_ids
        if dangling:
            errors.append(f"Graph edges reference unknown evidence record IDs: {sorted(dangling)}")
        bad_docs = set(archive.relationships.source_id) - doc_ids
        if bad_docs:
            errors.append(f"Graph edges reference unknown document IDs: {sorted(bad_docs)}")
    bad_sources = set(r.source_id) - doc_ids
    if bad_sources:
        errors.append(f"Records reference unknown document IDs: {sorted(bad_sources)}")
    source_ids = record_ids | doc_ids
    for row in archive.golden.itertuples(index=False):
        expected = {x for x in str(row.expected_source_ids).split(";") if x}
        unknown = expected - source_ids
        if unknown:
            errors.append(f"{row.question_id} has unknown expected source IDs: {sorted(unknown)}")
    return errors


def split_documents(documents: list[dict[str, Any]], chunk_size: int = 500, overlap: int = 100) -> list[dict[str, Any]]:
    """Course-aligned recursive character splitting with exact source offsets."""
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= overlap < chunk_size")
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap, add_start_index=True,
    )
    splits = splitter.create_documents(
        [doc["text"] for doc in documents],
        metadatas=[{**doc["metadata"], "source_id": doc["metadata"].get("document_id")} for doc in documents],
    )
    return [{"text": doc.page_content, "metadata": doc.metadata} for doc in splits]

