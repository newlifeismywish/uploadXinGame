import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from commands.zip import extract


@contextmanager
def workspace_tmp_dir():
    root = Path.cwd() / ".tmp-tests"
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()

    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class ExtractCommandTests(unittest.TestCase):
    def test_extract_force_removes_existing_output_directory(self):
        with workspace_tmp_dir() as base_dir:
            target_date = "20260513"
            zip_path = base_dir / "{}.7z".format(target_date)
            output_dir = base_dir / target_date
            stale_file = output_dir / "stale.json"

            zip_path.write_bytes(b"archive")
            output_dir.mkdir()
            stale_file.write_text("old-data", encoding="utf-8")

            job_context = SimpleNamespace(
                config=SimpleNamespace(base_dir=str(base_dir)),
                date=target_date,
                force=True,
                state=SimpleNamespace(current_step=None),
            )

            with patch("commands.zip.extract_7z") as extract_7z:
                extract(job_context)

            self.assertFalse(stale_file.exists())
            self.assertEqual(job_context.state.current_step, "extract_done")
            extract_7z.assert_called_once_with(
                zip_path=zip_path,
                output_dir=output_dir,
            )

    def test_extract_skips_existing_output_directory_without_force(self):
        with workspace_tmp_dir() as base_dir:
            target_date = "20260513"
            zip_path = base_dir / "{}.7z".format(target_date)
            output_dir = base_dir / target_date

            zip_path.write_bytes(b"archive")
            output_dir.mkdir()

            job_context = SimpleNamespace(
                config=SimpleNamespace(base_dir=str(base_dir)),
                date=target_date,
                force=False,
                state=SimpleNamespace(current_step=None),
            )

            with patch("commands.zip.extract_7z") as extract_7z:
                extract(job_context)

            extract_7z.assert_not_called()
            self.assertEqual(job_context.state.current_step, "extract_skipped")


if __name__ == "__main__":
    unittest.main()
