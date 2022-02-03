from src.common.Location import Location
from src.common.CommonFunctions import CommonFunctions
from src.common.UniqueID import UniqueID
from shapely.geometry import Polygon

import math


class Building():

    def __init__(self):
        uid = UniqueID()
        self.id = uid.getId()
        self.geometryLocations = []
        self.geometryShapely = None
        self.height = 0

        self.centroid = None
        self.com = CommonFunctions()
        self.tupleNodeLocations = ()

    def getGeometryShapely(self):
        if (self.geometryShapely is None):
            self.geometryShapely = Polygon(self.getTupleNodeLocations())
        return self.geometryShapely

    def getTupleNodeLocations(self):
        if (self.tupleNodeLocations == ()):
            for point in self.geometryLocations:
                tpoint = (point.latitude, point.longitude)
                self.tupleNodeLocations += (tpoint,)
        return self.tupleNodeLocations


    def getCentroid(self):
        if self.centroid is None:
            coords = self.getGeometryShapely().centroid.coords
            self.centroid = Location(coords[0][0], coords[0][1], self.height)
        return self.centroid

    def addLocationPoint(self, loc=Location):
        self.geometryLocations.append(loc)


    # y = latitude
    # x = longitude

    def setHeight(self, h):
        height = float(h)
        if (math.isnan(height) == False):
            self.height = height
        else:
            self.height = 0

    def pointInBuilding(self, testPoint=Location):
        poly = Polygon(self.getTupleNodeLocations())
        point = self.com.getPointFromLocation(testPoint)
        return point.within(poly)


    def getGeoJson(self):
        '''
        returns structure of data needed when creating geoJSON representation of this object
        @return: structure with object details, use json.dumps(obj.getGeoJson()) to obtain JSON
        '''
        data = {}
        data['id'] = self.id
        data['type'] = "Feature"

        properties = {}
        properties['type'] = "Building"
        properties["id"] = self.id
        properties['height'] = self.height
        data['properties'] = properties

        geometry = {}
        geometry['type'] = "Point"
        geometry['coordinates'] = [self.centroid.longitude, self.centroid.latitude, self.centroid.getAltitude()]
        data['geometry'] = geometry

        json_data = data
        return json_data
