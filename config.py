import os
import sys

from pathlib import Path


MIN_PYTHON_VERSION = (3, 6)

if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(
        "uploadXinGame requires Python 3.6 or newer. "
        "Current Python is {}.{}.{}. "
        "Please run this project with python3.6 or newer.".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
    )


PROJECT_DIR = Path(__file__).resolve().parent


def load_env_file(env_path=None):
    env_path = Path(env_path or PROJECT_DIR / ".env")

    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in ("'", '"')
            ):
                value = value[1:-1]

            if key:
                os.environ.setdefault(key, value)


load_env_file()


class FTPConfig:
    def __init__(self, host, port, user, password, remote_dir, timeout):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.remote_dir = remote_dir
        self.timeout = timeout


class ESConfig:
    def __init__(self, host, username, password, timeout, index):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.index = index


class MailConfig:
    def __init__(
        self,
        host,
        port,
        username,
        password,
        mail_from,
        mail_to,
        timeout,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mail_from = mail_from
        self.mail_to = mail_to
        self.timeout = timeout


class AppConfig:
    def __init__(self, ftp, es, mail, base_dir, bulk_size, workers):
        self.ftp = ftp
        self.es = es
        self.mail = mail
        self.base_dir = base_dir
        self.bulk_size = bulk_size
        self.workers = workers


def required_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(
            "Missing required environment variable: {}. "
            "Check that .env exists in {} and contains this setting.".format(
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
