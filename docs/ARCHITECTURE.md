# Runtime architecture

## Entry points

`streamlit_app.py` serves the space entrance, Home and Research. The entrance is CSS/SVG with a native Streamlit entry button; it makes no provider requests. The research page passes the user's question and optional launch scope to `agent.ask()` in a worker thread.

## Request flow

1. `agent.ask()` opens a LangSmith request trace. `providers.jev_check()` calls TypeSafe NOUL before any retrieval or answer generation. Blocked requests stop here.
2. A Nebius chat model receives the routing prompt, user question and tool schemas. It selects the relevant tool or combination:
   - `lookup_records`: pandas filters/aggregations over `data/records.csv`. Counts use all eligible rows.
   - `search_incident_documents`: metadata-filtered LangChain BM25 and Pinecone dense search, RRF fusion, then TypeSafe Score reranking. The current path retrieves 16 sparse / 8 dense candidates, fuses up to 8, sends the first 3 candidates to TypeSafe, and retains 2 reranked chunks.
   - `trace_relationships`: Neo4j component–incident–action paths, falling back to the local relationship CSV when the provider is unavailable or returns no paths.
3. Empty or failed retrieval may trigger one bounded recovery attempt. Repeated identical calls are rejected; the overall tool-call budget remains bounded.
4. The same Nebius model receives the answer prompt, question and compact evidence, without replaying tool schemas or planning history. Provenance and event/revision dates are retained.
5. Returned citations are checked against retrieved source IDs. Missing or unknown citations cause abstention. This is an ID check, not a semantic truth guarantee.
6. The UI shows the answer without citation markers. Rocket animation is illustrative progress; all three visual branches can animate even when the agent uses fewer tools.

## Components

| Module | Responsibility |
|---|---|
| `data.py` | LangChain TextLoader, front matter, CSV loading, validation, recursive chunking |
| `retrieval.py` | Structured operations, BM25, metadata filtering, RRF and local graph traversal |
| `providers.py` | Nebius, Pinecone, Neo4j and TypeSafe adapters |
| `agent.py` | Routing and answer prompts, LangGraph, retry budget, source-ID checks |
| `trace.py` | Stage timings, provider usage and ranking metrics |
| `evaluate.py` | Local source-hit diagnostic |
| `assessment.py` | LangSmith labelled datasets, answer judge and cost estimates |
| `config.py` | Environment loading and provider configuration |

Each question is independent. There is no cross-question conversation history. Token counts include provider-reported usage; missing usage stays unknown. Pandas, BM25 and RRF have no model-token usage, but still take processing time.
