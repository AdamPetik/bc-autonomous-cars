import abc
from datetime import datetime
from typing import Generic, TypeVar

from NFTAutonomousVehicles.taskProcessing.Task import Task


class Processable(abc.ABC):
    def __init__(self) -> None:
        super().__init__()
        self.processed_at: datetime = None

    @abc.abstractmethod
    @property
    def can_start_process_at(self) -> datetime:
        pass

    @abc.abstractmethod
    @property
    def to_process_amount(self) -> float:
        pass

    @abc.abstractmethod
    def process(self, amout) -> float:
        pass

    @abc.abstractmethod
    def is_processed(self) -> bool:
        pass


T = TypeVar('T')


class GeneralProcessable(Processable, Generic[T]):
    def __init__(self, entity: T, can_start_at: datetime, to_process: float) -> None:
        super().__init__()
        self.entity = entity
        self.can_start_at = can_start_at
        self._to_process = to_process

    @property
    def can_start_process_at(self) -> datetime:
        return self.can_start_at

    @property
    def to_process_amount(self) -> datetime:
        return self._to_process

    def process(self, amount) -> float:
        amount_to_use = min(amount, self._to_process)
        self._to_process-= amount_to_use
        return amount - amount_to_use

    def is_processed(self) -> bool:
        return self._to_process <= 0


class TaskCPUProcessable(GeneralProcessable[Task]):
    def __init__(self, entity: Task, can_start_at: datetime) -> None:
        super().__init__(entity, can_start_at, entity.instruction_count)
