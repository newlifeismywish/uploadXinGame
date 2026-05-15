import unittest
from unittest.mock import Mock, patch

from services.es import set_refresh_interval


class EsServiceTests(unittest.TestCase):
    def test_set_refresh_interval_uses_es7_body_argument(self):
        es_client = Mock()

        with patch("services.es.create_es_client", return_value=es_client):
            set_refresh_interval("upload_xin_game_20260514", "-1")

        es_client.indices.put_settings.assert_called_once_with(
            index="upload_xin_game_20260514",
            body={
                "index": {
                    "refresh_interval": "-1",
                }
            },
        )
        es_client.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
