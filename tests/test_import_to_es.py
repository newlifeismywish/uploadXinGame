import unittest

from services.import_to_es import build_es_action


class BuildEsActionTests(unittest.TestCase):
    def test_build_es_action_uses_mid_and_tid_as_document_id(self):
        action = {
            "_source": {
                "mid": "m001",
                "tid": "t002",
                "score": 10,
            }
        }

        result = build_es_action(action, "upload_xin_game_20260513")

        self.assertEqual(result["_op_type"], "create")
        self.assertEqual(result["_index"], "upload_xin_game_20260513")
        self.assertEqual(result["_id"], "m001_t002")
        self.assertEqual(result["_source"], action["_source"])


if __name__ == "__main__":
    unittest.main()
