import logging
import unittest
from unittest.mock import Mock, patch

from logger import setup_logging


class LoggerTests(unittest.TestCase):
    def test_setup_logging_silences_noisy_http_loggers(self):
        logger = Mock()

        with patch("logger.Path") as path_class:
            with patch("logger.logging.basicConfig"):
                with patch("logger.logging.FileHandler"):
                    with patch("logger.logging.StreamHandler"):
                        with patch(
                            "logger.logging.getLogger",
                            return_value=logger,
                        ) as get_logger:
                            setup_logging("20260513")

        self.assertEqual(get_logger.call_count, 4)
        logger.setLevel.assert_called_with(logging.WARNING)
        path_class.assert_any_call("logs")


if __name__ == "__main__":
    unittest.main()
