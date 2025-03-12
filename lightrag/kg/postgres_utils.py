import json
from lightrag.utils import logger, set_verbose_debug
from typing import Any

def safe_decode_agtype_column(value: str, column_name: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode JSON in column '{column_name}': {value}. Error: {e}")
        return value
