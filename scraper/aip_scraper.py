from typing import Type, List
from bs4 import Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_pagination_publisher_models import BasePaginationPublisherConfig, BasePaginationPublisherScrapeOutput
from scraper.base_pagination_publisher_scraper import BasePaginationPublisherScraper


class AIPScraper(BasePaginationPublisherScraper):
    def __init__(self):
        super().__init__()
        self.__source = None

    @property
    def config_model_type(self) -> Type[BasePaginationPublisherConfig]:
        return BasePaginationPublisherConfig

    def scrape(self) -> BasePaginationPublisherScrapeOutput | None:
        pdf_tags = []
        for idx, source in enumerate(self._config_model.sources):
            self.__source = source
            pdf_tags.extend(self._scrape_landing_page(source.landing_page_url, idx + 1))

        return {"AIP": [
            get_scraped_url_by_bs_tag(tag, self._config_model.base_url) for tag in pdf_tags
        ]} if pdf_tags else None

    def _scrape_landing_page(self, landing_page_url: str, source_number: int) -> List[Tag]:
        return self._scrape_pagination(landing_page_url, source_number, page_size=self.__source.page_size)

    def _scrape_page(self, url: str) -> List[Tag] | None:
        try:
            scraper = self._scrape_url(url)

            article_links = [
                get_scraped_url_by_bs_tag(tag, self._config_model.base_url, with_querystring=True)
                for tag in scraper.find_all(
                    "a",
                    href=lambda href: href and "/aip/adv/article/" in href,
                    class_=lambda cls: cls and "viewArticleLink" in cls,
                )
            ]

            pdf_tag_list = []
            # Now, visit each article link and find the PDF link
            for article_link in article_links:
                self._logger.debug(f"Processing Page {article_link}")

                page_scraper = self._scrape_url(article_link)
                pdf_tag_list.extend(
                    page_scraper.find_all(
                        "a", href=lambda href: href and ".pdf" in href, class_=lambda cls: cls and "pdf" in cls
                    )
                )

            if not pdf_tag_list:
                self._save_failure(url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(url, f"Failed to process URL {url}. Error: {e}")
            return None
