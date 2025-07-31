from typing import Type, List
from bs4 import Tag

from helper.utils import get_scraped_url_by_bs_tag, get_scraped_url_by_web_element
from model.base_pagination_publisher_models import BasePaginationPublisherConfig, BasePaginationPublisherScrapeOutput
from scraper.base_pagination_publisher_scraper import BasePaginationPublisherScraper


class NatureScraper(BasePaginationPublisherScraper):
    @property
    def config_model_type(self) -> Type[BasePaginationPublisherConfig]:
        return BasePaginationPublisherConfig

    def scrape(self) -> BasePaginationPublisherScrapeOutput | None:
        pdf_tags = []
        for idx, source in enumerate(self._config_model.sources):
            pdf_tags.extend(self._scrape_landing_page(source.landing_page_url, idx + 1))

        return {"Nature": [
            get_scraped_url_by_bs_tag(tag, self._config_model.base_url) for tag in pdf_tags
        ]} if pdf_tags else None

    def _scrape_landing_page(self, landing_page_url: str, source_number: int) -> List[Tag]:
        return self._scrape_pagination(landing_page_url, source_number)

    def _scrape_page(self, url: str) -> List[Tag] | None:
        try:
            self._scrape_url(url)

            try:
                tag_rows = self._driver.cdp.find_all("li.app-article-list-row__item", timeout=0.5)
            except:
                tag_rows = []

            pdf_tag_list = [
                Tag(
                    name="a",
                    attrs={"href": f"{get_scraped_url_by_web_element(a_tag, self._config_model.base_url)}.pdf"}
                )
                for tag_row in tag_rows
                if tag_row.query_selector("span.u-color-open-access")
                   and (a_tag := tag_row.query_selector("a.c-card__link"))
                   and (href := a_tag.get_attribute("href"))
                   and "/articles/" in href
            ]

            if not pdf_tag_list:
                self._save_failure(url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(url, f"Failed to process URL {url}. Error: {e}")
            return None
