# --------------------------------------------------------------------
"""
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 Refactored by Tech Nexus Clarity and injects the Rag instance into the FastAPI app.
 Created by TechNexusClarity.
 Description: Inserts the Rag instance into the FastAPI app.
 """
from ..utils_api_tnc import get_resolved_namespace, get_rag_from_app
from fastapi import Request, Depends
from lightrag.lightrag import LightRAG 
from typing import Optional
# Creates or returns rag instance
async def get_rag(
    request: Request,
    namespace: Optional[str] = Depends(get_resolved_namespace)
) -> LightRAG:
    return await get_rag_from_app(request, namespace)
# --------------------------------------------------------------------
"""
This module contains all graph-related routes for the LightRAG API.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..utils_api import get_combined_auth_dependency

router = APIRouter(tags=["graph"])


def create_graph_routes(api_key: Optional[str] = None):  # TNC remove rag
    combined_auth = get_combined_auth_dependency(api_key)

    @router.get("/graph/label/list", dependencies=[Depends(combined_auth)])
    async def get_graph_labels(
        rag=Depends(get_rag) # TNC
    ):
        """
        Get all graph labels

        Returns:
            List[str]: List of graph labels
        """
        return await rag.get_graph_labels()

    @router.get("/graphs", dependencies=[Depends(combined_auth)])
    async def get_knowledge_graph(
        label: str = Query(..., description="Label to get knowledge graph for"),
        max_depth: int = Query(3, description="Maximum depth of graph", ge=1),
        max_nodes: int = Query(1000, description="Maximum nodes to return", ge=1),
        rag=Depends(get_rag),
        namespace: Optional[str] = Depends(get_resolved_namespace),
    ):
        """
        Retrieve a connected subgraph of nodes where the label includes the specified label.
        When reducing the number of nodes, the prioritization criteria are as follows:
            1. Hops(path) to the staring node take precedence
            2. Followed by the degree of the nodes

        Args:
            label (str): Label of the starting node
            max_depth (int, optional): Maximum depth of the subgraph,Defaults to 3
            max_nodes: Maxiumu nodes to return

        Returns:
            Dict[str, List[str]]: Knowledge graph for label
        """
        return await rag.get_knowledge_graph(
            node_label=label,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )

    return router
