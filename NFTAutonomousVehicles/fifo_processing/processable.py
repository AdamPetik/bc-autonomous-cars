import abc
from datetime import datetime
from typing import Generic, TypeVar


class Processable(abc.ABC):
    """Base class for processables."""

    def __init__(self) -> None:
        super().__init__()
        self.processed_at: datetime = None

    @property
    def timeout_at(self) -> datetime:
        """Processable timeout. None means it does not have a timeout."""
        return None

    def is_timed_out(self, current_time: datetime):
        if self.timeout_at is None:
            return False
        return current_time >= self.timeout_at

    @property
    @abc.abstractmethod
    def can_start_process_at(self) -> datetime:
        """
        Returns datetime indicating from when the processable is ready
        to be processed
        """

    @property
    @abc.abstractmethod
    def to_process_amount(self) -> float:
        """Amount to be processed"""

    @abc.abstractmethod
    def process(self, amout) -> float:
        """Do processing.

        Args:
            amout (_type_): available amount to be used for processing

        Returns:
            float: Used amount for processing
        """

    @abc.abstractmethod
    def is_processed(self) -> bool:
        """Bool value indicating whether has been processed already"""


T = TypeVar('T')


class GeneralProcessable(Processable, Generic[T]):
    def __init__(
        self,
        entity: T,
        can_start_at: datetime,
        to_process: float,
        timeout: datetime = None,
    ) -> None:
        super().__init__()
        self.entity = entity
        self.can_start_at = can_start_at
        self._to_process = to_process
        self.timeout = timeout

    @property
    def can_start_process_at(self) -> datetime:
        return self.can_start_at

    @property
    def to_process_amount(self) -> float:
        return self._to_process

    @property
    def timeout_at(self) -> datetime:
        return self.timeout

    def process(self, amount) -> float:
        amount_to_use = min(amount, self._to_process)
        self._to_process -= amount_to_use
        return amount_to_use

    def is_processed(self) -> bool:
        return self._to_process <= 0
