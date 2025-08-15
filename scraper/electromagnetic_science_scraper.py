import os
from typing import Type, List
from urllib.parse import urlparse

from model.base_iterative_publisher_models import (
    IterativePublisherScrapeIssueOutput,
    BaseIterativePublisherConfig,
    BaseIterativePublisherJournal,
)
from model.sql_models import ScraperFailure
from scraper.base_iterative_publisher_scraper import BaseIterativePublisherScraper


class ElectromagneticScienceScraper(BaseIterativePublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseIterativePublisherConfig]:
        return BaseIterativePublisherConfig

    def _scrape_issue(
        self, journal: BaseIterativePublisherJournal, volume_num: str, issue_num: str
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_url = os.path.join(journal.url, "en", "article", volume_num, issue_num)
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

            tags = scraper.find_all(
            "a",
                href=lambda href: href and "javascript:void" in href,
                attrs={"onclick": lambda x: x and "downloadpdf" in x}
            )

            pdf_links = [
                os.path.join(
                    base_url, "article", "exportPdf"
                ) + "?language=en&id=" + tag.get("onclick").replace("downloadpdf('", "").replace("')", "")
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
