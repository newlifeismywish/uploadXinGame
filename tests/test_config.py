import os
import unittest
from unittest.mock import patch

from config import load_config


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


if __name__ == "__main__":
    unittest.main()
