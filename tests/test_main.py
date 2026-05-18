import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import main


def make_config():
    return SimpleNamespace(
        ftp=SimpleNamespace(),
        es=SimpleNamespace(index="upload_xin_game"),
        mail=SimpleNamespace(),
        base_dir="BaseDirector",
        bulk_size=1000,
        workers=4,
    )


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

    def test_resolve_index_name_appends_date_to_base_name(self):
        self.assertEqual(
            main.resolve_index_name("upload_xin_game", "20260513"),
            "upload_xin_game_20260513",
        )

    def test_resolve_index_name_replaces_date_placeholder(self):
        self.assertEqual(
            main.resolve_index_name("upload_xin_game_{date}", "20260513"),
            "upload_xin_game_20260513",
        )

    def test_resolve_index_name_replaces_yyyymmdd_placeholder(self):
        self.assertEqual(
            main.resolve_index_name("upload_xin_game_yyyymmdd", "20260513"),
            "upload_xin_game_20260513",
        )

    def test_resolve_index_name_does_not_append_existing_date(self):
        self.assertEqual(
            main.resolve_index_name("upload_xin_game_20260513", "20260513"),
            "upload_xin_game_20260513",
        )

    def test_successful_command_sends_success_notification(self):
        argv = [
            "main.py",
            "import",
            "--date",
            "20260513",
        ]

        def fake_import(job_context):
            job_context.state.current_step = "import_done"
            job_context.state.parsed_count = 2
            job_context.state.success_count = 2

        with patch.object(sys, "argv", argv):
            with patch("main.setup_logging"):
                with patch("main.load_config", return_value=make_config()):
                    with patch("main.import_to_es", side_effect=fake_import):
                        with patch("main.send_mail") as send_mail:
                            main.main()

        send_mail.assert_called_once()
        kwargs = send_mail.call_args.kwargs
        self.assertIn("SUCCESS", kwargs["subject"])
        self.assertIn("Current step: import_done", kwargs["body"])
        self.assertIn("Index: upload_xin_game_20260513", kwargs["body"])
        self.assertIn("Parsed: 2", kwargs["body"])
        self.assertIn("Success: 2", kwargs["body"])

    def test_failed_command_sends_failed_notification_with_step_and_reason(self):
        argv = [
            "main.py",
            "import",
            "--date",
            "20260513",
        ]

        def fake_import(job_context):
            job_context.state.current_step = "validate_import_counts"
            job_context.state.parsed_count = 3
            job_context.state.success_count = 2
            job_context.state.failed_count = 1
            raise RuntimeError("Import count mismatch: parsed=3 success=2 failed=1")

        with patch.object(sys, "argv", argv):
            with patch("main.setup_logging"):
                with patch("main.load_config", return_value=make_config()):
                    with patch("main.import_to_es", side_effect=fake_import):
                        with patch("main.send_mail") as send_mail:
                            with patch("main.logging.exception"):
                                with self.assertRaises(RuntimeError):
                                    main.main()

        send_mail.assert_called_once()
        kwargs = send_mail.call_args.kwargs
        self.assertIn("FAILED", kwargs["subject"])
        self.assertIn("Failed step: validate_import_counts", kwargs["body"])
        self.assertIn(
            "Failure reason: RuntimeError: Import count mismatch",
            kwargs["body"],
        )
        self.assertIn("Traceback", kwargs["body"])


if __name__ == "__main__":
    unittest.main()
