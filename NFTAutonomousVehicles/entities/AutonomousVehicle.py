from NFTAutonomousVehicles.taskProcessing.Task import Task
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


    def receiveSolvedTask(self, task:Task):
