import os
from typing import Type, List

from helper.utils import get_scraped_url_by_bs_tag
from model.base_iterative_publisher_models import (
    BaseIterativeIssuePublisherJournal,
    IterativePublisherScrapeIssueOutput,
    BaseIterativeIssuePublisherConfig,
)
from model.sql_models import ScraperFailure
from scraper.base_iterative_publisher_scraper import BaseIterativeIssuesPublisherScraper


class NationalAcademySciencesUkraineScraper(BaseIterativeIssuesPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseIterativeIssuePublisherConfig]:
        return BaseIterativeIssuePublisherConfig

    def _scrape_issue(
        self, journal: BaseIterativeIssuePublisherJournal, issue_num: int
    ) -> IterativePublisherScrapeIssueOutput | None:
        issue_url = os.path.join(journal.url, "issue", "view", str(issue_num))
        self._logger.info(f"Processing Issue URL: {issue_url}")

        return self.__scrape_issue_url(issue_url)

    def __scrape_issue_url(self, issue_url: str) -> IterativePublisherScrapeIssueOutput | None:
        _, issue_num = os.path.split(issue_url)

        try:
            scraper = self._scrape_url(issue_url)

            # Get all PDF links using Selenium to scroll and handle cookie popup once
            # Now find all PDF links using the class_="UD_Listings_ArticlePDF"
            tags = scraper.find_all(
                "a",
                class_=lambda cls: cls and "file" in cls,
                href=lambda href: href and "/article/view/" in href
            )

            pdf_links = [
                get_scraped_url_by_bs_tag(tag, self._config_model.base_url).replace("/view/", "/download/")
                for tag in tags
            ]

            self._logger.debug(f"PDF links found: {len(pdf_links)}")
            return pdf_links
        except Exception as e:
            self._log_and_save_failure(
                issue_url, f"Failed to process Issue {issue_num}. Error: {e}"
            )
            return None

    def _scrape_article(self, article_url: str) -> str | None:
        pass

    def journal_identifier(self, model: BaseIterativeIssuePublisherJournal) -> str:
        return model.name

    def scrape_failure(self, failure: ScraperFailure) -> List[str]:
        link = failure.source
        self._logger.info(f"Scraping URL: {link}")

        return self.__scrape_issue_url(link) or []
