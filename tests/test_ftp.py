import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from services.ftp import download_file


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


class FakeFTP:
    def __init__(self, payload=b"archive-bytes", error=None):
        self.payload = payload
        self.error = error
        self.command = None
        self.quit_called = False

    def retrbinary(self, command, callback):
        self.command = command
        callback(self.payload)
        if self.error:
            raise self.error

    def quit(self):
        self.quit_called = True

    def close(self):
        pass


class DownloadFileTests(unittest.TestCase):
    def test_download_file_moves_part_file_into_place(self):
        fake_ftp = FakeFTP()

        with workspace_tmp_dir() as tmp_dir:
            local_path = tmp_dir / "20260513.7z"

            with patch("services.ftp.connect_ftp", return_value=fake_ftp):
                result = download_file(
                    remote_path="/daily/20260513.7z",
                    local_path=local_path,
                )

            self.assertEqual(result, local_path)
            self.assertEqual(local_path.read_bytes(), b"archive-bytes")
            self.assertFalse(local_path.with_name(local_path.name + ".part").exists())
            self.assertEqual(fake_ftp.command, "RETR /daily/20260513.7z")
            self.assertTrue(fake_ftp.quit_called)

    def test_download_file_removes_part_file_after_failure(self):
        fake_ftp = FakeFTP(error=RuntimeError("download failed"))

        with workspace_tmp_dir() as tmp_dir:
            local_path = tmp_dir / "20260513.7z"

            with patch("services.ftp.connect_ftp", return_value=fake_ftp):
                with self.assertRaises(RuntimeError):
                    download_file(
                        remote_path="/daily/20260513.7z",
                        local_path=local_path,
                    )

            self.assertFalse(local_path.exists())
            self.assertFalse(local_path.with_name(local_path.name + ".part").exists())
            self.assertTrue(fake_ftp.quit_called)


if __name__ == "__main__":
    unittest.main()
