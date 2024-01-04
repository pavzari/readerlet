import json
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import click


class Mailer:
    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_server: str,
        smtp_port: str,
        kindle_email: str,
    ):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.kindle_email = kindle_email
        # self.email_subject = email_subject

    def send_attachment(self, attachment_path: Path) -> None:
        email = MIMEMultipart()
        email["From"] = self.sender_email
        email["To"] = self.kindle_email
        # email["Subject"] = self.email_subject

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet_stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {attachment_path.name}"
            )
            email.attach(part)
            email_str = email.as_string()

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.smtp_server, self.smtp_port, context=context
            ) as connection:
                connection.login(self.sender_email, self.sender_password)
                connection.sendmail(self.sender_email, self.kindle_email, email_str)
                connection.quit()
        except smtplib.SMTPException as e:
            raise click.ClickException("Error whilst sending email:", e)


def send_via_email(attachment_path: Path) -> None:
    config_file = "email_config.json"
    cfg = Path(click.get_app_dir("readerlet"), config_file)

    if not cfg.exists():
        raise click.ClickException(
            f"Email configuration json file not found at {cfg}. "
            f"See example config format:\n\n"
            f"{{'sender_email': 'my@email.com',"
            f"'sender_password': 'password123', \n"
            f"'smtp_server': 'smtp.gmail.com',\n"
            f"'smtp_port': 465,\n"
            f"'kindle_email': 'my_kindle@kindle.com'\n}}"
        )
    try:
        with open(cfg) as f:
            config = json.load(f)
        mailer = Mailer(**config)
    except json.JSONDecodeError:
        raise click.ClickException(f"Error: File '{cfg}' is not a valid JSON file.")

    mailer.send_attachment(attachment_path)
