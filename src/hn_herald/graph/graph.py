"""LangGraph StateGraph assembly for digest generation pipeline.

This module creates and compiles the HN Herald digest generation graph,
connecting all nodes with proper edges and enabling parallel article extraction.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from hn_herald.graph.nodes import (
    fetch_article,
    fetch_hn,
    filter_articles,
    format_digest,
    rank_articles,
    score_articles,
    summarize,
)
from hn_herald.graph.state import HNState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


def continue_to_fetch_article(state: HNState) -> list[Any]:
    """Conditional edge that returns Send objects for parallel article extraction.

    This function creates Send objects for each story, enabling parallel
    execution of the fetch_article node.

    Args:
        state: Current graph state with fetched stories.

    Returns:
        List of Send objects, one for each story.
    """
    from langgraph.types import Send

    stories = state.get("stories", [])
    profile = state["profile"]

    return [Send("fetch_article", {"story": story, "profile": profile}) for story in stories]


def create_hn_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create and compile the HN Herald digest generation graph.

    Assembles the StateGraph with all nodes and edges for the digest
    generation pipeline. Enables parallel article extraction using the
    Send pattern via conditional edges.

    Graph structure:
        START → fetch_hn → fetch_article (parallel via Send)
                          → filter → summarize → score → rank → format → END

    Returns:
        Compiled StateGraph ready for invocation with ainvoke().

    Example:
        >>> graph = create_hn_graph()
        >>> result = await graph.ainvoke(initial_state)
        >>> digest = Digest.model_validate(result["digest"])
    """
    logger.debug("create_hn_graph: Building StateGraph")

    # Create graph with HNState schema
    graph = StateGraph(HNState)

    # Add nodes
    graph.add_node("fetch_hn", fetch_hn)
    # fetch_article receives Send-transformed state, not full HNState
    graph.add_node("fetch_article", fetch_article)  # type: ignore[type-var]
    graph.add_node("filter", filter_articles)
    graph.add_node("summarize", summarize)
    graph.add_node("score", score_articles)
    graph.add_node("rank", rank_articles)
    graph.add_node("format", format_digest)

    # Add edges
    # START -> fetch_hn
    graph.add_edge(START, "fetch_hn")

    # fetch_hn -> fetch_article via conditional edge (Send pattern for parallel execution)
    graph.add_conditional_edges("fetch_hn", continue_to_fetch_article)

    # fetch_article -> filter (all parallel extractions complete before filter)
    graph.add_edge("fetch_article", "filter")

    # Linear pipeline after filtering
    graph.add_edge("filter", "summarize")
    graph.add_edge("summarize", "score")
    graph.add_edge("score", "rank")
    graph.add_edge("rank", "format")
    graph.add_edge("format", END)

    # Compile graph
    logger.debug("create_hn_graph: Compiling graph")
    compiled = graph.compile()

    logger.info("create_hn_graph: Graph compiled successfully")
    return compiled
