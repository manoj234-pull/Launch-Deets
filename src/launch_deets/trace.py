"""Optional, in-memory teaching trace. Never stores credentials or vector arrays."""
from __future__ import annotations

from copy import deepcopy
from threading import Lock
from time import perf_counter
from typing import Any


class RunTrace:
    def __init__(self, label: str = "request"):
        self.label = label
        self.events: list[dict[str, Any]] = []
        self.usage_rows: list[dict[str, Any]] = []
        self.started = perf_counter()
        self._lock = Lock()

    def record(self, stage: str, **details: Any) -> None:
        with self._lock:
            self.events.append({"step": len(self.events) + 1, "stage": stage,
                                "elapsed_seconds": round(perf_counter() - self.started, 3),
                                **deepcopy(details)})

    def usage(self, stage: str, provider: str, model: str, usage: Any, seconds: float) -> None:
        data = usage.model_dump() if hasattr(usage, "model_dump") else dict(usage or {})
        input_tokens = data.get("input_tokens", data.get("prompt_tokens"))
        output_tokens = data.get("output_tokens", data.get("completion_tokens"))
        total = data.get("total_tokens")
        if total is None and input_tokens is not None and output_tokens is not None:
            total = input_tokens + output_tokens
        from langsmith import get_current_run_tree
        run = get_current_run_tree()
        if run is not None:
            # Custom provider calls (JEV and embeddings) do not emit LangChain LLM callbacks.
            run.add_metadata({"provider_stage": stage, "provider": provider, "model": model,
                              "input_tokens": input_tokens, "output_tokens": output_tokens,
                              "total_tokens": total, "provider_seconds": round(seconds, 3)})
        with self._lock:
            self.usage_rows.append({"run": self.label, "call": len(self.usage_rows) + 1,
                                   "stage": stage, "provider": provider, "model": model,
                                   "input_tokens": input_tokens, "output_tokens": output_tokens,
                                   "total_tokens": total, "seconds": round(seconds, 3),
                                   "usage_status": "reported" if any(v is not None for v in (input_tokens, output_tokens, total)) else "not reported",
                                   "raw_usage": deepcopy(data)})


class TracedEmbeddingClient:
    """Retain API usage before LangChain extracts just the embedding vectors."""
    def __init__(self, client: Any, trace: RunTrace, stage: str):
        self.client, self.trace, self.stage = client, trace, stage

    def create(self, **kwargs: Any) -> Any:
        start = perf_counter()
        response = self.client.create(**kwargs)
        body = response if isinstance(response, dict) else response.model_dump()
        self.trace.usage(self.stage, "Nebius", kwargs.get("model", "unknown"),
                         body.get("usage"), perf_counter() - start)
        inputs = kwargs.get("input", [])
        self.trace.record(self.stage, texts=len(inputs) if isinstance(inputs, list) else 1,
                          dimensions=len(body["data"][0]["embedding"]) if body.get("data") else 0)
        return response


def ranking_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Small tables retain chunk identity, dates and scores; text is a preview."""
    return [{"rank": rank, "document_id": c["metadata"].get("document_id"),
             "start_index": c["metadata"].get("start_index", 0),
             "launch_id": c["metadata"].get("launch_id"),
             "occurred_at": c["metadata"].get("occurred_at"),
             "score": c.get("score"), "rrf_score": c.get("rrf_score"),
             "jev_score": c.get("jev_score"), "rrf_sources": c.get("rrf_sources", []),
             "text_preview": c.get("text", "")[:220]}
            for rank, c in enumerate(candidates, 1)]


def ranking_metrics(candidates: list[dict[str, Any]], expected_docs: set[str]) -> dict[str, Any]:
    ids = [c["metadata"].get("document_id") for c in candidates]
    hits = expected_docs.intersection(ids)
    first = next((i for i, doc in enumerate(ids, 1) if doc in expected_docs), None)
    return {"returned_chunks": len(ids), "expected_documents": sorted(expected_docs),
            "source_hit": bool(hits), "document_recall": len(hits) / len(expected_docs) if expected_docs else None,
            "reciprocal_rank": 1 / first if first else 0.0}
