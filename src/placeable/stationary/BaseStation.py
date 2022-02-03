from src.city.Map import Map
from src.placeable.Placeable import Placeable

class BaseStation(Placeable):
    def __init__(self, locationsTable, map:Map):
        super(BaseStation, self).__init__(locationsTable, map)

        self.openCellId = 0
        self.created_at = 0
        self.updated_at = 0
        self.radio = 0
        self.mcc = 0
        self.net = 0
        self.area = 0
        self.cell = 0
        self.unit = 0
        self.range = 0
        self.samples = 0
        self.changeable = 0
        self.created = 0
        self.updated = 0
        self.averageSignal = 0
        self.onBuilding = False

        self.Tx_frequency = 2100
        self.Tx_power= 6.3

    def getGeoJson(self):
        data = {}
        data["id"] = self.id
        data["type"] = "Feature"

        properties = {}
        properties["type"] = self.__class__.__name__
        properties["id"] = self.id
        properties["height"] = self.location.height
        properties["onBuilding"] = self.onBuilding
        properties["gridCoordinates"] = self.location.gridCoordinates

        btsDetails = {}
        btsDetails['self.openCellId'] = self.openCellId
        btsDetails['self.radio'] = self.radio
        btsDetails['self.mcc'] = self.mcc
        btsDetails['self.net'] = self.net
        btsDetails['self.area'] = self.area
        btsDetails['self.cell'] = self.cell
        btsDetails['self.unit'] = self.unit
        btsDetails['self.range'] = self.range
        btsDetails['self.samples'] = self.samples
        btsDetails['self.changeable'] = self.changeable
        btsDetails['self.averageSignal'] = self.averageSignal

        properties['btsDetails'] = btsDetails
        data["properties"] = properties

        geometry = {}
        geometry["type"] = "Point"
        geometry["coordinates"] = [self.location.longitude, self.location.latitude, self.location.height]
        data["geometry"] = geometry

        json_data = data
        return json_data
