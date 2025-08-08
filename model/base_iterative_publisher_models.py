from typing import Dict, List, TypeAlias
from pydantic import BaseModel

from model.base_models import BaseConfig


class BaseIterativeIssuePublisherJournal(BaseModel):
    url: str
    name: str
    start_issue: int | None = 1
    end_issue: int | None = 30
    special_issues: List[str] | None = None


class BaseIterativeIssuePublisherConfig(BaseConfig):
    journals: List[BaseIterativeIssuePublisherJournal]


class BaseIterativePublisherJournal(BaseIterativeIssuePublisherJournal):
    start_volume: int | None = 1
    end_volume: int | None = 30


class BaseIterativePublisherConfig(BaseConfig):
    journals: List[BaseIterativePublisherJournal]


class BaseIterativeWithConstraintPublisherJournal(BaseIterativePublisherJournal):
    consecutive_missing_volumes_threshold: int | None = 3
    consecutive_missing_issues_threshold: int | None = 3


class BaseIterativeWithConstraintPublisherConfig(BaseConfig):
    journals: List[BaseIterativeWithConstraintPublisherJournal]


IterativePublisherScrapeIssueOutput: TypeAlias = List[str]
IterativePublisherScrapeVolumeOutput: TypeAlias = Dict[str, IterativePublisherScrapeIssueOutput]
IterativePublisherScrapeJournalOutput: TypeAlias = Dict[str, IterativePublisherScrapeVolumeOutput]
IterativePublisherScrapeOutput: TypeAlias = Dict[str, IterativePublisherScrapeJournalOutput]

IterativeIssuePublisherScrapeJournalOutput: TypeAlias = IterativePublisherScrapeVolumeOutput
IterativeIssuePublisherScrapeOutput: TypeAlias = Dict[str, IterativeIssuePublisherScrapeJournalOutput]
