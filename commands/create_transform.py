# commands/create_transform.py

import json
import logging

from pathlib import Path

from services.es import (
    create_es_client,
    create_transform as put_transform,
    delete_transform,
    exists_transform,
)


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "transform_template"
    / "user_sample.json"
)


def load_transform_template(template_path=TEMPLATE_PATH):
    try:
        with template_path.open("r", encoding="utf-8") as template_file:
            transform_body = json.load(template_file)
    except ValueError as exc:
        raise RuntimeError(
            "Transform template is not valid JSON: {}".format(template_path)
        ) from exc

    if not isinstance(transform_body, dict):
        raise RuntimeError(
            "Transform template root must be a JSON object: {}".format(
                template_path
            )
        )

    return transform_body


def set_source_index(transform_body, index_name):
    source = transform_body.get("source")

    if not isinstance(source, dict):
        raise RuntimeError("Transform template must define source object")

    if isinstance(source.get("index"), list):
        source["index"] = [index_name]
    else:
        source["index"] = index_name


def resolve_transform_id(transform_body, date):
    transform_id = transform_body.pop("transform_id", None)

    if transform_id:
        return str(transform_id)

    dest = transform_body.get("dest")

    if not isinstance(dest, dict) or not dest.get("index"):
        raise RuntimeError(
            "Transform template must define transform_id or dest.index"
        )

    return "{}_{}".format(dest["index"], date)


def create_transform(jobContext):
    jobContext.state.current_step = "create_transform_prepare"

    transform_body = load_transform_template()
    set_source_index(transform_body, jobContext.config.es.index)
    transform_id = resolve_transform_id(transform_body, jobContext.date)

    jobContext.state.processed_files.append(str(TEMPLATE_PATH))
    jobContext.state.parsed_count = 1

    logging.info(
        "CREATE_TRANSFORM_START transform_id=%s source_index=%s",
        transform_id,
        jobContext.config.es.index,
    )

    es_client = create_es_client(jobContext.config.es)

    try:
        jobContext.state.current_step = "create_transform_check_exists"

        if exists_transform(es_client, transform_id):
            if not jobContext.force:
                raise RuntimeError(
                    "Transform already exists: {}. "
                    "Use --force to recreate it.".format(transform_id)
                )

            jobContext.state.current_step = "create_transform_delete_existing"
            delete_transform(
                es_client=es_client,
                transform_id=transform_id,
            )

        jobContext.state.current_step = "create_transform_put"

        put_transform(
            es_client=es_client,
            transform_id=transform_id,
            transform_body=transform_body,
        )

    finally:
        es_client.close()

    jobContext.state.success_count = 1
    jobContext.state.current_step = "create_transform_done"

    logging.info(
        "CREATE_TRANSFORM_DONE transform_id=%s source_index=%s",
        transform_id,
        jobContext.config.es.index,
    )
