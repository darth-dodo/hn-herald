# ADR-001: LangGraph Pipeline Architecture

**Date**: 2026-01-04
**Status**: Accepted
**Context**: Core digest generation pipeline
**Deciders**: Architecture Team

---

## Summary

We chose LangGraph as the orchestration framework for HN Herald's digest generation pipeline. This decision enables parallel article extraction, graceful partial failure handling, and comprehensive observability through LangSmith integration, while providing a declarative graph-based workflow that is easier to understand and modify than imperative code.

---

## Problem Statement

### The Challenge

HN Herald needs to transform HackerNews stories into personalized, AI-summarized digests through a multi-stage pipeline:
1. Fetch stories from HN API
2. Extract article content from URLs (parallelizable)
3. Filter articles with valid content
4. Summarize articles using LLM (batched)
5. Score relevance based on user interests
6. Rank and format final digest

This requires orchestrating multiple async services, handling partial failures (some articles will fail extraction), and providing observability for debugging and optimization.

### Why This Matters

- **Performance**: Sequential article extraction would take 60+ seconds for 30 articles
- **Reliability**: Pipeline must continue even when individual articles fail
- **Observability**: LLM costs and latency need monitoring for optimization
- **Maintainability**: Complex async coordination is error-prone without structure

### Success Criteria

- [x] Pipeline executes end-to-end with parallel article extraction
- [x] Partial failures don't block pipeline completion
- [x] Full traceability via LangSmith for all LLM calls
- [x] Pipeline completes in <30s for 30 articles
- [x] State transitions are type-safe and debuggable

---

## Context

### Current State

**Before This Decision**:
- No pipeline implementation existed
- Services (HNClient, ArticleLoader, LLMService, ScoringService) were implemented in isolation
- No orchestration layer to coordinate service calls

**Pain Points**:
- Manual async coordination is complex and error-prone
- No standardized way to handle partial failures
- Difficult to trace execution flow across services
- No built-in support for parallel execution patterns

**Technical Constraints**:
- Python 3.12+ async/await ecosystem
- LangChain ecosystem already in use for LLM integration
- Need for LangSmith observability
- Must support both sync and async execution

### Requirements

**Functional Requirements**:
- Process UserProfile → Digest transformation
- Support parallel article extraction (10+ concurrent)
- Accumulate errors without stopping pipeline
- Batch LLM calls for efficiency

**Non-Functional Requirements**:
- **Performance**: <30s for 30 articles with parallelism
- **Reliability**: Continue on partial failures
- **Observability**: Full tracing in LangSmith
- **Maintainability**: Clear node boundaries and state transitions

---

## Options Considered

### Option A: LangGraph StateGraph

**Description**:
Use LangGraph's StateGraph with TypedDict state, node functions, and Send pattern for parallel execution.

**Implementation**:
```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

graph = StateGraph(HNState)
graph.add_node("fetch_hn", fetch_hn)
graph.add_node("fetch_article", fetch_article)  # Send target
graph.add_node("filter", filter_articles)
graph.add_node("summarize", summarize)
graph.add_node("score", score_articles)
graph.add_node("rank", rank_articles)
graph.add_node("format", format_digest)
```

**Pros**:
- Native LangChain ecosystem integration
- Built-in LangSmith tracing
- Send pattern for parallel execution
- TypedDict state with reducer support
- Declarative graph definition

**Cons**:
- Learning curve for Send pattern
- State must be serializable
- Limited conditional branching compared to full workflow engines

**Risks**:
- LangGraph is newer, API may change (mitigated by pinning versions)

**Estimated Effort**: 18 hours

---

### Option B: Custom Async Orchestrator

**Description**:
Build custom async coordination using asyncio.gather() and manual state management.

**Implementation**:
```python
async def generate_digest(profile: UserProfile) -> Digest:
    stories = await hn_client.fetch_stories(profile)
    articles = await asyncio.gather(*[
        loader.load_article(s) for s in stories
    ], return_exceptions=True)
    # Manual error handling, state passing...
```

**Pros**:
- Full control over execution
- No external dependencies
- Familiar async patterns

**Cons**:
- Manual error accumulation logic
- No built-in tracing
- Complex state management
- Harder to visualize flow

**Risks**:
- Bug-prone manual coordination
- Observability requires custom implementation

**Estimated Effort**: 25 hours

---

### Option C: Celery/Dramatiq Task Queue

**Description**:
Use distributed task queue for pipeline stages with Redis backend.

**Pros**:
- Battle-tested distributed execution
- Built-in retry and error handling
- Horizontal scaling

