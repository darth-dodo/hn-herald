# HN Herald - Task Tracking

> **Source of Truth**: This file is the single source of truth for project state.

## Table of Contents

- [How to Use This File](#how-to-use-this-file)
- [XP Programming Flow](#xp-programming-flow)
- [Project Timeline](#project-timeline)
- [Current Work](#current-work)
- [Completed Phases](#completed-phases)
- [Task History Archive](#task-history-archive)
- [Notes for Future Agents](#notes-for-future-agents)

---

## How to Use This File

### Session Start

```bash
# 1. Check current state
cat tasks.md
git status && git branch

# 2. Verify environment
make test  # or uv run pytest

# 3. Create/checkout feature branch
git checkout -b feature/descriptive-name
```

### During Work

- Update task status to 🔄 when starting
- Commit every 15-30 minutes
- Update tasks.md every 30 minutes
- Run quality gates before each commit

### Session End

```bash
# 1. Full validation
make test && make lint

# 2. Update tasks.md with session log

# 3. Final commit
git add . && git commit -m "feat: complete feature X"

# 4. Push
git push origin feature/name
```

---

## XP Programming Flow

| XP Practice              | Task Integration                              |
| ------------------------ | --------------------------------------------- |
| **TDD**                  | Tasks specify test requirements before impl   |
| **Small Steps**          | Tasks decomposed into commit-sized units      |
| **Continuous Integration** | Tasks include quality gate verification     |
| **Collective Ownership** | Tasks assigned to phases, not individuals     |

### Agentic Workflow Phases

1. **Design (Architect)**: Create `docs/design/*.md`
2. **Implementation (Developer)**: TDD with quality gates
3. **Validation (QA)**: Full test suite + coverage check

---

## Project Timeline

| Session   | Deliverable                    | User Value                 | CI/CD Gate            |
| --------- | ------------------------------ | -------------------------- | --------------------- |
| **Setup** | Project scaffolding            | Development ready          | ✅ Complete           |
| **MVP-1** | HN API client + basic fetch    | Can fetch stories          | ✅ Complete           |
| **MVP-2** | Article extraction             | Can read article content   | ✅ Complete           |
| **MVP-3** | LLM summarization              | Get AI summaries           | ⏳ Mock LLM tests     |
| **MVP-4** | Relevance scoring              | Personalized ranking       | ⏳ Scoring accuracy   |
| **MVP-5** | FastAPI endpoints              | API is callable            | ⏳ API contract tests |
| **MVP-6** | HTMX templates                 | Usable web UI              | ⏳ E2E smoke tests    |
| **MVP-7** | Tag system UI                  | Can select interests       | ⏳ Component tests    |
| **MVP-8** | Mobile polish                  | Works on phones            | ⏳ Lighthouse >90     |

---

## Current Work

### Active Tasks

| Task                              | Status | Notes                          |
| --------------------------------- | ------ | ------------------------------ |
| MVP-1 HN API Client               | ✅     | Complete - branch ready for PR |

### Up Next - Priority Tasks

#### 🟠 High Priority (MVP-1: HN API Client) ✅ COMPLETE

| Task                              | Status | Priority | Notes                          |
| --------------------------------- | ------ | -------- | ------------------------------ |
| Create design document            | ✅     | 🟠       | `docs/design/hn-api-client.md` |
| Create models/story.py            | ✅     | 🟠       | Story Pydantic model + StoryType enum |
| Create services/hn_client.py      | ✅     | 🟠       | HN API async client with httpx |
| Create tests for HN client        | ✅     | 🟠       | 68 unit tests with mocked responses |
| Verify HN API fetching works      | ✅     | 🟠       | Integration test (marked slow) |

#### 🟡 Medium Priority (MVP-2: Article Extraction) ✅ COMPLETE

| Task                              | Status | Priority | Notes                          |
| --------------------------------- | ------ | -------- | ------------------------------ |
| Create models/article.py          | ✅     | 🟡       | Article Pydantic model         |
| Create services/loader.py         | ✅     | 🟡       | WebBaseLoader + text splitter  |
| Handle problematic domains        | ✅     | 🟡       | Skip Twitter, Reddit, etc.     |
| Add extraction tests              | ✅     | 🟡       | Mock external URLs             |

#### 🟡 Medium Priority (MVP-3: LLM Summarization)

| Task                              | Status | Priority | Notes                          |
| --------------------------------- | ------ | -------- | ------------------------------ |
| Create design document            | ⏳     | 🟡       | `docs/design/llm-summarization.md` |
| Create ArticleSummary model       | ⏳     | 🟡       | models/summary.py              |
| Create services/llm.py            | ⏳     | 🟡       | Claude integration via Anthropic SDK |
| Write integration tests           | ⏳     | 🟡       | Real LLM calls (no mocking)    |
| Verify summarization works        | ⏳     | 🟡       | Test with real articles        |

---

## Completed Phases

### Phase 0: Project Planning ✅

| Task                              | Status | Notes                          |
| --------------------------------- | ------ | ------------------------------ |
| Create product.md                 | ✅     | PRD with features and stories  |
| Create architecture.md            | ✅     | Technical design with diagrams |
| Initialize git repository         | ✅     | Main branch created            |

### Phase 0.5: Project Setup ✅

| Task                              | Status | Notes                          |
| --------------------------------- | ------ | ------------------------------ |
| Create tasks.md                   | ✅     | Task tracking system           |
| Create .agentic/config.yml        | ✅     | Agentic framework config       |
| Create pyproject.toml             | ✅     | Dependencies + ruff/pytest/mypy|
| Create Makefile                   | ✅     | Dev commands (install/test/lint)|
| Create .env.example               | ✅     | Environment template           |
| Create Dockerfile                 | ✅     | Simple production container    |
| Create src/hn_herald/__init__.py  | ✅     | Package with version           |
| Create src/hn_herald/config.py    | ✅     | Pydantic Settings class        |
| Create src/hn_herald/main.py      | ✅     | FastAPI app + /api/health      |
| Create package structure          | ✅     | api/graph/services/models dirs |
| Create tests/conftest.py          | ✅     | Pytest fixtures                |

### Phase 1: Testing & CI/CD ✅

| Task                              | Status | Notes                          |
| --------------------------------- | ------ | ------------------------------ |
| Write health endpoint tests       | ✅     | 8 tests, 79% coverage          |
| Setup pre-commit hooks            | ✅     | ruff, mypy, pre-commit-hooks   |
| Setup GitHub Actions CI/CD        | ✅     | lint, typecheck, test, build   |
| Update README (product-focused)   | ✅     | Features, quick start, privacy |

---

## Task History Archive

### Session Log: 2026-01-04 (Session 1)

**Session Focus**: Project Setup - Complete Scaffolding with Subagent Orchestration

**Key Decisions**:
1. Using XP development approach with session-based iteration
2. Tasks.md as single source of truth for project state
3. Following agentic framework from `.agentic-framework/`
4. Privacy-first principles (no user tracking, local storage only)
5. Used parallel subagents for faster setup (5 agents in parallel)

**Branch**: `feature/project-setup`

**Artifacts Created**:
- `tasks.md` - Task tracking (this file)
- `.agentic/config.yml` - Project configuration
- `pyproject.toml` - Dependencies with ruff, pytest, mypy config
- `Makefile` - Dev commands (install, dev, test, lint, format, typecheck)
- `.env.example` - Environment template with all variables
- `Dockerfile` - Simple production container
- `src/hn_herald/__init__.py` - Package init with version
- `src/hn_herald/config.py` - Pydantic Settings class
- `src/hn_herald/main.py` - FastAPI app with health check
- `src/hn_herald/api/__init__.py` - API module placeholder
- `src/hn_herald/graph/__init__.py` - Graph module placeholder
- `src/hn_herald/graph/nodes/__init__.py` - Nodes module placeholder
- `src/hn_herald/services/__init__.py` - Services module placeholder
- `src/hn_herald/models/__init__.py` - Models module placeholder
- `src/hn_herald/callbacks/__init__.py` - Callbacks module placeholder
- `tests/__init__.py` - Test package marker
- `tests/conftest.py` - Pytest fixtures (profiles, mock HN data)

**Subagent Orchestration**:
- 5 parallel subagents used for project scaffolding
- python-expert: pyproject.toml
- devops-architect: Makefile, Dockerfile
- backend-architect: .env.example, package structure

**Quality Gates Passed**:
- Project documentation reviewed
- Framework structure understood
- All placeholder files created

**Next Steps**:
- [x] Run `make install` to sync dependencies
- [x] Run `make test` to verify setup
- [ ] Begin MVP-1: HN API Client

### Session Log: 2026-01-04 (Session 2)

**Session Focus**: Testing Infrastructure & CI/CD Setup

**Key Decisions**:
1. Health endpoint tests use pytest fixtures with env vars set before imports
2. Pre-commit hooks with ruff (lint + format) and mypy
3. GitHub Actions CI with 4 jobs: lint, typecheck, test, build
4. No Codecov integration (not needed)

**Branch**: `feature/project-setup` (continued)

**Artifacts Created**:
- `tests/test_api.py` - Health endpoint tests (8 tests)
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.github/workflows/ci.yml` - GitHub Actions CI pipeline
- Updated `README.md` - Product-focused documentation

**Quality Gates Passed**:
- ✅ All 8 tests passing
- ✅ 79% test coverage (threshold: 70%)
- ✅ Ruff linting passes
- ✅ Ruff formatting passes

**Commits**:
- `1a095ef` - feat: complete project setup with FastAPI scaffolding
- `98157eb` - test: add health endpoint tests and CI/CD setup
- `d12df06` - chore: remove Codecov integration from CI

### Session Log: 2026-01-04 (Session 3)

**Session Focus**: MVP-1 Design Phase - HN API Client Architecture

**Agent**: Architect

**Key Decisions**:
1. Use httpx for async HTTP client (already in dependencies)
2. Use tenacity for retry logic with exponential backoff
3. StoryType enum for type-safe story type selection
4. Story Pydantic model with computed `hn_url` property
5. HNClient as async context manager for proper resource cleanup
6. Max 10 concurrent requests to respect HN API

**Artifacts Created**:
- `docs/design/hn-api-client.md` - Comprehensive design document

**Design Highlights**:
- Complete HN API reference documentation
- Data models: Story, StoryType, HNClientError hierarchy
- HNClient interface with async context manager pattern
- Testing strategy: 14 unit tests + 2 integration tests
- Error handling matrix with retry strategies
- Implementation plan: 10 tasks, ~5 hours total

**Quality Gates Passed**:
- ✅ Requirements clearly defined with acceptance criteria
- ✅ Architecture supports scalability and maintainability
- ✅ Data models and interfaces documented
- ✅ Implementation tasks broken into <4h chunks
- ✅ Risks identified with mitigation plans
- ✅ Testing strategy defined

**Next Steps**:
- [x] Hand off to Developer agent for implementation
- [x] Create Story model and StoryType enum
- [x] Implement HNClient with retry logic
- [x] Write unit tests with mocked responses
- [x] Write integration test against real HN API

### Session Log: 2026-01-04 (Session 4)

**Session Focus**: MVP-1 Implementation - HN API Client with Parallel Subagents

**Agent**: Developer (3 parallel subagents)

**Key Decisions**:
1. Used parallel subagents for faster implementation (XP collective ownership)
2. Story model with computed properties (`hn_url`, `has_external_url`)
3. StoryType enum with endpoint property for all HN story types
4. Async HNClient with context manager, retry logic, rate limiting
5. Exception hierarchy: HNClientError → HNAPIError, HNTimeoutError
6. Comprehensive unit tests with respx mocking (68 new tests)

**Branch**: `feature/hn-api-client`

**Artifacts Created**:
- `src/hn_herald/models/story.py` - Story and StoryType models
- `src/hn_herald/services/hn_client.py` - Async HN API client
- `tests/test_models/test_story.py` - 33 Story model tests
- `tests/test_services/test_hn_client.py` - 35 HNClient tests
- Updated `pyproject.toml` - Added httpx/tenacity to mypy overrides
- Updated `.pre-commit-config.yaml` - Added httpx/tenacity deps

**Quality Gates Passed**:
- ✅ 76 tests passing (8 existing + 68 new)
- ✅ Ruff linting passes
- ✅ Mypy type checking passes
- ✅ Pre-commit hooks pass

**Commits**:
- `58a3582` - feat: implement HN API client with Story model and async HTTP client

**Next Steps**:
- [ ] Create PR for feature/hn-api-client
- [ ] Begin MVP-2: Article Extraction

### Session Log: 2026-01-04 (Session 5)

**Session Focus**: MVP-3 Design Phase - LLM Summarization

**Agent**: Architect

**Key Decisions**:
1. Using real LLM calls for integration tests (no mocking)
2. Claude integration via Anthropic SDK
3. ArticleSummary model for structured summary output
4. services/llm.py for LLM service abstraction

**Artifacts Planned**:
- `docs/design/llm-summarization.md` - Design document
- `src/hn_herald/models/summary.py` - ArticleSummary Pydantic model
- `src/hn_herald/services/llm.py` - Claude integration service
- Integration tests with real LLM calls

**Quality Gates**:
- [ ] Design document reviewed
- [ ] Integration tests pass with real LLM
- [ ] Summarization produces useful output

**Next Steps**:
- [ ] Create design document for LLM summarization
- [ ] Implement ArticleSummary model
- [ ] Implement services/llm.py with Claude integration
- [ ] Write and run integration tests

---

## Notes for Future Agents

### Project State

- **Current Phase**: MVP-2 Complete - Ready for MVP-3
- **Test Coverage**: Tests passing (unit + E2E via Playwright MCP)
- **CI/CD**: ✅ GitHub Actions configured (lint, typecheck, test, build)
- **Pre-commit**: ✅ Configured (ruff, mypy, pre-commit-hooks)
- **Dependencies**: ✅ Installed via `make install`
- **Design Docs**: ✅ `docs/design/hn-api-client.md`, `docs/design/article-extraction.md`
- **Completed Artifacts**: `models/story.py`, `models/article.py`, `services/hn_client.py`, `services/loader.py`

### Key Files to Review

| File                              | Purpose                                    |
| --------------------------------- | ------------------------------------------ |
| `docs/product.md`                 | Product requirements and user stories      |
| `docs/architecture.md`            | Technical design and data models           |
| `docs/design/hn-api-client.md`    | MVP-1 HN API client design document        |
| `tasks.md`                        | Current state and task tracking            |
| `.agentic/config.yml`             | Project configuration for agentic workflow |

### Technology Stack

| Component      | Technology        | Purpose                    |
| -------------- | ----------------- | -------------------------- |
| Framework      | FastAPI           | Async REST API             |
| Templates      | Jinja2 + HTMX     | Server-side rendering      |
| Styling        | Tailwind CSS      | Mobile-first CSS           |
| AI Pipeline    | LangGraph         | Orchestration              |
| LLM            | Claude Sonnet     | Summarization and scoring  |
| Observability  | LangSmith         | Tracing and monitoring     |
| Package Mgmt   | uv                | Fast Python dependencies   |

### Privacy-First Principles

- **No Account Required**: Use immediately without signup
- **Local-First Storage**: Preferences in localStorage
- **No Tracking**: No analytics or behavior logging
- **No Server-Side Storage**: User profiles never leave browser
- **Ephemeral Processing**: Article content processed in real-time

### Agent Integration Status

| Agent       | In Flow | Standalone | Notes                              |
| ----------- | ------- | ---------- | ---------------------------------- |
| Architect   | ✅      | ✅         | MVP-1 design complete              |
| Developer   | ✅      | ✅         | MVP-1 implementation complete      |
| QA          | ✅      | ✅         | 76 tests passing                   |
| Writer      | ⏳      | ⏳         | Docs update after MVP              |

---

## Definition of Done

Every task must pass before marking complete:

- [ ] All tests passing (unit, integration)
- [ ] Code reviewed (if applicable)
- [ ] No decrease in test coverage
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] tasks.md updated with status

---

## Quick Reference

### Status Icons

| Icon | Meaning          | When to Use                     |
| ---- | ---------------- | ------------------------------- |
| ✅   | Complete         | Task finished and verified      |
| 🔄   | In Progress      | Currently being worked on       |
| ⏳   | Blocked/Pending  | Waiting on dependency           |
| ❌   | Failed/Cancelled | Task abandoned or failed        |

### Priority Levels

| Level | Label    | Response Time | Examples                         |
| ----- | -------- | ------------- | -------------------------------- |
| 🔴    | Critical | Immediate     | Blocking issues, security        |
| 🟠    | High     | Next sprint   | Major features, core MVP         |
| 🟡    | Medium   | This quarter  | Enhancements, nice-to-haves      |
| 🟢    | Low      | Backlog       | Documentation, minor improvements|

### Commit Types

| Type       | Description                    |
| ---------- | ------------------------------ |
| `feat`     | New feature                    |
| `fix`      | Bug fix                        |
| `refactor` | Code change (no behavior)      |
| `test`     | Adding tests                   |
| `docs`     | Documentation                  |
| `chore`    | Maintenance                    |
