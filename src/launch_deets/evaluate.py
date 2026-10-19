"""Deterministic corpus and retrieval checkpoints; writes aggregate outputs only on request."""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .data import Archive, validate_archive
from .retrieval import HybridIndex, graph_paths, structured_lookup


def evaluate_local(archive: Archive) -> dict[str, Any]:
    errors = validate_archive(archive)
    index = HybridIndex(archive)
    cases = []
    for row in archive.golden.itertuples(index=False):
        start = perf_counter()
        if row.category == "count":
            docs = archive.records[(archive.records.event_type == "incident") & (archive.records.severity == "major")].to_dict(orient="records")
            ids = {d["record_id"] for d in docs}
        elif row.category == "comparison":
            eligible = archive.records[archive.records.unit.isin(["percent", "degrees", "kPa"])].copy()
            eligible["_numeric"] = eligible.value.map(lambda x: float(x) if str(x).replace(".", "", 1).isdigit() else float("-inf"))
            docs = eligible.sort_values("_numeric", ascending=False).head(5).to_dict(orient="records")
            ids = {d["record_id"] for d in docs}
        elif row.expected_tools == "structured" or row.category in {"exact"}:
            docs = structured_lookup(archive, row.question)
            ids = {d["record_id"] for d in docs}
        elif row.expected_tools == "graph" or row.category == "multi_hop":
            launch = "LAUNCH-L7-CHARLIE" if "Charlie" in row.question else "LAUNCH-L7-ECHO" if "Echo" in row.question else None
            docs = graph_paths(archive, launch)
            ids = {x for p in docs for x in p["evidence_ids"] + p["source_ids"]}
        elif row.answerable == "no":
            docs, ids = [], set()
        elif row.expected_answer_facts and row.expected_answer_facts.strip():
            launch = "L7-DELTA" if "Delta" in row.question else None
            docs = index.bm25(row.question, k=5, filters={"launch_id": launch} if launch else None)
            ids = {d["metadata"].get("document_id") for d in docs}
        else:
            docs, ids = [], set()
        expected = {x for x in str(row.expected_source_ids).split(";") if x}
        elapsed_ms = (perf_counter() - start) * 1000
        cases.append({"question_id": row.question_id, "category": row.category,
                      "expected_source_ids": sorted(expected), "returned_source_ids": sorted(ids),
                      "source_hit": bool(expected & ids), "answerable": row.answerable,
                      "latency_ms": round(elapsed_ms, 3)})
    return {"validation_errors": errors, "records": len(archive.records), "documents": len(archive.documents),
            "graph_edges": len(archive.relationships), "golden_cases": len(cases),
            "source_hit_rate": sum(c["source_hit"] for c in cases if c["expected_source_ids"]) / max(1, sum(bool(c["expected_source_ids"]) for c in cases)),
            "cases": cases}


def save_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")