**Cons**:
- Overkill for single-user pipelines
- Requires Redis infrastructure
- Higher latency for simple flows
- Complex setup for local development

**Risks**:
- Infrastructure complexity
- Debugging distributed tasks is harder

**Estimated Effort**: 30 hours

---

## Comparison Matrix

| Criteria | Weight | LangGraph | Custom Async | Celery |
|----------|--------|-----------|--------------|--------|
| **LangSmith Integration** | High | 5 | 2 | 2 |
| **Parallel Execution** | High | 5 | 4 | 5 |
| **Error Handling** | High | 5 | 3 | 4 |
| **Development Speed** | High | 4 | 3 | 2 |
| **Maintainability** | Medium | 5 | 3 | 3 |
| **Learning Curve** | Medium | 3 | 5 | 2 |
| **Infrastructure Needs** | Low | 5 | 5 | 2 |
| **Total Score** | - | **32** | 25 | 20 |

---

## Decision

### Chosen Option

**Selected**: Option A: LangGraph StateGraph

**Rationale**:
LangGraph provides the best balance of features for our use case:
1. **Native LangSmith integration** gives us free observability
2. **Send pattern** elegantly solves parallel article extraction
3. **TypedDict state** provides type safety and clear data flow
4. **Ecosystem alignment** with existing LangChain usage
5. **Declarative graph** makes pipeline easy to understand and modify

**Key Factors**:
- LangSmith tracing is critical for LLM cost optimization
- Send pattern is purpose-built for our fan-out/fan-in extraction pattern
- Graph visualization aids debugging and documentation

**Trade-offs Accepted**:
- Learning curve for Send pattern (acceptable, well-documented)
- Dependency on LangGraph versioning (mitigated by pinning)

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- Parallel extraction reduces pipeline time from 60s to ~10s
- Full LangSmith tracing from day one
- Clear node boundaries improve testability

**Long-term Benefits**:
- Easy to add new pipeline stages
- Built-in support for checkpointing (future)
- Graph visualization for documentation

### Negative Outcomes

**Immediate Costs**:
- Team must learn LangGraph concepts
- State serialization requirements

**Technical Debt Created**:
- None significant - LangGraph is well-maintained

**Trade-offs**:
- Less flexibility than custom code (acceptable)
- Tied to LangChain ecosystem (acceptable, already committed)

---

## Implementation Plan

### Phases

**Phase 1**: State and Node Implementation
- Duration: 10 hours
- Tasks:
  - [x] Define HNState TypedDict
  - [x] Implement all 7 node functions
  - [x] Add comprehensive logging
- Deliverable: Working nodes with tests

**Phase 2**: Graph Assembly
- Duration: 4 hours
- Tasks:
  - [x] Create StateGraph
  - [x] Configure Send pattern for parallel extraction
  - [x] Compile and test graph
- Deliverable: Compiled graph

**Phase 3**: Integration
- Duration: 4 hours
- Tasks:
  - [x] LangSmith configuration
  - [x] Integration testing
  - [x] Performance validation
- Deliverable: Production-ready pipeline

### Rollback Plan

**Trigger Conditions**:
- LangGraph has breaking changes we can't adapt to
- Performance issues that can't be resolved

**Fallback Option**:
- Revert to Option B (Custom Async) using existing node logic

---

## Validation

### Post-Implementation Results

**Success Metrics Achieved**:
- Pipeline execution time: ~15-25s for 30 articles ✅
- Parallel extraction: 10 concurrent article fetches ✅
- LangSmith tracing: Full visibility into all LLM calls ✅
- Test coverage: 78 graph tests (64 unit + 14 integration) ✅

**Architecture**:
```
fetch_hn → [Send] → fetch_article (×N parallel)
                          ↓
                       filter
                          ↓
                      summarize (batched LLM)
                          ↓
                        score
                          ↓
                        rank
                          ↓
                       format → Digest
```

---

## References

### Code References

- `src/hn_herald/graph/state.py` - HNState TypedDict definition
- `src/hn_herald/graph/graph.py` - StateGraph assembly
- `src/hn_herald/graph/nodes/` - All node implementations
- `tests/unit/graph/` - 64 unit tests
- `tests/integration/graph/` - 14 integration tests

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Send Pattern Guide](https://langchain-ai.github.io/langgraph/how-tos/send/)
- [LangSmith Tracing](https://docs.smith.langchain.com/)

---

## Metadata

**ADR Number**: 001
**Created**: 2026-01-04
**Last Updated**: 2026-01-08
**Version**: 1.0

**Tags**: architecture, langgraph, pipeline, orchestration

**Project Phase**: Development (MVP-5a)
