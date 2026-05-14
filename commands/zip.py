# commands/zip.py

import logging

from pathlib import Path

from services.zip import (
    compress as compress_7z,
    extract as extract_7z,
)

from commands.ftp import download_zip


def compress(jobContext) -> None:
    base_dir = Path(jobContext.config.base_dir)

    source_path = base_dir / jobContext.date
    output_path = base_dir / "{}.7z".format(jobContext.date)

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    if output_path.exists() and not jobContext.force:
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

    compress_7z(
        source_path=source_path,
        output_path=output_path,
    )

    logging.info(
        "COMPRESS_DONE output=%s",
        output_path,
    )


def extract(jobContext) -> None:
    base_dir = Path(jobContext.config.base_dir)

    zip_path = base_dir / "{}.7z".format(jobContext.date)
    output_dir = base_dir / jobContext.date

    if not zip_path.exists():
        logging.info(
            "ZIP_NOT_FOUND start_download path=%s",
            zip_path,
        )

        download_zip(jobContext)

    if output_dir.exists() and not jobContext.force:
        logging.info(
            "EXTRACT_SKIP output_exists path=%s",
            output_dir,
        )
        return

    logging.info(
        "EXTRACT_START zip=%s output=%s",
        zip_path,
        output_dir,
    )

    extract_7z(
        zip_path=zip_path,
        output_dir=output_dir,
    )

    logging.info(
        "EXTRACT_DONE output=%s",
        output_dir,
    )
