from src.common.Location import Location
from src.movement.movementStrategies.MovementStrategy import MovementStrategy
from src.common.SimulationClock import *

from src.placeable.movable.Movable import Movable
from src.placeable.movable.Person import Person


class PreloadedLocationsStrategy(MovementStrategy):
    preloaded_locations_dict = dict()

    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType):
        super(PreloadedLocationsStrategy, self).__init__(locationsTable, movableSet, map, mapGrid, strategyType)

    def move(self):
        # print("Before move-------\n", self.locationsTable.table)
        for actorId in self.locationsTable.getAllIds():
            walkable: Movable = self.movableSet[int(actorId)]
            walkable.setLocation(self.getPreloadedLocation(walkable, getDateTime()))
        # print("After move-------\n", self.locationsTable.table)

    def preloadLocationForWalkable(self, walkable, timestamp, location):
        if (walkable.id not in self.preloaded_locations_dict):
            self.preloaded_locations_dict[walkable.id] = dict()
        self.preloaded_locations_dict[walkable.id][timestamp] = location

    def preloadLocationsDictForWalkable(self, walkable, dictionary):
        # if (walkable.id not in self.preloaded_locations_dict):
        #     self.preloaded_locations_dict[walkable.id] = dict()
        # self.preloaded_locations_dict[walkable.id] = {**self.preloaded_locations_dict[walkable.id], **dictionary}
        self.preloaded_locations_dict[walkable.id] = dictionary

    def getPreloadedLocation(self, walkable, timestamp):
        if walkable.id not in self.preloaded_locations_dict:
            return None
        if timestamp not in self.preloaded_locations_dict[walkable.id]:
            return None
        return self.preloaded_locations_dict[walkable.id][timestamp]
























