import json


class Location:
    def __init__(self, latitude=0, longitude=0, altitude=0, osmnxNode=None):
        '''
        Location class representing point with GPS coordinates
        @param latitude: latitude
        @param longitude: longitude
        @param altitude: height above the surface of map
        '''
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.osmnxNode = osmnxNode
        self.gridCoordinates = []

    def getLatitude(self):
        return self.latitude

    def getLongitude(self):
        return self.longitude

    def getAltitude(self):
        return self.altitude

    def setLatitude(self, lat):
        self.latitude = lat

    def setLongitude(self, lon):
        self.longitude = lon

    def setAltitude(self, alt):
        self.altitude = alt

    def setGridCoordinates(self, x, y):
        self.gridCoordinates = [x, y]

    def getGridCoordinates(self):
        return self.gridCoordinates

    def getGridXcoor(self):
        return self.gridCoordinates[0]

    def getGridYcoor(self):
        return self.gridCoordinates[1]

    def getOsmnxNode(self):
        return self.osmnxNode

    def setOsmnxNode(self, node):
        self.osmnxNode = node

    def equlsWithLocation(self, location):
        if location is None:
            return False

        # if both locations have osmnx node id assigned compare those
        if ((self.osmnxNode is not None) and (location.osmnxNode is not None)):
            return self.osmnxNode == location.osmnxNode

        # else compare locations themsleves
        else:
            return self.longitude == location.longitude and self.latitude == location.latitude

    def toJson(self):
        data = {}
        data['latitude'] = self.getLatitude()
        data['longitude'] = self.getLongitude()
        data['altitude'] = self.getAltitude()
        if self.osmnxNode != None:
            data['osmnxNode'] = int(self.osmnxNode)
        else:
            data['osmnxNode'] = None
        # gridCoordinates = {}
        # gridCoordinates['x'] = self.getGridXcoor()
        # gridCoordinates['y'] = self.getGridYcoor()
        # data['gridCoordinates'] = gridCoordinates
        json_data = json.dumps(data)
        return json_data

    def toString(self):
        return f"osmid={self.osmnxNode}_latitude={self.latitude},longitude={self.longitude}"

    def toRoundedString(self):
        return format(self.latitude, '.6f') + "_" + format(self.longitude, '.6f')
        # return str(round(self.latitude, 6)) + "_" + str(round(self.longitude, 6))
