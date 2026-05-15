import os
import sys

MIN_PYTHON_VERSION = (3, 9)

if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(
        "uploadXinGame requires Python 3.9 or newer. "
        "Current Python is {}.{}.{}. "
        "Please run this project with python3.9.".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
    )

from dataclasses import dataclass
from pathlib import Path


try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


@dataclass(frozen=True)
class FTPConfig:
    host: str
    port: int
    user: str
    password: str
    remote_dir: str
    timeout: int


@dataclass(frozen=True)
class ESConfig:
    host: str
    username: str
    password: str
    timeout: int
    index: str

@dataclass(frozen=True)
class MailConfig:
    host: str
    port: int

    username: str
    password: str

    mail_from: str
    mail_to: list[str]
    timeout: int


@dataclass(frozen=True)
class AppConfig:
    ftp: FTPConfig
    es: ESConfig
    mail: MailConfig

    base_dir: str

    bulk_size: int
    workers: int


def required_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(
            "Missing required environment variable: {}. "
            "Check that .env exists in {} and that python-dotenv is installed "
            "for the Python interpreter running this script.".format(
                name,
                PROJECT_DIR,
            )
        ) from None


def load_ftp_config() -> FTPConfig:
    return FTPConfig(
        host=required_env("FTP_HOST"),
        port=int(os.getenv("FTP_PORT", "21")),
        user=required_env("FTP_USER"),
        password=required_env("FTP_PASSWORD"),
        remote_dir=required_env("FTP_REMOTE_DIR"),
        timeout=int(os.getenv("FTP_TIMEOUT", "30")),
    )


def load_es_config() -> ESConfig:
    return ESConfig(
        host=required_env("ES_HOST"),
        username=required_env("ES_USERNAME"),
        password=required_env("ES_PASSWORD"),
        timeout=int(os.getenv("ES_TIMEOUT", "30")),
        index=required_env("ES_INDEX"),
    )


def load_mail_config() -> MailConfig:
    return MailConfig(
        host=required_env("MAIL_HOST"),
        port=int(os.getenv("MAIL_PORT", "587")),
        username=required_env("MAIL_USERNAME"),
        password=required_env("MAIL_PASSWORD"),
        timeout=int(os.getenv("MAIL_TIMEOUT", "30")),
        mail_from=required_env("MAIL_FROM"),
        mail_to=[
            x.strip()
            for x in required_env("MAIL_TO").split(",")
            if x.strip()
        ],
    )


def load_config() -> AppConfig:
    return AppConfig(
        ftp=load_ftp_config(),
        es=load_es_config(),
        mail=load_mail_config(),
        base_dir=os.getenv("BASE_DIR", "BaseDirector"),
        bulk_size=int(os.getenv("BULK_SIZE", "1000")),
        workers=int(os.getenv("WORKERS", "4")),
    )
