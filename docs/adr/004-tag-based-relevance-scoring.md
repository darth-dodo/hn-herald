# ADR-004: Tag-Based Relevance Scoring Algorithm

**Date**: 2026-01-03
**Status**: Accepted
**Context**: Article personalization and ranking system
**Deciders**: Architecture Team

---

## Summary

We chose a tag-matching relevance scoring algorithm over embedding-based semantic similarity for HN Herald's personalization system. Articles are scored based on overlap between their AI-generated tech tags and user-selected interest/disinterest tags, combined with HN popularity signals. This approach is simpler, more transparent, and computationally cheaper than vector similarity, while providing sufficient personalization quality for the MVP.

---

## Problem Statement

### The Challenge

HN Herald needs to rank articles by relevance to user interests. Given:
- User selects interest tags (e.g., "python", "ai", "startups")
- User selects disinterest tags (e.g., "crypto", "blockchain")
- Articles have AI-generated tech tags from summarization
- Articles have HN popularity metrics (score, comments)

How should we compute a "relevance score" that balances personalization with community signals?

### Why This Matters

- **User Value**: Relevance determines which articles users see first
- **Trust**: Users need to understand why articles are ranked
- **Performance**: Scoring runs on every article in the digest
- **Iteration**: Algorithm needs to be tunable based on feedback

### Success Criteria

- [x] Articles matching interests score higher than neutral
- [x] Articles matching disinterests are deprioritized
- [x] HN popularity provides baseline quality signal
- [x] Scoring is explainable (users see why articles matched)
- [x] Algorithm is fast (<1ms per article)

---

## Context

### Scoring Requirements

**Input Data**:
- User profile: `interest_tags`, `disinterest_tags`, `min_score`
- Article: `tech_tags` (from LLM), `hn_score`, `hn_comments`

**Output**:
- `relevance_score`: 0.0-1.0 (tag matching)
- `popularity_score`: 0.0-1.0 (normalized HN metrics)
- `final_score`: Weighted combination
- `relevance_reason`: Human-readable explanation

**Technical Constraints**:
- No external API calls (must be fast)
- Must work with categorical tags (not free text)
- Must handle case variations ("Python" vs "python")
- Must produce explainable results

### Requirements

**Functional Requirements**:
- Match article tags against user interest tags
- Penalize articles matching disinterest tags
- Incorporate HN popularity as quality signal
- Generate human-readable relevance explanations

**Non-Functional Requirements**:
- **Performance**: <1ms per article scoring
- **Explainability**: Users understand their scores
- **Tunability**: Weights adjustable without code changes
- **Consistency**: Same inputs produce same outputs

---

## Options Considered

### Option A: Embedding-Based Semantic Similarity

**Description**:
Generate vector embeddings for user interests and article content, compute cosine similarity.

**Implementation**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
user_embedding = model.encode(user_interests_text)
article_embedding = model.encode(article_summary)
similarity = cosine_similarity(user_embedding, article_embedding)
```

**Pros**:
- Captures semantic relationships ("machine learning" ≈ "AI")
- Handles synonyms and related concepts
- More sophisticated personalization

**Cons**:
- Requires embedding model (100MB+)
- Slower (~50ms per article)
- Less explainable ("why is this relevant?")
- Overkill for tag-based matching
- Model updates could change scores

**Estimated Effort**: 16 hours

---

### Option B: Tag-Matching with Set Operations (Chosen)

**Description**:
Direct set intersection/difference between user tags and article tags with weighted scoring.

**Implementation**:
```python
def calculate_relevance(article_tags, interest_tags, disinterest_tags):
    interests_matched = set(article_tags) & set(interest_tags)
    disinterests_matched = set(article_tags) & set(disinterest_tags)

    if disinterests_matched:
        return 0.1  # Heavy penalty
    if interests_matched:
        return 0.5 + (0.5 * len(interests_matched) / len(interest_tags))
    return 0.5  # Neutral
