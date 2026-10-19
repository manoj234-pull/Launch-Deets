"""Specialist archive retrieval: structured, BM25, dense, RRF, graph fallback."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langsmith import traceable

from .data import Archive, split_documents


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*")


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


class HybridIndex:
    """LangChain BM25 over eligible chunks; dense results come from Pinecone."""

    def __init__(self, archive: Archive):
        self.archive = archive
        self.chunks = split_documents(archive.documents)

    @traceable(name="BM25 metadata-filtered search", process_inputs=lambda inputs: {
        key: inputs.get(key) for key in ("query", "k", "filters")})
    def bm25(self, query: str, k: int = 5, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
        eligible = [Document(page_content=c["text"], metadata=dict(c["metadata"]))
                    for c in self.chunks if not filters or all(
                        c["metadata"].get(key, "").lower() == value.lower()
                        for key, value in filters.items())]
        if not eligible or k <= 0 or not tokens(query):
            return []
        # Rank the eligible corpus, then exclude zero-overlap filler documents.
        # BM25 scores can be negative in small corpora; score > 0 is not a match test.
        retriever = BM25Retriever.from_documents(
            eligible, preprocess_func=tokens, bm25_params={"k1": 1.2, "b": 0.75}, k=len(eligible))
        scores = retriever.vectorizer.get_scores(tokens(query))
        score_by_chunk = {(d.metadata["document_id"], d.metadata["start_index"]): float(s)
                          for d, s in zip(eligible, scores)}
        terms = set(tokens(query))
        return [{"text": d.page_content, "metadata": d.metadata, "retriever": "bm25",
                 "score": score_by_chunk[(d.metadata["document_id"], d.metadata["start_index"])]}
                for d in retriever.invoke(query) if terms.intersection(tokens(d.page_content))][:k]

    @traceable(name="RRF fusion", process_inputs=lambda inputs: {
        key: inputs.get(key) for key in ("query", "k", "filters", "rrf_constant")})
    def hybrid(self, query: str, dense: list[dict[str, Any]] | None = None, k: int = 5,
               filters: dict[str, str] | None = None, rrf_constant: int = 60,
               sparse: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        if sparse is None:
            sparse = self.bm25(query, k=max(k * 2, 10), filters=filters)
        dense = [d for d in (dense or []) if not filters or all(d["metadata"].get(f, "").lower() == v.lower() for f, v in filters.items())]
        fused: dict[str, dict[str, Any]] = {}
        for ranking in (dense, sparse):
            for rank, item in enumerate(ranking, 1):
                sid = item["metadata"].get("document_id", item["metadata"].get("source_id", ""))
                key = f"{sid}:{item['metadata'].get('start_index', 0)}"
                if key not in fused:
                    fused[key] = {**item, "rrf_score": 0.0, "rrf_sources": []}
                fused[key]["rrf_score"] += 1 / (rrf_constant + rank)
                fused[key]["rrf_sources"].append(item.get("retriever", "dense" if ranking is dense else "bm25"))
        return sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)[:k]


def structured_lookup(archive: Archive, query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Return provenance-bearing matching rows; conservative token matching baseline."""
    def lookup_tokens(value):
        terms = tokens(value)
        return set(terms) | {piece for term in terms for piece in term.split("-")}
    q = lookup_tokens(query)
    df = archive.records.copy()
    text = (df["summary"].fillna("") + " " + df["entity_id"].fillna("") + " " + df["component_id"].fillna("") + " " + df["launch_id"].fillna("")).map(lookup_tokens)
    df = df.assign(_match=[len(q.intersection(set(row))) for row in text])
    rows = df[df._match > 0].sort_values("_match", ascending=False).head(limit)
    return [{k: v for k, v in row.items() if k != "_match"} for row in rows.to_dict(orient="records")]



def resolve_launch_scope(archive: Archive, question: str, requested: str = "") -> str:
    """Use an unambiguous explicit launch; never guess a cross-launch filter."""
    known = {str(x).upper() for x in archive.records.launch_id.unique()}
    requested = requested.strip().upper()
    mentioned = {lid for lid in known if re.search(r"\b" + re.escape(lid.split("-")[-1]) + r"\b", question, re.I)}
    if requested and "L7-" + requested in known:
        requested = "L7-" + requested
    # The user's unambiguous launch wins over an invented identifier from the model.
    if requested not in known and len(mentioned) == 1:
        return next(iter(mentioned))
    if requested and (requested not in known or (mentioned and requested not in mentioned)):
        raise ValueError("launch_id must match the question and a known launch.")
    return requested or (next(iter(mentioned)) if len(mentioned) == 1 else "")


