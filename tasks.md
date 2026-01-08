# HN Herald - Task Tracking

## Session Handoff

| Field | Value |
|-------|-------|
| current_task | All MVPs Complete |
| next_action | Deploy to production |
| blockers | None |
| quality_status | ✅ 8/8 gates passing |
| test_coverage | 469 tests, 91% coverage |

### Recent Changes (Jan 2026)
- **Rate limiting**: Global rate limiting (30 req/60s) on digest endpoints (privacy-first, no per-IP tracking)
- **Batch summarization chunking**: Fixed max_tokens truncation by chunking articles (batch_size=5)
- **SSE streaming**: Real-time pipeline progress via `/api/v1/digest/stream`
- **Model switch**: Claude Sonnet → Claude 3.5 Haiku for cost efficiency
- **Enhanced logging**: Batch progress, filter status breakdown, score distribution

---

## XP Development Approach

We follow **Extreme Programming (XP)** principles:

| Principle | Practice |
|-----------|----------|
| Small Releases | Each MVP delivers shippable increment |
| TDD Cycle | Red → Green → Refactor |
| Small Commits | Every 15-30 minutes |
| CI/CD | Pre-commit hooks → Tests → Build → Deploy |
| Simple Design | Build only what's needed now |
| Collective Ownership | Any agent can modify any code |

---

## 8-Step Quality Gates

| Gate | Check | Tool | Threshold |
|------|-------|------|-----------|
| 1. Syntax | Code parses | `uv run python -m py_compile` | Zero errors |
| 2. Types | Type safety | `uv run mypy src/` | Strict mode |
| 3. Lint | Code style | `uv run ruff check src/` | Zero warnings |
| 4. Security | Vulnerabilities | `uv pip audit` | No high/critical |
| 5. Tests | Coverage | `uv run pytest --cov` | ≥70% |
| 6. Performance | Load time | Lighthouse | ≥90 score |
| 7. Accessibility | WCAG | Playwright a11y | AA compliance |
| 8. Integration | Smoke tests | E2E suite | All pass |

**Pre-commit**: Gates 1-4 | **CI**: Gates 5-8

---

## Agentic Workflow Phases

| Phase | Persona | Duration | Output |
|-------|---------|----------|--------|
| Design | Architect | 30-60min | `docs/design/*.md` |
| Implementation | Developer | 1-3hr | `src/**/*.py`, `tests/**/*.py` |
| Validation | QA | 30-60min | Test results, quality report |

**MCP Servers**: Context7 (docs) | Sequential (analysis) | Playwright (E2E)

---

## Progress Summary

| MVP | Deliverable | User Value | CI/CD Gate | Status |
|-----|-------------|------------|------------|--------|
| Setup | Project scaffolding | Foundation | ✅ All hooks passing | DONE |
| MVP-1 | HN API client | Can fetch stories | ✅ 68 unit tests | DONE |
| MVP-2 | Article extraction | Can read content | ✅ Loader tests | DONE |
| MVP-3 | LLM summarization | Get AI summaries | ✅ 11 integration tests | DONE |
| MVP-4 | Relevance scoring | Personalized ranking | ✅ 186 scoring tests | DONE |
| MVP-5 | FastAPI endpoints | API is callable | ✅ 15 API contract tests | DONE |
| MVP-6 | Web UI + SSE | Usable web UI | ✅ SSE streaming, themes | DONE |
| Rate Limit | API protection | Protects API quotas | ✅ 30 tests | DONE |
| MVP-7 | Tag system UI | Can select interests | ✅ localStorage | DONE |
| MVP-8 | Mobile polish | Works on phones | ✅ Touch targets | DONE |

**Overall**: 45/45+ tasks | 469 tests passing | 8/8 gates green | **MVP COMPLETE**

---

## Current Focus

### Rate Limiting [COMPLETE]

| # | Task | Status | Quality Gate | Artifact |
|---|------|--------|--------------|----------|
| 1 | Create design document | DONE | Reviewed | `docs/design/07-rate-limiting.md` |
| 2 | Add ratelimit dependency | DONE | pip install | `pyproject.toml` |
| 3 | Create rate_limit module | DONE | mypy strict | `src/hn_herald/rate_limit.py` |
| 4 | Apply to /digest endpoint | DONE | 429 response | `api/routes.py` |
| 5 | Apply to /digest/stream | DONE | 429 response | `api/routes.py` |
| 6 | Write comprehensive tests | DONE | 30 tests | `tests/test_rate_limit.py` |

### MVP-6: Web UI [COMPLETE]

| # | Task | Status | Quality Gate | Artifact |
|---|------|--------|--------------|----------|
| 1 | Create design document | DONE | Reviewed | `docs/design/06-htmx-templates.md` |
| 2 | Create base template | DONE | Types pass | `templates/base.html` |
| 3 | Create digest partial | DONE | HTMX swap | `partials/digest.html` |
| 4 | Create digest form | DONE | Form submit | `partials/digest_form.html` |
| 5 | SSE streaming endpoint | DONE | Real-time updates | `/api/v1/digest/stream` |
| 6 | Loading screen with fun facts | DONE | UX polish | Animated spinner + HN facts |
| 7 | Theme system | DONE | 3 themes | HN Orange, Ocean, Dark |
| 8 | Fix batch summarization | DONE | 100% success | Chunked batches (size=5) |

---

## Completed Milestones

