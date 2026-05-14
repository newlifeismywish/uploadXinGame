import sys
import unittest
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_dry_run_does_not_load_config_or_run_command(self):
        argv = [
            "main.py",
            "import",
            "--date",
            "20260513",
            "--dry-run",
        ]

        with patch.object(sys, "argv", argv):
            with patch("main.setup_logging") as setup_logging:
                with patch("main.load_config") as load_config:
                    with patch("main.logging.info") as log_info:
                        main.main()

        setup_logging.assert_called_once_with("20260513")
        load_config.assert_not_called()
        log_info.assert_called_once_with(
            "DRY_RUN command=%s date=%s force=%s",
            "import",
            "20260513",
            False,
        )

    def test_resolve_date_accepts_explicit_date(self):
        self.assertEqual(main.resolve_date("20260513", 1), "20260513")


if __name__ == "__main__":
    unittest.main()
