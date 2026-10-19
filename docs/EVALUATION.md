# Evaluation and regression checks

## Current workflow

1. Validate IDs, required metadata, graph evidence links and chunk offsets locally.
2. Compare structured lookup and BM25 source hits with the golden questions. This baseline diagnostic is not end-to-end accuracy.
3. With live calls enabled, inspect dense retrieval, RRF candidates and TypeSafe reranking. Relevance scores are not probabilities of truth.
4. Run an independent agent request. Inspect tool choice, final evidence, answer, citation-ID acceptance, time and provider token ledger.
5. Review semantic correctness and completeness against expected facts. The optional model judge is supporting evidence, not a substitute for human review.
6. Run labelled guardrail cases separately and verify blocked input stops before retrieval.

Notebook 02 separates controlled branch calls, the complete agent request, optional ingestion and extra evaluation. Do not sum all notebook calls and label that total as one application request. Preserve unknown provider usage as unknown, not zero. Live scripts save under `reports/evaluation/` and use LangSmith.

## Minimal offline tests

The suite covers source/chunk integrity, structured filters and aggregates, empty results, citation acceptance/rejection, document provenance, reranking order, usage accounting and NOUL early termination. External providers are mocked. Tests must reflect the current compact answer prompt, not require obsolete full-history replay.

## Historical findings

- Initial user-observed simple-query usage was **4,076 tokens**. It is a historical baseline, not a measurement from this cleanup.
- Earlier runs explored prompt/context size, candidate selection, reranking, routing and model choice. Keep request usage separate from judges and repeated experiments when comparing results.
- Historical reports and notebook outputs were archived rather than rewritten as fresh successes. This cleanup does not claim new live accuracy, latency or token improvements.


## Historical verification

The renamed application passed 22 offline tests, including entrance → Home → Research navigation. Both notebooks executed top to bottom in local-only mode with tracing disabled. No fresh paid-model accuracy or latency benchmark was run. Browser animation appearance still needs a visual review.
