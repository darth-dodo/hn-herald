"""LangGraph pipeline module for digest generation workflow.

This module provides the main entry point for creating the digest generation
graph. Import create_hn_graph to build and compile the StateGraph.
"""

from hn_herald.graph.graph import create_hn_graph

__all__ = ["create_hn_graph"]
