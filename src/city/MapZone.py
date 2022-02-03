from src.city.ZoneType import ZoneType
from shapely.geometry import Polygon
import random

from src.common.CommonFunctions import CommonFunctions


class MapZone:

    def __init__(self, name, zoneType: ZoneType, probability, lacationsPolygon: [], map):
        self.com = CommonFunctions()
        self.name = name
        self.zoneType = zoneType
        self.map = map
        self.buildings = []
        self.probability = probability

        polygonList = []
        for location in lacationsPolygon:
            point = (location.getLatitude(), location.getLongitude())
            polygonList.append(point)

        self.polygon = Polygon(polygonList)

        for building in map.buildings:
            if self.com.getPointFromLocation(building.centroid).within(self.polygon):
                self.buildings.append(building)

    def printBuildings(self):
        print(">  Buildings for Map Zone ", self.name, " with type ", self.zoneType, " with centroid at: ",
              self.polygon.centroid)
        for building in self.buildings:
            print(building.getGeoJson())


    def getRandomBuilding(self):
        return random.choice(self.buildings)