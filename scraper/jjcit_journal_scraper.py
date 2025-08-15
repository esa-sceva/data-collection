from typing import Type, List
from bs4 import Tag, ResultSet

from helper.utils import get_scraped_url_by_bs_tag
from model.base_url_publisher_models import BaseUrlPublisherConfig, BaseUrlPublisherSource
from scraper.base_url_publisher_scraper import BaseUrlPublisherScraper


class JJCITJournalScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseUrlPublisherConfig]:
        return BaseUrlPublisherConfig

    def _scrape_journal(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        try:
            scraper = self._scrape_url(source.url)

            tags = scraper.find_all(
                "a",
                href=lambda href: href and "/issue/" in href
            )

            pdf_tags = [
                Tag(name="a", attrs={"href": get_scraped_url_by_bs_tag(
                        tag, self._config_model.base_url
                    ).replace("/issue/", "/issue/download/")
                })
                for tag in tags
            ]

            self._logger.debug(f"PDF links found: {len(pdf_tags)}")
            return pdf_tags
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Journal {source.url}. Error: {e}")
            return None

    def _scrape_issue_or_collection(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        pass

    def _scrape_article(self, source: BaseUrlPublisherSource) -> Tag | None:
        pass
