# Codex Audit Request

## Project Overview

This project is a Python ETL-style command-line job.

Primary responsibilities:

1. Download a `{date}.7z` archive from FTP if needed.
2. Extract the archive into `BaseDirector/{date}/`.
3. Parse multiple JSON files under `BaseDirector/{date}/*.json`.
4. Convert each parsed record into Elasticsearch bulk actions.
5. Upload records to Elasticsearch using multiprocessing.
6. Track parsed / successful / failed counts.
7. Optionally export data, compress files, upload files, and send mail notifications.

Target Python version: **Python 3.9**

Please keep the implementation compatible with Python 3.9.

---

## Current CLI

Main entrypoint:

```bash
python main.py <command> --date yyyymmdd