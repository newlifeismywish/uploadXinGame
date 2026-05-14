# uploadXinGame

Python ETL command-line job for importing daily game data into Elasticsearch.

## Workflow

The job is organized around a target date in `yyyymmdd` format.

1. Locate `BaseDirector/{date}.7z`.
2. Download the archive from FTP when it does not exist locally.
3. Extract the archive into `BaseDirector/{date}/`.
4. Parse JSON files under `BaseDirector/{date}/*.json`.
5. Convert each parsed record into Elasticsearch bulk actions.
6. Recreate the date-specific Elasticsearch index and upload records.
7. Validate parsed, successful, failed, and indexed document counts.
8. Send a mail notification with the final status, step, counts, and error reason.

## Requirements

- Python 3.9
- 7-Zip command-line executable `7za`
- FTP access
- Elasticsearch access

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file from the example:

```bash
copy .env.example .env
```

Required settings:

```env
FTP_HOST=ftp.example.com
FTP_PORT=21
FTP_USER=user
FTP_PASSWORD=password
FTP_REMOTE_DIR=/remote/path
FTP_TIMEOUT=30

ES_HOST=http://localhost:9200
ES_USERNAME=elastic
ES_PASSWORD=password
ES_TIMEOUT=30
ES_INDEX=upload_xin_game_yyyymmdd

MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user
MAIL_PASSWORD=password
MAIL_FROM=noreply@example.com
MAIL_TO=receiver@example.com
MAIL_TIMEOUT=30

BASE_DIR=BaseDirector
BULK_SIZE=1000
WORKERS=4
```

## CLI

Run the full extract and import flow:

```bash
python main.py run --date 20260513
```

Run a single step:

```bash
python main.py downloadZip --date 20260513
python main.py extract --date 20260513
python main.py import --date 20260513
python main.py compress --date 20260513
python main.py uploadZip --date 20260513
```

Use yesterday by default:

```bash
python main.py run
```

Use a relative date:

```bash
python main.py run --days-ago 2
```

Force rerun behavior:

```bash
python main.py extract --date 20260513 --force
```

When `extract --force` is used, the existing extracted directory is removed before extraction.

Preview the selected command without validating configuration or running the job:

```bash
python main.py import --date 20260513 --dry-run
```

## Notes

- The Elasticsearch index is recreated during import. This is expected because the configured index is date-specific.
- FTP downloads are written to a `.part` file first and moved into place only after the download succeeds.
- Success and failure notifications are sent by mail after the selected command finishes.
- Failure notifications include the failed step, exception reason, and traceback.
- Runtime logs are written to `logs/job_{date}.log`.
- Generated archives, extracted data, logs, and `.env` files are intentionally ignored by git.

## Audit Notes

The original audit request has been preserved in `AUDIT_REQUEST.md`.
