import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Union, Optional, final
import numpy as np
import configparser

from lightrag.types import KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge

import sys
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    DocProcessingStatus,
    DocStatus,
    DocStatusStorage,
)
from ..namespace import NameSpace, is_namespace
from ..utils import logger

if sys.platform.startswith("win"):
    import asyncio.windows_events
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncpg  # type: ignore
from asyncpg import Pool  # type: ignore

from .postgres_utils import safe_decode_agtype_column

class PostgreSQLDB:
    def __init__(self, config: dict[str, Any], **kwargs: Any):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 5432)
        self.user = config.get("user", "postgres")
        self.password = config.get("password", None)
        self.database = config.get("database", "postgres")
        self.workspace = config.get("workspace", "default")
        self.max = 12
        self.increment = 1
        self.pool: Pool | None = None

        if self.user is None or self.password is None or self.database is None:
            raise ValueError("Missing database user, password, or database")

    async def initdb(self):
        try:
            self.pool = await asyncpg.create_pool(  # type: ignore
                user=self.user,
                password=self.password,
                database=self.database,
                host=self.host,
                port=self.port,
                min_size=1,
                max_size=self.max,
            )

            logger.info(
                f"PostgreSQL, Connected to database at {self.host}:{self.port}/{self.database}"
            )
        except Exception as e:
            logger.error(
                f"PostgreSQL, Failed to connect database at {self.host}:{self.port}/{self.database}, Got:{e}"
            )
            raise


    @staticmethod
    def sanitize_namespace_prefix(name: str) -> str:
        # Replace all non-alphanumeric characters with underscore
        name = re.sub(r'\W+', '_', name)
        # Ensure it doesn't start with a digit (PostgreSQL restriction)
        if name and name[0].isdigit():
            name = f"g_{name}"
        return name

    @staticmethod
    async def configure_age(connection: asyncpg.Connection, graph_name: str) -> None:
        """Set the Apache AGE environment and creates a graph if it does not exist.

        This method:
        - Sets the PostgreSQL `search_path` to include `ag_catalog`, ensuring that Apache AGE functions can be used without specifying the schema.
        - Attempts to create a new graph with the provided `graph_name` if it does not already exist.
        - Silently ignores errors related to the graph already existing.

        """
        try:
            sanitized_name = PostgreSQLDB.sanitize_namespace_prefix(graph_name)
            await connection.execute(  # type: ignore
                'SET search_path = ag_catalog, "$user", public'
            )
            await connection.execute(  # type: ignore
                f"select create_graph('{sanitized_name}')"
            )
        except (
            asyncpg.exceptions.InvalidSchemaNameError,
            asyncpg.exceptions.UniqueViolationError,
        ):
            pass

    
    async def check_tables(self):
        for k, v in TABLES.items():
            try:
                await self.query(f"SELECT 1 FROM {k} LIMIT 1")
            except Exception:
                try:
                    logger.info(f"PostgreSQL, Try Creating table {k} in database")
                    await self.execute(v["ddl"])
                    logger.info(
                        f"PostgreSQL, Creation success table {k} in PostgreSQL database"
                    )
                except Exception as e:
                    logger.error(
                        f"PostgreSQL, Failed to create table {k} in database, Please verify the connection with PostgreSQL database, Got: {e}"
                    )
                    raise e

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        multirows: bool = False,
        with_age: bool = False,
        graph_name: str | None = None,
    ) -> dict[str, Any] | None | list[dict[str, Any]]:
        async with self.pool.acquire() as connection:  # type: ignore
            if with_age and graph_name:
                await self.configure_age(connection, graph_name)  # type: ignore
            elif with_age and not graph_name:
                raise ValueError("Graph name is required when with_age is True")

            try:
                if params:
                    rows = await connection.fetch(sql, *params.values())
                else:
                    rows = await connection.fetch(sql)

                if multirows:
                    if rows:
                        columns = [col for col in rows[0].keys()]
                        data = [dict(zip(columns, row)) for row in rows]
                    else:
                        data = []
                else:
                    if rows:
                        columns = rows[0].keys()
                        data = dict(zip(columns, rows[0]))
                    else:
                        data = None
                return data
            except Exception as e:
                logger.error(f"PostgreSQL database, error:{e}")
                raise

    async def execute(
        self,
        sql: str,
        data: dict[str, Any] | None = None,
        upsert: bool = False,
        with_age: bool = False,
        graph_name: str | None = None,
    ):
        try:
            async with self.pool.acquire() as connection:  # type: ignore
                if with_age and graph_name:
                    await self.configure_age(connection, graph_name)  # type: ignore
                elif with_age and not graph_name:
                    raise ValueError("Graph name is required when with_age is True")

                if data is None:
                    await connection.execute(sql)  # type: ignore
                else:
                    await connection.execute(sql, *data.values())  # type: ignore
        except (
            asyncpg.exceptions.UniqueViolationError,
            asyncpg.exceptions.DuplicateTableError,
        ) as e:
            if upsert:
                print("Key value duplicate, but upsert succeeded.")
            else:
                logger.error(f"Upsert error: {e}")
        except Exception as e:
            logger.error(f"PostgreSQL database,\nsql:{sql},\ndata:{data},\nerror:{e}")
            raise


