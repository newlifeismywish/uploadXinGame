import os
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from commands.download_from_es import (
    download_from_es,
    resolve_output_paths,
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


def make_job_context(tmp_root):
    return SimpleNamespace(
        config=SimpleNamespace(
            es=SimpleNamespace(index="upload_xin_game_20260513"),
        ),
        date="20260513",
        force=True,
        state=SimpleNamespace(
            current_step=None,
            parsed_count=0,
            success_count=0,
            failed_count=0,
            processed_files=[],
            failed_files=[],
        ),
    )


class DownloadFromEsTests(unittest.TestCase):
    def test_resolve_output_paths_defaults_to_tmp(self):
        with patch.dict(os.environ, {}, clear=True):
            output_dir, archive_path = resolve_output_paths("20260513")

        self.assertEqual(output_dir, Path("/tmp") / "20260513")
        self.assertEqual(archive_path, Path("/tmp") / "20260513.7z")

    def test_download_from_es_writes_tsv_chunks_and_compresses_output_dir(self):
        docs = [
            {
                "_source": {
                    "mid": "m1",
                    "tid": "t1",
                    "score": 10,
                }
            },
            {
                "_source": {
                    "mid": "m2",
                    "tid": "t2",
                    "score": 20,
                }
            },
            {
                "_source": {
                    "mid": "m3",
                    "tid": "t3",
                    "extra": "ignored",
                }
            },
        ]

        es_client = Mock()

        with workspace_tmp_dir() as tmp_root:
            job_context = make_job_context(tmp_root)

            with patch.dict(
                os.environ,
                {
                    "DOWNLOAD_TMP_DIR": str(tmp_root),
                    "DOWNLOAD_ARCHIVE_DIR": str(tmp_root),
                },
                clear=True,
            ):
                with patch(
                    "commands.download_from_es.create_es_client",
                    return_value=es_client,
                ) as create_es_client:
                    with patch(
                        "commands.download_from_es.scan_all_documents",
                        return_value=iter(docs),
                    ) as scan_all_documents:
                        with patch(
                            "commands.download_from_es.compress_7z",
                        ) as compress_7z:
                            with patch(
                                "commands.download_from_es.ROWS_PER_FILE",
                                2,
                            ):
                                download_from_es(job_context)

            output_dir = tmp_root / "20260513"
            archive_path = tmp_root / "20260513.7z"

            self.assertEqual(
                (output_dir / "1.tsv").read_text(encoding="utf-8"),
                "mid\ttid\tscore\nm1\tt1\t10\nm2\tt2\t20\n",
            )
            self.assertEqual(
                (output_dir / "2.tsv").read_text(encoding="utf-8"),
                "mid\ttid\tscore\nm3\tt3\t\n",
            )

            create_es_client.assert_called_once_with(job_context.config.es)
            scan_all_documents.assert_called_once_with(
                es_client=es_client,
                index_name="upload_xin_game_20260513",
            )
            compress_7z.assert_called_once_with(
                source_path=output_dir,
                output_path=archive_path,
            )
            es_client.close.assert_called_once_with()
            self.assertEqual(job_context.state.parsed_count, 3)
            self.assertEqual(job_context.state.success_count, 3)
            self.assertEqual(len(job_context.state.processed_files), 2)
            self.assertEqual(
                job_context.state.current_step,
                "download_from_es_done",
            )


if __name__ == "__main__":
    unittest.main()
