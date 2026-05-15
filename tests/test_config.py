import os
import shutil
import uuid
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from config import load_config, load_env_file, load_mail_config


@contextmanager
def workspace_tmp_dir():
    root = Path.cwd() / ".tmp-tests"
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()

    try:
        yield path
    finally:
        shutil.rmtree(str(path), ignore_errors=True)


REQUIRED_ENV = {
    "FTP_HOST": "ftp.example.com",
    "FTP_USER": "ftp-user",
    "FTP_PASSWORD": "ftp-password",
    "FTP_REMOTE_DIR": "/daily",
    "ES_HOST": "http://localhost:9200",
    "ES_USERNAME": "elastic",
    "ES_PASSWORD": "es-password",
    "ES_INDEX": "upload_xin_game_20260513",
    "MAIL_HOST": "smtp.example.com",
    "MAIL_USERNAME": "smtp-user",
    "MAIL_PASSWORD": "smtp-password",
    "MAIL_FROM": "noreply@example.com",
    "MAIL_TO": "one@example.com, two@example.com",
}


class LoadConfigTests(unittest.TestCase):
    def test_load_config_parses_defaults_and_mail_recipients(self):
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            config = load_config()

        self.assertEqual(config.ftp.port, 21)
        self.assertEqual(config.es.timeout, 30)
        self.assertEqual(config.mail.mail_to, ["one@example.com", "two@example.com"])
        self.assertEqual(config.base_dir, "BaseDirector")
        self.assertEqual(config.bulk_size, 1000)
        self.assertEqual(config.workers, 4)

    def test_load_mail_config_does_not_require_ftp_or_es_settings(self):
        mail_env = {
            "MAIL_HOST": "smtp.example.com",
            "MAIL_USERNAME": "smtp-user",
            "MAIL_PASSWORD": "smtp-password",
            "MAIL_FROM": "noreply@example.com",
            "MAIL_TO": "one@example.com",
        }

        with patch.dict(os.environ, mail_env, clear=True):
            config = load_mail_config()

        self.assertEqual(config.host, "smtp.example.com")
        self.assertEqual(config.mail_to, ["one@example.com"])

    def test_missing_required_env_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "Missing required environment variable: MAIL_HOST",
            ):
                load_mail_config()

    def test_load_env_file_accepts_spaces_around_equals(self):
        with workspace_tmp_dir() as tmp_dir:
            env_path = tmp_dir / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "FTP_HOST = x.x.x.x",
                        "MAIL_HOST=smtp.example.com",
                        "QUOTED_VALUE = 'hello world'",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                load_env_file(env_path)

                self.assertEqual(os.environ["FTP_HOST"], "x.x.x.x")
                self.assertEqual(os.environ["MAIL_HOST"], "smtp.example.com")
                self.assertEqual(os.environ["QUOTED_VALUE"], "hello world")


if __name__ == "__main__":
    unittest.main()