<details>
<summary><strong>MVP-8: Mobile Polish [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Viewport meta tag | Responsive | `base.html` |
| 2 | Touch target sizing | ≥48px | `styles.css`, `article_card.html` |
| 3 | Mobile screenshots | Visual QA | `docs/screenshots/04-mobile-*.png` |
| 4 | Dark theme mobile | Theme system | `05-mobile-dark-theme.png` |

</details>

<details>
<summary><strong>MVP-7: Tag System UI [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Tag selector component | Jinja2 | `partials/tag_selector.html` |
| 2 | Predefined tag categories | Categories | Languages, AI/ML, Web, DevOps |
| 3 | Custom tag creation | Input field | Add button with Enter/comma support |
| 4 | localStorage persistence | Privacy-first | `app.js` saveProfile/loadProfile |
| 5 | Form integration | Hidden input | Tags sent with digest request |

</details>

<details>
<summary><strong>MVP-5: FastAPI Endpoints [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Design document exists | Reviewed | `docs/design/05-fastapi-endpoints.md` |
| 2 | Create API routes | Types pass | `api/routes.py` |
| 3 | Implement POST /api/generate | 15 tests | Digest generation endpoint |
| 4 | Implement GET /api/health | Integration | Health check endpoint |
| 5 | Write API contract tests | 93% coverage | 15 integration tests |

</details>

<details>
<summary><strong>MVP-4: Relevance Scoring [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Create design document | Reviewed | `docs/design/04-relevance-scoring.md` |
| 2 | Create UserProfile model | Types pass | `models/profile.py` |
| 3 | Create RelevanceScore and ScoredArticle models | Types pass | `models/scoring.py` |
| 4 | Implement ScoringService | Lint pass | `services/scoring.py` |
| 5 | Write UserProfile tests | 41 tests | Tag normalization, validation |
| 6 | Write RelevanceScore/ScoredArticle tests | 80 tests | Bounds, properties, filtering |
| 7 | Write ScoringService tests | 65 tests | Tag matching, batch scoring |

</details>

<details>
<summary><strong>MVP-3: LLM Summarization [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Create design document | Reviewed | `docs/design/03-llm-summarization.md` |
| 2 | Create ArticleSummary model | Types pass | `models/summary.py` |
| 3 | Create LLM service | Lint pass | `services/llm.py` |
| 4 | Write integration tests | 11 tests | Real LLM calls |
| 5 | Verify batch summarization | E2E pass | Single + batch working |

</details>

<details>
<summary><strong>MVP-2: Article Extraction [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Create Article model | Types pass | `models/article.py` |
| 2 | Create loader service | Lint pass | `services/loader.py` |
| 3 | Handle problematic domains | Unit tests | Skip Twitter, Reddit, etc. |
| 4 | Add extraction tests | Coverage | Mock external URLs |

</details>

<details>
<summary><strong>MVP-1: HN API Client [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Create design document | Reviewed | `docs/design/01-hn-api-client.md` |
| 2 | Create Story model | Types pass | `models/story.py` |
| 3 | Create HN client service | Lint pass | `services/hn_client.py` |
| 4 | Write unit tests | 68 tests | Mocked responses |
| 5 | Write integration test | Slow marker | Real HN API |

</details>

<details>
<summary><strong>Setup: Project Scaffolding [DONE]</strong></summary>

| # | Task | Quality Gate | Artifact |
|---|------|--------------|----------|
| 1 | Create product.md | Reviewed | `docs/product.md` |
| 2 | Create architecture.md | Reviewed | `docs/architecture.md` |
| 3 | Create tasks.md | Reviewed | This file |
| 4 | Create pyproject.toml | uv sync | Dependencies + tooling |
| 5 | Create Makefile | Commands work | Dev automation |
| 6 | Create .env.example | Documented | Environment template |
| 7 | Create Dockerfile | Build passes | Production container |
| 8 | Create package structure | Import works | `src/hn_herald/*` |
| 9 | Create tests/conftest.py | Fixtures load | Pytest fixtures |
| 10 | Setup pre-commit hooks | Hooks pass | ruff, mypy |
| 11 | Setup GitHub Actions | CI green | lint, typecheck, test |

</details>

---

## Definition of Done

Every MVP must pass before merge:

- [ ] All 8 quality gates passing
- [ ] Test coverage ≥70%
- [ ] Documentation updated
- [ ] tasks.md session handoff updated
- [ ] Pre-commit hooks pass
- [ ] Docker build successful

---

## Quick Reference

### Commands

| Command | Quality Gate | Purpose |
|---------|--------------|---------|
| `make test` | Gate 5 | Run all tests |
| `make lint` | Gate 3 | Run ruff |
| `make typecheck` | Gate 2 | Run mypy |
| `make install` | Setup | Install deps |
| `make dev` | - | Start server |

### Git Workflow

```bash
# Session start
git status && git branch
make test

# Feature branch
git checkout -b feature/mvp-N-name

# Commit (every 15-30 min per XP)
make test && make lint
git add . && git commit -m "feat: description"

# Session end
git push origin feature/name
```

### Commit Types

`feat` | `fix` | `refactor` | `test` | `docs` | `chore`

---

## Key Files

| File | Purpose |
|------|---------|
| `docs/product.md` | Product requirements, XP approach |
| `docs/architecture.md` | Technical design |
| `docs/design/*.md` | MVP design documents |
| `.agentic/config.yml` | Project-specific agentic config |
| `.agentic-framework/` | Reusable agentic patterns |
| `pyproject.toml` | Dependencies, quality gates |
