"""
This module contains all graph-related routes for the LightRAG API.
"""

from typing import Optional, Any

from fastapi import APIRouter, Depends, Request

from ..utils_api import get_api_key_dependency, get_resolved_namespace, get_rag_from_app

router = APIRouter(tags=["graph"])

# Creates or returns rag instance
async def get_rag(
    request: Request,
    namespace: Optional[str] = Depends(get_resolved_namespace)
) -> Any:
    return await get_rag_from_app(request, namespace)


def create_graph_routes(api_key: Optional[str] = None):
    optional_api_key = get_api_key_dependency(api_key)

    @router.get("/graph/label/list", dependencies=[Depends(optional_api_key)])
    async def get_graph_labels(rag: Any = Depends(get_rag)):
        """
        Get all graph labels

        Returns:
            List[str]: List of graph labels
        """
        return await rag.get_graph_labels()

    @router.get("/graphs", dependencies=[Depends(optional_api_key)])
    async def get_knowledge_graph(label: str, max_depth: int = 3, rag: Any = Depends(get_rag)):
        """
        Retrieve a connected subgraph of nodes where the label includes the specified label.
        Maximum number of nodes is constrained by the environment variable `MAX_GRAPH_NODES` (default: 1000).
        When reducing the number of nodes, the prioritization criteria are as follows:
            1. Label matching nodes take precedence
            2. Followed by nodes directly connected to the matching nodes
            3. Finally, the degree of the nodes
        Maximum number of nodes is limited to env MAX_GRAPH_NODES(default: 1000)

        Args:
            label (str): Label to get knowledge graph for
            max_depth (int, optional): Maximum depth of graph. Defaults to 3.

        Returns:
            Dict[str, List[str]]: Knowledge graph for label
        """
        return await rag.get_knowledge_graph(node_label=label, max_depth=max_depth)

    return router
