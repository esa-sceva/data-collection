import os
from abc import ABC
from typing import Type, List
from urllib.parse import urlparse

from bs4 import ResultSet

from helper.utils import get_scraped_url_by_bs_tag
from model.base_iterative_publisher_models import (
    BaseIterativeIssuePublisherJournal,
    IterativePublisherScrapeIssueOutput,
    BaseIterativeIssuePublisherConfig,
)
from model.sql_models import ScraperFailure
from scraper.base_iterative_publisher_scraper import BaseIterativeIssuesPublisherScraper


class FramedScraper(BaseIterativeIssuesPublisherScraper, ABC):
    @property
    def config_model_type(self) -> Type[BaseIterativeIssuePublisherConfig]:
        return BaseIterativeIssuePublisherConfig

    def _get_issue_num(self, issue_url: str) -> str:
        """
        Extract the issue number from the issue URL.

        Args:
            issue_url (str): The URL of the issue.

        Returns:
            int: The issue number extracted from the URL.
        """
        parsed_url = urlparse(issue_url)
        path = parsed_url.path.lstrip("/")
        return path[-1]

    def _get_base_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def _scrape_issue(
        self, journal: BaseIterativeIssuePublisherJournal, issue_num: str
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_url = os.path.join(journal.url, "issue", "view", issue_num)
        self._logger.info(f"Processing Issue URL: {issue_url}")

        return self._scrape_issue_url(issue_url)

    def _get_pdf_tags(self, issue_url: str, cls_tag: str | None = "pdf") -> ResultSet:
        scraper = self._scrape_url(issue_url)

        return scraper.find_all(
            "a",
            class_=lambda cls: cls and cls_tag in cls,
            href=lambda href: href and "/article/view" in href
        )

    def _scrape_issue_url(
        self, issue_url: str, cls_tag: str | None = "pdf"
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_num = self._get_issue_num(issue_url)
        base_url = self._get_base_url(issue_url)

        try:
            tags = self._get_pdf_tags(issue_url, cls_tag)

            pdf_links = [
                pdf_link
                for tag in tags
                if (pdf_link := self._scrape_article(get_scraped_url_by_bs_tag(tag, base_url)))
            ]

            self._logger.debug(f"PDF links found: {len(pdf_links)}")
            return pdf_links
        except Exception as e:
            self._log_and_save_failure(
                issue_url, f"Failed to process Issue {issue_num}. Error: {e}"
            )
            return None

    def _scrape_article(self, article_url: str) -> str | None:
        self._logger.info(f"Processing article URL: {article_url}")
        base_url = self._get_base_url(article_url)

        try:
            scraper = self._scrape_url(article_url)

            # Find the PDF link in the article page
            if pdf_tag := scraper.find("a", class_="download", href=True):
                pdf_link = get_scraped_url_by_bs_tag(pdf_tag, base_url)
                self._logger.debug(f"PDF link found: {pdf_link}")
                return pdf_link

            self._logger.warning(f"No PDF link found for article: {article_url}")
            return None
        except Exception as e:
            self._log_and_save_failure(
                article_url, f"Failed to scrape Article {article_url}. Error: {e}"
            )
            return None

    def scrape_failure(self, failure: ScraperFailure) -> List[str]:
        link = failure.source
        self._logger.info(f"Scraping URL: {link}")

        if "article" in failure.message.lower():
            result = self._scrape_article(link)
            return [result] or []

        return self._scrape_issue_url(link) or []


class RigaTechnicalUniversityScraper(FramedScraper):
    pass


class JTITScraper(FramedScraper):
    pass


class CIMSJournalScraper(FramedScraper):
    pass


class CSTJournalScraper(FramedScraper):
    def _scrape_issue_url(
        self, issue_url: str, cls_tag: str | None = "pdf"
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_num = self._get_issue_num(issue_url)
        base_url = self._get_base_url(issue_url)

        try:
            tags = self._get_pdf_tags(issue_url, cls_tag)
            if not tags:
                tags = self._get_pdf_tags(issue_url, "file")

            pdf_links = [
                pdf_link
                for tag in tags
                if (pdf_link := self._scrape_article(get_scraped_url_by_bs_tag(tag, base_url)))
            ]

            self._logger.debug(f"PDF links found: {len(pdf_links)}")
            return pdf_links
        except Exception as e:
            self._log_and_save_failure(
                issue_url, f"Failed to process Issue {issue_num}. Error: {e}"
            )
            return None

