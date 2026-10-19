# Synthetic dataset and metadata

The archive is entirely fictional. Launch-Deets uses it to demonstrate retrieval across structured records, narrative reports and graph relationships.

## Files

- `records.csv`: events, measurements, components and corrective actions with record/source IDs.
- `documents/*.md`: report bodies with front-matter metadata.
- `relationships.csv`: entity links with supporting record and document IDs.
- `golden_questions.csv`: labelled questions, answer facts, acceptable sources, expected tools, answerability, split and notes.
- `guardrail_cases.csv`: labelled benign and adversarial questions.

## Semantics to preserve

- `occurred_at` is the event date; `revised_at` is the document revision date. A later corrective action must not be described as preceding its incident.
- `finding_status` is active/superseded at the finding level. `document_status` describes the document, not every finding it mentions.
- `status` is entity-specific: an incident may be closed, an action verified, and a report final.
- `revision` is local to its source; it is not a global precedence score.
- `summary_scope=retrospective` identifies reports that discuss multiple dated events. No historical as-of-query capability is claimed.
- `related_ids` is document-level provenance. A chunk does not necessarily support every fact listed by its parent document.

LangChain RecursiveCharacterTextSplitter uses 500 characters and target overlap 100 with exact `start_index` offsets. Chunks inherit source metadata. Actual overlap varies at natural boundaries. Inspect current counts in the notebooks rather than relying on historical hardcoded totals.

Changing source content or chunk settings requires an explicit Pinecone refresh. Renaming the app does not change the corpus, hosted namespace or Neo4j labels. No hosted upload is performed by this cleanup.
