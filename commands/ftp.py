# commands/ftp.py

import logging

from pathlib import Path

from services.ftp import (
    download_file,
    upload_file,
)


def download_zip(jobContext) -> None:
    base_dir = Path(jobContext.config.base_dir)

    local_path = base_dir / "{}.7z".format(jobContext.date)

    remote_path = (
        jobContext.config.ftp.remote_dir
        + "/"
        + jobContext.date
        + ".7z"
    )

    if local_path.exists() and not jobContext.force:
        logging.info(
            "DOWNLOAD_SKIP local_exists path=%s",
            local_path,
        )
        return

    logging.info(
        "DOWNLOAD_START remote=%s local=%s",
        remote_path,
        local_path,
    )

    download_file(
        remote_path=remote_path,
        local_path=local_path,
    )

    logging.info(
        "DOWNLOAD_DONE local=%s",
        local_path,
    )


def upload_zip(jobContext) -> None:
    base_dir = Path(jobContext.config.base_dir)

    local_path = base_dir / "{}.7z".format(jobContext.date)

    remote_path = (
        jobContext.config.ftp.remote_dir
        + "/"
        + jobContext.date
        + ".7z"
    )

    if not local_path.exists():
        raise FileNotFoundError(local_path)

    logging.info(
        "UPLOAD_START local=%s remote=%s",
        local_path,
        remote_path,
    )

    upload_file(
        remote_path=remote_path,
        local_path=local_path,
    )

    logging.info(
        "UPLOAD_DONE remote=%s",
        remote_path,
    )
