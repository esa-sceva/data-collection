import os
from typing import Type, List

from helper.utils import get_resource_from_remote_by_request
from model.base_pagination_publisher_models import BasePaginationPublisherConfig, BasePaginationPublisherScrapeOutput
from scraper.base_pagination_publisher_scraper import BasePaginationLinksPublisherScraper


class AIMSPressScraper(BasePaginationLinksPublisherScraper):
    def __init__(self):
        super().__init__()
        self.__source = None

    @property
    def config_model_type(self) -> Type[BasePaginationPublisherConfig]:
        return BasePaginationPublisherConfig

    def scrape(self) -> BasePaginationPublisherScrapeOutput | None:
        pdf_urls = []
        for idx, source in enumerate(self._config_model.sources):
            self.__source = source
            pdf_urls.extend(self._scrape_landing_page(source.landing_page_url, idx + 1))

        return {"AIMS Press": pdf_urls} if pdf_urls else None

    def _scrape_landing_page(self, landing_page_url: str, source_number: int) -> List[str]:
        return self._scrape_pagination(landing_page_url, source_number, page_size=self.__source.page_size)

    def _scrape_page(self, url: str) -> List[str] | None:
        try:
            response = get_resource_from_remote_by_request(url, ask_json=True)
            if not (result_list := response.get("resultlist")):
                self._save_failure(url)
                return None

            pdf_urls = [
                f"{os.path.join(self._config_model.base_url, 'data/article/export-pdf?id=')}{item['id']}"
                for item in result_list
            ]

            self._logger.debug(f"PDF URLs found: {len(pdf_urls)}")
            return pdf_urls
        except Exception as e:
            self._log_and_save_failure(url, f"Failed to process URL {url}. Error: {e}")
            return None
