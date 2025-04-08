"""
This module contains all the routers for the LightRAG API.
"""

from .document_routes import router as document_router
from .query_routes import router as query_router
from .graph_routes import router as graph_router
from .ollama_api import OllamaAPI


"""
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: This module contains all reply-related routes for the LightRAG API.
 * Owner: TechNexusClarityUtility functions for the LightRAG API.
"""
from .reply_routes_tnc import router as reply_router

__all__ = ["document_router", "query_router", "graph_router", "OllamaAPI", "reply_router"]
