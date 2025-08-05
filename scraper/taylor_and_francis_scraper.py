from typing import List, Type, Dict
from bs4 import Tag

from helper.utils import get_scraped_url_by_bs_tag
from model.base_mapped_models import BaseMappedUrlConfig, BaseMappedUrlSource, BaseMappedPaginationConfig
from model.base_pagination_publisher_models import BasePaginationPublisherScrapeOutput
from scraper.base_mapped_publisher_scraper import BaseMappedPublisherScraper
from scraper.base_pagination_publisher_scraper import BasePaginationPublisherScraper
from scraper.base_scraper import BaseMappedSubScraper
from scraper.base_url_publisher_scraper import BaseUrlPublisherScraper, SourceType


class TaylorAndFrancisScraper(BaseMappedPublisherScraper):
    @property
    def mapping(self) -> Dict[str, Type[BaseMappedSubScraper]]:
        return {
            "TaylorAndFrancisUrlScraper": TaylorAndFrancisUrlScraper,
            "TaylorAndFrancisPaginationScraper": TaylorAndFrancisPaginationScraper,
        }


class TaylorAndFrancisUrlScraper(BaseUrlPublisherScraper, BaseMappedSubScraper):
    @property
    def config_model_type(self) -> Type[BaseMappedUrlConfig]:
        return BaseMappedUrlConfig

    def _scrape_journal(self, source: BaseMappedUrlSource) -> List[Tag] | None:
        self._logger.info(f"Processing Journal {source.url}")

        try:
            self._scrape_url(source.url)

            buttons = self._driver.cdp.find_elements("li.vol_li > button.volume_link", timeout=0.5)

            issues_links = []
            for button in buttons:
                button.click()
                self._driver.cdp.sleep(2)
                issues_links.extend([
                    get_scraped_url_by_bs_tag(x, self._config_model.base_url)
                    for x in self._get_parsed_page_source().find_all("a", href=True, class_="issue-link")
                ])
            issues_links = list(set(issues_links))

            # For each tag of issues previously collected, scrape the issue as a collection of articles
            pdf_tag_list = [
                tag
                for link in issues_links
                if (tags := self._scrape_issue_or_collection(
                    BaseMappedUrlSource(url=link, type=str(SourceType.ISSUE_OR_COLLECTION))
                ))
                for tag in tags
            ]

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Journal {source.url}. Error: {e}")
            return None

    def _scrape_issue_or_collection(self, source: BaseMappedUrlSource) -> List[Tag] | None:
        self._logger.info(f"Processing Issue / Collection {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            # Find all PDF links using appropriate class or tag (if lambda returns True, it will be included in the list)
            articles_links = [
                get_scraped_url_by_bs_tag(tag, self._config_model.base_url).replace("/doi/full/", "/doi/pdf/")
                for tag in scraper.find_all(
                    "a",
                    href=lambda href: href and "/doi/full/" in href,
                    class_=lambda cls: cls and "ref" in cls and "nowrap" in cls,
                )
            ]
            if not articles_links:
                self._save_failure(source.url)

            pdf_tag_list = [Tag(name="a", attrs={"href": link}) for link in articles_links]

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Issue / Collection {source.url}. Error: {e}")
            return None

    def _scrape_article(self, source: BaseMappedUrlSource) -> Tag | None:
        self._logger.info(f"Processing Article {source.url}")

        try:
            scraper = self._scrape_url(source.url)

            # Find the PDF link using appropriate class or tag (if lambda returns True, it will be included in the list)
            if not (tag := scraper.find("a", href=lambda href: href and "/doi/" in href and "/pdf/" in href, class_="show-pdf")):
                self._save_failure(source.url)

            return tag
        except Exception as e:
            self._log_and_save_failure(source.url, f"Failed to process Article {source.url}. Error: {e}")
            return None


class TaylorAndFrancisPaginationScraper(BasePaginationPublisherScraper, BaseMappedSubScraper):
    def __init__(self):
        super().__init__()
        self.__source = None

    @property
    def config_model_type(self) -> Type[BaseMappedPaginationConfig]:
        return BaseMappedPaginationConfig

    def scrape(self) -> BasePaginationPublisherScrapeOutput | None:
        pdf_tags = []
        for idx, source in enumerate(self._config_model.sources):
            self.__source = source
            pdf_tags.extend(self._scrape_landing_page(source.landing_page_url, idx + 1))

        return {"Taylor&Francis Search": [
            get_scraped_url_by_bs_tag(tag, self._config_model.base_url) for tag in pdf_tags
        ]} if pdf_tags else None

    def _scrape_landing_page(self, landing_page_url: str, source_number: int) -> List[Tag] | None:
        return self._scrape_pagination(
            landing_page_url, source_number, base_zero=True, page_size=self.__source.page_size
        )

    def _scrape_page(self, url: str) -> List[Tag] | None:
        try:
            scraper = self._scrape_url(url)

            articles_links = [
                get_scraped_url_by_bs_tag(tag, self._config_model.base_url).replace("/doi/full/", "/doi/pdf/")
                for tag in scraper.find_all(
                    "a",
                    href=lambda href: href and "/doi/full/" in href,
                    class_=lambda cls: cls and "showFull" in cls,
                )
            ]
            if not articles_links:
                self._save_failure(url)

            pdf_tag_list = [Tag(name="a", attrs={"href": f"{link}?download=true"}) for link in articles_links]

            self._logger.debug(f"PDF links found: {len(pdf_tag_list)}")
            return pdf_tag_list
        except Exception as e:
            self._log_and_save_failure(url, f"Failed to process URL {url}. Error: {e}")
            return None
