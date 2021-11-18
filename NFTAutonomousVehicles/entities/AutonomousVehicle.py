from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from src.city.ZoneType import ZoneType
from src.placeable.movable.Movable import Movable
from src.common.CommonFunctions import CommonFunctions
from datetime import datetime, time, timedelta

from src.placeable.movable.MovementActivity import MovementActivity


class AutonomousVehicle(Movable):

    def __init__(self, locationsTable, map, operator=None):
        super(AutonomousVehicle, self).__init__(locationsTable, map)
        self.com = CommonFunctions()

        self.active_tasks = {}
        self.successfully_solved_tasks = {}
        self.failed_tasks = {}

    def receiveSolvedTask(self, task: Task) -> bool:
        self.active_tasks.pop(task.id)

        if task.status == TaskStatus.SOLVED and task.returned_to_creator_at <= task.deadline_at:
            self.successfully_solved_tasks[task.id] = task
            task.solver.increaseReputation()
        else:
            self.failed_tasks[task.id] = task
            task.solver.decreaseReputation()


    # TODO vehicle have to buy NFTs that will guarantee tasks to be solved in single iteration