from src.city.Map import Map
from src.movement.LocationsTable import LocationsTable
from src.placeable.Placeable import Placeable


class Attractor(Placeable):
    def __init__(self, locationsTable: LocationsTable, map: Map, radius: int, startTime=None, endTime=None,
                 severity=50):
        super(Attractor, self).__init__(locationsTable, map)
        self.name = "Default attractor name"
        self.radius = radius
        self.startTime = startTime
        self.endTime = endTime
        self.severity = severity

    def getGeoJson(self):
        data = {}
        data["id"] = self.id
        data["type"] = "Feature"

        properties = {}
        properties["type"] = self.__class__.__name__
        properties["id"] = self.id
        properties["height"] = self.getLocation().getAltitude()
        properties["gridCoordinates"] = self.getLocation().gridCoordinates

        attractorDetails = {}
        attractorDetails['name'] = self.name
        attractorDetails['radius'] = self.radius
        attractorDetails['startTime'] = self.startTime
        attractorDetails['endTime'] = self.endTime

        properties['attractorDetails'] = attractorDetails
        data["properties"] = properties

        geometry = {}
        geometry["type"] = "Point"
        geometry["coordinates"] = [self.getLocation().getLongitude(), self.getLocation().getLatitude(),
                                   self.getLocation().getAltitude()]
        data["geometry"] = geometry

        json_data = data
        return json_data
