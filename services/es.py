# services/es.py
import logging
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import streaming_bulk, scan, bulk

from config import load_config


_config = load_config()


def create_es_client() -> Elasticsearch:
    return Elasticsearch(
        hosts=[_config.es.host],
        basic_auth=(
            _config.es.username,
            _config.es.password,
        ),
        request_timeout=_config.es.timeout,
    )


def index_exists(index_name: str) -> bool:
    es = create_es_client()

    try:
        return es.indices.exists(index=index_name)

    finally:
        es.close()


def delete_index(index_name: str) -> None:
    es = create_es_client()

    try:
        es.indices.delete(index=index_name)

    finally:
        es.close()


def create_index(index_name: str, settings=None, mappings=None) -> None:
    es = create_es_client()

    try:
        body = {}

        if settings is not None:
            body["settings"] = settings

        if mappings is not None:
            body["mappings"] = mappings

        es.indices.create(
            index=index_name,
            body=body if body else None,
        )

    finally:
        es.close()


def recreate_index(index_name: str, settings=None, mappings=None) -> None:
    if index_exists(index_name):
        delete_index(index_name)

    create_index(
        index_name=index_name,
        settings=settings,
        mappings=mappings,
    )


def set_refresh_interval(index_name: str, interval: str) -> None:
    es = create_es_client()

    try:
        es.indices.put_settings(
            index=index_name,
            settings={
                "index": {
                    "refresh_interval": interval,
                }
            },
        )

    finally:
        es.close()


def refresh_index(index_name: str) -> None:
    es = create_es_client()

    try:
        es.indices.refresh(index=index_name)

    finally:
        es.close()


def count_index(index_name: str) -> int:
    es = create_es_client()

    try:
        result = es.count(index=index_name)
        return result["count"]

    finally:
        es.close()


def streaming_bulk_upload(es_client: Elasticsearch, actions):
    success_count = 0
    failed_count = 0

    for ok, result in streaming_bulk(
        client=es_client,
        actions=actions,
        raise_on_error=False,
        raise_on_exception=False,
    ):
        if ok:
            success_count += 1
        else:
            failed_count += 1
            print("ES_BULK_FAILED:", result)

    return {
        "success": success_count,
        "failed": failed_count,
    }

def bulk_upload(
    es_client,
    actions,
    chunk_size: int = 1000,
) -> dict:

    success_count, errors = bulk(
        client=es_client,
        actions=actions,
        chunk_size=chunk_size,
        raise_on_error=False,
        raise_on_exception=False,
    )

    failed_count = len(errors) if errors else 0

    if failed_count > 0:
        logging.error(
            "ES_BULK_FAILED success=%s failed=%s errors_sample=%s",
            success_count,
            failed_count,
            errors[:5],
        )

    return {
        "success": success_count,
        "failed": failed_count,
    }

def scan_documents(
    es_client: Elasticsearch, 
    index_name: str, 
    search_body: dict, 
    batch_size: int = 1000, 
    scroll: str = "5m"
):
    iter_data = scan(
        client=es_client, 
        index=index_name, 
        query=search_body, 
        size=batch_size, 
        scroll=scroll
    )

    for d in iter_data:
        yield d["_source"]

def create_transform(
    es_client: Elasticsearch,
    transform_id: str,
    transform_body: dict,
) -> None:
    es_client.transform.put_transform(
        transform_id=transform_id,
        body=transform_body
    )

def exists_transform(
    es_client: Elasticsearch,
    transform_id: str
) -> bool:
    try:
        es_client.transform.get_transform(
            transform_id=transform_id
        )
        return True
    except NotFoundError:
        return False


def start_transform(
    es_client: Elasticsearch,
    transform_id: str
) -> None:
    es_client.transform.start_transform(
        transform_id=transform_id
    )


def delete_transform(
    es_client: Elasticsearch,
    transform_id: str,
    force: bool = True,
    delete_dest_index : bool = False
) -> None:
    es_client.transform.delete_transform(
        transform_id=transform_id,
        force=force,
        delete_dest_index=delete_dest_index
    )
