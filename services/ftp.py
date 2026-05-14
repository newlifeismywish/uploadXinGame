from ftplib import FTP
from pathlib import Path
from typing import Union, Optional, List, Dict, Any

from config import load_config

_config = load_config()

def connect_ftp() -> FTP:
    ftp = FTP()
    ftp.connect(host=_config.ftp.host, port=_config.ftp.port, timeout=_config.ftp.timeout)
    ftp.login(user=_config.ftp.user, passwd=_config.ftp.password)
    return ftp


def download_file(
    *,
    remote_path: str,
    local_path: Union[str,Path]
) -> Path:
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    ftp = connect_ftp()

    try:
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)

        return local_path

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def upload_file(
    *,
    remote_path: str,
    local_path: Union[str,Path]
) -> str:
    local_path = Path(local_path)

    if not local_path.exists():
        raise FileNotFoundError(local_path)

    ftp = connect_ftp()

    try:
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_path}", f)

        return remote_path

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()
