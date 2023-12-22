import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


class Mailer:
    def __init__(
        self, sender_email, sender_password, smtp_server, smtp_port, kindle_email
    ):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.kindle_email = kindle_email
        # self.email_subject = email_subject
        # self.attachment_path = attachment_path

    def send_attachment(self, attachment_path):
        email = MIMEMultipart()
        email["From"] = self.sender_email
        email["To"] = self.kindle_email
        # email["Subject"] = self.email_subject

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet_stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {attachment_path}"
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
            print("Email sent successfully!")
        except smtplib.SMTPException as e:
            print("Error whilst sending email", e)
            # raise SystemExit(e)
