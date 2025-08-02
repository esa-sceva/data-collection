from typing import List, Type
from bs4 import ResultSet, Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_url_publisher_models import BaseUrlPublisherConfig, SourceType
from scraper.base_url_publisher_scraper import BaseUrlPublisherSource, BaseUrlPublisherScraper


class AEMJournalScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseUrlPublisherConfig]:
        return BaseUrlPublisherConfig

    def _scrape_journal(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        self._logger.info(f"Processing Journal {source.url}")

        pdf_tag_list = []
        try:
            scraper = self._scrape_url(source.url)

            issue_or_collection_tags = scraper.find_all(
                "a", class_="title", href=lambda href: href and "/issue/view" in href
            )
            if not issue_or_collection_tags:
                return None

            # Iterate through each tag and extract the PDF links
            for tag in issue_or_collection_tags:
                pdf_tag_list.extend(self._scrape_issue_or_collection(
                    BaseUrlPublisherSource(
                        url=get_scraped_url_by_bs_tag(tag, self._config_model.base_url),
                        type=str(SourceType.ISSUE_OR_COLLECTION),
                    )
                ))

            self._logger.debug(f"Total PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Journal {source.url}. Error: {e}")
            return None

    def _scrape_issue_or_collection(self, source: BaseUrlPublisherSource) -> ResultSet | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            # Find all PDF links using appropriate class or tag (if lambda returns True, it will be included in the list)
            if not (pdf_tag_list := scraper.find_all(
                    "a",
                    class_=lambda cls: cls and "pdf" in cls,
                    href=lambda href: href and "/article/view" in href
            )):
                self._save_failure(source.url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: BaseUrlPublisherSource) -> Tag | None:
        pass
