import re
from typing import List, Type
from bs4 import Tag, ResultSet

from helper.utils import get_scraped_url_by_bs_tag, get_scraped_url_by
from model.base_url_publisher_models import BaseUrlPublisherSource, SourceType, BaseUrlPublisherConfig
from scraper.base_url_publisher_scraper import BaseUrlPublisherScraper


class TamkangUniversityPressScraper(BaseUrlPublisherScraper):
    @property
    def config_model_type(self) -> Type[BaseUrlPublisherConfig]:
        return BaseUrlPublisherConfig

    def _scrape_journal(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        try:
            self._scrape_url(source.url)

            buttons = self._driver.cdp.find_elements('a[data-toggle="collapse"]:not(.collapsed)', timeout=0.5)
            for button in buttons:
                button.click()
                self._driver.sleep(1)

            issues_tag_list = self._get_parsed_page_source().find_all(
                "a",
                href=lambda href: (
                        href
                        and "/articles/" in href
                        and len([m.start() for m in re.finditer('/', href)]) == 3
                )
            )

            # For each tag of issues previously collected, scrape the issue as a collection of articles
            pdf_tag_list = [
                tag
                for tags in (
                    self._scrape_issue_or_collection(BaseUrlPublisherSource(
                        url=get_scraped_url_by_bs_tag(issue_tag, self._config_model.base_url),
                        type=str(SourceType.ISSUE_OR_COLLECTION)
                    ))
                    for issue_tag in issues_tag_list
                )
                if tags for tag in tags
            ]

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Journal {source.url}. Error: {e}")
            return None

    def _scrape_issue_or_collection(self, source: BaseUrlPublisherSource) -> ResultSet | List[Tag] | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            if not (articles_tag_list := scraper.find_all(
                    "a",
                    href=lambda href: href and "/articles/jase" in href,
                    attrs={"itemprop": lambda x: x and "url" in x}
            )):
                self._save_failure(source.url)

            pdf_tag_list = [
                tag
                for article_tag in articles_tag_list
                if (tag := self._scrape_article(
                    BaseUrlPublisherSource(
                        url=get_scraped_url_by_bs_tag(article_tag, self._config_model.base_url),
                        type=str(SourceType.ARTICLE)
                    )
                )) is not None
            ]

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: BaseUrlPublisherSource) -> Tag | None:
        self._logger.info(f"Processing Article {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            if not (button_tag := scraper.find("button", attrs={"onclick": lambda x: x and "window.open" in x})):
                self._save_failure(source.url)
                return None

            pdf_tag = Tag(
                name="a",
                attrs={"href": get_scraped_url_by(button_tag["onclick"].split("'")[1], self._config_model.base_url)}
            )

            self._logger.debug(f"PDF link found: {pdf_tag['href']}")
            return pdf_tag
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Article {source.url}. Error: {e}")
            return None