class ClientManager:
    _instances: dict[str, Any] = {"db": None, "ref_count": 0}
    _lock = asyncio.Lock()

    @classmethod
    def get_config(cls, namespace_prefix: Optional[str] = None, global_config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        config = configparser.ConfigParser()
        config.read("config.ini", "utf-8")

        if global_config is None:
            global_config = {}

        return {
            "host": global_config.get("host") or os.environ.get(
                "POSTGRES_HOST", config.get("postgres", "host", fallback="postgres")
            ),
            "port": global_config.get("port") or os.environ.get(
                "POSTGRES_PORT", config.get("postgres", "port", fallback=5432)
            ),
            "user": global_config.get("user") or os.environ.get(
                "POSTGRES_USER", config.get("postgres", "user", fallback=None)
            ),
            "password": global_config.get("password") or os.environ.get(
                "POSTGRES_PASSWORD", config.get("postgres", "password", fallback=None)
            ),
            "database": global_config.get("database") or os.environ.get(
                "POSTGRES_DB", config.get("postgres", "database", fallback=None)
            ),
            "workspace": PostgreSQLDB.sanitize_namespace_prefix(
                namespace_prefix or global_config.get("workspace") or os.environ.get(
                    "POSTGRES_WORKSPACE", config.get("postgres", "workspace", fallback="default")
                )
            ),
        }

    @classmethod
    async def get_client(cls, namespace_prefix: Optional[str] = None) -> PostgreSQLDB:
        async with cls._lock:
            if cls._instances["db"] is None:
                config = ClientManager.get_config(namespace_prefix=namespace_prefix)
                db = PostgreSQLDB(config)
                await db.initdb()
                await db.check_tables()
                cls._instances["db"] = db
                cls._instances["ref_count"] = 0
            cls._instances["ref_count"] += 1
            return cls._instances["db"]

    @classmethod
    async def release_client(cls, db: PostgreSQLDB):
        async with cls._lock:
            if db is not None:
                if db is cls._instances["db"]:
                    cls._instances["ref_count"] -= 1
                    if cls._instances["ref_count"] == 0:
                        await db.pool.close()
                        logger.info("Closed PostgreSQL database connection pool")
                        cls._instances["db"] = None
                else:
                    await db.pool.close()


@final
@dataclass
class PGKVStorage(BaseKVStorage):
    db: PostgreSQLDB = field(default=None)

    def __post_init__(self):
        namespace_prefix = self.global_config.get("namespace_prefix")
        self.base_namespace = self.namespace.replace(namespace_prefix, "")
        self._max_batch_size = self.global_config["embedding_batch_num"]

    async def initialize(self):
        if self.db is None:
            namespace_prefix = self.global_config.get("namespace_prefix")
            self.db = await ClientManager.get_client(namespace_prefix=namespace_prefix)

    async def finalize(self):
        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    ################ QUERY METHODS ################

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get doc_full data by id."""
        sql = SQL_TEMPLATES["get_by_id_" + self.base_namespace]
        params = {"workspace": self.db.workspace, "id": id}
        if is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
            array_res = await self.db.query(sql, params, multirows=True)
            res = {}
            for row in array_res:
                res[row["id"]] = row
            return res if res else None
        else:
            response = await self.db.query(sql, params)
            return response if response else None

    async def get_by_mode_and_id(self, mode: str, id: str) -> Union[dict, None]:
        """Specifically for llm_response_cache."""
        sql = SQL_TEMPLATES["get_by_mode_id_" + self.base_namespace]
        params = {"workspace": self.db.workspace, mode: mode, "id": id}
        if is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
            array_res = await self.db.query(sql, params, multirows=True)
            res = {}
            for row in array_res:
                res[row["id"]] = row
            return res
        else:
            return None

    # Query by id
    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by id"""
        sql = SQL_TEMPLATES["get_by_ids_" + self.base_namespace].format(
            ids=",".join([f"'{id}'" for id in ids])
        )
        params = {"workspace": self.db.workspace}
        if is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
            array_res = await self.db.query(sql, params, multirows=True)
            modes = set()
            dict_res: dict[str, dict] = {}
            for row in array_res:
                modes.add(row["mode"])
            for mode in modes:
                if mode not in dict_res:
                    dict_res[mode] = {}
            for row in array_res:
                dict_res[row["mode"]][row["id"]] = row
            return [{k: v} for k, v in dict_res.items()]
        else:
            return await self.db.query(sql, params, multirows=True)

    async def get_by_status(self, status: str) -> Union[list[dict[str, Any]], None]:
        """Specifically for llm_response_cache."""
        SQL = SQL_TEMPLATES["get_by_status_" + self.base_namespace]
        params = {"workspace": self.db.workspace, "status": status}
        return await self.db.query(SQL, params, multirows=True)

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        sql = SQL_TEMPLATES["filter_keys"].format(
            table_name=namespace_to_table_name(self.namespace),
            ids=",".join([f"'{id}'" for id in keys]),
        )
        params = {"workspace": self.db.workspace}
        try:
            res = await self.db.query(sql, params, multirows=True)
            if res:
                exist_keys = [key["id"] for key in res]
            else:
                exist_keys = []
            new_keys = set([s for s in keys if s not in exist_keys])
            return new_keys
        except Exception as e:
            logger.error(
                f"PostgreSQL database,\nsql:{sql},\nparams:{params},\nerror:{e}"
            )
            raise

    ################ INSERT METHODS ################
    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        logger.info(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        if is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
            pass
        elif is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
            for k, v in data.items():
                upsert_sql = SQL_TEMPLATES["upsert_doc_full"]
                _data = {
                    "id": k,
                    "content": v["content"],
                    "workspace": self.db.workspace,
                }
                await self.db.execute(upsert_sql, _data)
        elif is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
            for mode, items in data.items():
                for k, v in items.items():
                    upsert_sql = SQL_TEMPLATES["upsert_llm_response_cache"]
                    _data = {
                        "workspace": self.db.workspace,
                        "id": k,
                        "original_prompt": v["original_prompt"],
                        "return_value": v["return"],
                        "mode": mode,
                    }

                    await self.db.execute(upsert_sql, _data)

    async def index_done_callback(self) -> None:
        # PG handles persistence automatically
        pass

    async def drop(self) -> None:
        """Drop the storage"""
        drop_sql = SQL_TEMPLATES["drop_all"]
        await self.db.execute(drop_sql)


@final
@dataclass
class PGVectorStorage(BaseVectorStorage):
    db: PostgreSQLDB | None = field(default=None)

    def __post_init__(self):
        self._max_batch_size = self.global_config["embedding_batch_num"]
        namespace_prefix = self.global_config.get("namespace_prefix")
        self.base_namespace = self.namespace.replace(namespace_prefix, "")
        config = self.global_config.get("vector_db_storage_cls_kwargs", {})
        cosine_threshold = config.get("cosine_better_than_threshold")
        if cosine_threshold is None:
            raise ValueError(
                "cosine_better_than_threshold must be specified in vector_db_storage_cls_kwargs"
            )
        self.cosine_better_than_threshold = cosine_threshold

    async def initialize(self):
        if self.db is None:
            namespace_prefix = self.global_config.get("namespace_prefix")
            self.db = await ClientManager.get_client(namespace_prefix=namespace_prefix)

    async def finalize(self):
        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    def _upsert_chunks(self, item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        try:
            upsert_sql = SQL_TEMPLATES["upsert_chunk"]
            data: dict[str, Any] = {
                "workspace": self.db.workspace,
                "id": item["__id__"],
                "tokens": item["tokens"],
                "chunk_order_index": item["chunk_order_index"],
                "full_doc_id": item["full_doc_id"],
                "content": item["content"],
                "content_vector": json.dumps(item["__vector__"].tolist()),
            }
        except Exception as e:
            logger.error(f"Error to prepare upsert,\nsql: {e}\nitem: {item}")
            raise

        return upsert_sql, data

    def _upsert_entities(self, item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        upsert_sql = SQL_TEMPLATES["upsert_entity"]
        data: dict[str, Any] = {
            "workspace": self.db.workspace,
            "id": item["__id__"],
            "entity_name": item["entity_name"],
            "content": item["content"],
            "content_vector": json.dumps(item["__vector__"].tolist()),
        }
        return upsert_sql, data

    def _upsert_relationships(self, item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        upsert_sql = SQL_TEMPLATES["upsert_relationship"]
        data: dict[str, Any] = {
            "workspace": self.db.workspace,
            "id": item["__id__"],
            "source_id": item["src_id"],
            "target_id": item["tgt_id"],
            "content": item["content"],
            "content_vector": json.dumps(item["__vector__"].tolist()),
        }
        return upsert_sql, data

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        logger.info(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        current_time = time.time()
        list_data = [
            {
                "__id__": k,
                "__created_at__": current_time,
                **{k1: v1 for k1, v1 in v.items()},
            }
            for k, v in data.items()
        ]
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]

        embedding_tasks = [self.embedding_func(batch) for batch in batches]
        embeddings_list = await asyncio.gather(*embedding_tasks)

        embeddings = np.concatenate(embeddings_list)
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]
        for item in list_data:
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                upsert_sql, data = self._upsert_chunks(item)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                upsert_sql, data = self._upsert_entities(item)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                upsert_sql, data = self._upsert_relationships(item)
            else:
                raise ValueError(f"{self.namespace} is not supported")

            await self.db.execute(upsert_sql, data)

    #################### query method ###############
    async def query(self, query: str, top_k: int) -> list[dict[str, Any]]:
        embeddings = await self.embedding_func([query])
        embedding = embeddings[0]
        embedding_string = ",".join(map(str, embedding))

        sql = SQL_TEMPLATES[self.base_namespace].format(
            embedding_string=embedding_string
        )
        params = {
            "workspace": self.db.workspace,
            "better_than_threshold": self.cosine_better_than_threshold,
            "top_k": top_k,
        }
        results = await self.db.query(sql, params=params, multirows=True)
        return results

    async def index_done_callback(self) -> None:
        # PG handles persistence automatically
        pass

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors with specified IDs from the storage.

        Args:
            ids: List of vector IDs to be deleted
        """
        if not ids:
            return

        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for vector deletion: {self.namespace}")
            return

        ids_list = ",".join([f"'{id}'" for id in ids])
        delete_sql = (
            f"DELETE FROM {table_name} WHERE workspace=$1 AND id IN ({ids_list})"
        )

        try:
            await self.db.execute(delete_sql, {"workspace": self.db.workspace})
            logger.debug(
                f"Successfully deleted {len(ids)} vectors from {self.namespace}"
            )
        except Exception as e:
            logger.error(f"Error while deleting vectors from {self.namespace}: {e}")

    async def delete_entity(self, entity_name: str) -> None:
        """Delete an entity by its name from the vector storage.

        Args:
            entity_name: The name of the entity to delete
        """
        try:
            # Construct SQL to delete the entity
            delete_sql = """DELETE FROM LIGHTRAG_VDB_ENTITY
                            WHERE workspace=$1 AND entity_name=$2"""

            await self.db.execute(
                delete_sql, {"workspace": self.db.workspace, "entity_name": entity_name}
            )
            logger.debug(f"Successfully deleted entity {entity_name}")
        except Exception as e:
            logger.error(f"Error deleting entity {entity_name}: {e}")

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity.

        Args:
            entity_name: The name of the entity whose relations should be deleted
        """
        try:
            # Delete relations where the entity is either the source or target
            delete_sql = """DELETE FROM LIGHTRAG_VDB_RELATION
                            WHERE workspace=$1 AND (source_id=$2 OR target_id=$2)"""

            await self.db.execute(
                delete_sql, {"workspace": self.db.workspace, "entity_name": entity_name}
            )
            logger.debug(f"Successfully deleted relations for entity {entity_name}")
        except Exception as e:
            logger.error(f"Error deleting relations for entity {entity_name}: {e}")


@final
@dataclass
class PGDocStatusStorage(DocStatusStorage):
    db: PostgreSQLDB = field(default=None)

    async def initialize(self):
        if self.db is None:
            self.db = await ClientManager.get_client()

    async def finalize(self):
        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        sql = SQL_TEMPLATES["filter_keys"].format(
            table_name=namespace_to_table_name(self.namespace),
            ids=",".join([f"'{id}'" for id in keys]),
        )
        params = {"workspace": self.db.workspace}
        try:
            res = await self.db.query(sql, params, multirows=True)
            if res:
                exist_keys = [key["id"] for key in res]
            else:
                exist_keys = []
            new_keys = set([s for s in keys if s not in exist_keys])
            print(f"keys: {keys}")
            print(f"new_keys: {new_keys}")
            return new_keys
        except Exception as e:
            logger.error(
                f"PostgreSQL database,\nsql:{sql},\nparams:{params},\nerror:{e}"
            )
            raise

    async def get_by_id(self, id: str) -> Union[dict[str, Any], None]:
        sql = "select * from LIGHTRAG_DOC_STATUS where workspace=$1 and id=$2"
        params = {"workspace": self.db.workspace, "id": id}
        result = await self.db.query(sql, params, True)
        if result is None or result == []:
            return None
        else:
            return DocProcessingStatus(
                content=result[0]["content"],
                content_length=result[0]["content_length"],
                content_summary=result[0]["content_summary"],
                status=result[0]["status"],
                chunks_count=result[0]["chunks_count"],
                created_at=result[0]["created_at"],
                updated_at=result[0]["updated_at"],
            )

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by id"""
        raise NotImplementedError

    async def get_status_counts(self) -> dict[str, int]:
        """Get counts of documents in each status"""
        sql = """SELECT status as "status", COUNT(1) as "count"
                   FROM LIGHTRAG_DOC_STATUS
                  where workspace=$1 GROUP BY STATUS
                 """
        result = await self.db.query(sql, {"workspace": self.db.workspace}, True)
        counts = {}
        for doc in result:
            counts[doc["status"]] = doc["count"]
        return counts

    async def get_docs_by_status(
        self, status: DocStatus
    ) -> dict[str, DocProcessingStatus]:
        """all documents with a specific status"""
        sql = "select * from LIGHTRAG_DOC_STATUS where workspace=$1 and status=$2"
        params = {"workspace": self.db.workspace, "status": status.value}
        result = await self.db.query(sql, params, True)
        docs_by_status = {
            element["id"]: DocProcessingStatus(
                content=result[0]["content"],
                content_summary=element["content_summary"],
                content_length=element["content_length"],
                status=element["status"],
                created_at=element["created_at"],
                updated_at=element["updated_at"],
                chunks_count=element["chunks_count"],
            )
            for element in result
        }
        return docs_by_status

    async def index_done_callback(self) -> None:
        # PG handles persistence automatically
        pass

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Update or insert document status

        Args:
            data: dictionary of document IDs and their status data
        """
        logger.info(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        sql = """insert into LIGHTRAG_DOC_STATUS(workspace,id,content,content_summary,content_length,chunks_count,status)
                 values($1,$2,$3,$4,$5,$6,$7)
                  on conflict(id,workspace) do update set
                  content = EXCLUDED.content,
                  content_summary = EXCLUDED.content_summary,
                  content_length = EXCLUDED.content_length,
                  chunks_count = EXCLUDED.chunks_count,
                  status = EXCLUDED.status,
                  updated_at = CURRENT_TIMESTAMP"""
        for k, v in data.items():
            # chunks_count is optional
            await self.db.execute(
                sql,
                {
                    "workspace": self.db.workspace,
                    "id": k,
                    "content": v["content"],
                    "content_summary": v["content_summary"],
                    "content_length": v["content_length"],
                    "chunks_count": v["chunks_count"] if "chunks_count" in v else -1,
                    "status": v["status"],
                },
            )

    async def drop(self) -> None:
        """Drop the storage"""
        drop_sql = SQL_TEMPLATES["drop_doc_full"]
        await self.db.execute(drop_sql)


class PGGraphQueryException(Exception):
    """Exception for the AGE queries."""

    def __init__(self, exception: Union[str, dict[str, Any]]) -> None:
        if isinstance(exception, dict):
            self.message = exception["message"] if "message" in exception else "unknown"
            self.details = exception["details"] if "details" in exception else "unknown"
        else:
            self.message = exception
            self.details = "unknown"

    def get_message(self) -> str:
        return self.message

    def get_details(self) -> Any:
        return self.details


@final
@dataclass
class PGGraphStorage(BaseGraphStorage):
    def __post_init__(self):
        self.graph_name = self.namespace or os.environ.get("AGE_GRAPH_NAME", "lightrag")
        self._node_embed_algorithms = {
            "node2vec": self._node2vec_embed,
        }
        self.db: PostgreSQLDB | None = None

    async def initialize(self):
        if self.db is None:
            self.db = await ClientManager.get_client(namespace_prefix=None)

    async def finalize(self):
        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    async def index_done_callback(self) -> None:
        # PG handles persistence automatically
        pass

    @staticmethod
    def _record_to_dict(record: asyncpg.Record) -> dict[str, Any]:
        """
        Convert a record returned from an age query to a dictionary
 
        Args:
            record (): a record from an age query result
 
        Returns:
            dict[str, Any]: a dictionary representation of the record where
                the dictionary key is the field name and the value is the
                value converted to a python type
        """
        # result holder
        d = {}
 
        # prebuild a mapping of vertex_id to vertex mappings to be used
        # later to build edges
        vertices = {}
        for k in record.keys():
            v = record[k]
            dtype = ""
            try:
                formatted_value = json.dumps(json.loads(re.sub(r'::[^,\\]]*(?=[,\\]])', ']', v)), indent=2)
                logger.debug(f"vertex Processing column '{k}' with value:\n{formatted_value}")
            except Exception:
                logger.debug(f"vertex Processing column '{k}' with value: {repr(v)}")
            # agtype comes back '{key: value}::type' which must be parsed
            if isinstance(v, str) and "::" in v:
                import re
                v = re.sub(r'::[^,\]]*(?=[,\]])', ']', v)  #TODO fix why v is missing the last bracket
                dtype_match = re.search(r"::([^\s,\]]+)", v)
                dtype = dtype_match.group(1) if dtype_match else ""
                # logger.debug(f"Post Processing column '{k}' with value: {repr(v)}")
                if dtype == "vertex":
                    try:
                        # logger.debug(f"Attempting to decode vertex JSON from column '{k}': {repr(v)}")
                        vertex = json.loads(v)
                        vertices[vertex["id"]] = vertex.get("properties", {})
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode vertex JSON in column '{k}': {v}. Error: {e}")
                        continue
 
        for column in record.keys():
            value = record[column]
            dtype = ""
            try:
                logger.debug(f"vertex, node, other Processing column '{column}' with value:\n{json.dumps(json.loads(value), indent=2)}")
            except Exception:
                logger.debug(f"vertex, node, other Processing column '{column}' with value: {repr(value)}")
            if isinstance(value, str) and "::" in value:
                dtype_match = re.search(r"::([^\s,\]]+)", value)
                dtype = dtype_match.group(1) if dtype_match else ""
                value = re.sub(r'::[^,\]]*(?=[,\]])', '', value)
            # logger.debug(f"Post Processing dtype '{dtype}' column '{column}' with value: {repr(value)}")
            try:
                if dtype == "vertex":
                    if isinstance(value, str):
                        value = json.loads(value)
                    if isinstance(value, list):
                        processed = []
                        for vertex in value:
                            if isinstance(vertex, dict):
                                processed.append(vertex.get("properties", {}))
                        d[column] = processed
                    elif isinstance(value, dict):
                        d[column] = value.get("properties", {})
                    else:
                        d[column] = value
                elif dtype == "edge":
                    if isinstance(value, str):
                        value = json.loads(value)
                    if isinstance(value, list):
                        processed = []
                        for edge in value:
                            if isinstance(edge, dict):
                                edge_dict = {
                                    "id": edge.get("id"),
                                    "label": edge.get("label"),
                                    "start_id": edge.get("start_id"),
                                    "end_id": edge.get("end_id"),
                                    "properties": edge.get("properties", {})
                                }
                                processed.append(edge_dict)
                        d[column] = processed
                    elif isinstance(value, dict):
                        edge_dict = {
                            "id": value.get("id"),
                            "label": value.get("label"),
                            "start_id": value.get("start_id"),
                            "end_id": value.get("end_id"),
                            "properties": value.get("properties", {})
                        }
                        d[column] = edge_dict
                    else:
                        d[column] = safe_decode_agtype_column(value, column) if isinstance(value, str) and value.strip() else value
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON in column '{column}': {value}. Error: {e}")
                d[column] = value
 
        return d

    @staticmethod
    def _format_properties(
        properties: dict[str, Any], _id: Union[str, None] = None
    ) -> str:
        """
        Convert a dictionary of properties to a string representation that
        can be used in a cypher query insert/merge statement.

        Args:
            properties (dict[str,str]): a dictionary containing node/edge properties
            _id (Union[str, None]): the id of the node or None if none exists

        Returns:
            str: the properties dictionary as a properly formatted string
        """
        props = []
        # wrap property key in backticks to escape
        for k, v in properties.items():
            prop = f"`{k}`: {json.dumps(v)}"
            props.append(prop)
        if _id is not None and "id" not in properties:
            props.append(
                f"id: {json.dumps(_id)}" if isinstance(_id, str) else f"id: {_id}"
            )
        return "{" + ", ".join(props) + "}"

    @staticmethod
    def _encode_graph_label(label: str) -> str:
        """
        Since AGE supports only alphanumerical labels, we will encode generic label as HEX string

        Args:
            label (str): the original label

        Returns:
            str: the encoded label
        """
        return "x" + label.encode().hex()

    @staticmethod
    def _decode_graph_label(encoded_label: str) -> str:
        """
        Since AGE supports only alphanumerical labels, we will encode generic label as HEX string
 
        Args:
            encoded_label (str): the encoded label
 
        Returns:
            str: the decoded label
        """
        if not isinstance(encoded_label, str):
            encoded_label = str(encoded_label)

        try:
            return bytes.fromhex(encoded_label.removeprefix("x")).decode()
        except (ValueError, AttributeError):
            logger.warning(f"Could not decode graph label: {encoded_label}")
            return str(encoded_label)

    @staticmethod
    def _get_col_name(field: str, idx: int) -> str:
        """
        Convert a cypher return field to a pgsql select field
        If possible keep the cypher column name, but create a generic name if necessary

        Args:
            field (str): a return field from a cypher query to be formatted for pgsql
            idx (int): the position of the field in the return statement

        Returns:
            str: the field to be used in the pgsql select statement
        """
        # remove white space
        field = field.strip()
        # if an alias is provided for the field, use it
        if " as " in field:
            return field.split(" as ")[-1].strip()
        # if the return value is an unnamed primitive, give it a generic name
        if field.isnumeric() or field in ("true", "false", "null"):
            return f"column_{idx}"
        # otherwise return the value stripping out some common special chars
        return field.replace("(", "_").replace(")", "")

    async def _query(
        self,
        query: str,
        readonly: bool = True,
        upsert: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Query the graph by taking a cypher query, converting it to an
        age compatible query, executing it and converting the result

        Args:
            query (str): a cypher query to be executed
            params (dict): parameters for the query

        Returns:
            list[dict[str, Any]]: a list of dictionaries containing the result set
        """
        try:
            if readonly:
                data = await self.db.query(
                    query,
                    multirows=True,
                    with_age=True,
                    graph_name=self.graph_name,
                )
            else:
                data = await self.db.execute(
                    query,
                    upsert=upsert,
                    with_age=True,
                    graph_name=self.graph_name,
                )

        except Exception as e:
            raise PGGraphQueryException(
                {
                    "message": f"Error executing graph query: {query}",
                    "wrapped": query,
                    "detail": str(e),
                }
            ) from e

        if data is None:
            result = []
        # decode records
        else:
            result = [self._record_to_dict(d) for d in data]

        return result

    async def has_node(self, node_id: str) -> bool:
        entity_name_label = self._encode_graph_label(node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity {node_id: "%s"})
                     RETURN count(n) > 0 AS node_exists
                   $$) AS (node_exists bool)""" % (self.graph_name, entity_name_label)

        single_result = (await self._query(query))[0]

        return single_result["node_exists"]

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        src_label = self._encode_graph_label(source_node_id.strip('"'))
        tgt_label = self._encode_graph_label(target_node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (a:Entity {node_id: "%s"})-[r]-(b:Entity {node_id: "%s"})
                     RETURN COUNT(r) > 0 AS edge_exists
                   $$) AS (edge_exists bool)""" % (
            self.graph_name,
            src_label,
            tgt_label,
        )

        single_result = (await self._query(query))[0]

        return single_result["edge_exists"]

    async def get_node(self, node_id: str) -> dict[str, str] | None:
        label = self._encode_graph_label(node_id.strip('"'))
        query = """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity {node_id: "%s"})
                     RETURN n
                   $$) AS (n agtype)""" % (self.graph_name, label)
        record = await self._query(query)
        if record:
            node = record[0]
            node_dict = node["n"]

            return node_dict
        return None

    async def node_degree(self, node_id: str) -> int:
        label = self._encode_graph_label(node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity {node_id: "%s"})-[]->(x)
                     RETURN count(x) AS total_edge_count
                   $$) AS (total_edge_count integer)""" % (self.graph_name, label)
        record = (await self._query(query))[0]
        if record:
            edge_count = int(record["total_edge_count"])

            return edge_count

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        src_degree = await self.node_degree(src_id)
        trg_degree = await self.node_degree(tgt_id)

        # Convert None to 0 for addition
        src_degree = 0 if src_degree is None else src_degree
        trg_degree = 0 if trg_degree is None else trg_degree

        degrees = int(src_degree) + int(trg_degree)

        return degrees

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> dict[str, str] | None:
        src_label = self._encode_graph_label(source_node_id.strip('"'))
        tgt_label = self._encode_graph_label(target_node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (a:Entity {node_id: "%s"})-[r]->(b:Entity {node_id: "%s"})
                     RETURN properties(r) as edge_properties
                     LIMIT 1
                   $$) AS (edge_properties agtype)""" % (
            self.graph_name,
            src_label,
            tgt_label,
        )
        record = await self._query(query)
        if record and record[0] and record[0]["edge_properties"]:
            result = record[0]["edge_properties"]

            return result

    async def get_node_edges(self, source_node_id: str) -> list[tuple[str, str]] | None:
        """
        Retrieves all edges (relationships) for a particular node identified by its label.
        :return: list of dictionaries containing edge information
        """
        label = self._encode_graph_label(source_node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                      MATCH (n:Entity {node_id: "%s"})
                      OPTIONAL MATCH (n)-[]-(connected)
                      RETURN n, connected
                    $$) AS (n agtype, connected agtype)""" % (
            self.graph_name,
            label,
        )

        results = await self._query(query)
        edges = []
        for record in results:
            source_node = record["n"] if record["n"] else None
            connected_node = record["connected"] if record["connected"] else None

            source_label = (
                source_node["node_id"]
                if source_node and source_node["node_id"]
                else None
            )
            target_label = (
                connected_node["node_id"]
                if connected_node and connected_node["node_id"]
                else None
            )

            if source_label and target_label:
                edges.append(
                    (
                        self._decode_graph_label(source_label),
                        self._decode_graph_label(target_label),
                    )
                )

        return edges

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((PGGraphQueryException,)),
    )
    async def upsert_node(self, node_id: str, node_data: dict[str, str]) -> None:
        label = self._encode_graph_label(node_id.strip('"'))
        properties = node_data

        query = """SELECT * FROM cypher('%s', $$
                     MERGE (n:Entity {node_id: "%s"})
                     SET n += %s
                     RETURN n
                   $$) AS (n agtype)""" % (
            self.graph_name,
            label,
            self._format_properties(properties),
        )

        try:
            await self._query(query, readonly=False, upsert=True)

        except Exception as e:
            logger.error("POSTGRES, Error during upsert: {%s}", e)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((PGGraphQueryException,)),
    )
    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ) -> None:
        """
        Upsert an edge and its properties between two nodes identified by their labels.

        Args:
            source_node_id (str): Label of the source node (used as identifier)
            target_node_id (str): Label of the target node (used as identifier)
            edge_data (dict): dictionary of properties to set on the edge
        """
        src_label = self._encode_graph_label(source_node_id.strip('"'))
        tgt_label = self._encode_graph_label(target_node_id.strip('"'))
        edge_properties = edge_data

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (source:Entity {node_id: "%s"})
                     WITH source
                     MATCH (target:Entity {node_id: "%s"})
                     MERGE (source)-[r:DIRECTED]->(target)
                     SET r += %s
                     RETURN r
                   $$) AS (r agtype)""" % (
            self.graph_name,
            src_label,
            tgt_label,
            self._format_properties(edge_properties),
        )

        try:
            await self._query(query, readonly=False, upsert=True)

        except Exception as e:
            logger.error("Error during edge upsert: {%s}", e)
            raise

    async def _node2vec_embed(self):
        print("Implemented but never called.")

    async def delete_node(self, node_id: str) -> None:
        """
        Delete a node from the graph.

        Args:
            node_id (str): The ID of the node to delete.
        """
        label = self._encode_graph_label(node_id.strip('"'))

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity {node_id: "%s"})
                     DETACH DELETE n
                   $$) AS (n agtype)""" % (self.graph_name, label)

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error("Error during node deletion: {%s}", e)
            raise

    async def remove_nodes(self, node_ids: list[str]) -> None:
        """
        Remove multiple nodes from the graph.

        Args:
            node_ids (list[str]): A list of node IDs to remove.
        """
        encoded_node_ids = [
            self._encode_graph_label(node_id.strip('"')) for node_id in node_ids
        ]
        node_id_list = ", ".join([f'"{node_id}"' for node_id in encoded_node_ids])

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity)
                     WHERE n.node_id IN [%s]
                     DETACH DELETE n
                   $$) AS (n agtype)""" % (self.graph_name, node_id_list)

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error("Error during node removal: {%s}", e)
            raise

    async def remove_edges(self, edges: list[tuple[str, str]]) -> None:
        """
        Remove multiple edges from the graph.

        Args:
            edges (list[tuple[str, str]]): A list of edges to remove, where each edge is a tuple of (source_node_id, target_node_id).
        """
        encoded_edges = [
            (
                self._encode_graph_label(src.strip('"')),
                self._encode_graph_label(tgt.strip('"')),
            )
            for src, tgt in edges
        ]
        edge_list = ", ".join([f'["{src}", "{tgt}"]' for src, tgt in encoded_edges])

        query = """SELECT * FROM cypher('%s', $$
                     MATCH (a:Entity)-[r]->(b:Entity)
                     WHERE [a.node_id, b.node_id] IN [%s]
                     DELETE r
                   $$) AS (r agtype)""" % (self.graph_name, edge_list)

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error("Error during edge removal: {%s}", e)
            raise

    async def get_all_labels(self) -> list[str]:
        """
        Get all labels (node IDs) in the graph.

        Returns:
            list[str]: A list of all labels in the graph.
        """
        query = (
            """SELECT * FROM cypher('%s', $$
                     MATCH (n:Entity)
                     RETURN DISTINCT n.node_id AS label
                   $$) AS (label text)"""
            % self.graph_name
        )

        results = await self._query(query)
        labels = []
        for result in results:
            try:
                labels.append(self._decode_graph_label(result["label"]))
            except Exception as e:
                logger.warning(f"Failed to decode label: {result['label']}. Error: {e}")
        return labels

    async def embed_nodes(
        self, algorithm: str
    ) -> tuple[np.ndarray[Any, Any], list[str]]:
        """
        Generate node embeddings using the specified algorithm.

        Args:
            algorithm (str): The name of the embedding algorithm to use.

        Returns:
            tuple[np.ndarray[Any, Any], list[str]]: A tuple containing the embeddings and the corresponding node IDs.
        """
        if algorithm not in self._node_embed_algorithms:
            raise ValueError(f"Unsupported embedding algorithm: {algorithm}")

        embed_func = self._node_embed_algorithms[algorithm]
        return await embed_func()

    async def get_knowledge_graph(
        self, node_label: str, max_depth: int = 5
    ) -> KnowledgeGraph:
        """
        Retrieve a subgraph containing the specified node and its neighbors up to the specified depth.

        Args:
            node_label (str): The label of the node to start from. If "*", the entire graph is returned.
            max_depth (int): The maximum depth to traverse from the starting node.

        Returns:
            KnowledgeGraph: The retrieved subgraph.
        """
        MAX_GRAPH_NODES = 1000

        if node_label == "*":
            query = """SELECT * FROM cypher('%s', $$
                         MATCH (n:Entity)
                         OPTIONAL MATCH (n)-[r]->(m:Entity)
                         RETURN n, r, m
                         LIMIT %d
                       $$) AS (n agtype, r agtype, m agtype)""" % (
                self.graph_name,
                MAX_GRAPH_NODES,
            )
        else:
            encoded_node_label = self._encode_graph_label(node_label.strip('"'))
            query = """SELECT * FROM cypher('%s', $$
                         MATCH (n:Entity {node_id: "%s"})
                         OPTIONAL MATCH p = (n)-[*..%d]-(m)
                         RETURN nodes(p) AS nodes, relationships(p) AS relationships
                         LIMIT %d
                       $$) AS (nodes agtype, relationships agtype)""" % (
                self.graph_name,
                encoded_node_label,
                max_depth,
                MAX_GRAPH_NODES,
            )

        results = await self._query(query)
        logger.debug(f"------------------------------------------")
        logger.debug(f"Graph query results:\n{json.dumps(results, indent=2)}")
        nodes_by_id = {}
        edges = []

        for result in results:
            if node_label == "*":
                if result.get("n"):
                    node = result["n"]
                    node_id = self._decode_graph_label(node.get("node_id", ""))
                    node_obj = KnowledgeGraphNode(
                        id=node_id,
                        labels=[node.get("label", "Entity")],
                        properties=node.get("properties", {})
                    )
                    nodes_by_id[node_id] = node_obj
                if result.get("m"):
                    node = result["m"]
                    node_id = self._decode_graph_label(node.get("node_id", ""))
                    node_obj = KnowledgeGraphNode(
                        id=node_id,
                        labels=[node.get("label", "Entity")],
                        properties=node.get("properties", {})
                    )
                    nodes_by_id[node_id] = node_obj
                if result.get("r"):
                    edge = result["r"]
                    src_id = self._decode_graph_label(edge.get("start_id", ""))
                    tgt_id = self._decode_graph_label(edge.get("end_id", ""))
                    edge_id = str(edge.get("id", f"{src_id}->{tgt_id}"))
                    edge_type = str(edge.get("label", "DIRECTED"))
                    properties = edge.get("properties", {})
                    edges.append(KnowledgeGraphEdge(
                        id=edge_id,
                        source=src_id,
                        target=tgt_id,
                        type=edge_type,
                        properties=properties,
                    ))
            else:
                node_entries = result.get("nodes")
                rel_entries = result.get("relationships")

                if isinstance(node_entries, str):
                    try:
                        node_entries = json.loads(node_entries)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON in column 'nodes': {node_entries}. Error: {e}")
                        node_entries = []

                if isinstance(rel_entries, str):
                    try:
                        rel_entries = json.loads(rel_entries)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON in column 'relationships': {rel_entries}. Error: {e}")
                        rel_entries = []

                if not isinstance(node_entries, list):
                    node_entries = [node_entries]
                if not isinstance(rel_entries, list):
                    rel_entries = [rel_entries]

                for node in node_entries:
                    if isinstance(node, dict):
                        node_id = self._decode_graph_label(node.get("node_id", ""))
                        label = node.get("label", "Entity")
                        properties = {k: v for k, v in node.items() if k not in ("node_id", "label")}
                        node_obj = KnowledgeGraphNode(
                            id=node_id,
                            labels=[label],
                            properties=properties
                        )
                        nodes_by_id[node_id] = node_obj

                for edge in rel_entries:
                    if isinstance(edge, dict):
                        src_id = self._decode_graph_label(edge.get("start_id", "")) if edge.get("start_id") else ""
                        tgt_id = self._decode_graph_label(edge.get("end_id", "")) if edge.get("end_id") else ""
                        edge_id = str(edge.get("id", f"{src_id}->{tgt_id}"))
                        edge_type = str(edge.get("label", "DIRECTED"))
                        properties = edge.get("properties", {})
                        edges.append(KnowledgeGraphEdge(
                            id=edge_id,
                            source=src_id,
                            target=tgt_id,
                            type=edge_type,
                            properties=properties
                        ))

        kg = KnowledgeGraph(
            nodes=list(nodes_by_id.values()),
            edges=edges
        )
        return kg

    async def drop(self) -> None:
        """Drop the storage"""
        drop_sql = SQL_TEMPLATES["drop_vdb_entity"]
        await self.db.execute(drop_sql)
        drop_sql = SQL_TEMPLATES["drop_vdb_relation"]
        await self.db.execute(drop_sql)


NAMESPACE_TABLE_MAP = {
    NameSpace.KV_STORE_FULL_DOCS: "LIGHTRAG_DOC_FULL",
    NameSpace.KV_STORE_TEXT_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_ENTITIES: "LIGHTRAG_VDB_ENTITY",
    NameSpace.VECTOR_STORE_RELATIONSHIPS: "LIGHTRAG_VDB_RELATION",
    NameSpace.DOC_STATUS: "LIGHTRAG_DOC_STATUS",
    NameSpace.KV_STORE_LLM_RESPONSE_CACHE: "LIGHTRAG_LLM_CACHE",
}


def namespace_to_table_name(namespace: str) -> str:
    for k, v in NAMESPACE_TABLE_MAP.items():
        if is_namespace(namespace, k):
            return v


TABLES = {
    "LIGHTRAG_DOC_FULL": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_FULL (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    doc_name VARCHAR(1024),
                    content TEXT,
                    meta JSONB,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
	                CONSTRAINT LIGHTRAG_DOC_FULL_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_DOC_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    full_doc_id VARCHAR(256),
                    chunk_order_index INTEGER,
                    tokens INTEGER,
                    content TEXT,
                    content_vector VECTOR,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
	                CONSTRAINT LIGHTRAG_DOC_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_ENTITY": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_ENTITY (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    entity_name VARCHAR(255),
                    content TEXT,
                    content_vector VECTOR,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
	                CONSTRAINT LIGHTRAG_VDB_ENTITY_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_RELATION": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_RELATION (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    source_id VARCHAR(256),
                    target_id VARCHAR(256),
                    content TEXT,
                    content_vector VECTOR,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
	                CONSTRAINT LIGHTRAG_VDB_RELATION_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_LLM_CACHE": {
        "ddl": """CREATE TABLE LIGHTRAG_LLM_CACHE (
	                workspace varchar(255) NOT NULL,
	                id varchar(255) NOT NULL,
	                mode varchar(32) NOT NULL,
                    original_prompt TEXT,
                    return_value TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
	                CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, mode, id)
                    )"""
    },
    "LIGHTRAG_DOC_STATUS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_STATUS (
	               workspace varchar(255) NOT NULL,
	               id varchar(255) NOT NULL,
	               content TEXT NULL,
	               content_summary varchar(255) NULL,
	               content_length int4 NULL,
	               chunks_count int4 NULL,
	               status varchar(64) NULL,
	               created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	               updated_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	               CONSTRAINT LIGHTRAG_DOC_STATUS_PK PRIMARY KEY (workspace, id)
	              )"""
    },
}


