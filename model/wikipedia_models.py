from typing import List

from model.base_url_publisher_models import BaseUrlPublisherSource, BaseUrlPublisherConfig


class WikipediaSource(BaseUrlPublisherSource):
    with_categories: bool = True


class WikipediaConfig(BaseUrlPublisherConfig):
    sources: List[WikipediaSource]
