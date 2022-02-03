from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from src.placeable.Placeable import Placeable
from src.common.SimulationClock import *
from src.placeable.movable.MovementActivity import MovementActivity


class Movable(Placeable):
    def __init__(self, locationsTable, map):
        super(Movable, self).__init__(locationsTable, map)
        self.activityQueue = []
        self.com = CommonFunctions()
        self.locationLog = ""
        self.previousTarget = None

    def getSpeed(self) -> int:
        return self.locationsTable.getSpeed(self.tableRow)

    def setSpeed(self, speed):
        self.locationsTable.setSpeed(self.tableRow, speed)

    def getTargetLocation(self) -> Location:
        return self.locationsTable.getTargetLocation(self.tableRow)

    def setTargetLocation(self, loc):
        self.previousTarget = self.getTargetLocation()
        self.locationsTable.setTargetLocation(self.tableRow, loc)

    def getTargetReached(self) -> bool:
        return self.locationsTable.getTargetReached(self.tableRow)

    def setTargetReached(self, boolValue):
        self.locationsTable.setTargetReached(self.tableRow, boolValue)

    def getIsAtIntersection(self) -> bool:
        self.locationsTable.getIsAtIntersection(self.tableRow)

    def setIsAtIntersection(self, boolValue):
        self.locationsTable.setIsAtIntersection(self.tableRow, boolValue)

    def logLocation(self, newDay=False):
        if (newDay):
            with open("movementLogs/" + str(self.id) + "_" + self.com.getYesterdaysDate(getDateTime()).strftime(
                    "%Y-%m-%d") + ".txt", "w") as text_file:
                print(self.locationLog, file=text_file)
            self.locationLog = ""
        location = self.getLocation()
        global DATE
        self.locationLog = self.locationLog + getDateTime().strftime("%Y-%m-%d %H:%M:%S") + ", " + str(
            location.getLatitude()) + ", " + str(location.getLongitude()) + "\n"

    def getCurrentMovementActivity(self) -> MovementActivity:
        if not self.activityQueue:
            return None
        return self.activityQueue[0]

    def getLastPlannedActivity(self) -> MovementActivity:
        return self.activityQueue[-1]

    def storeMovementActivity(self, activity: MovementActivity, asFirst=False):
        if (asFirst):
            if self.activityQueue:
                self.activityQueue[0].setRoutePlanningRequired(True)
            self.activityQueue.insert(0, activity)
        else:
            raise ValueError('Inserting an event into list based on time not yet implemented, use asFist=True')
            # TODO add proper inserting of activity between already planned activities
            # based on time of newly inserted activity

    def appendMovementActivity(self, activity: MovementActivity):
        self.activityQueue.append(activity)

    def removeFirstActivity(self):
        self.activityQueue.pop(0)