SQL_TEMPLATES = {
    # SQL for KVStorage
    "get_by_id_full_docs": """SELECT id, COALESCE(content, '') as content
                                FROM LIGHTRAG_DOC_FULL WHERE workspace=$1 AND id=$2
                            """,
    "get_by_id_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                chunk_order_index, full_doc_id
                                FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=$1 AND id=$2
                            """,
    "get_by_id_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                                FROM LIGHTRAG_LLM_CACHE WHERE workspace=$1 AND mode=$2
                               """,
    "get_by_mode_id_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                           FROM LIGHTRAG_LLM_CACHE WHERE workspace=$1 AND mode=$2 AND id=$3
                          """,
    "get_by_ids_full_docs": """SELECT id, COALESCE(content, '') as content
                                 FROM LIGHTRAG_DOC_FULL WHERE workspace=$1 AND id IN ({ids})
                            """,
    "get_by_ids_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                  chunk_order_index, full_doc_id
                                   FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=$1 AND id IN ({ids})
                                """,
    "get_by_ids_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                                 FROM LIGHTRAG_LLM_CACHE WHERE workspace=$1 AND mode= IN ({ids})
                                """,
    "filter_keys": "SELECT id FROM {table_name} WHERE workspace=$1 AND id IN ({ids})",
    "upsert_doc_full": """INSERT INTO LIGHTRAG_DOC_FULL (id, content, workspace)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (workspace,id) DO UPDATE
                           SET content = $2, update_time = CURRENT_TIMESTAMP
                       """,
    "upsert_llm_response_cache": """INSERT INTO LIGHTRAG_LLM_CACHE(workspace,id,original_prompt,return_value,mode)
                                      VALUES ($1, $2, $3, $4, $5)
                                      ON CONFLICT (workspace,mode,id) DO UPDATE
                                      SET original_prompt = EXCLUDED.original_prompt,
                                      return_value=EXCLUDED.return_value,
                                      mode=EXCLUDED.mode,
                                      update_time = CURRENT_TIMESTAMP
                                     """,
    "upsert_chunk": """INSERT INTO LIGHTRAG_DOC_CHUNKS (workspace, id, tokens,
                      chunk_order_index, full_doc_id, content, content_vector)
                      VALUES ($1, $2, $3, $4, $5, $6, $7)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET tokens=EXCLUDED.tokens,
                      chunk_order_index=EXCLUDED.chunk_order_index,
                      full_doc_id=EXCLUDED.full_doc_id,
                      content = EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      update_time = CURRENT_TIMESTAMP
                     """,
    "upsert_entity": """INSERT INTO LIGHTRAG_VDB_ENTITY (workspace, id, entity_name, content, content_vector)
                      VALUES ($1, $2, $3, $4, $5)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET entity_name=EXCLUDED.entity_name,
                      content=EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      update_time=CURRENT_TIMESTAMP
                     """,
    "upsert_relationship": """INSERT INTO LIGHTRAG_VDB_RELATION (workspace, id, source_id,
                      target_id, content, content_vector)
                      VALUES ($1, $2, $3, $4, $5, $6)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET source_id=EXCLUDED.source_id,
                      target_id=EXCLUDED.target_id,
                      content=EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector, update_time = CURRENT_TIMESTAMP
                     """,
    # SQL for VectorStorage
    "entities": """SELECT entity_name FROM
        (SELECT id, entity_name, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
        FROM LIGHTRAG_VDB_ENTITY where workspace=$1)
        WHERE distance>$2 ORDER BY distance DESC  LIMIT $3
       """,
    "relationships": """SELECT source_id as src_id, target_id as tgt_id FROM
        (SELECT id, source_id,target_id, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
        FROM LIGHTRAG_VDB_RELATION where workspace=$1)
        WHERE distance>$2 ORDER BY distance DESC  LIMIT $3
       """,
    "chunks": """SELECT id FROM
        (SELECT id, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
        FROM LIGHTRAG_DOC_CHUNKS where workspace=$1)
        WHERE distance>$2 ORDER BY distance DESC  LIMIT $3
       """,
    # DROP tables
    "drop_all": """
	    DROP TABLE IF EXISTS LIGHTRAG_DOC_FULL CASCADE;
	    DROP TABLE IF EXISTS LIGHTRAG_DOC_CHUNKS CASCADE;
	    DROP TABLE IF EXISTS LIGHTRAG_LLM_CACHE CASCADE;
	    DROP TABLE IF EXISTS LIGHTRAG_VDB_ENTITY CASCADE;
	    DROP TABLE IF EXISTS LIGHTRAG_VDB_RELATION CASCADE;
       """,
    "drop_doc_full": """
	    DROP TABLE IF EXISTS LIGHTRAG_DOC_FULL CASCADE;
       """,
    "drop_doc_chunks": """
	    DROP TABLE IF EXISTS LIGHTRAG_DOC_CHUNKS CASCADE;
       """,
    "drop_llm_cache": """
	    DROP TABLE IF EXISTS LIGHTRAG_LLM_CACHE CASCADE;
       """,
    "drop_vdb_entity": """
	    DROP TABLE IF EXISTS LIGHTRAG_VDB_ENTITY CASCADE;
       """,
    "drop_vdb_relation": """
	    DROP TABLE IF EXISTS LIGHTRAG_VDB_RELATION CASCADE;
       """,
}
