import math

import numpy
from src.city.grid.MapCell import MapCell
from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location


class MapGrid:

    def __init__(self, widthHeight, rows, actorCollectionsSet, latmin, latmax, lonmin, lonmax):
        self.widthHeight = widthHeight
        self.cellWidthAndHeight = widthHeight / rows
        self.rows = rows
        self.actorCollectionsSet = actorCollectionsSet
        self.com = CommonFunctions()

        self.latmin = latmin
        self.latmax = latmax
        self.lonmin = lonmin
        self.lonmax = lonmax
        self.latStep = abs(latmax - latmin) / rows
        self.lonStep = abs(lonmax - lonmin) / rows

        self.tableSteps = numpy.empty((3, 3))
        self.tableSteps[1, 0] = self.latStep
        self.tableSteps[1, 1] = self.latmin
        self.tableSteps[1, 2] = self.latmax

        self.tableSteps[2, 0] = self.lonStep
        self.tableSteps[2, 1] = self.lonmin
        self.tableSteps[2, 2] = self.lonmax

        self.grid = [[0 for x in range(rows)] for y in range(rows)]
        for x in range(0, rows):
            for y in range(0, rows):
                latitude = self.latmin + x * self.latStep + (self.latStep / 2)
                longitude = self.lonmin + y * self.lonStep + (self.lonStep / 2)
                altitude = 0
                centerLocation = Location(latitude, longitude, altitude)
                centerLocation.setGridCoordinates(x, y)
                self.grid[x][y] = MapCell(x, y, centerLocation)

    def getGridCoordinates(self, location=Location):
        x = int((location.getLatitude() - self.latmin) // self.latStep)
        y = int((location.getLongitude() - self.lonmin) // self.lonStep)
        return x, y

    def getGridCoordinatesAsList(self, location=Location):
        x, y = self.getGridCoordinates(location)
        return [x, y]

    def getMovablesAtXYFromCollections(self, collectionNames, x, y):
        movables = []
        for collectionName in collectionNames:
            collection = self.actorCollectionsSet[collectionName]
            movables = movables + collection.getMovablesAtGridXY(x, y)
        return movables

    def getMovablesAtXY(self, x, y):
        movables = []
        for key, collection in self.actorCollectionsSet.items():
            movables = movables + collection.getMovablesAtGridXY(x, y)
        return movables

    def getCountPerCell(self, collectionNames):
        countMatrix = numpy.zeros((self.rows, self.rows), dtype=int)

        for collectionName in collectionNames:
            collection = self.actorCollectionsSet[collectionName]
            for x in (0, self.rows):
                for y in (0, self.rows):
                    movables = collection.getMovablesAtGridXY(x, y)
                    countMatrix[x, y] = countMatrix[x, y] + len(movables)
        return countMatrix

    def getCountPerCell(self):
        countMatrix = numpy.zeros((self.rows, self.rows), dtype=int)
        for key, collection in self.actorCollectionsSet.items():
            for x in range(self.rows):
                for y in range(self.rows):
                    movables = collection.getMovablesAtGridXY(x, y)
                    countMatrix[x, y] = countMatrix[x, y] + len(movables)
        return countMatrix

    def getRssPerCell(self):
        rssMatrix = numpy.zeros((self.rows, self.rows), dtype=float)
        for x in range(self.rows):
            for y in range(self.rows):
                rssMatrix[x, y] = self.grid[x][y].rss

        # print(rssMatrix)
        return rssMatrix

    def getClosestActorAndDistanceFrom(self, distance, collectionNames, loc=Location):
        actors =  self.getClosestActorsFrom(distance, collectionNames, loc)
        return self.com.getClosestActorFromListAndDistance(loc,actors)

    def getClosestActorsFrom(self, distance, collectionNames, location=Location):
        x, y = self.getGridCoordinates(location)
        actors = []
        for xx in range(x - distance, x + distance + 1):
            for yy in range(y - distance, y + distance + 1):
                if (xx >= 0 and yy >= 0 and xx < self.rows and yy < self.rows):
                    for collectionName in collectionNames:
                        collection = self.actorCollectionsSet[collectionName]
                        actors = actors + collection.getMovablesAtGridXY(xx, yy)

        if (len(actors) == 0 and distance < self.rows):
            # print("Number of agents found at distance: ", distance, "is: ", len(actors), "starting recursion")
            actors = self.getClosestActorsFrom(distance + 1, collectionNames, location)

        # print("Found",len(actors)," RESULTS : ",actors)
        return actors


    def getClosestActorsFromV2(self, distance, collectionNames, location=Location, visitedMatrix=None):
        if (visitedMatrix == None):
            visitedMatrix = [[0 for x in range(self.rows)] for y in range(self.rows)]
            for x in range(0, self.rows):
                for y in range(0, self.rows):
                    visitedMatrix[x][y] = False
        x, y = self.getGridCoordinates(location)
        actors = []
        for xx in range(x - distance, x + distance + 1):
            for yy in range(y - distance, y + distance + 1):
                if (xx >= 0 and yy >= 0 and xx < self.rows and yy < self.rows and visitedMatrix[xx][yy] == False):
                    visitedMatrix[xx][yy] = True
                    for collectionName in collectionNames:
                        collection = self.actorCollectionsSet[collectionName]
                        actors = actors + collection.getMovablesAtGridXY(xx, yy)

        if (len(actors) == 0 and distance < self.rows):
            # print("Number of agents found at distance: ", distance, "is: ", len(actors), "starting recursion")
            actors = self.getClosestActorsFromV2(distance + 1, collectionNames, location, visitedMatrix)

        # print("Found",len(actors)," RESULTS : ",actors)
        return actors

    def getClosestActorsFromV3(self, distance, collectionNames, location=Location):
        x, y = self.getGridCoordinates(location)
        actors = []
        for xx in range(x - distance, x + distance + 1):
            for yy in range(y - distance, y + distance + 1):
                if (xx >= 0 and yy >= 0 and xx < self.rows and yy < self.rows):
                    for collectionName in collectionNames:
                        collection = self.actorCollectionsSet[collectionName]
                        actors = actors + collection.getMovablesAtGridXY(xx, yy)

        if (len(actors) == 0 and distance < self.rows):
            # print("Number of agents found at distance: ", distance, "is: ", len(actors), "starting recursion")
            actors = self.getClosestActorsFromV3(distance + 1, collectionNames, location)

        # print("Found",len(actors)," RESULTS : ",actors)
        return actors

    def getActorsInRadius(self, radius, collectionNames, location=Location):
        gridDistance = math.ceil(radius / self.cellWidthAndHeight)
        actorsInGrid = self.getClosestActorsFrom(gridDistance, collectionNames, location)
        actorsInRadius = []
        for actor in actorsInGrid:
            if self.com.getReal2dDistance(actor.getLocation(), location) < radius:
                actorsInRadius.append(actor)
        return actorsInRadius
