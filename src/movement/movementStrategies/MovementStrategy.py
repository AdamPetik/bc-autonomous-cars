from src.common.Location import Location

class MovementStrategy:

    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType):
        self.locationsTable = locationsTable
        self.movableSet = movableSet
        self.map = map
        self.mapGrid = mapGrid
        self.strategyType = strategyType

    def move(self):
        raise ValueError('Do not call method of abstract class')

    def getNewRoute(self, walkable):
        raise ValueError('Do not call method of abstract class')

    def getRouteTo(self, walkable, location: Location):
        raise ValueError('Do not call method of abstract class')

    def onDayChange(self, walkable):
        raise ValueError('Do not call method of abstract class')
