from __future__ import annotations

from typing import Iterable


class NameSpace:
    KV_STORE_FULL_DOCS = "full_docs"
    KV_STORE_TEXT_CHUNKS = "text_chunks"
    KV_STORE_LLM_RESPONSE_CACHE = "llm_response_cache"

    VECTOR_STORE_ENTITIES = "entities"
    VECTOR_STORE_RELATIONSHIPS = "relationships"
    VECTOR_STORE_CHUNKS = "chunks"

    GRAPH_STORE_CHUNK_ENTITY_RELATION = "chunk_entity_relation"

    DOC_STATUS = "doc_status"

    @staticmethod
    def sanitize_namespace_prefix(prefix: str) -> str:
        """
        Sanitize the namespace prefix to ensure it is safe for use in file systems and database identifiers.
        Replaces unsafe characters such as |, /, \\, etc.
        """
        return prefix.replace("|", "_").replace("/", "_").replace("\\", "_").strip()


def make_namespace(prefix: str, base_namespace: str):
    sanitized_prefix = NameSpace.sanitize_namespace_prefix(prefix)
    return sanitized_prefix + base_namespace


def is_namespace(namespace: str, base_namespace: str | Iterable[str]):
    if isinstance(base_namespace, str):
        return namespace.endswith(base_namespace)
    return any(is_namespace(namespace, ns) for ns in base_namespace)
