from typing import List

from model.base_iterative_publisher_models import BaseIterativePublisherConfig, BaseIterativePublisherJournal


class EUDLJournal(BaseIterativePublisherJournal):
    end_volume: int | None = 16


class EUDLConfig(BaseIterativePublisherConfig):
    journals: List[EUDLJournal]
