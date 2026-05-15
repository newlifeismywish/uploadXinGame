from ftplib import FTP
from pathlib import Path
from typing import Optional, Union

from config import FTPConfig, load_ftp_config


def connect_ftp(config: Optional[FTPConfig] = None) -> FTP:
    ftp_config = config or load_ftp_config()

    ftp = FTP()
    ftp.connect(
        host=ftp_config.host,
        port=ftp_config.port,
        timeout=ftp_config.timeout,
    )
    ftp.login(
        user=ftp_config.user,
        passwd=ftp_config.password,
    )
    return ftp


def download_file(
    *,
    remote_path: str,
    local_path: Union[str, Path],
    config: Optional[FTPConfig] = None,
) -> Path:
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    part_path = local_path.with_name(local_path.name + ".part")

    if part_path.exists():
        part_path.unlink()

    ftp = connect_ftp(config)

    try:
        with open(part_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)

        part_path.replace(local_path)
        return local_path

    except Exception:
        if part_path.exists():
            part_path.unlink()
        raise

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def upload_file(
    *,
    remote_path: str,
    local_path: Union[str, Path],
    config: Optional[FTPConfig] = None,
) -> str:
    local_path = Path(local_path)

    if not local_path.exists():
        raise FileNotFoundError(local_path)

    ftp = connect_ftp(config)

    try:
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_path}", f)

        return remote_path

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()
