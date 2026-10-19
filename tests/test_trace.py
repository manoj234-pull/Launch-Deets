"""Offline checks for usage accounting, evidence visibility and conversation state."""
import os
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from launch_deets import agent, providers
from launch_deets.data import load_archive
from launch_deets.trace import RunTrace, TracedEmbeddingClient, ranking_metrics
from launch_deets.retrieval import HybridIndex


class TraceChecks(unittest.TestCase):
    def test_reported_and_unknown_usage(self):
        trace = RunTrace()
        trace.usage("chat", "Nebius", "model", {"input_tokens": 10, "output_tokens": 2}, 0.1)
        trace.usage("embedding.query", "Nebius", "embed", {"prompt_tokens": 7, "total_tokens": 7}, 0.2)
        trace.usage("rerank", "TypeSafe", "model", None, 0.3)
        self.assertEqual(trace.usage_rows[0]["total_tokens"], 12)
        self.assertEqual(trace.usage_rows[1]["input_tokens"], 7)
        self.assertIsNone(trace.usage_rows[1]["output_tokens"])
        self.assertIsNone(trace.usage_rows[2]["total_tokens"])

    def test_embedding_passthrough_without_vector_logging(self):
        response = {"data": [{"embedding": [0.1, 0.2]}], "usage": {"prompt_tokens": 4, "total_tokens": 4}}
        client, trace = Mock(), RunTrace()
        client.create.return_value = response
        wrapped = TracedEmbeddingClient(client, trace, "embedding.query")
        self.assertIs(wrapped.create(input=["Charlie"], model="embed"), response)
        self.assertEqual(client.create.call_args.kwargs["input"], ["Charlie"])
        self.assertEqual(trace.events[0]["dimensions"], 2)
        self.assertNotIn("[0.1, 0.2]", json.dumps(trace.events))

    def test_reranking_records_all_scores_and_stable_top_k(self):
        candidates = [{"text": str(i), "metadata": {"document_id": f"DOC-{i}"}} for i in range(4)]
        trace = RunTrace()
        response = SimpleNamespace(model="score-model", usage={"input_tokens": 12, "output_tokens": 4},
                                   scores={f"candidate_{i}": SimpleNamespace(score=score) for i, score in enumerate([1, 4, 4, 0])})
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.system_one.return_value = response
        settings = Mock(typesafe_api_key="test-only")
        settings.missing_for.return_value = []
        with patch("typesafe_sdk.TypeSafeClient", return_value=client):
            result = providers.jev_score(settings, "query", candidates, top_k=2, trace=trace)
        self.assertEqual([c["text"] for c in result], ["1", "2"])
        self.assertEqual(len(trace.events[0]["after"]), 3)
        self.assertEqual(len(trace.events[0]["selected"]), 2)
        self.assertNotIn("jev_score", candidates[0])
        sent = client.system_one.call_args.kwargs["questions"]["candidate_0"]
        self.assertEqual(sent.instructions, "Relevance of candidate_0 to query?")
        self.assertEqual(sent.criteria[-1], "answers query")
        self.assertEqual(trace.events[0]["rubric"], list(sent.criteria))
        self.assertEqual(trace.events[0]["instructions"].replace("candidate_i", "candidate_0"), sent.instructions)



    def test_blocked_request_cannot_reach_workflow(self):
        with patch.object(agent, "configure_langsmith"), patch.object(agent, "jev_check", return_value={"blocked": True}), patch.object(agent, "build_workflow") as build:
            result = agent.ask("blocked", archive=load_archive(ROOT), settings=Mock(langsmith_project="offline-tests"), trace=RunTrace())
        self.assertEqual(result["status"], "blocked")
        build.assert_not_called()

    def test_filters_rrf_and_metrics(self):
        index = HybridIndex(load_archive(ROOT))
        sparse = index.bm25("Charlie IM-03 firmware C8", k=16, filters={"launch_id": "L7-CHARLIE"})
        self.assertTrue(sparse)
        self.assertTrue(all(c["metadata"]["launch_id"] == "L7-CHARLIE" for c in sparse))
        fused = index.hybrid("Charlie IM-03 firmware C8", dense=[sparse[0]], k=8, filters={"launch_id": "L7-CHARLIE"})
        self.assertAlmostEqual(fused[0]["rrf_score"], 2/61)
        metrics = ranking_metrics(fused, {fused[0]["metadata"]["document_id"]})
        self.assertEqual(metrics["reciprocal_rank"], 1)


if __name__ == "__main__":
    unittest.main()
