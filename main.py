# main.py

import argparse
import logging
import shutil
import traceback

from datetime import datetime, timedelta
from pathlib import Path

from config import load_config
from job_context import JobContext
from logger import setup_logging
from services.mail import send as send_mail

from commands.create_transform import create_transform
from commands.download_from_es import download_from_es
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
            "download_from_es",
            "create_transform",
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

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the selected command and date without running the job",
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
    cleanup_extracted_data(jobContext)


def cleanup_extracted_data(jobContext):
    jobContext.state.current_step = "cleanup_extracted_data"

    data_dir = Path(jobContext.config.base_dir) / jobContext.date

    if not data_dir.exists():
        logging.info(
            "CLEANUP_SKIP data_dir_not_exists path=%s",
            data_dir,
        )
        jobContext.state.current_step = "cleanup_skipped"
        return

    if not data_dir.is_dir():
        raise RuntimeError(
            "Cleanup target is not a directory: {}".format(data_dir)
        )

    logging.info(
        "CLEANUP_START path=%s",
        data_dir,
    )

    shutil.rmtree(data_dir)

    jobContext.state.current_step = "cleanup_done"

    logging.info(
        "CLEANUP_DONE path=%s",
        data_dir,
    )


def resolve_index_name(base_index, date):
    if "{date}" in base_index:
        return base_index.replace("{date}", date)

    if "yyyymmdd" in base_index:
        return base_index.replace("yyyymmdd", date)

    if base_index.endswith("_{}".format(date)):
        return base_index

    return "{}_{}".format(base_index, date)


def build_notification_subject(command, date, success):
    status = "SUCCESS" if success else "FAILED"
    return "[uploadXinGame] {} command={} date={}".format(
        status,
        command,
        date,
    )


def build_notification_body(
    *,
    command,
    jobContext,
    success,
    started_at,
    ended_at,
    error=None,
    traceback_text=None,
):
    state = jobContext.state
    status = "SUCCESS" if success else "FAILED"
    elapsed_seconds = int((ended_at - started_at).total_seconds())

    lines = [
        "Job status: {}".format(status),
        "Command: {}".format(command),
        "Date: {}".format(jobContext.date),
        "Current step: {}".format(state.current_step or "unknown"),
        "Index: {}".format(jobContext.config.es.index),
        "Base directory: {}".format(jobContext.config.base_dir),
        "Force: {}".format(jobContext.force),
        "Started at: {}".format(started_at.isoformat(timespec="seconds")),
        "Ended at: {}".format(ended_at.isoformat(timespec="seconds")),
        "Elapsed seconds: {}".format(elapsed_seconds),
        "",
        "Counts",
        "Parsed: {}".format(state.parsed_count),
        "Success: {}".format(state.success_count),
        "Failed: {}".format(state.failed_count),
        "Processed files: {}".format(len(state.processed_files)),
        "Failed files: {}".format(len(state.failed_files)),
    ]

    if state.failed_files:
        lines.extend(["", "Failed file list:"])
        lines.extend(state.failed_files)

    if error is not None:
        lines.extend(
            [
                "",
                "Error",
                "Failed step: {}".format(state.current_step or "unknown"),
                "Failure reason: {}: {}".format(type(error).__name__, error),
            ]
        )

    if traceback_text:
        lines.extend(["", "Traceback", traceback_text])

    return "\n".join(lines)


def send_job_notification(
    *,
    command,
    jobContext,
    success,
    started_at,
    ended_at,
    error=None,
    traceback_text=None,
):
    subject = build_notification_subject(
        command=command,
        date=jobContext.date,
        success=success,
    )
    body = build_notification_body(
        command=command,
        jobContext=jobContext,
        success=success,
        started_at=started_at,
        ended_at=ended_at,
        error=error,
        traceback_text=traceback_text,
    )

    send_mail(
        subject=subject,
        body=body,
        config=jobContext.config.mail,
    )


def main():
    args = parse_args()

    target_date = resolve_date(
        args.date,
        args.days_ago,
    )

    setup_logging(target_date)

    if args.dry_run:
        logging.info(
            "DRY_RUN command=%s date=%s force=%s",
            args.command,
            target_date,
            args.force,
        )
        return

    config = load_config()
    config.es.index = resolve_index_name(config.es.index, target_date)

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
        "download_from_es": download_from_es,
        "create_transform": create_transform,
    }

    started_at = datetime.now()

    try:
        commands[args.command](jobContext)

    except Exception as exc:
        traceback_text = traceback.format_exc()
        logging.exception(
            "JOB_FAILED command=%s date=%s",
            args.command,
            target_date,
        )

        try:
            send_job_notification(
                command=args.command,
                jobContext=jobContext,
                success=False,
                started_at=started_at,
                ended_at=datetime.now(),
                error=exc,
                traceback_text=traceback_text,
            )
            logging.info(
                "MAIL_NOTIFICATION_SENT status=failed command=%s date=%s",
                args.command,
                target_date,
            )
        except Exception:
            logging.exception(
                "MAIL_NOTIFICATION_FAILED status=failed command=%s date=%s",
                args.command,
                target_date,
            )

        raise

    else:
        try:
            send_job_notification(
                command=args.command,
                jobContext=jobContext,
                success=True,
                started_at=started_at,
                ended_at=datetime.now(),
            )
            logging.info(
                "MAIL_NOTIFICATION_SENT status=success command=%s date=%s",
                args.command,
                target_date,
            )
        except Exception:
            logging.exception(
                "MAIL_NOTIFICATION_FAILED status=success command=%s date=%s",
                args.command,
                target_date,
            )


if __name__ == "__main__":
    main()
