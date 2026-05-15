# services/zip.py

import subprocess

from pathlib import Path
from typing import Union


def compress(
    *,
    source_path: Union[str, Path],
    output_path: Union[str, Path],
    threads: int = 0,
    level: int = 1,
) -> Path:
    source_path = Path(source_path)
    output_path = Path(output_path)

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cmd = [
        "7za",
        "a",
        "-t7z",

        "-mx={}".format(level),

        "-mmt={}".format(
            "on" if threads == 0 else threads
        ),

        str(output_path),
        str(source_path),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "7za compress failed\n"
            "stdout:\n{}\n"
            "stderr:\n{}".format(
                result.stdout,
                result.stderr,
            )
        )

    return output_path


def extract(
    *,
    zip_path: Union[str, Path],
    output_dir: Union[str, Path],
    overwrite: bool = True,
) -> Path:
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)

    if not zip_path.exists():
        raise FileNotFoundError(zip_path)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    cmd = [
        "7za",
        "x",

        "-y" if overwrite else "-aos",

        str(zip_path),

        "-o{}".format(output_dir),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "7za extract failed\n"
            "stdout:\n{}\n"
            "stderr:\n{}".format(
                result.stdout,
                result.stderr,
            )
        )

    return output_dir
