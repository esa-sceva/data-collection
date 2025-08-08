from typing import List, Type
from bs4 import ResultSet, Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_url_publisher_models import BaseUrlPublisherSource, BaseUrlPublisherConfig, SourceType
from scraper.base_url_publisher_scraper import BaseUrlPublisherScraper


class ACIGJournalScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseUrlPublisherConfig]:
        return BaseUrlPublisherConfig

    def _scrape_journal(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        self._logger.info(f"Processing Journal {source.url}")

        base_url = source.base_url or self._config_model.base_url

        try:
            scraper = self._scrape_url(source.url)

            # unique issue tags
            issue_links = set([
                get_scraped_url_by_bs_tag(tag, base_url)
                for tag in scraper.find_all("a", class_=lambda cls: cls and "archiveVolume" in cls)
            ])

            pdf_tag_list = [
                tag
                for issue_link in issue_links
                if (tags := self._scrape_issue_or_collection(
                    BaseUrlPublisherSource(url=issue_link, type=str(SourceType.ISSUE_OR_COLLECTION))
                ))
                for tag in tags
            ]

            if not pdf_tag_list:
                self._save_failure(source.url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_issue_or_collection(self, source: BaseUrlPublisherSource) -> List[Tag] | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            if not (pdf_tag_list := scraper.find_all(
                "a", href=lambda href: href and ".pdf" in href, class_=lambda cls: cls and "magFullT" in cls
            )):
                self._save_failure(source.url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: BaseUrlPublisherSource) -> Tag | None:
        pass
