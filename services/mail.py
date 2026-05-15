# services/mail.py

import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from config import MailConfig, load_mail_config


def send(
    *,
    subject: str,
    body: str,
    to_list=None,
    is_html: bool = False,
    config: Optional[MailConfig] = None,
) -> None:

    mail_config = config or load_mail_config()

    if to_list is None:
        to_list = mail_config.mail_to

    message = MIMEMultipart()

    message["From"] = mail_config.mail_from
    message["To"] = ",".join(to_list)
    message["Subject"] = subject

    content_type = "html" if is_html else "plain"

    message.attach(
        MIMEText(
            body,
            content_type,
            "utf-8",
        )
    )

    smtp = smtplib.SMTP(
        host=mail_config.host,
        port=mail_config.port,
        timeout=mail_config.timeout,
    )

    try:
        smtp.starttls()

        smtp.login(
            mail_config.username,
            mail_config.password,
        )

        smtp.sendmail(
            from_addr=mail_config.mail_from,
            to_addrs=to_list,
            msg=message.as_string(),
        )

    finally:
        try:
            smtp.quit()
        except Exception:
            smtp.close()
