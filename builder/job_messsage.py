"""Job message builder for Telegram notifications."""

from urllib.parse import urlparse


class JobMessageBuilder:
    """Builds job messages from job data."""

    @staticmethod
    def get_source(url):
        """
        Extracts and returns the domain name from a URL.

        Args:
            url (str): The URL string.

        Returns:
            str: The domain source, or 'apply' if parsing fails.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain[4:] if domain.startswith("www.") else domain
        except Exception:  # pylint: disable=broad-exception-caught
            return "apply"

    @classmethod
    def build(cls, job):
        """
        Builds a formatted job message.

        Args:
            job (tuple): A tuple containing job data.

        Returns:
            str: Formatted job message.
        """
        _, title, company, location, links, posted_at = job
        link_lines = ""
        for link in links.split(","):
            safe_link = link.strip()
            if safe_link:
                source = cls.get_source(safe_link)
                link_lines += f"🔗 <a href='{safe_link}'>{source}</a>\n"

        return (
            f"📋 <b>{title}</b>\n"
            f"🏢 <i>{company}</i>\n"
            f"🕒 Posted: {posted_at}\n"
            f"{link_lines.strip()}"
        )