def structured_query(archive: Archive, query: str = "", operation: str = "lookup",
                     launch_id: str = "", event_type: str = "", severity: str = "",
                     unit: str = "", component_id: str = "") -> dict[str, Any]:
    """Explicit field operations; aggregate over all matching rows, never top-k."""
    import pandas as pd
    from types import SimpleNamespace
    if operation not in {"lookup", "count_launches", "max_value"}:
        raise ValueError("operation must be lookup, count_launches or max_value.")
    if re.search(r"\b(SELECT|WHERE|GROUP BY|ORDER BY)\b|[<>=]", query, re.I):
        raise ValueError("SQL and query predicates are unsupported. Use the explicit operation and filter fields.")
    df = archive.records.copy()
    filters = {k: v.strip() for k, v in {"launch_id": launch_id, "event_type": event_type,
               "severity": severity, "unit": unit, "component_id": component_id}.items() if v.strip()}
    for field, value in filters.items():
        if field == "unit":
            # Accept singular/plural spelling, but never change the measurement unit.
            matches = {str(u).strip() for u in archive.records.unit
                       if str(u).strip().casefold().removesuffix("s") == value.casefold().removesuffix("s")}
            if len(matches) == 1:
                value = filters[field] = matches.pop()
        known = archive.records[field].fillna("").astype(str).str.strip().str.casefold()
        if value.casefold() not in set(known):
            raise ValueError(f"Unknown {field}: use a value present in the archive.")
        df = df[df[field].fillna("").astype(str).str.strip().str.casefold() == value.casefold()]
    if operation == "count_launches":
        launches = sorted(df.launch_id.unique().tolist())
        return {"status": "ok", "operation": operation, "filters": filters, "source_id": "records.csv",
                "value": len(launches), "launch_ids": launches, "matched_records": len(df),
                "records": df.to_dict("records")}
    if operation == "max_value":
        if not unit.strip():
            raise ValueError("max_value requires unit; unlike units cannot be compared.")
        numeric = pd.to_numeric(df["value"], errors="coerce")
        if numeric.isna().any():
            raise ValueError("Some eligible records have no numeric value; maximum cannot be established.")
        if df.empty:
            return {"status": "no_match", "operation": operation, "filters": filters, "records": []}
        value = float(numeric.max())
        return {"status": "ok", "operation": operation, "filters": filters, "source_id": "records.csv",
                "value": value, "unit": unit, "matched_records": len(df),
                "records": df[numeric == value].to_dict("records")}
    # Field-only lookup is exact; narrative lookup remains explicitly lexical within the scope.
    rows = structured_lookup(SimpleNamespace(records=df), query) if query.strip() else df.to_dict("records")
    return {"status": "ok" if rows else "no_match", "operation": operation, "filters": filters,
            "matched_records": len(rows), "records": rows}


def graph_paths(archive: Archive, start_entity_id: str | None = None) -> list[dict[str, Any]]:
    """Local source-backed path fallback over relationships.csv."""
    edges = archive.relationships.to_dict(orient="records")
    adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in edges:
        adjacency[e["source_entity_id"]].append(e)
    starts = [start_entity_id] if start_entity_id else [e["source_entity_id"] for e in edges if e["relationship"] == "LAUNCH_HAS_COMPONENT"]
    paths = []
    for start in starts:
        first = adjacency.get(start, [])
        for e1 in first:
            if e1["relationship"] != "LAUNCH_HAS_COMPONENT":
                continue
            for e2 in adjacency.get(e1["target_entity_id"], []):
                if e2["relationship"] != "COMPONENT_INVOLVED_IN_INCIDENT":
                    continue
                for e3 in adjacency.get(e2["target_entity_id"], []):
                    if e3["relationship"] == "INCIDENT_ADDRESSED_BY_ACTION":
                        paths.append({"path": [start, e1["target_entity_id"], e2["target_entity_id"], e3["target_entity_id"]],
                                      "evidence_ids": [e1["evidence_id"], e2["evidence_id"], e3["evidence_id"]],
                                      "source_ids": [e1["source_id"], e2["source_id"], e3["source_id"]]})
    return paths

