from abc import ABC
from pydantic import BaseModel


class ReadMoreButton(BaseModel):
    selector: str
    text: str


class Config(ABC, BaseModel):
    bucket_key: str
    files_by_request: bool | None = True  # Indicates whether the uploader should download or scrape the final sources


class BaseConfig(Config, ABC):
    base_url: str | None = None
    cookie_selector: str | None = None
    read_more_button: ReadMoreButton | None = None
    loading_tag: str | None = None  # The tag that indicates that the page is still loading
    waited_tag: str | None = None  # The tag that indicates that the page has loaded
    request_with_proxy: bool = False  # Indicates whether the downloading request should be made with a proxy (only for download, not scrape)
