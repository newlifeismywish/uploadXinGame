# commands/download_from_es.py

import csv
import logging
import os
import shutil

from pathlib import Path

from services.es import create_es_client, scan_all_documents
from services.zip import compress as compress_7z


ROWS_PER_FILE = 50000


def resolve_output_paths(date):
    tmp_root = Path(os.getenv("DOWNLOAD_TMP_DIR", "/tmp"))
    archive_root = Path(os.getenv("DOWNLOAD_ARCHIVE_DIR", str(tmp_root)))

    output_dir = tmp_root / date
    archive_path = archive_root / "{}.7z".format(date)

    return output_dir, archive_path


def prepare_output_paths(output_dir, archive_path, force):
    if output_dir.exists():
        if not force:
            raise RuntimeError(
                "Download output directory already exists: {}. "
                "Use --force to overwrite it.".format(output_dir)
            )

        shutil.rmtree(str(output_dir))

    if archive_path.exists():
        if not force:
            raise RuntimeError(
                "Download archive already exists: {}. "
                "Use --force to overwrite it.".format(archive_path)
            )

        archive_path.unlink()

    output_dir.mkdir(parents=True)
    archive_path.parent.mkdir(parents=True, exist_ok=True)


def write_tsv_file(file_path, fields, rows):
    with file_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(
            output_file,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writerow(fields)
        writer.writerows(rows)


def flush_buffer(output_dir, file_index, fields, rows):
    file_path = output_dir / "{}.tsv".format(file_index)

    write_tsv_file(
        file_path=file_path,
        fields=fields,
        rows=rows,
    )

    logging.info(
        "DOWNLOAD_FROM_ES_FILE_DONE file=%s rows=%s",
        file_path,
        len(rows),
    )

    return file_path


def download_from_es(jobContext):
    jobContext.state.current_step = "download_from_es_prepare"

    output_dir, archive_path = resolve_output_paths(jobContext.date)

    prepare_output_paths(
        output_dir=output_dir,
        archive_path=archive_path,
        force=jobContext.force,
    )

    logging.info(
        "DOWNLOAD_FROM_ES_START date=%s index=%s output_dir=%s archive=%s",
        jobContext.date,
        jobContext.config.es.index,
        output_dir,
        archive_path,
    )

    es_client = create_es_client(jobContext.config.es)

    total_count = 0
    file_index = 1
    buffer = []
    fields = None

    try:
        jobContext.state.current_step = "download_from_es_scan"

        for doc in scan_all_documents(
            es_client=es_client,
            index_name=jobContext.config.es.index,
        ):
            source = doc.get("_source", {})

            if fields is None:
                fields = list(source.keys())

            row = [source.get(field, "") for field in fields]
            buffer.append(row)
            total_count += 1

            if len(buffer) >= ROWS_PER_FILE:
                jobContext.state.current_step = "download_from_es_write_tsv"
                file_path = flush_buffer(
                    output_dir=output_dir,
                    file_index=file_index,
                    fields=fields,
                    rows=buffer,
                )
                jobContext.state.processed_files.append(str(file_path))
                jobContext.state.success_count += len(buffer)
                buffer = []
                file_index += 1
                jobContext.state.current_step = "download_from_es_scan"

        if fields is None:
            fields = []

        if buffer or total_count == 0:
            jobContext.state.current_step = "download_from_es_write_tsv"
            file_path = flush_buffer(
                output_dir=output_dir,
                file_index=file_index,
                fields=fields,
                rows=buffer,
            )
            jobContext.state.processed_files.append(str(file_path))
            jobContext.state.success_count += len(buffer)

    finally:
        es_client.close()

    jobContext.state.parsed_count = total_count

    jobContext.state.current_step = "download_from_es_compress"

    compress_7z(
        source_path=output_dir,
        output_path=archive_path,
    )

    jobContext.state.current_step = "download_from_es_done"

    logging.info(
        "DOWNLOAD_FROM_ES_DONE index=%s rows=%s files=%s archive=%s",
        jobContext.config.es.index,
        total_count,
        len(jobContext.state.processed_files),
        archive_path,
    )
