import json
import shutil
import unittest
import uuid

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from commands.create_transform import (
    create_transform,
    load_transform_template,
    resolve_transform_id,
    set_source_index,
)


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


def make_job_context():
    return SimpleNamespace(
        config=SimpleNamespace(
            es=SimpleNamespace(index="playergameinfo_20260518"),
        ),
        date="20260518",
        force=False,
        state=SimpleNamespace(
            current_step=None,
            parsed_count=0,
            success_count=0,
            failed_count=0,
            processed_files=[],
            failed_files=[],
        ),
    )


class CreateTransformTests(unittest.TestCase):
    def test_load_transform_template_reads_json_object(self):
        with workspace_tmp_dir() as tmp_root:
            template_path = tmp_root / "template.json"
            template_path.write_text(
                json.dumps({"source": {"index": ["old"]}}),
                encoding="utf-8",
            )

            result = load_transform_template(template_path)

        self.assertEqual(result, {"source": {"index": ["old"]}})

    def test_set_source_index_replaces_list_source_index(self):
        body = {
            "source": {
                "index": ["playergameinfo_20250101"],
            }
        }

        set_source_index(body, "playergameinfo_20260518")

        self.assertEqual(
            body["source"]["index"],
            ["playergameinfo_20260518"],
        )

    def test_resolve_transform_id_defaults_to_dest_index_and_date(self):
        body = {
            "dest": {
                "index": "user_daily_playergameinfo",
            }
        }

        self.assertEqual(
            resolve_transform_id(body, "20260518"),
            "user_daily_playergameinfo_20260518",
        )

    def test_resolve_transform_id_removes_template_transform_id(self):
        body = {
            "transform_id": "sample_transform",
            "dest": {
                "index": "user_daily_playergameinfo",
            },
        }

        self.assertEqual(
            resolve_transform_id(body, "20260518"),
            "sample_transform",
        )
        self.assertNotIn("transform_id", body)

    def test_create_transform_puts_template_with_resolved_source_index(self):
        job_context = make_job_context()
        es_client = Mock()
        template_body = {
            "source": {
                "index": ["playergameinfo_20250101"],
                "query": {
                    "match_all": {},
                },
            },
            "dest": {
                "index": "user_daily_playergameinfo",
            },
        }

        with patch(
            "commands.create_transform.load_transform_template",
            return_value=template_body,
        ):
            with patch(
                "commands.create_transform.create_es_client",
                return_value=es_client,
            ) as create_es_client:
                with patch(
                    "commands.create_transform.exists_transform",
                    return_value=False,
                ) as exists_transform:
                    with patch(
                        "commands.create_transform.put_transform",
                    ) as put_transform:
                        create_transform(job_context)

        create_es_client.assert_called_once_with(job_context.config.es)
        exists_transform.assert_called_once_with(
            es_client,
            "user_daily_playergameinfo_20260518",
        )
        put_transform.assert_called_once_with(
            es_client=es_client,
            transform_id="user_daily_playergameinfo_20260518",
            transform_body={
                "source": {
                    "index": ["playergameinfo_20260518"],
                    "query": {
                        "match_all": {},
                    },
                },
                "dest": {
                    "index": "user_daily_playergameinfo",
                },
            },
        )
        es_client.close.assert_called_once_with()
        self.assertEqual(job_context.state.parsed_count, 1)
        self.assertEqual(job_context.state.success_count, 1)
        self.assertEqual(
            job_context.state.current_step,
            "create_transform_done",
        )

    def test_create_transform_recreates_existing_transform_when_forced(self):
        job_context = make_job_context()
        job_context.force = True
        es_client = Mock()

        with patch(
            "commands.create_transform.load_transform_template",
            return_value={
                "source": {
                    "index": ["old"],
                },
                "dest": {
                    "index": "user_daily_playergameinfo",
                },
            },
        ):
            with patch(
                "commands.create_transform.create_es_client",
                return_value=es_client,
            ):
                with patch(
                    "commands.create_transform.exists_transform",
                    return_value=True,
                ):
                    with patch(
                        "commands.create_transform.delete_transform",
                    ) as delete_transform:
                        with patch(
                            "commands.create_transform.put_transform",
                        ):
                            create_transform(job_context)

        delete_transform.assert_called_once_with(
            es_client=es_client,
            transform_id="user_daily_playergameinfo_20260518",
        )

    def test_create_transform_fails_when_existing_transform_is_not_forced(self):
        job_context = make_job_context()
        es_client = Mock()

        with patch(
            "commands.create_transform.load_transform_template",
            return_value={
                "source": {
                    "index": ["old"],
                },
                "dest": {
                    "index": "user_daily_playergameinfo",
                },
            },
        ):
            with patch(
                "commands.create_transform.create_es_client",
                return_value=es_client,
            ):
                with patch(
                    "commands.create_transform.exists_transform",
                    return_value=True,
                ):
                    with self.assertRaises(RuntimeError):
                        create_transform(job_context)

        es_client.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
