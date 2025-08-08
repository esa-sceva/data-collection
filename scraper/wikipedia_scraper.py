from typing import List, Type
from bs4 import ResultSet, Tag

from helper.utils import get_scraped_url_by_web_element
from model.base_url_publisher_models import SourceType
from model.wikipedia_models import WikipediaConfig, WikipediaSource
from scraper.base_url_publisher_scraper import BaseUrlPublisherScraper


class WikipediaScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[WikipediaConfig]:
        return WikipediaConfig

    def _scrape_journal(self, source: WikipediaSource) -> ResultSet | List[Tag] | None:
        pass

    def _scrape_issue_or_collection(self, source: WikipediaSource) -> List[Tag] | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            self._scrape_url(source.url)

            html_tag_list = self._driver.cdp.find_elements("div.mw-category-generated a", timeout=0.5)
            html_tag_list = [tag for tag in html_tag_list if tag.get_attribute("href")]

            pages_tags = []
            categories_links = []
            for tag in html_tag_list:
                href = tag.get_attribute("href")
                if source.with_categories and "Category:" in href:
                    categories_links.append(
                        get_scraped_url_by_web_element(
                            tag,
                            base_url=source.base_url or self._config_model.base_url
                        )
                    )
                else:
                    pages_tags.append(Tag(name="a", attrs={"href": href}))

            result = pages_tags
            for category_link in categories_links:
                result.extend(self._scrape_issue_or_collection(
                    WikipediaSource(
                        url=category_link,
                        type=str(SourceType.ISSUE_OR_COLLECTION),
                        with_categories=False,
                    )
                ))

            if not result:
                self._save_failure(source.url)

            self._logger.debug(f"HTML links found: {len(result)}")
            return result
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: WikipediaSource) -> Tag | None:
        pass
