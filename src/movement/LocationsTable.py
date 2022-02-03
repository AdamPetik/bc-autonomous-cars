import random

import numpy

from src.city.grid.MapGrid import MapGrid
from src.common.Location import Location
from src.placeable.movable.Movable import Movable


class LocationsTable:

    def __init__(self, mapGrid: MapGrid):
        self.columns = 18
        self.rows = 0
        self.table = numpy.empty((self.rows, self.columns))
        self.mapGrid = mapGrid

    #     TABLE STRUCTURE
    #
    # 0 current latitude
    # 1 current longitude
    # 2 current altitude
    # 3 target latitude
    # 4 target longitude
    # 5 target altitude
    # 6 speed
    # 7 target reached ?
    # 8 current grid x-coordinate
    # 9 current grid y-coordinate
    # 10 id
    # 11 latStep
    # 12 latMin
    # 13 lonStep
    # 14 lonMin
    # 15 atIntersection?
    # 16 routeIndex (for prediction functionality)
    # 17 targetOsmnxNodeId


    def getId(self, row):
        return self.table[row, 10]

    def setId(self, row, id):
        self.table[row, 10] = id

    def getLocation(self, row):
        location = Location(self.table[row, 0], self.table[row, 1], self.table[row, 2])
        location.setGridCoordinates(int(self.table[row, 8]), int(self.table[row, 9]))
        return location

    def setLocation(self, row, location: Location):
        self.table[row, 0] = location.getLatitude()
        self.table[row, 1] = location.getLongitude()
        self.table[row, 2] = location.getAltitude()
        if (location.getGridCoordinates() != []):
            self.table[row, 8] = location.getGridXcoor()
            self.table[row, 9] = location.getGridYcoor()

    def getTargetLocation(self, row):
        return Location(self.table[row, 3], self.table[row, 4], self.table[row, 5], self.table[row, 17])

    def setTargetLocation(self, row, location: Location):
        self.table[row, 3] = location.getLatitude()
        self.table[row, 4] = location.getLongitude()
        self.table[row, 5] = location.getAltitude()
        self.table[row, 17] = location.getOsmnxNode()

    def getTargetReached(self, row):
        return self.table[row, 7]

    def setTargetReached(self, row, boolValue):
        self.table[row, 7] = boolValue

    def getIsAtIntersection(self, row):
        # print(f"getting value is at intersection for row {row} - {self.table[row, 15]}")
        return self.table[row, 15]

    def setIsAtIntersection(self, row, boolValue):
        # print(f"setting is at intersection for row {row} to {boolValue}")
        self.table[row, 15] = boolValue
        # self.getIsAtIntersection(row)

    def insertNewActor(self, movable: Movable):
        rowNumber = len(self.table)

        self.table = numpy.vstack([self.table,
                                   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, movable.id, self.mapGrid.latStep, self.mapGrid.latmin,
                                    self.mapGrid.lonStep, self.mapGrid.lonmin, False, 0, 0]])
        return rowNumber

    def insertNewRow(self, movable: Movable, currentLocation: Location, targetLocation: Location, speed, routeIndex):
        rowNumber = len(self.table)

        self.table = numpy.vstack([self.table,
                                   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, movable.id, self.mapGrid.latStep, self.mapGrid.latmin,
                                    self.mapGrid.lonStep, self.mapGrid.lonmin, False, routeIndex, 0]])
        self.setLocation(rowNumber, currentLocation)
        self.setTargetLocation(rowNumber, targetLocation)
        self.setSpeed(rowNumber, speed)
        return rowNumber

    def getSpeed(self, row):
        speed = self.table[row, 6]
        return speed

    def setSpeed(self, row, value):
        self.table[row, 6] = value

    def getRowsInDestinations(self):
        rows = self.table[self.table[:, 7] == 1]
        return rows

    def getIdsInDestinations(self):
        # return IDs of walkables from rows
        return self.getRowsInDestinations()[:, [10]].ravel()

    def getRowsAtIntersections(self):
        rows = self.table[self.table[:, 15] == 1]
        return rows

    def getRouteIndex(self, row):
        return int(self.table[row, 16])

    def getIdsAtIntersections(self):
        return self.getRowsAtIntersections()[:, [10]].ravel()

    def getTable(self):
        return self.table

    def getIdsAtGridXY(self, x, y):
        # rows = self.table[numpy.where(self.table[:, 8] == x)]
        # rows = rows[numpy.where(rows[:, 9] == y)]
        # return rows[:, [10]].ravel()

        rows = self.table[self.table[:, 8] == x]
        rows = rows[rows[:, 9] == y]
        return rows[:, [10]].flatten()

    def getAllIds(self):
        return self.table[:, [10]].flatten()

    def getAllIdsShuffled(self):
        return random.shuffle(self.table[:, [10]].flatten())