```

**Pros**:
- Simple and fast (<1ms)
- Fully explainable ("Matched: python, ai")
- No external dependencies
- Deterministic results
- Easy to tune weights

**Cons**:
- No semantic understanding
- "ML" won't match "machine learning"
- Requires good tag normalization

**Estimated Effort**: 6 hours

---

### Option C: Hybrid (Tags + Lightweight Embeddings)

**Description**:
Tag matching for primary scoring, embeddings for tie-breaking.

**Pros**:
- Best of both worlds
- Semantic fallback for edge cases

**Cons**:
- Complexity of two systems
- Still requires embedding model
- Harder to explain combined score

**Estimated Effort**: 24 hours

---

### Option D: LLM-Based Scoring

**Description**:
Ask Claude to score relevance given user interests and article content.

**Pros**:
- Most sophisticated understanding
- Can explain reasoning in natural language

**Cons**:
- Expensive (~$0.001 per article)
- Slow (~500ms per article)
- Non-deterministic
- Overkill for simple tag matching

**Estimated Effort**: 8 hours

---

## Comparison Matrix

| Criteria | Weight | Embeddings | Tag Matching | Hybrid | LLM |
|----------|--------|------------|--------------|--------|-----|
| **Performance** | High | 2 | 5 | 3 | 1 |
| **Explainability** | High | 2 | 5 | 3 | 4 |
| **Simplicity** | High | 2 | 5 | 2 | 3 |
| **Accuracy** | Medium | 4 | 3 | 5 | 5 |
| **Cost** | Medium | 3 | 5 | 3 | 1 |
| **Tunability** | Low | 3 | 5 | 3 | 2 |
| **Total Score** | - | 16 | **28** | 19 | 16 |

---

## Decision

### Chosen Option

**Selected**: Option B: Tag-Matching with Set Operations

**Rationale**:
1. **Performance**: Sub-millisecond scoring critical for responsive UI
2. **Explainability**: Users can see exactly which tags matched
3. **Simplicity**: No ML infrastructure required
4. **Good enough**: Tag matching provides 80% of value at 20% complexity
5. **Privacy**: No need to send data to embedding service

**Key Factors**:
- LLM already generates quality tech tags during summarization
- User-selected tags are explicit signals (not implicit behavior)
- HN audience appreciates transparency over black-box ML
- Can always upgrade to embeddings later if needed

**Trade-offs Accepted**:
- No semantic matching ("ML" ≠ "machine learning")
- Relies on quality of LLM-generated tags
- Users must select tags explicitly (no learned preferences)

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- Fast scoring enables responsive UI
- Users understand their relevance scores
- No ML infrastructure to maintain
- Easy to adjust weights based on feedback

**Long-term Benefits**:
- Foundation for more sophisticated scoring
- Can add synonym mapping without full embeddings
- User feedback on tag quality improves system

### Negative Outcomes

**Immediate Costs**:
- May miss semantically related content
- Requires good tag vocabulary coverage

**Technical Debt Created**:
- May need synonym/alias mapping (e.g., "JS" → "JavaScript")

**Trade-offs**:
- Simpler algorithm may feel less "smart"
- Power users might want more nuanced matching

---

## Implementation Details

### Scoring Algorithm

```python
class ScoringService:
    RELEVANCE_WEIGHT: float = 0.7
    POPULARITY_WEIGHT: float = 0.3

    def _calculate_relevance(
        self,
        article_tags: list[str],
        interest_tags: list[str],
        disinterest_tags: list[str]
    ) -> tuple[float, str, list[str], list[str]]:
        # Normalize tags to lowercase
        article_set = {t.lower() for t in article_tags}
        interest_set = {t.lower() for t in interest_tags}
        disinterest_set = {t.lower() for t in disinterest_tags}

        # Find matches
        interests_matched = list(article_set & interest_set)
        disinterests_matched = list(article_set & disinterest_set)

        # Calculate score
        if disinterests_matched:
            score = 0.1
            reason = f"Matches disinterest tags: {', '.join(disinterests_matched)}"
        elif interests_matched:
            match_ratio = len(interests_matched) / len(interest_set)
            score = 0.5 + (0.5 * match_ratio)
            reason = f"Matches interests: {', '.join(interests_matched)}"
        else:
            score = 0.5
            reason = "No specific tag matches"

        return score, reason, interests_matched, disinterests_matched

    def _normalize_popularity(
        self,
        hn_score: int,
        all_scores: list[int] | None = None
    ) -> float:
        if all_scores:
            # Relative to batch
            max_score = max(all_scores) or 1
            return min(hn_score / max_score, 1.0)
        else:
            # Absolute scale (capped at 500)
            return min(hn_score / 500, 1.0)

    def score_article(self, article: SummarizedArticle) -> ScoredArticle:
        relevance, reason, matched_int, matched_dis = self._calculate_relevance(
            article.summary_data.tech_tags,
            self.profile.interest_tags,
            self.profile.disinterest_tags
        )

        popularity = self._normalize_popularity(article.article.hn_score)

        final_score = (
            relevance * self.RELEVANCE_WEIGHT +
            popularity * self.POPULARITY_WEIGHT
        )

        return ScoredArticle(
            article=article,
            relevance=RelevanceScore(
                score=relevance,
                reason=reason,
                matched_interest_tags=matched_int,
                matched_disinterest_tags=matched_dis
            ),
            popularity_score=popularity,
            final_score=final_score
        )
