import os
from typing import Type, List

from helper.utils import get_scraped_url_by_bs_tag
from model.base_iterative_publisher_models import IterativePublisherScrapeIssueOutput
from model.eudl_models import EUDLConfig, EUDLJournal
from model.sql_models import ScraperFailure
from scraper.base_iterative_publisher_scraper import BaseIterativePublisherScraper


class RadioEngCZScraper(BaseIterativePublisherScraper):
    @property
    def config_model_type(self) -> Type[EUDLConfig]:
        return EUDLConfig

    def journal_identifier(self, model: EUDLJournal) -> str:
        return model.name

    def _scrape_issue(
        self, journal: EUDLJournal, volume_num: int, issue_num: int
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_url = os.path.join(journal.url, "papers", f"{volume_num}-{issue_num}.htm")
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
            BaseIterativePublisherScrapeIssueOutput | None: A list of PDF links found in the issue, or None if something went wrong.
        """
        path, volume_issue_num = os.path.split(url)
        volume_num, issue_num = volume_issue_num.split("-")
        issue_num = issue_num.replace(".htm", "")

        try:
            scraper = self._scrape_url(url)

            # Get all PDF links using Selenium to scroll and handle cookie popup once
            # Now find all PDF links using the class_="UD_Listings_ArticlePDF"
            tags = scraper.find_all("a", href=lambda href: href and "fulltexts" in href and ".pdf" in href)

            pdf_links = [
                get_scraped_url_by_bs_tag(tag, self._config_model.base_url)
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
