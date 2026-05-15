import email
import unittest
from unittest.mock import patch

from config import MailConfig
from services.mail import send


def first_part_payload(message, content_type):
    for part in message.walk():
        if part.get_content_type() == content_type:
            return part.get_payload(decode=True).decode(part.get_content_charset())

    return None


def make_mail_config():
    return MailConfig(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-password",
        mail_from="noreply@example.com",
        mail_to=["one@example.com", "two@example.com"],
        timeout=30,
    )


class FakeSMTP:
    def __init__(self, *, quit_error=None):
        self.quit_error = quit_error
        self.starttls_called = False
        self.login_args = None
        self.sendmail_args = None
        self.quit_called = False
        self.close_called = False

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_args = (username, password)

    def sendmail(self, from_addr, to_addrs, msg):
        self.sendmail_args = (from_addr, to_addrs, msg)

    def quit(self):
        self.quit_called = True
        if self.quit_error:
            raise self.quit_error

    def close(self):
        self.close_called = True


class SendMailTests(unittest.TestCase):
    def test_send_uses_config_defaults_and_plain_text_body(self):
        smtp = FakeSMTP()

        with patch("services.mail.smtplib.SMTP", return_value=smtp) as smtp_class:
            send(
                subject="Job succeeded",
                body="All records imported",
                config=make_mail_config(),
            )

        smtp_class.assert_called_once_with(
            host="smtp.example.com",
            port=587,
            timeout=30,
        )
        self.assertTrue(smtp.starttls_called)
        self.assertEqual(smtp.login_args, ("smtp-user", "smtp-password"))
        self.assertTrue(smtp.quit_called)
        self.assertFalse(smtp.close_called)

        from_addr, to_addrs, raw_message = smtp.sendmail_args
        self.assertEqual(from_addr, "noreply@example.com")
        self.assertEqual(to_addrs, ["one@example.com", "two@example.com"])

        message = email.message_from_string(raw_message)
        self.assertEqual(message["From"], "noreply@example.com")
        self.assertEqual(message["To"], "one@example.com,two@example.com")
        self.assertEqual(message["Subject"], "Job succeeded")
        self.assertIn("Content-Type: text/plain", raw_message)
        self.assertEqual(
            first_part_payload(message, "text/plain"),
            "All records imported",
        )

    def test_send_accepts_custom_recipients_and_html_body(self):
        smtp = FakeSMTP()

        with patch("services.mail.smtplib.SMTP", return_value=smtp):
            send(
                subject="Job failed",
                body="<strong>Failed step: validate_index_count</strong>",
                to_list=["ops@example.com"],
                is_html=True,
                config=make_mail_config(),
            )

        from_addr, to_addrs, raw_message = smtp.sendmail_args
        self.assertEqual(from_addr, "noreply@example.com")
        self.assertEqual(to_addrs, ["ops@example.com"])

        message = email.message_from_string(raw_message)
        self.assertEqual(message["To"], "ops@example.com")
        self.assertIn("Content-Type: text/html", raw_message)
        self.assertEqual(
            first_part_payload(message, "text/html"),
            "<strong>Failed step: validate_index_count</strong>",
        )

    def test_send_closes_smtp_when_quit_fails(self):
        smtp = FakeSMTP(quit_error=RuntimeError("quit failed"))

        with patch("services.mail.smtplib.SMTP", return_value=smtp):
            send(
                subject="Job finished",
                body="Done",
                config=make_mail_config(),
            )

        self.assertTrue(smtp.quit_called)
        self.assertTrue(smtp.close_called)


if __name__ == "__main__":
    unittest.main()
