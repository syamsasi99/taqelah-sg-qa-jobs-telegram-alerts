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
        Builds a formatted job message from a job dictionary.

        Args:
            job (dict): A dictionary containing job data.

        Returns:
            str: Formatted job message.
        """
        title = job.get("job_title", "No Title")
        company = job.get("employer_name", "Unknown Company")

        # Work Location
        if job.get("job_is_remote"):
            work_location = "Worldwide"
        else:
            work_location = job.get("job_location") or job.get("job_country", "Unknown")

        # Work Arrangement
        desc = job.get("job_description", "").lower()
        if job.get("job_is_remote"):
            work_arrangement = "Remote"
        elif "hybrid" in desc:
            work_arrangement = "Hybrid"
        else:
            work_arrangement = "Onsite"

        # Work Status
        emp_type = job.get("job_employment_type", "").lower()
        if "full" in emp_type:
            work_status = "Full Time"
        elif "part" in emp_type:
            work_status = "Part Time"
        elif "contract" in emp_type:
            work_status = "Contract"
        else:
            work_status = "Not Specified"

        # Salary Range
        min_salary = job.get("job_min_salary")
        max_salary = job.get("job_max_salary")
        salary_period = (job.get("job_salary_period") or "").capitalize()

        if min_salary is not None and max_salary is not None:
            salary_info = f"💰 Salary: ${min_salary:,} – ${max_salary:,}"
            if salary_period:
                salary_info += f" per {salary_period}"
        elif min_salary is not None:
            salary_info = f"💰 Salary: From ${min_salary:,}"
        elif max_salary is not None:
            salary_info = f"💰 Salary: Up to ${max_salary:,}"
        else:
            salary_info = None

        # Links
        apply_links = set()
        if job.get("job_apply_link"):
            apply_links.add(job["job_apply_link"])

        if isinstance(job.get("apply_options"), list):
            for option in job["apply_options"]:
                link = option.get("apply_link")
                if link:
                    apply_links.add(link)

        link_lines = ""
        for link in apply_links:
            source = cls.get_source(link)
            if source:
                link_lines += f"🔗 <a href='{link}'>{source}</a>\n"

        posted_at = job.get("job_posted_at", "N/A")

        parts = [
            f"📋 <b>{title}</b>",
            f"🏢 <i>{company}</i>",
            f"🕒 Posted: {posted_at}",
            f"🌍 Location: {work_location}",
            f"🏠 Arrangement: {work_arrangement}",
            f"📌 Status: {work_status}",
        ]

        if salary_info:
            parts.append(salary_info)

        if link_lines.strip():
            parts.append(link_lines.strip())

        return "\n".join(parts)