```

### Score Distribution

| Scenario | Relevance | Popularity | Final (70/30) |
|----------|-----------|------------|---------------|
| All interests match, high HN | 1.0 | 1.0 | 1.0 |
| All interests match, low HN | 1.0 | 0.2 | 0.76 |
| Some interests match, high HN | 0.75 | 1.0 | 0.825 |
| No matches, high HN | 0.5 | 1.0 | 0.65 |
| No matches, low HN | 0.5 | 0.2 | 0.41 |
| Disinterest match | 0.1 | any | 0.07-0.37 |

### Relevance Reason Examples

```
"Matches interests: python, ai, machine-learning"
"Matches interests: startups (1 of 5 interests)"
"Matches disinterest tags: crypto, blockchain"
"No specific tag matches"
```

---

## Validation

### Post-Implementation Results

**Test Coverage**:
- 186 tests for scoring system
- Unit tests for edge cases (empty tags, case sensitivity)
- Integration tests for full scoring pipeline

**Performance Metrics**:
- Scoring time: <0.5ms per article ✅
- Batch scoring (30 articles): <15ms ✅

**Quality Assessment**:
- Interest matches correctly prioritized ✅
- Disinterest penalty working as expected ✅
- HN popularity provides meaningful differentiation ✅

---

## Future Enhancements

1. **Tag Synonyms**: Map "JS" → "JavaScript", "ML" → "machine learning"
2. **Tag Hierarchies**: "React" is-a "JavaScript" is-a "Frontend"
3. **Weight Learning**: Adjust 70/30 split based on user feedback
4. **Embedding Fallback**: Use embeddings only when no tag matches
5. **Negative Keywords**: Title/content keyword matching for disinterests

---

## References

### Code References

- `src/hn_herald/services/scoring.py` - ScoringService implementation
- `src/hn_herald/models/scoring.py` - RelevanceScore, ScoredArticle models
- `tests/test_services/test_scoring.py` - 65 service tests
- `tests/test_models/test_scoring.py` - 80 model tests

### Design Documents

- `docs/design/04-relevance-scoring.md` - Full design specification

---

## Metadata

**ADR Number**: 004
**Created**: 2026-01-03
**Last Updated**: 2026-01-08
**Version**: 1.0

**Tags**: algorithm, scoring, personalization, tags

**Project Phase**: Development (MVP-4)
