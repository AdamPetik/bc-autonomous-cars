from src.city.Map import Map
from src.common.CommonFunctions import CommonFunctions
from src.common.UniqueID import UniqueID
from src.common.SimulationClock import *


class Placeable:

    def __init__(self, locationsTable, map:Map):
        uid = UniqueID()
        self.id = uid.getId()
        self.map = map

        self.locationsTable = locationsTable
        self.tableRow = 0

        self.latestPlaceableCounterUpdate = getDateTime()
        self.nearPlaceablesCounter = 0
        self.com = CommonFunctions()


    def setMap(self, map:Map):
        self.map = map

    def getLocation(self):
        return self.locationsTable.getLocation(self.tableRow)

    def setLocation(self, loc):
        self.locationsTable.setLocation(self.tableRow, loc)

    def getGeoStruct(self):
        '''
        returns structure of data needed when creating geoJSON representation of this object
        @return: structure with object details, use json.dumps(obj.getGeoJson()) to obtain JSON
        '''
        data = {}
        data["id"] = self.id
        data["type"] = "Feature"

        properties = {}
        properties["type"] = self.__class__.__name__
        properties["id"] = self.id
        properties["gridCoordinates"] = self.getLocation().getGridCoordinates()
        # properties["nearPlaceables"] = self.nearPlaceablesCounter
        data["properties"] = properties

        geometry = {}
        geometry["type"] = "Point"
        location = self.getLocation()
        geometry["coordinates"] = [location.getLongitude(), location.getLatitude(), location.getAltitude()]
        data["geometry"] = geometry

        return data

    def incrementNearPlaceablesCounter(self):
        self.nearPlaceablesCounter+=1

    def savePlaceableCounterToLog(self):
        content = self.com.getYesterdaysDate(getDateTime()).strftime("%Y-%m-%d %H:%M:%S") + ", " + str(self.nearPlaceablesCounter) + "\n"
        self.com.appendToFile("movementLogs/placeablesInZone/"+ self.__class__.__name__ + "_" +str(self.id), content)
        self.latestPlaceableCounterUpdate = getDateTime()
        self.nearPlaceablesCounter = 0