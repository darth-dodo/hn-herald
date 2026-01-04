# HN Herald

**Your personalized, privacy-first HackerNews digest with AI-powered summaries.**

Stop drowning in links. Get the stories that matter to you, summarized and scored for relevance.

## Why HN Herald?

HackerNews is a firehose of great content, but finding what matters to *you* takes time. HN Herald solves this by:

- **Understanding your interests** through simple tag selection (no account required)
- **Summarizing articles** with AI-generated key points and insights
- **Scoring relevance** based on your profile + community engagement
- **Respecting your privacy** with zero tracking and local-only storage

## Key Features

### Tag-Based Personalization
Select from predefined interest tags or create custom ones:
- **Tech Domains**: AI/ML, Web Development, DevOps, Security, Mobile
- **Topics**: Startups, Career, Open Source, Hardware, Science
- **Languages**: Python, JavaScript, Rust, Go, and more

Your preferences stay in your browser - we never see them.

### AI-Powered Summaries
Each article gets:
- A concise 2-3 sentence summary
- 3-5 key points extracted from the content
- Relevance explanation tailored to your interests

### Smart Ranking
Stories are ranked using a hybrid score:
- **70%** relevance to your selected tags
- **30%** HackerNews community signals (points, comments)

### Mobile-First Design
Built for on-the-go reading with:
- Fast, responsive interface
- Touch-friendly interactions
- Works offline after first load

## Quick Start

```bash
# Clone and install
git clone https://github.com/darth-dodo/ai-adventures.git
cd ai-adventures/hn-herald
make install

# Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the development server
make dev
```

Open [http://localhost:8000](http://localhost:8000) and start reading.

## How It Works

```
HackerNews API --> Fetch Top Stories --> Extract Article Content
                                                |
                                                v
Your Browser <-- Ranked Results <-- AI Scoring <-- AI Summarization
```

1. **Fetch**: Pulls top/new/best stories from HN API
2. **Extract**: Retrieves and processes article content
3. **Summarize**: Claude AI generates summaries and key points
4. **Score**: Matches content against your interest profile
5. **Deliver**: Presents ranked, summarized stories in your browser

## Privacy First

- **No accounts**: Use immediately, no sign-up required
- **No tracking**: Zero analytics, no behavior logging
- **Local storage**: Your preferences never leave your browser
- **Ephemeral processing**: Article content processed in real-time, not stored

## Technology

Built with modern, production-ready tools:

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| AI Pipeline | LangGraph + Claude |
| Frontend | HTMX + Jinja2 + Tailwind |
| Package Manager | uv |

## Development

```bash
make install     # Install dependencies
make dev         # Start dev server with hot reload
make test        # Run test suite (346 tests)
make lint        # Run linting
make typecheck   # Run type checking
```

### Project Status

| Component | Status | Description |
|-----------|--------|-------------|
| HN API Client | ✅ Complete | Async client with retry logic |
| Article Extraction | ✅ Complete | ArticleLoader with blocked domains, content extraction |
| LLM Summarization | ✅ Complete | LangChain-Anthropic with batch support |
| Relevance Scoring | ✅ Complete | Tag-based personalization with 186 tests |
| API Endpoints | 🔄 Next | FastAPI REST API |
| Web UI | ⏳ Planned | HTMX + Tailwind interface |

See [docs/architecture.md](docs/architecture.md) for technical details and [tasks.md](tasks.md) for current progress.

## Contributing

Contributions welcome! Please read the architecture docs first and ensure tests pass before submitting PRs.

## License

MIT
