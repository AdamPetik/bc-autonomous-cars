from src.common.Location import Location


class MapEdge:

    def __init__(self):
        self.osmid = None
        self.oneway = None
        # self.lanes
        # self.maxspeed
        self.length = None
        self.highway = None
        self.geometry = None
        self.name = None
        self.startLocation = None
        self.endLocation = None
        self.edgeId = None

    def getOppsiteEnd(self, location: Location):
        if (location.equlsWithLocation(self.startLocation)):
            return self.endLocation

        if (location.equlsWithLocation(self.endLocation)):
            return self.startLocation

        raise ValueError(
            f'It seems that specified location {location.toJson()} does not belong to this edge {self.toString()}')

    def toString(self):
        return f"{self.osmid}|start:{self.startLocation.toString()} end:{self.endLocation.toString()}"
