import json

from src.common.Location import Location
from src.common.SimulationClock import *
from src.placeable.movable.MovementActivityType import MovementActivityType
from src.common.UniqueID import UniqueID

class MovementActivity():

    def __init__(self, destination: Location, startTime=None, endTime=None, importance=0, name="Default activity name",
                 type=MovementActivityType.REGULAR_ACTIVITY, routePlanningRequired=True):
        uid = UniqueID()
        self.id = uid.getId()
        self.destination = destination
        self.route = []
        self.startTime = startTime
        self.endTime = endTime
        self.importance = importance
        self.name = name
        self.type = type
        self.routePlanningRequired = routePlanningRequired

    def setRoutePlanningRequired(self, value):
        self.routePlanningRequired = value

    def getRoutePlanningRequired(self) -> bool:
        return self.routePlanningRequired

    def getDestination(self) -> Location:
        return self.destination

    def getType(self) -> MovementActivityType:
        return self.type

    def isReadyForActivation(self) -> bool:
        global DATETIME
        if(getDateTime() > self.datetime):
            return True
        else:
            return False

    def getStarted(self) -> bool:
        global DATETIME
        if (self.startTime == None):
            return True
        else:
            if (getDateTime() >= self.startTime):
                return True
            else:
                return False

    def getFinished(self) -> bool:
        global DATETIME
        if (self.endTime == None):
            return True
        else:
            if (getDateTime() >= self.endTime):
                return True
            else:
                return False

    def getNextLoctionFromRouteAndPopIt(self) -> Location:
        if not self.route:
            return self.destination
        location = self.route[0]
        self.route.pop(0)
        return location

    def pushLocationListToRoute(self, locationList):
        self.route.extend(locationList)

    def routeEmpty(self):
        if not self.route:
            return True
        else:
            return False

        self.destination = destination
        self.route = []
        self.startTime = startTime
        self.endTime = endTime
        self.importance = importance
        self.name = name
        self.type = type
        self.routePlanningRequired = routePlanningRequired

    def toJson(self):
        data = {}
        data['id'] = self.id
        data['name'] = self.name
        data['destination'] = self.destination.toJson()
        data['routeLength'] = len(self.route)
        data['startTime'] = self.startTime
        data['endTime'] = self.endTime
        data['importance'] = self.importance
        data['type'] = self.type.name
        data['routePlanningRequired'] = self.routePlanningRequired
        json_data = json.dumps(data, default=str)
        return json_data
