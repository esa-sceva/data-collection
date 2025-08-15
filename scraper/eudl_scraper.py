import os
from typing import Type, List
from urllib.parse import urlparse

from helper.utils import get_scraped_url_by_bs_tag
from model.base_iterative_publisher_models import IterativePublisherScrapeIssueOutput
from model.eudl_models import EUDLConfig, EUDLJournal
from model.sql_models import ScraperFailure
from scraper.base_iterative_publisher_scraper import BaseIterativePublisherScraper


class EUDLScraper(BaseIterativePublisherScraper):
    @property
    def config_model_type(self) -> Type[EUDLConfig]:
        return EUDLConfig

    def _scrape_issue(
        self, journal: EUDLJournal, volume_num: str, issue_num: str
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_url = os.path.join(journal.url, volume_num, issue_num)
        self._logger.info(f"Processing Issue URL: {issue_url}")

        return self.__scrape_url(issue_url)

    def scrape_failure(self, failure: ScraperFailure) -> List[str]:
        link = failure.source
        self._logger.info(f"Scraping URL: {link}")

        return self.__scrape_url(link) or []

    def __scrape_url(self, url: str) -> IterativePublisherScrapeIssueOutput | None:
        """
        Scrape the issue URL for PDF links.

        Args:
            url (str): The issue URL.

        Returns:
            IterativePublisherScrapeIssueOutput | None: A list of PDF links found in the issue, or None if something went wrong.
        """

        parsed_url = urlparse(url)

        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        path = parsed_url.path.lstrip("/")
        _, _, volume_num, issue_num = path.split("/")

        try:
            scraper = self._scrape_url(url)

            tags = scraper.find_all("a", href=lambda href: href and "/doi/" in href)

            pdf_links = [
                get_scraped_url_by_bs_tag(tag, base_url).replace("/doi/", "/pdf/")
                for tag in tags
            ]
            if not pdf_links:
                self._save_failure(url)

            self._logger.debug(f"PDF links found: {len(pdf_links)}")
            return pdf_links
        except Exception as e:
            self._log_and_save_failure(
                url, f"Failed to process Issue {issue_num} in Volume {volume_num}. Error: {e}"
            )
            return None

    def _scrape_article(self, article_url: str) -> str | None:
        pass
