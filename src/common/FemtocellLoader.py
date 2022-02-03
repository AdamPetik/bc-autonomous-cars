from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from src.placeable.stationary.FemtoCell import FemtoCell
import requests
import json
import os

import os.path


class FemtocellLoader:
    def __init__(self):
        self.com = CommonFunctions()

    def getFemtocells(self,locationsTable, map, count, minRadius):
        locations = []
        madeFemtocells = []
        for i in range(0, count):
            location = map.getRandomNode()
            while (self.com.getShortestDistanceFromLocations(locations, location) < minRadius):
                location = map.getRandomNode()
            locations.append(location)

            femtocell = FemtoCell(locationsTable, map)
            x, y = map.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            femtocell.tableRow = locationsTable.insertNewActor(femtocell)
            femtocell.setLocation(location)
            madeFemtocells.append(femtocell)
        return madeFemtocells

    def loadSmallCellsFromFile(self,locationsTable, map, filename):
        madeFemtocells = []
        if os.path.exists("cellCache/smallcellCache/" + filename):
            with open("cellCache/smallcellCache/" + filename) as cachedData:
                cached = json.load(cachedData)

            for item in cached:
                location = Location()
                location.longitude = item['longitude']
                location.latitude = item['latitude']

                femtocell = FemtoCell(locationsTable, map)
                x, y = map.mapGrid.getGridCoordinates(location)
                location.setGridCoordinates(x, y)
                femtocell.tableRow = locationsTable.insertNewActor(femtocell)
                femtocell.setLocation(location)
                madeFemtocells.append(femtocell)
        else:
            raise ValueError('Failed to load SmallCells from given file', filename)

        return madeFemtocells


    def storePlaceablesLocationsIntoFile(self, list, filename):
        if not os.path.exists('cellCache/smallcellCache/'):
            os.makedirs('cellCache/smallcellCache/')
        data = []
        for placeable in list:
            item = {}
            location = placeable.getLocation()
            item['latitude'] = location.getLatitude()
            item['longitude'] = location.getLongitude()
            data.append(item)

        with open("cellCache/smallcellCache/" + filename, 'w+') as outfile:
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
