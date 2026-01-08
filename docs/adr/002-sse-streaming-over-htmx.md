# ADR-002: SSE Streaming over HTMX Partial Swaps

**Date**: 2026-01-06
**Status**: Accepted
**Context**: Frontend communication pattern for digest generation
**Deciders**: Architecture Team

---

## Summary

We chose Server-Sent Events (SSE) with vanilla JavaScript over HTMX partial swaps for real-time digest generation updates. While HTMX was initially planned and is still loaded in the application, the need for streaming pipeline progress (7 stages over 15-30 seconds) made SSE a better fit. This decision provides real-time feedback during long-running operations while maintaining a simple, dependency-light frontend.

---

## Problem Statement

### The Challenge

Digest generation takes 15-30 seconds and involves 7 distinct pipeline stages:
1. Fetching HN stories
2. Extracting article content (parallel)
3. Filtering articles
4. Summarizing with AI
5. Scoring relevance
6. Ranking articles
7. Formatting digest

Users need real-time feedback about which stage is executing, otherwise they see a static loading spinner for 30 seconds with no indication of progress.

### Why This Matters

- **User Experience**: 30 seconds of silence feels like the app is broken
- **Perceived Performance**: Progress updates make waits feel shorter
- **Debugging**: Stage-by-stage feedback helps identify where issues occur
- **Engagement**: HN fun facts during loading keep users engaged

### Success Criteria

- [x] Real-time pipeline stage updates in the UI
- [x] Graceful error handling with specific error messages
- [x] Final digest display without page reload
- [x] Works on all modern browsers
- [x] Minimal JavaScript footprint

---

## Context

### Initial Design

**Original Plan (from `06-htmx-templates.md`)**:
```html
<form
  hx-post="/api/v1/digest"
  hx-target="#results"
  hx-swap="innerHTML"
  hx-indicator="#loading">
```

HTMX would POST the form, show a loading indicator, and swap the results div with the server response.

**Pain Points with HTMX Approach**:
- Single request/response model - no streaming
- Loading indicator is binary (loading/not loading)
- No way to show which pipeline stage is executing
- User sees static spinner for 30 seconds

**Technical Constraints**:
- Pipeline stages are distinct and sequential
- Each stage has different duration (fetch: 2s, extract: 10s, summarize: 15s)
- Need to stream progress without multiple HTTP requests
- Must work with existing FastAPI backend

### Requirements

**Functional Requirements**:
- Show current pipeline stage during generation
- Display stage-specific messages (e.g., "Summarizing with AI...")
- Stream final digest without page reload
- Handle errors with specific error messages

**Non-Functional Requirements**:
- **Latency**: Progress updates within 100ms of stage change
- **Reliability**: Graceful degradation if SSE fails
- **Simplicity**: Minimal JavaScript, no build step
- **Compatibility**: Works in all modern browsers

---

## Options Considered

### Option A: HTMX Partial Swaps (Original Plan)

**Description**:
Use HTMX `hx-post` with loading indicator and HTML partial response.

**Implementation**:
```html
<form hx-post="/api/v1/digest" hx-target="#results" hx-indicator="#loading">
```

**Pros**:
- Declarative, minimal JavaScript
- Simple request/response model
- Built-in loading states

**Cons**:
- No streaming - single response only
- Can't show pipeline stage progress
- 30 seconds of static loading spinner
- Poor UX for long-running operations

**Estimated Effort**: 4 hours

---

### Option B: HTMX SSE Extension

**Description**:
Use HTMX's SSE extension (`hx-ext="sse"`) for streaming updates.

**Implementation**:
```html
<div hx-ext="sse" sse-connect="/api/v1/digest/stream" sse-swap="message">
```

**Pros**:
- Stays within HTMX ecosystem
- Declarative SSE handling
- Partial HTML swaps

**Cons**:
- SSE extension is separate dependency
- Limited control over event handling
- Harder to coordinate with complex UI updates
- Less flexible than vanilla JS for our use case

**Estimated Effort**: 8 hours

---

### Option C: Vanilla JS with Fetch + SSE (Chosen)

**Description**:
Use native `fetch()` API with streaming response reader and manual DOM updates.

**Implementation**:
```javascript
const response = await fetch('/api/v1/digest/stream', {
  method: 'POST',
  body: JSON.stringify(payload)
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Parse SSE events, update UI
}
```

**Pros**:
- Full control over streaming and UI updates
- No additional dependencies
- Works with POST requests (SSE typically GET-only)
- Flexible error handling
- Can show progress, fun facts, and final results

**Cons**:
- More JavaScript code than HTMX
- Manual DOM manipulation
- HTMX becomes unused dependency

**Estimated Effort**: 6 hours

---

### Option D: WebSockets

**Description**:
Bidirectional WebSocket connection for real-time updates.

**Pros**:
- True bidirectional communication
- Lower latency than SSE
- Can send client messages during generation

**Cons**:
- Overkill - we only need server-to-client
- More complex server implementation
- Connection management complexity
- Doesn't work through some proxies

**Estimated Effort**: 12 hours

---

## Comparison Matrix

