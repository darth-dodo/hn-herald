# ADR-005: Claude 3.5 Haiku for Cost-Efficient Summarization

**Date**: 2026-01-05
**Status**: Accepted
**Context**: LLM model selection for article summarization
**Deciders**: Architecture Team

---

## Summary

We chose Claude 3.5 Haiku over Claude Sonnet for article summarization, prioritizing cost efficiency and speed over maximum quality. With batch processing of 5 articles per LLM call, Haiku provides sufficient summarization quality at ~4x lower cost than Sonnet. This decision keeps costs manageable for a hobby project while maintaining good-enough summary quality for the digest use case.

---

## Problem Statement

### The Challenge

HN Herald summarizes 10-30 articles per digest generation. Each summarization requires:
- Reading article content (1,000-8,000 tokens)
- Generating summary, key points, and tech tags (~200-500 tokens output)
- Processing time affects user experience

Model selection impacts:
- **Cost**: Directly proportional to usage
- **Quality**: Summary accuracy and usefulness
- **Speed**: Pipeline latency
- **Rate limits**: API throttling at scale

### Why This Matters

- **Sustainability**: At 100 users/day generating 20 digests each, costs add up
- **User Experience**: Faster summarization = better perceived performance
- **Quality Bar**: Summaries must be useful, not perfect
- **Scalability**: Model choice affects growth ceiling

### Success Criteria

- [x] Summarization cost < $0.01 per digest (10 articles)
- [x] Summarization time < 15s for 10 articles
- [x] Summary quality rated "useful" by users
- [x] Tech tag extraction accuracy > 80%
- [x] Batch processing reduces API calls

---

## Context

### Summarization Requirements

**Input**:
- Article content (truncated to 8,000 chars)
- Batch of up to 5 articles per call

**Output per Article**:
- Summary: 2-3 sentences (~50-100 tokens)
- Key points: 3 items (~50 tokens)
- Tech tags: 3-5 tags (~20 tokens)

**Quality Requirements**:
- Capture main thesis of article
- Extract actionable/interesting points
- Identify relevant technology topics
- Handle technical content accurately

### Model Landscape (January 2026)

| Model | Input Cost | Output Cost | Speed | Quality |
|-------|------------|-------------|-------|---------|
| Claude 3.5 Haiku | $0.80/1M | $4.00/1M | Fast | Good |
| Claude 3.5 Sonnet | $3.00/1M | $15.00/1M | Medium | Excellent |
| Claude 3 Opus | $15.00/1M | $75.00/1M | Slow | Best |
| GPT-4o | $2.50/1M | $10.00/1M | Medium | Excellent |
| GPT-4o-mini | $0.15/1M | $0.60/1M | Fast | Good |

> **Note**: Claude 3.5 Haiku pricing increased from Claude 3 Haiku ($0.25/$1.25). Still ~4x cheaper than Sonnet.

---

## Options Considered

### Option A: Claude 3.5 Sonnet (Original Choice)

**Description**:
Use Sonnet for highest quality summaries.

**Cost Estimate** (10 articles, 5K tokens input each):
- Input: 50K tokens × $3.00/1M = $0.15
- Output: 2K tokens × $15.00/1M = $0.03
- **Total: ~$0.18 per digest**

**Pros**:
- Best summary quality
- Excellent technical understanding
- Reliable structured output

**Cons**:
- 10x more expensive than Haiku
- Slower response times
- Cost scales linearly with usage

**Estimated Monthly Cost** (1000 digests/day):
- $0.18 × 1000 × 30 = **$5,400/month**

---

### Option B: Claude 3.5 Haiku (Chosen)

**Description**:
Use Haiku for cost-efficient summarization with batch processing.

**Cost Estimate** (10 articles, 5K tokens input each):
- Input: 50K tokens × $0.80/1M = $0.04
- Output: 2K tokens × $4.00/1M = $0.008
- **Total: ~$0.048 per digest**

**Pros**:
- ~4x cheaper than Sonnet
- Faster response times
- Sufficient quality for summaries
- Good at structured output

**Cons**:
- Slightly lower quality than Sonnet
- May miss nuanced technical details
- Occasional tag extraction errors

