import json
import logging
from typing import Any, Dict, Iterator, Optional

from config import ESConfig
from services.es import create_es_client, bulk_upload

def build_es_action(action, index_name):
    source=action["_source"]
    return {
        "_op_type": "create",
        "_index": index_name,
        "_id": f'{source["mid"]}_{source["tid"]}',
        "_source": source
    }

def iter_es_actions(
    file_path: str,
    index_name: str,
    stats: Dict[str, int],
) -> Iterator[Dict[str, Any]]:

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("\n  }}")

    for part_index, part in enumerate(parts, start=1):
        part = part.strip()

        if "_source" not in part:
            continue

        part += "\n  }}"

        try:
            action = json.loads(part)
            stats["parsed"] += 1

            yield build_es_action(
                action=action,
                index_name=index_name,
            )

        except Exception:
            stats["failed"] += 1

            logging.exception(
                "PARSE_OR_BUILD_ACTION_FAILED file=%s part_index=%s parsed=%s part_sample=%r",
                file_path,
                part_index,
                stats["parsed"],
                part[:500],
            )


def process_file(
    file_path: str,
    index_name: str,
    chunk_size: int = 1000,
    es_config: Optional[ESConfig] = None,
) -> dict:

    es_client = create_es_client(es_config)

    stats = {
        "parsed": 0,
        "failed": 0,
    }

    try:
        actions = iter_es_actions(
            file_path=file_path,
            index_name=index_name,
            stats=stats,
        )

        result = bulk_upload(
            es_client=es_client,
            actions=actions,
            chunk_size=chunk_size,
        )

        success_count = result["success"]
        failed_count = stats["failed"] + result["failed"]

        logging.info(
            "IMPORT_FILE_DONE file=%s parsed=%s success=%s failed=%s",
            file_path,
            stats["parsed"],
            success_count,
            failed_count,
        )

        return {
            "file": file_path,
            "parsed": stats["parsed"],
            "success": success_count,
            "failed": failed_count,
        }

    finally:
        es_client.close()
