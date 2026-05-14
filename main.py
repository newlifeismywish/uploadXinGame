# main.py

import argparse

from datetime import datetime, timedelta

from config import load_config
from job_context import JobContext
from logger import setup_logging

from commands.import_to_es import import_to_es
from commands.zip import compress, extract
from commands.ftp import download_zip, upload_zip


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=[
            "run",
            "downloadZip",
            "uploadZip",
            "extract",
            "compress",
            "import",
        ],
        help="run full job or execute one step only",
    )

    parser.add_argument(
        "--date",
        help="target date, format yyyymmdd",
    )

    parser.add_argument(
        "--days-ago",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--force",
        action="store_true",
    )

    return parser.parse_args()


def resolve_date(date_str, days_ago):
    if date_str:
        datetime.strptime(date_str, "%Y%m%d")
        return date_str

    return (
        datetime.today() - timedelta(days=days_ago)
    ).strftime("%Y%m%d")


def run(jobContext):
    extract(jobContext)
    import_to_es(jobContext)


def main():
    args = parse_args()

    config = load_config()

    target_date = resolve_date(
        args.date,
        args.days_ago,
    )

    setup_logging(target_date)

    jobContext = JobContext(
        config=config,
        date=target_date,
        force=args.force,
    )

    commands = {
        "run": run,
        "downloadZip": download_zip,
        "uploadZip": upload_zip,
        "extract": extract,
        "compress": compress,
        "import": import_to_es,
    }

    #commands[args.command](jobContext)


if __name__ == "__main__":
    main()