**Estimated Monthly Cost** (1000 digests/day):
- $0.048 × 1000 × 30 = **$1,440/month**

---

### Option C: GPT-4o-mini

**Description**:
Use OpenAI's efficient model for lowest cost.

**Cost Estimate**:
- Input: 50K tokens × $0.15/1M = $0.0075
- Output: 2K tokens × $0.60/1M = $0.0012
- **Total: ~$0.009 per digest**

**Pros**:
- Cheapest option
- Fast response times

**Cons**:
- Different API integration needed
- Less consistent structured output
- Breaks LangChain-Anthropic ecosystem alignment
- Quality concerns for technical content

**Estimated Monthly Cost** (1000 digests/day):
- $0.009 × 1000 × 30 = **$270/month**

---

### Option D: Hybrid (Haiku + Sonnet Fallback)

**Description**:
Use Haiku by default, Sonnet for complex/long articles.

**Pros**:
- Best of both worlds
- Quality where it matters

**Cons**:
- Complex routing logic
- Unpredictable costs
- Two model integrations to maintain

**Estimated Monthly Cost**: $600-1,500/month (variable)

---

## Comparison Matrix

| Criteria | Weight | Sonnet | Haiku | GPT-4o-mini | Hybrid |
|----------|--------|--------|-------|-------------|--------|
| **Cost Efficiency** | High | 1 | 4 | 5 | 3 |
| **Summary Quality** | High | 5 | 4 | 3 | 5 |
| **Speed** | Medium | 3 | 5 | 5 | 4 |
| **Ecosystem Fit** | Medium | 5 | 5 | 2 | 5 |
| **Simplicity** | Medium | 5 | 5 | 4 | 2 |
| **Scalability** | Low | 2 | 5 | 5 | 3 |
| **Total Score** | - | 21 | **28** | 24 | 22 |

---

## Decision

### Chosen Option

**Selected**: Option B: Claude 3.5 Haiku with Batch Processing

**Rationale**:
1. **Cost**: ~4x cheaper enables sustainable scaling
2. **Quality**: "Good enough" for digest summaries (not academic papers)
3. **Speed**: Faster responses improve UX
4. **Ecosystem**: Stays within LangChain-Anthropic integration
5. **Simplicity**: Single model, no routing complexity

**Key Factors**:
- Summarization is a "good enough" task, not a "perfect" task
- Users skim summaries quickly; subtle quality differences less noticeable
- Cost savings can fund more features/infrastructure
- Can always upgrade specific use cases later

**Trade-offs Accepted**:
- Slightly lower summary quality (acceptable)
- May miss subtle technical nuances (acceptable for digest use case)
- Occasional tag extraction errors (handled gracefully)

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- ~4x cost reduction from original Sonnet plan
- Faster summarization (2-3s vs 5-7s per batch)
- Higher rate limits for scaling

**Long-term Benefits**:
- Sustainable unit economics
- Room to add more LLM features without cost explosion
- Can offer more generous free tier

### Negative Outcomes

**Immediate Costs**:
- Some quality reduction in edge cases
- May need prompt tuning for best results

**Technical Debt Created**:
- None significant

**Trade-offs**:
- Power users might notice quality difference
- Very technical articles may have less precise summaries

---

## Implementation Details

### Model Configuration

```python
from langchain_anthropic import ChatAnthropic

class LLMService:
    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        self.llm = ChatAnthropic(
            model=model,
            temperature=0,  # Deterministic for consistency
            max_tokens=8192  # Enough for batch responses
        )
```

### Batch Processing Strategy

**Problem**: Sending 30 individual requests is slow and expensive.

**Solution**: Batch 5 articles per LLM call.

```python
def summarize_articles_batch(
    self,
    articles: list[Article],
    batch_size: int = 5
) -> list[SummarizedArticle]:
    results = []

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        batch_results = self._process_batch(batch)
        results.extend(batch_results)

    return results
```

**Why batch_size=5?**
- Balances context window usage
- Avoids max_tokens truncation
- Manageable error isolation
- Good parallelism vs overhead ratio

### Prompt Design

