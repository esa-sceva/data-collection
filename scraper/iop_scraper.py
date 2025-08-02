from copy import deepcopy
from typing import List, Type
from bs4 import ResultSet, Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_url_publisher_models import BaseUrlPublisherConfig
from scraper.base_url_publisher_scraper import BaseUrlPublisherSource, BaseUrlPublisherScraper


class IOPScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseUrlPublisherConfig]:
        return BaseUrlPublisherConfig

    def _scrape_journal(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        self._logger.info(f"Processing Journal {source.url}")

        pdf_tag_list = []
        current_source = deepcopy(source)
        while True:
            pdf_tag_issue_list = self._scrape_issue_or_collection(current_source)
            if pdf_tag_issue_list is not None:
                pdf_tag_list.extend(pdf_tag_issue_list)

            # now, find the link to the next issue or collection
            scraper = self._scrape_url(current_source.url)

            next_issue_tag = scraper.find(
                "a",
                class_=lambda cls: cls and "ml-1" in cls,
                href=lambda href: href and "/issue/" in href,
            )
            if next_issue_tag:
                next_issue_url = get_scraped_url_by_bs_tag(next_issue_tag, self._config_model.base_url)
                current_source.url = next_issue_url
                self._logger.info(f"Next issue URL: {current_source.url}")
            else:
                self._logger.info("No more issues or collections found.")
                break

    def _scrape_issue_or_collection(self, source: BaseUrlPublisherSource) -> ResultSet | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            # Find all PDF links using appropriate class or tag (if lambda returns True, it will be included in the list)
            if not (pdf_tag_list := scraper.find_all(
                    "a", href=lambda href: href and "/article/" in href and "/pdf" in href
            )):
                self._save_failure(source.url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: BaseUrlPublisherSource) -> Tag | None:
        pass
