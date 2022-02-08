from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from src.placeable.stationary.FemtoCell import FemtoCell
import requests
import json
import os

import os.path


class TaskSolverLoader:
    def __init__(self):
        self.com = CommonFunctions()

    def getTaskSolvers(self,locationsTable, map, count, minRadius, dt):
        locations = []
        madeSolvers = []
        for i in range(0, count):
            location = map.getRandomPoint()
            while (self.com.getShortestDistanceFromLocations(locations, location) < minRadius):
                location = map.getRandomPoint()
            locations.append(location)

            solver = TaskSolver(locationsTable, map, dt)
            x, y = map.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            solver.tableRow = locationsTable.insertNewActor(solver)
            solver.setLocation(location)
            madeSolvers.append(solver)
        return madeSolvers

    def loadTaskSolversFromFile(self,locationsTable, map, filename, dt):
        madeSolvers = []
        if os.path.exists("iism_cache/taskSolverCache/" + filename):
            with open("iism_cache/taskSolverCache/" + filename) as cachedData:
                cached = json.load(cachedData)

            for item in cached:
                location = Location()
                location.longitude = item['longitude']
                location.latitude = item['latitude']

                taskSolver = TaskSolver(locationsTable, map, dt)
                x, y = map.mapGrid.getGridCoordinates(location)
                location.setGridCoordinates(x, y)
                taskSolver.tableRow = locationsTable.insertNewActor(taskSolver)
                taskSolver.setLocation(location)
                madeSolvers.append(taskSolver)
        else:
            raise ValueError('Failed to load TaskSolvers from given file', filename)

        return madeSolvers


    def storeTaskSolverLocationsIntoFile(self, list, filename):
        if not os.path.exists('iism_cache/taskSolverCache/'):
            os.makedirs('iism_cache/taskSolverCache/')
        data = []
        for placeable in list:
            item = {}
            location = placeable.getLocation()
            item['latitude'] = location.getLatitude()
            item['longitude'] = location.getLongitude()
            data.append(item)

        with open("iism_cache/taskSolverCache/" + filename, 'w+') as outfile:
            json.dump(data, outfile)


def addFemtoCellsToModel(self, count, minRadius, height, fixHeight=False):
    '''
    Function that creates femtocells
    :param count: number of desired femtocells
    :param minRadius: minimum distance from other femtocells
    :param height: height of femtocell deployment
    :return: returns a list of created femtocells
    '''
    locations = []
    for cell in self.femtocells:
        locations.append(cell.location)

    madeFemtocells = []
    for i in range(0, count):
        location = self.com.getRandomLocationWithinCity(self.city.latitudeInterval, self.city.longitudeInterval,)
        while (self.com.getShortestDistanceFromLocations(locations, location) < minRadius):
            location = self.com.getRandomLocationWithinCity(self.city.latitudeInterval, self.city.longitudeInterval,
                                                            height)

        locations.append(location)
        femtocell = FemtoCell()
        femtocell.location = location
        madeFemtocells.append(femtocell)

    if (fixHeight):
        self.updateCellHeights(madeFemtocells)

    for cell in madeFemtocells:
        if cell.location.height == 0:
            cell.location.height = height

    self.BTSs = self.BTSs + madeFemtocells
    self.grid.addAllToGrid(madeFemtocells)
    return madeFemtocells
