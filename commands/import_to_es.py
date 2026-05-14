# commands/import_to_es.py

import logging

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from services.es import (
    recreate_index,
    set_refresh_interval,
    refresh_index,
    count_index,
)

from services.import_to_es import process_file


def import_to_es(jobContext) -> None:
    index_name = jobContext.config.es.index

    base_dir = Path(jobContext.config.base_dir)
    data_dir = base_dir / jobContext.date

    json_files = sorted(data_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            "No json files found: {}".format(data_dir)
        )

    logging.info(
        "IMPORT_START date=%s index=%s data_dir=%s files=%s",
        jobContext.date,
        index_name,
        data_dir,
        len(json_files),
    )

    recreate_index(index_name, config=jobContext.config.es)

    set_refresh_interval(index_name, "-1", config=jobContext.config.es)

    try:
        with ProcessPoolExecutor(
            max_workers=jobContext.config.workers,
        ) as executor:

            futures = {
                executor.submit(
                    process_file,
                    str(file_path),
                    index_name,
                    jobContext.config.bulk_size,
                    jobContext.config.es,
                ): file_path
                for file_path in json_files
            }

            for future in as_completed(futures):
                file_path = futures[future]

                try:
                    result = future.result()

                    jobContext.state.parsed_count += result["parsed"]
                    jobContext.state.success_count += result["success"]
                    jobContext.state.failed_count += result["failed"]
                    jobContext.state.processed_files.append(result["file"])

                    logging.info(
                        "IMPORT_FILE_RESULT file=%s parsed=%s success=%s failed=%s",
                        result["file"],
                        result["parsed"],
                        result["success"],
                        result["failed"],
                    )

                except Exception:
                    jobContext.state.failed_files.append(str(file_path))

                    logging.exception(
                        "IMPORT_FILE_FAILED file=%s",
                        file_path,
                    )

                    raise

    finally:
        set_refresh_interval(index_name, "1s", config=jobContext.config.es)
        refresh_index(index_name, config=jobContext.config.es)

    actual_count = count_index(index_name, config=jobContext.config.es)

    logging.info(
        "IMPORT_DONE parsed=%s success=%s failed=%s actual_index_count=%s",
        jobContext.state.parsed_count,
        jobContext.state.success_count,
        jobContext.state.failed_count,
        actual_count,
    )

    if jobContext.state.parsed_count != jobContext.state.success_count:
        raise RuntimeError(
            "Import count mismatch: parsed={} success={} failed={}".format(
                jobContext.state.parsed_count,
                jobContext.state.success_count,
                jobContext.state.failed_count,
            )
        )

    if actual_count != jobContext.state.success_count:
        raise RuntimeError(
            "Elasticsearch count mismatch: success={} actual={}".format(
                jobContext.state.success_count,
                actual_count,
            )
        )
