from typing import Type, List
from bs4 import Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_pagination_publisher_models import BasePaginationPublisherConfig, BasePaginationPublisherScrapeOutput
from scraper.base_pagination_publisher_scraper import BasePaginationPublisherScraper


class SciencePartnerJournalScraper(BasePaginationPublisherScraper):
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

        return {"SciencePartnerJournal": [
            get_scraped_url_by_bs_tag(tag, self._config_model.base_url) for tag in pdf_tags
        ]} if pdf_tags else None

    def _scrape_landing_page(self, landing_page_url: str, source_number: int) -> List[Tag]:
        return self._scrape_pagination(landing_page_url, source_number, base_zero=True, page_size=self.__source.page_size)

    def _scrape_page(self, url: str) -> List[Tag] | None:
        try:
            scraper = self._scrape_url(url)

            # Now, visit each article link and find the PDF link
            if not (pdf_tag_list := scraper.find_all("a", href=lambda href: href and "/doi/epdf/" in href)):
                self._save_failure(url)

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return [
                Tag(
                    name="a",
                    attrs={
                        "href": get_scraped_url_by_bs_tag(
                            tag, self._config_model.base_url
                        ).replace("/doi/epdf/", "/doi/pdf/") + "?download=true"
                    }
                )
                for tag in pdf_tag_list
            ]
        except Exception as e:
            self._log_and_save_failure(url, f"Failed to process URL {url}. Error: {e}")
            return None
