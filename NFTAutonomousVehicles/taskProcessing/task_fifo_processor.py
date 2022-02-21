import datetime
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor
from NFTAutonomousVehicles.fifo_processing.processable import Processable
from NFTAutonomousVehicles.resultCollectors.MainCollector import MainCollector
from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus


class TaskFIFOProcessor(FIFOProcessor):
    def __init__(self, step_available_power, dt, logger: MainCollector) -> None:
        super().__init__(step_available_power, dt)
        self.logger = logger

    def _on_deadline(self, processable: Processable, time: datetime) -> None:
        task = processable.entity
        task.status = TaskStatus.TASK_TIMED_OUT
        self.logger.logTask(task)