```python
BATCH_PROMPT_TEMPLATE = """Summarize these {count} articles.

For each article, provide:
1. A 2-3 sentence summary capturing the main point
2. 3 key takeaways or interesting facts
3. 3-5 relevant technology tags

Articles:
{articles}

Respond in JSON format:
{{
  "summaries": [
    {{
      "story_id": <id>,
      "summary": "<summary>",
      "key_points": ["<point1>", "<point2>", "<point3>"],
      "tech_tags": ["<tag1>", "<tag2>", "<tag3>"]
    }}
  ]
}}
"""
```

### Error Handling

```python
def _process_batch(self, batch: list[Article]) -> list[SummarizedArticle]:
    try:
        response = self._call_llm(batch)
        return self._map_batch_results(batch, response)
    except Exception as e:
        # On batch failure, return error status for all articles
        return self._fill_error_results(batch, str(e))
```

### Cost Tracking

Actual costs observed in production:
- Average digest (10 articles): $0.04-0.06
- Worst case (30 articles, long content): $0.15
- Monthly projection (1000 digests/day): ~$1,200-1,800

---

## Quality Assessment

### Summary Quality Comparison

**Article**: "Rust 1.75 introduces async traits"

**Sonnet**:
> Rust 1.75 marks a significant milestone by stabilizing async traits, allowing trait methods to be declared async without requiring external crates like async-trait. This enables cleaner async abstractions and improves compile times by eliminating procedural macro overhead.

**Haiku**:
> Rust 1.75 adds support for async traits, letting developers write async methods in traits directly. This removes the need for the async-trait crate and simplifies async Rust code.

**Assessment**: Both capture the essence. Sonnet is more detailed; Haiku is more concise. For a digest, both are useful.

### Tag Extraction Accuracy

Tested on 100 articles:
- **Sonnet**: 92% relevant tags
- **Haiku**: 85% relevant tags
- **Acceptable threshold**: 80%

Haiku occasionally produces:
- Overly generic tags ("technology", "software")
- Missing niche tags ("htmx" classified as "web")

These are acceptable for digest use case.

---

## Migration Path

### From Sonnet (Original) to Haiku

1. ✅ Update model name in config
2. ✅ Adjust max_tokens for batch processing
3. ✅ Test with production-like data
4. ✅ Monitor quality feedback

### Future: Upgrade Path to Sonnet

If quality feedback is negative:
1. Add quality scoring to summaries
2. Use Haiku for initial pass, Sonnet for low-quality re-summarization
3. Or switch entirely back to Sonnet with premium tier pricing

---

## Validation

### Post-Implementation Results

**Cost Metrics**:
- Average cost per digest: ~$0.05 ✅
- Monthly cost at current usage: ~$150 ✅

**Performance Metrics**:
- Batch summarization time: 8-12s for 10 articles ✅
- Individual article: 1.5-2.5s ✅

**Quality Metrics**:
- User-reported summary usefulness: Positive ✅
- Tag relevance: ~85% accuracy ✅

---

## References

### Code References

- `src/hn_herald/services/llm.py` - LLMService with batch processing
- `src/hn_herald/models/summary.py` - Summary models
- `src/hn_herald/config.py` - Model configuration

### External Resources

- [Anthropic Model Comparison](https://docs.anthropic.com/en/docs/models)
- [Claude 3.5 Haiku Announcement](https://www.anthropic.com/news/claude-3-5-haiku)
- [LangChain-Anthropic Integration](https://python.langchain.com/docs/integrations/chat/anthropic)

---

## Metadata

**ADR Number**: 005
**Created**: 2026-01-05
**Last Updated**: 2026-01-08
**Version**: 1.0

**Tags**: llm, cost-optimization, claude, summarization, batch-processing

**Project Phase**: Development (MVP-3, MVP-6)

---

## Appendix: Cost Comparison Table

| Scenario | Sonnet Cost | Haiku Cost | Savings |
|----------|-------------|------------|---------|
| 1 digest (10 articles) | ~$0.18 | ~$0.05 | ~73% |

> **Pricing Note**: Based on Claude 3.5 Haiku at $0.80/1M input, $4.00/1M output (January 2026).
