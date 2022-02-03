from src.placeable.movable.Movable import Movable
from src.placeable.stationary.BaseStation import BaseStation


class Drone(BaseStation, Movable):


    def __init__(self, locationsTable, map):
        BaseStation.__init__(self, locationsTable, map)
        Movable.__init__(self,locationsTable, map)

    def generateDailyActivityQueue(self):
        pass
