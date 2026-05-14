import os

from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()


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


def load_config() -> AppConfig:
    return AppConfig(
        ftp=FTPConfig(
            host=os.environ["FTP_HOST"],
            port=int(os.getenv("FTP_PORT", "21")),
            user=os.environ["FTP_USER"],
            password=os.environ["FTP_PASSWORD"],
            remote_dir=os.environ["FTP_REMOTE_DIR"],
            timeout=int(os.getenv("FTP_TIMEOUT", "30")),
        ),

        es=ESConfig(
            host=os.environ["ES_HOST"],
            username=os.environ["ES_USERNAME"],
            password=os.environ["ES_PASSWORD"],
            timeout=int(os.getenv("ES_TIMEOUT", "30")),
            index=os.environ["ES_INDEX"],
        ),

        mail=MailConfig(
            host=os.environ["MAIL_HOST"],
            port=int(os.getenv("MAIL_PORT", "587")),

            username=os.environ["MAIL_USERNAME"],
            password=os.environ["MAIL_PASSWORD"],
            timeout=int(os.getenv("MAIL_TIMEOUT", "30")),
            mail_from=os.environ["MAIL_FROM"],
            mail_to=[
                x.strip()
                for x in os.environ["MAIL_TO"].split(",")
                if x.strip()
            ],
        ),

        base_dir=os.getenv("BASE_DIR", "BaseDirector"),

        bulk_size=int(os.getenv("BULK_SIZE", "1000")),
        workers=int(os.getenv("WORKERS", "4")),
    )