| Criteria | Weight | HTMX Partials | HTMX SSE | Vanilla SSE | WebSockets |
|----------|--------|---------------|----------|-------------|------------|
| **Streaming Support** | High | 1 | 4 | 5 | 5 |
| **Implementation Simplicity** | High | 5 | 3 | 4 | 2 |
| **UI Control** | High | 2 | 3 | 5 | 5 |
| **Dependencies** | Medium | 4 | 3 | 5 | 4 |
| **Browser Support** | Medium | 5 | 4 | 5 | 4 |
| **Debugging** | Low | 4 | 3 | 5 | 3 |
| **Total Score** | - | 21 | 20 | **29** | 23 |

---

## Decision

### Chosen Option

**Selected**: Option C: Vanilla JS with Fetch + SSE

**Rationale**:
1. **Streaming is essential** for 30-second operations - rules out Option A
2. **Full UI control** needed for progress bar, fun facts, stats display
3. **POST support** - native SSE is GET-only, fetch streaming works with POST
4. **No new dependencies** - vanilla JS keeps bundle small
5. **Simpler than WebSockets** for unidirectional streaming

**Key Factors**:
- Pipeline has 7 distinct stages that benefit from progress feedback
- Fun facts rotation requires JavaScript interval anyway
- Complex results display (stats, articles, scores) needs JS DOM manipulation
- HTMX SSE extension adds complexity without solving our POST requirement

**Trade-offs Accepted**:
- HTMX remains loaded but mostly unused (14KB gzipped, acceptable)
- More JavaScript than pure HTMX approach (~300 lines)
- Manual DOM manipulation instead of declarative

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- Real-time pipeline stage updates ("Summarizing with AI...")
- Fun facts rotation every 5 seconds during loading
- Detailed stats display (funnel, performance, quality metrics)
- Better error messages with specific failure points

**Long-term Benefits**:
- Foundation for more interactive features
- Easy to add progress percentages per stage
- Can extend to show partial results as they arrive

### Negative Outcomes

**Immediate Costs**:
- HTMX is vestigial (loaded but barely used)
- More JavaScript to maintain than HTMX-only approach

**Technical Debt Created**:
- Should either remove HTMX or find uses for it
- Design doc (`06-htmx-templates.md`) is now partially outdated

**Trade-offs**:
- Lost declarative simplicity of HTMX
- More code to test and maintain

---

## Implementation Details

### Server-Side (FastAPI)

```python
@router.post("/digest/stream")
async def generate_digest_stream(request: GenerateDigestRequest):
    async def event_generator():
        yield f"data: {json.dumps({'stage': 'starting', 'message': 'Initializing...'})}\n\n"

        async for state in graph.astream(initial_state, stream_mode="values"):
            node = _detect_current_node(state)
            yield f"data: {json.dumps({'stage': node, 'message': _STAGE_MESSAGES[node]})}\n\n"

        yield f"data: {json.dumps({'stage': 'complete', 'digest': result})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Client-Side (Vanilla JS)

```javascript
async function generateDigest() {
  const response = await fetch('/api/v1/digest/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // Parse SSE format: "data: {...}\n\n"
    const lines = decoder.decode(value).split('\n\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        if (data.stage === 'complete') {
          displayDigestResults(data.digest);
        } else {
          updatePipelineStage(data.message);
        }
      }
    }
  }
}
```

### HTMX Remaining Usage

HTMX is still loaded but only used for:
- `htmx-indicator` CSS class (could be replaced with custom CSS)
- Potential future use for simpler interactions

**Recommendation**: Keep HTMX for now, evaluate removal in future cleanup.

---

## Validation

### Post-Implementation Results

**Success Metrics Achieved**:
- Real-time stage updates: ✅ Updates within 100ms of stage change
- User engagement: ✅ Fun facts rotate every 5 seconds
- Error handling: ✅ Specific error messages displayed
- Browser support: ✅ Works in Chrome, Firefox, Safari, Edge

**User Experience**:
```
[Loading Screen]
┌─────────────────────────────────────────┐
│  Generating Your Digest...              │
│                                         │
│  ⟳ Summarizing with AI...              │
│                                         │
│  💡 Fun Fact: HN's algorithm favors    │
│     newer stories - upvotes from the   │
│     first few hours count more...      │
└─────────────────────────────────────────┘
```

---

## Future Considerations

1. **Remove HTMX**: If no other uses emerge, remove to reduce bundle size
2. **Progress Percentages**: Add estimated progress per stage
3. **Partial Results**: Stream articles as they're summarized
4. **Abort Support**: Add cancel button using AbortController

---

## References

### Code References

- `src/hn_herald/api/routes.py` - SSE streaming endpoint
- `src/hn_herald/static/js/app.js` - Client-side streaming handler
- `src/hn_herald/templates/base.html` - HTMX script tag (vestigial)

### External Resources

- [MDN: Using Readable Streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams)
- [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [HTMX SSE Extension](https://htmx.org/extensions/server-sent-events/)

---

## Metadata

**ADR Number**: 002
**Created**: 2026-01-06
**Last Updated**: 2026-01-08
**Version**: 1.0

**Tags**: frontend, sse, streaming, htmx, javascript

**Project Phase**: Development (MVP-6)

---

## Notes

This ADR documents a pivot from the original design. The design document `docs/design/06-htmx-templates.md` reflects the original HTMX-heavy approach and should be read with this ADR in mind. The implementation chose SSE for better UX during long-running operations.
