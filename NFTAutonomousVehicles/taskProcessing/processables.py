
import datetime
from NFTAutonomousVehicles.fifo_processing.processable import GeneralProcessable
from NFTAutonomousVehicles.taskProcessing.Task import Task


class TaskCPUProcessable(GeneralProcessable[Task]):
    def __init__(self, entity: Task, can_start_at: datetime) -> None:
        super().__init__(entity, can_start_at, entity.instruction_count)


class TaskConnectionProcessable(GeneralProcessable[Task]):
    def __init__(self, entity: Task, can_start_at: datetime) -> None:
        super().__init__(entity, can_start_at, entity.size_in_megabytes)
