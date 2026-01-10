# HN Herald - Project Overview

## Purpose
Privacy-first, personalized HackerNews digest application that:
- Fetches top stories from HN API
- Extracts and summarizes articles using AI (Claude)
- Scores relevance based on user interests
- Delivers curated reading experience via mobile-first web UI

## Privacy-First Principles
- No account required
- All preferences stored in browser localStorage
- No tracking, no analytics, no server-side user storage
- Ephemeral processing (content processed in real-time, never stored)

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Templates | Jinja2 |
| Validation | Pydantic v2 |
| HTTP Client | httpx |
| HTML Parsing | BeautifulSoup4, lxml |

### AI/ML (LangChain Ecosystem)
| Component | Technology |
|-----------|------------|
| Orchestration | LangGraph 0.2+ |
| LLM Interface | LangChain-Anthropic |
| Model | Claude Sonnet 4 |
| Observability | LangSmith |
| Caching | Not implemented |
| Output Parsing | PydanticOutputParser |
| Document Loading | WebBaseLoader |
| Text Processing | RecursiveCharacterSplitter |

### Frontend
| Component | Technology |
|-----------|------------|
| Interactivity | HTMX 2.0 |
| Styling | Tailwind CSS 3.4 |
| Icons | Heroicons |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12+ |
| Server | Uvicorn |
| Container | Docker |
| Package Manager | uv |

## Current State
- **Phase**: Project Setup Complete - Ready for MVP-1
- **Test Coverage**: 79% (8 tests passing)
- **CI/CD**: GitHub Actions (lint, typecheck, test, build)
- **Pre-commit**: Configured (ruff, mypy, pre-commit-hooks)

## Key Documentation
- `docs/product.md` - Product requirements and user stories
- `docs/architecture.md` - Technical design and data models
- `tasks.md` - Current state and task tracking
