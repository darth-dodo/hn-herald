# Architecture Decision Records (ADRs)

This directory contains the Architecture Decision Records for HN Herald - a privacy-first, personalized HackerNews digest application.

## What are ADRs?

Architecture Decision Records capture significant architectural decisions made during the development of a project. Each ADR describes:
- The context and problem being addressed
- Options considered with pros/cons
- The decision made and rationale
- Consequences (positive and negative)
- Implementation details

## ADR Index

| ADR | Title | Status | Date | Tags |
|-----|-------|--------|------|------|
| [001](001-langgraph-pipeline-architecture.md) | LangGraph Pipeline Architecture | Accepted | 2026-01-04 | architecture, langgraph, pipeline, orchestration |
| [002](002-sse-streaming-over-htmx.md) | SSE Streaming over HTMX Partials | Accepted | 2026-01-06 | frontend, sse, streaming, htmx, javascript |
| [003](003-privacy-first-architecture.md) | Privacy-First Data Architecture | Accepted | 2026-01-01 | privacy, architecture, localStorage, gdpr, data-handling |
| [004](004-tag-based-relevance-scoring.md) | Tag-Based Relevance Scoring | Accepted | 2026-01-03 | algorithm, scoring, personalization, tags |
| [005](005-claude-haiku-for-summarization.md) | Claude 3.5 Haiku for Cost-Efficient Summarization | Accepted | 2026-01-05 | llm, cost-optimization, claude, summarization, batch-processing |

## ADR Summaries

### ADR-001: LangGraph Pipeline Architecture
**Decision**: Use LangGraph StateGraph for digest generation pipeline orchestration.

**Key Points**:
- Enables parallel article extraction via Send pattern
- Provides graceful partial failure handling
- Integrates with LangSmith for observability
- Pipeline: fetch_hn → fetch_article (parallel) → filter → summarize → score → rank → format

---

### ADR-002: SSE Streaming over HTMX Partials
**Decision**: Use Server-Sent Events with vanilla JavaScript instead of HTMX partial swaps.

**Key Points**:
- HTMX is loaded but underutilized (vestigial)
- SSE provides real-time pipeline progress updates
- 7-stage pipeline (15-30s) benefits from streaming feedback
- Vanilla JS fetch + stream reader implementation

---

### ADR-003: Privacy-First Data Architecture
**Decision**: Store all user preferences in browser localStorage with no server-side user data.

**Key Points**:
- Zero server-side user data storage
- No accounts, no tracking, no analytics
- GDPR/CCPA compliance by design
- User can export/delete data anytime

---

### ADR-004: Tag-Based Relevance Scoring
**Decision**: Use tag-matching algorithm over embedding-based semantic similarity.

**Key Points**:
- Direct set intersection between user tags and article tags
- 70% relevance weight + 30% HN popularity weight
- Sub-millisecond scoring performance
- Fully explainable ("Matched: python, ai")

---

### ADR-005: Claude 3.5 Haiku for Summarization
**Decision**: Use Claude 3.5 Haiku over Sonnet for article summarization.

**Key Points**:
- 10x cost reduction (~$0.015 vs ~$0.18 per digest)
- Batch processing of 5 articles per LLM call
- "Good enough" quality for digest summaries
- Faster response times improve UX

---

## ADR Status Lifecycle

- **Proposed**: Under discussion
- **Accepted**: Decision made and implemented
- **Deprecated**: No longer applies (superseded or removed)
- **Superseded**: Replaced by another ADR

## Creating New ADRs

When creating a new ADR:

1. Copy the template structure from an existing ADR
2. Use sequential numbering (e.g., `006-descriptive-name.md`)
3. Include all sections: Summary, Problem Statement, Context, Options, Decision, Consequences, Implementation
4. Update this index file
5. Link to relevant code files and design documents

## Related Documentation

- [Product Requirements](../product.md) - Product vision and requirements
- [Architecture Overview](../architecture.md) - System architecture
- [Design Documents](../design/) - Detailed design specifications
- [Tasks](../tasks.md) - MVP milestones and progress
