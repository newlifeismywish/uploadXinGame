# commands/zip.py

import logging
import shutil

from pathlib import Path

from services.zip import (
    compress as compress_7z,
    extract as extract_7z,
)

from commands.ftp import download_zip


def compress(jobContext) -> None:
    jobContext.state.current_step = "compress_prepare"

    base_dir = Path(jobContext.config.base_dir)

    source_path = base_dir / jobContext.date
    output_path = base_dir / "{}.7z".format(jobContext.date)

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    if output_path.exists() and not jobContext.force:
        jobContext.state.current_step = "compress_skipped"
        logging.info(
            "COMPRESS_SKIP output_exists path=%s",
            output_path,
        )
        return

    logging.info(
        "COMPRESS_START source=%s output=%s",
        source_path,
        output_path,
    )

    jobContext.state.current_step = "compress_archive"

    compress_7z(
        source_path=source_path,
        output_path=output_path,
    )

    jobContext.state.current_step = "compress_done"

    logging.info(
        "COMPRESS_DONE output=%s",
        output_path,
    )


def extract(jobContext) -> None:
    jobContext.state.current_step = "extract_prepare"

    base_dir = Path(jobContext.config.base_dir)

    zip_path = base_dir / "{}.7z".format(jobContext.date)
    data_dir = base_dir / jobContext.date
    extract_dir = base_dir

    if not zip_path.exists():
        logging.info(
            "ZIP_NOT_FOUND start_download path=%s",
            zip_path,
        )

        download_zip(jobContext)
        jobContext.state.current_step = "extract_prepare"

    if data_dir.exists():
        if not jobContext.force:
            jobContext.state.current_step = "extract_skipped"
            logging.info(
                "EXTRACT_SKIP output_exists path=%s",
                data_dir,
            )
            return

        jobContext.state.current_step = "extract_cleanup"

        logging.info(
            "EXTRACT_CLEANUP output_exists path=%s",
            data_dir,
        )
        shutil.rmtree(data_dir)

    logging.info(
        "EXTRACT_START zip=%s output=%s expected_data_dir=%s",
        zip_path,
        extract_dir,
        data_dir,
    )

    jobContext.state.current_step = "extract_archive"

    extract_7z(
        zip_path=zip_path,
        output_dir=extract_dir,
    )

    jobContext.state.current_step = "extract_done"

    logging.info(
        "EXTRACT_DONE output=%s expected_data_dir=%s",
        extract_dir,
        data_dir,
    )
