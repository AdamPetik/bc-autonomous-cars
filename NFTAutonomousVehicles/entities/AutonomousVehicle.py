from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from src.city.ZoneType import ZoneType
from src.placeable.movable.Movable import Movable
from src.common.CommonFunctions import CommonFunctions
from datetime import datetime, time, timedelta

from src.placeable.movable.MovementActivity import MovementActivity


class AutonomousVehicle(Movable):

    def __init__(self, locationsTable, map, vehicle_type):
        super(AutonomousVehicle, self).__init__(locationsTable, map)
        self.vehicle_type = vehicle_type
        self.com = CommonFunctions()

        self.active_tasks = {}
        self.successfully_solved_tasks = {}
        self.failed_tasks = {}

        self.sample_task = Task(vehicle=self, size_in_megabytes=1, capacity_needed_to_solve=4, solving_time=0.1, limit_time=0.2)
        self.active_proposed_route = None

    def receiveSolvedTask(self, task: Task, logger) -> bool:
        self.active_tasks.pop(task.id)

        if task.status == TaskStatus.SOLVED and task.returned_to_creator_at <= task.deadline_at:
            self.successfully_solved_tasks[task.id] = task
            task.solver.increaseReputation()
        else:
            self.failed_tasks[task.id] = task
            task.solver.decreaseReputation()

        logger.insertTask(task)