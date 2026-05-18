# logger.py

import logging

from pathlib import Path


def setup_logging(date: str) -> None:
    log_dir = Path("logs")

    log_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_dir / f"job_{date}.log"

    logging.basicConfig(
        level=logging.INFO,

        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "[%(process)d] "
            "%(message)s"
        ),

        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            ),

            logging.StreamHandler(),
        ],
    )

    for logger_name in (
        "elasticsearch",
        "elasticsearch.trace",
        "urllib3",
        "urllib3.connectionpool",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
