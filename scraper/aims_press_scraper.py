import os
from typing import Type, List
import random
import time

from helper.constants import DEFAULT_CRAWLING_FOLDER
from model.base_crawling_models import BaseCrawlingConfig, BaseCrawlingScraperOutput
from model.sql_models import ScraperFailure
from scraper.base_scraper import BaseScraper


class AIMSPressScraper(BaseScraper):
    """Scraper for AIMS Press publications."""

    @property
    def config_model_type(self) -> Type[BaseCrawlingConfig]:
        return BaseCrawlingConfig

    @property
    def local_folder_path(self) -> str:
        return "aims_press"

    def scrape(self) -> BaseCrawlingScraperOutput | None:

        for source in self._config_model.sources:
            self._logger.info(f"Scraping URL: {source.url}")
            self.__scrape_source(source.url)

        return {source.name: source.url for source in self._config_model.sources}

    def scrape_failure(self, failure: ScraperFailure) -> List[str]:
        link = failure.source
        self._logger.info(f"Scraping URL: {link}")

        res = self.__scrape_source(link)
        return [res] if res else []

    def post_process(self, scrape_output: BaseCrawlingScraperOutput) -> List[str]:
        return list(scrape_output.values())

    def __scrape_source(self, url: str) -> str | None:
        try:
            # Here you would implement the logic to scrape the source URL
            # For example, using Selenium or BeautifulSoup to extract the PDF links
            # For now, we will just return a placeholder list
            # In a real implementation, you would return the actual scraped links

            return url
        except Exception as e:
            self._log_and_save_failure(url,f"Failed to process URL {url}. Error: {e}")
            return None

    def upload_to_s3(self, sources_links: List[str]):
        self._logger.debug("Uploading files to S3")
        local_download_folder = self._get_local_download_folder_path()

        file_paths = [
            os.path.join(local_download_folder, file)
            for file in os.listdir(local_download_folder)
            if os.path.isfile(os.path.join(local_download_folder, file))
        ]
        if not file_paths:
            for source_link in sources_links:
                self._save_failure(source_link, f"No files found in the crawling folder: {source_link}")

        for file_path in file_paths:
            current_resource = self._uploaded_resource_repository.get_by_content(
                self._logging_db_scraper, self._config_model.bucket_key, file_path
            )
            self._upload_resource_to_s3(current_resource, file_path.replace(local_download_folder, ""))

            # Sleep after each successful upload to avoid overwhelming the server
            time.sleep(random.uniform(2, 5))

    def _get_local_download_folder_path(self) -> str:
        return str(os.path.join(DEFAULT_CRAWLING_FOLDER, self.local_folder_path))
