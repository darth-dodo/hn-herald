"""Mock data for HN Herald development and testing.

This module provides realistic mock data for the digest generation API,
enabling frontend development without requiring API keys or external services.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from fastapi.responses import StreamingResponse

# Realistic mock articles with varied tech topics
MOCK_ARTICLES = [
    {
        "story_id": 42847291,
        "title": "SQLite Internals: How the World's Most Used Database Engine Works",
        "url": "https://fly.io/blog/sqlite-internals/",
        "hn_url": "https://news.ycombinator.com/item?id=42847291",
        "hn_score": 892,
        "summary": (
            "A deep dive into SQLite's architecture, exploring its B-tree storage "
            "engine, WAL mode for concurrent access, and why it's become the most "
            "deployed database in the world."
        ),
        "key_points": [
            "SQLite uses B-trees for both tables and indexes",
            "WAL enables concurrent reads during writes",
            "The entire database is a single file",
            "ACID compliance via journaling and locking",
        ],
        "tech_tags": ["sqlite", "databases", "storage-engines"],
        "relevance_score": 0.92,
        "relevance_reason": "Relevant for database internals and systems programming",
        "final_score": 0.89,
    },
    {
        "story_id": 42851023,
        "title": "Building Real-Time Collaborative Features with CRDTs",
        "url": "https://jamsocket.com/blog/crdts-for-real-time-collaboration",
        "hn_url": "https://news.ycombinator.com/item?id=42851023",
        "hn_score": 456,
        "summary": (
            "An exploration of CRDTs and how they enable real-time collaboration "
            "without central coordination. Walks through implementing a "
            "collaborative text editor using Yjs."
        ),
        "key_points": [
            "CRDTs allow concurrent edits without conflicts",
            "Yjs is a popular CRDT implementation for JS",
            "No central server required unlike OT",
            "Memory managed with garbage collection",
        ],
        "tech_tags": ["crdts", "distributed-systems", "real-time"],
        "relevance_score": 0.85,
        "relevance_reason": "Useful for building collaborative applications",
        "final_score": 0.82,
    },
    {
        "story_id": 42849876,
        "title": "Rust in the Linux Kernel: One Year Later",
        "url": "https://lwn.net/Articles/rust-kernel-2024/",
        "hn_url": "https://news.ycombinator.com/item?id=42849876",
        "hn_score": 723,
        "summary": (
            "A retrospective on Rust's integration into the Linux kernel. "
            "Discusses early driver implementations, toolchain challenges, "
            "and the cultural shift among kernel developers."
        ),
        "key_points": [
            "Drivers now in Rust: Android Binder, NVMe",
            "Ownership model prevents common kernel bugs",
            "Toolchain integration still needs work",
            "Community adapting to Rust idioms",
        ],
        "tech_tags": ["rust", "linux", "kernel", "systems-programming"],
        "relevance_score": 0.88,
        "relevance_reason": "Essential for systems programming and Rust adoption",
        "final_score": 0.86,
    },
    {
        "story_id": 42852134,
        "title": "The Hidden Complexity of Implementing Unicode Properly",
        "url": "https://tonsky.me/blog/unicode/",
        "hn_url": "https://news.ycombinator.com/item?id=42852134",
        "hn_score": 567,
        "summary": (
            "A guide to Unicode's tricky edge cases. Covers grapheme clusters, "
            "normalization forms, and why 'string length' is surprisingly complex."
        ),
        "key_points": [
            "One character can be multiple code points",
            "Normalization crucial for string comparison",
            "Emoji with skin tones: multiple code points",
            "Most string APIs handle graphemes incorrectly",
        ],
        "tech_tags": ["unicode", "text-processing", "internationalization"],
        "relevance_score": 0.78,
        "relevance_reason": "Important for text processing and i18n work",
        "final_score": 0.76,
    },
    {
        "story_id": 42848567,
        "title": "How We Scaled Our PostgreSQL Database to 10TB",
        "url": "https://blog.cloudflare.com/postgresql-scaling/",
        "hn_url": "https://news.ycombinator.com/item?id=42848567",
        "hn_score": 634,
        "summary": (
            "Cloudflare's journey scaling PostgreSQL to handle massive workloads. "
            "Covers partitioning strategies, connection pooling, and sharding."
        ),
        "key_points": [
            "Table partitioning improves query performance",
            "PgBouncer essential for connection pooling",
            "BRIN indexes better for time-series data",
            "Vacuum tuning prevents bloat",
        ],
        "tech_tags": ["postgresql", "databases", "scaling", "infrastructure"],
        "relevance_score": 0.84,
        "relevance_reason": "Valuable insights for scaling relational databases",
        "final_score": 0.81,
    },
    {
        "story_id": 42850234,
        "title": "WebAssembly Components: A New Era of Portable Software",
        "url": "https://bytecodealliance.org/articles/wasm-components-2024",
        "hn_url": "https://news.ycombinator.com/item?id=42850234",
        "hn_score": 389,
        "summary": (
            "The Component Model brings modularity to WebAssembly, enabling "
            "language-agnostic libraries and secure sandboxing."
        ),
        "key_points": [
            "Components use WIT for explicit interfaces",
            "Link-time virtualization for dependency injection",
            "Capability-based security model",
            "WASI Preview 2 built on Component Model",
        ],
        "tech_tags": ["webassembly", "wasm", "components", "portability"],
        "relevance_score": 0.79,
        "relevance_reason": "Relevant for WebAssembly beyond the browser",
        "final_score": 0.75,
    },
    {
        "story_id": 42853456,
        "title": "Why We Moved from Kubernetes to Nomad",
        "url": "https://blog.example.com/kubernetes-to-nomad",
        "hn_url": "https://news.ycombinator.com/item?id=42853456",
        "hn_score": 512,
        "summary": (
            "A startup's experience migrating from Kubernetes to HashiCorp Nomad, "
            "citing reduced complexity and better resource efficiency."
        ),
        "key_points": [
            "Nomad has gentler learning curve than K8s",
            "Single binary simplifies deployment",
            "Docker and exec drivers cover most cases",
            "40% better resource utilization",
        ],
        "tech_tags": ["kubernetes", "nomad", "devops", "infrastructure"],
        "relevance_score": 0.76,
        "relevance_reason": "Useful for container orchestration decisions",
        "final_score": 0.73,
    },
    {
        "story_id": 42847890,
        "title": "The State of Frontend Build Tools in 2024",
        "url": "https://dev.to/frontend-build-tools-2024",
        "hn_url": "https://news.ycombinator.com/item?id=42847890",
        "hn_score": 445,
        "summary": (
            "Comparison of modern frontend build tools: Vite, esbuild, Turbopack, "
            "and Rspack. Benchmarks and trade-offs between speed and ecosystems."
        ),
        "key_points": [
            "Vite remains most popular for new projects",
            "esbuild powers most tools but lacks HMR",
            "Turbopack promising but still maturing",
            "Rspack offers Webpack compat with Rust speed",
        ],
        "tech_tags": ["frontend", "build-tools", "vite", "javascript"],
        "relevance_score": 0.81,
        "relevance_reason": "Essential for frontend developers choosing build tools",
        "final_score": 0.78,
    },
    {
        "story_id": 42854789,
        "title": "Implementing a Neural Network from Scratch in Python",
        "url": "https://karpathy.github.io/2024/neural-networks-scratch/",
        "hn_url": "https://news.ycombinator.com/item?id=42854789",
        "hn_score": 678,
        "summary": (
            "Andrej Karpathy's walkthrough of implementing a neural network "
            "without frameworks. Covers backprop, gradient descent, and math."
        ),
        "key_points": [
            "Backprop needs only basic chain rule",
            "NumPy sufficient for working neural net",
            "Batch norm and dropout improve training",
            "Forward pass is matrix mults + activations",
        ],
        "tech_tags": ["machine-learning", "neural-networks", "python"],
        "relevance_score": 0.87,
        "relevance_reason": "Excellent for understanding ML fundamentals",
        "final_score": 0.85,
    },
    {
        "story_id": 42855123,
        "title": "GitHub Copilot Alternatives: A Comprehensive Comparison",
        "url": "https://blog.pragmaticengineer.com/copilot-alternatives/",
        "hn_url": "https://news.ycombinator.com/item?id=42855123",
        "hn_score": 534,
        "summary": (
            "In-depth comparison of AI coding assistants: Cursor, Cody, Tabnine, "
            "CodeWhisperer. Evaluates accuracy, latency, privacy, and pricing."
        ),
        "key_points": [
            "Cursor leads for complex multi-file edits",
            "Tabnine best for self-hosted privacy",
            "CodeWhisperer free for individuals",
            "All struggle with niche languages",
        ],
        "tech_tags": ["ai", "coding-assistants", "developer-tools"],
        "relevance_score": 0.83,
        "relevance_reason": "Relevant for evaluating AI coding tools",
        "final_score": 0.80,
    },
]


async def generate_mock_digest_stream(
    profile: Any,
    delay_multiplier: float = 1.0,
) -> StreamingResponse:
    """Generate a mock SSE stream that simulates the real pipeline.

    Args:
        profile: User profile with interests (used for filtering mock data).
        delay_multiplier: Speed up (< 1) or slow down (> 1) the simulation.

    Returns:
        StreamingResponse with SSE events simulating pipeline progress.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        start_time = time.monotonic()

        # Pipeline stages with realistic timing
        stages = [
            ("starting", "Initializing pipeline...", 0.2),
            ("fetch", "Fetching HN stories...", 0.8),
            ("extract", "Extracting article content...", 1.2),
            ("filter", "Filtering articles...", 0.3),
            ("summarize", "Summarizing with AI...", 2.0),
            ("score", "Scoring relevance...", 0.8),
            ("rank", "Ranking articles...", 0.3),
            ("format", "Formatting digest...", 0.2),
        ]

        # Send progress events
        for stage, message, delay in stages:
            event_data = json.dumps({"stage": stage, "message": message})
            yield f"data: {event_data}\n\n"
            await asyncio.sleep(delay * delay_multiplier)

        # Select articles based on max_articles and randomize order slightly
        max_articles = getattr(profile, "max_articles", 5)
        selected_articles = random.sample(
            MOCK_ARTICLES,
            min(max_articles, len(MOCK_ARTICLES)),
        )

        # Sort by final_score descending
        selected_articles.sort(
            key=lambda x: float(x["final_score"]),  # type: ignore[arg-type]
            reverse=True,
        )

        # Calculate mock stats
        generation_time_ms = int((time.monotonic() - start_time) * 1000)

        # Build response matching GenerateDigestResponse structure
        response = {
            "articles": selected_articles,
            "stats": {
                "stories_fetched": 50,
                "articles_extracted": 42,
                "articles_summarized": 38,
                "articles_scored": 35,
                "articles_returned": len(selected_articles),
                "errors": 2,
                "generation_time_ms": generation_time_ms,
            },
            "timestamp": datetime.now(UTC).isoformat(),
            "profile_summary": {
                "interests": getattr(profile, "interest_tags", []),
                "disinterests": getattr(profile, "disinterest_tags", []),
                "min_score": getattr(profile, "min_score", 0.5),
                "max_articles": max_articles,
            },
        }

        # Send completion event
        complete_data = json.dumps({"stage": "complete", "digest": response})
        yield f"data: {complete_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
