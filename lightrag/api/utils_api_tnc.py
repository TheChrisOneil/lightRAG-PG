"""
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: Utilities for API.
 * Owner: TechNexusClarityUtility functions for the LightRAG API.
"""
import re
import os
import argparse
from typing import Optional, List, Tuple
import sys
from ascii_colors import ASCIIColors
from fastapi import HTTPException, Security, Header, Query, Request

from lightrag.lightrag import LightRAG  
async def get_rag_from_app(request: Request, workspace: Optional[str] = None) -> LightRAG:
    """
    Retrieve a LightRAG instance from FastAPI app state using a factory method.
 
    Args:
        request (Request): The FastAPI request object.
        workspace (Optional[str]): Optional workspace for multi-tenant instantiation.
 
    Returns:
        LightRAG: An initialized LightRAG instance.
    """
    if not hasattr(request.app.state, "rag_factory"):
        raise RuntimeError("rag_factory not found in app.state. Make sure it is set in create_app.")
 
    resolved_workspace = workspace or "default"
    rag_instance = await request.app.state.rag_factory(workspace=resolved_workspace)
    ASCIIColors.green("\nServer is ready to accept connections! 🚀\n")
    return rag_instance

def get_resolved_namespace(
    namespace: Optional[str] = Query(default=None),
    x_namespace: Optional[str] = Header(default=None, alias="X-Namespace"),
) -> Optional[str]:
    """
    Dependency to resolve the effective namespace, checking both query param and header.
    Priority: ?namespace= takes precedence over X-Namespace header.
    """
    workspace = namespace or x_namespace
    if workspace:
        # Sanitize the namespace prefix to ensure it is valid
        workspace = sanitize_namespace_prefix(workspace)
    else:
        # If both are None, use default namespace
        workspace = "default"
    return workspace

#---------------------------------------------------------
# Ensure the namespace prefix is sanitized #TNC
def sanitize_namespace_prefix(name: str) -> str:
        # Replace all non-alphanumeric characters with underscore
        name = re.sub(r'\W+', '_', name)
        # Ensure it doesn't start with a digit (PostgreSQL restriction)
        if name and name[0].isdigit():
            name = f"g_{name}"
        return name