import os
from dataclasses import dataclass
from typing import Any, final

from lightrag.base import (
    BaseKVStorage,
)
from lightrag.utils import (
    load_json,
    logger,
    write_json,
)
from .shared_storage import get_namespace_data, get_storage_lock


@final
@dataclass
class JsonKVStorage(BaseKVStorage):
    def __post_init__(self):
        working_dir = self.global_config["working_dir"]
        self._storage_lock = get_storage_lock()
        self._data = get_namespace_data(self.namespace)
        with self._storage_lock:
            if not self._data:
                self._file_name = os.path.join(working_dir, f"kv_store_{self.namespace}.json")
                self._data: dict[str, Any] = load_json(self._file_name) or {}
        logger.info(f"Load KV {self.namespace} with {len(self._data)} data")


    async def index_done_callback(self) -> None:
        # 文件写入需要加锁，防止多个进程同时写入导致文件损坏
        with self._storage_lock:
            write_json(self._data, self._file_name)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        with self._storage_lock:
            return self._data.get(id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        with self._storage_lock:
            return [
                (
                    {k: v for k, v in self._data[id].items()}
                    if self._data.get(id, None)
                    else None
                )
                for id in ids
            ]

    async def filter_keys(self, keys: set[str]) -> set[str]:
        with self._storage_lock:
            return set(keys) - set(self._data.keys())

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        logger.info(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return
        with self._storage_lock:
            left_data = {k: v for k, v in data.items() if k not in self._data}
            self._data.update(left_data)

    async def delete(self, ids: list[str]) -> None:
        with self._storage_lock:
            for doc_id in ids:
                self._data.pop(doc_id, None)
        await self.index_done_callback()
