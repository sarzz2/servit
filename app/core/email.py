import logging
from pathlib import Path

import premailer
import requests
from jinja2 import Environment, FileSystemLoader

from .config import Settings

log = logging.getLogger("fastapi")
settings = Settings()

template_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates/emails")), autoescape=True
)


class MailgunService:
    def __init__(self):
        self.api_url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
        self.api_key = settings.MAILGUN_API_KEY

    def send_verification_email(self, email: str, token: str, username: str) -> None:
        verification_url = f"{settings.BASE_URL}/verify-email?token={token}"

        # Render HTML template
        template = template_env.get_template("verification.html")
        html_content = template.render(username=username, verification_url=verification_url)
        # Inline CSS
        html_content = premailer.transform(html_content)

        # Mailgun API request
        response = requests.post(
            self.api_url,
            auth=("api", self.api_key),
            data={
                "from": f"Servit <noreply@{settings.MAILGUN_DOMAIN}>",
                "to": [email],
                "subject": "Verify Your Email Address",
                "html": html_content,
            },
        )

        if response.status_code != 200:
            log.error(f"Mailgun API error: {response.text}")
