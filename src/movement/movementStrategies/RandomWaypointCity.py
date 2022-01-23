import copy
import math

from src.common.Location import Location
from src.movement.movementStrategies.MovementStrategy import MovementStrategy

# CUDA kernel
from src.placeable.movable.Movable import Movable
from src.placeable.movable.Person import Person


class RandomWaypointCity(MovementStrategy):

    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType):
        super(RandomWaypointCity, self).__init__(locationsTable, movableSet, map, mapGrid, strategyType)

    def move(self):
        # print("Before move-------\n", self.locationsTable.table)
        def toRadians(degrees):
            return degrees * math.pi / 180

        def toDegrees(radians):
            return radians * 180 / math.pi

        latstep = self.mapGrid.latStep
        latmin = self.mapGrid.latmin

        lonstep = self.mapGrid.lonStep
        lonmin = self.mapGrid.lonmin

        for actorId in self.locationsTable.getAllIds():
            walkable: Movable = self.movableSet[int(actorId)]

            lat1 = walkable.getLocation().getLatitude()
            lon1 = walkable.getLocation().getLongitude()
            lat2 = walkable.getTargetLocation().getLatitude()
            lon2 = walkable.getTargetLocation().getLongitude()
            distanceToWalk = walkable.getSpeed()  # speed actually

            d = distanceToWalk
            R = 6371000
            lat1rad = math.radians(lat1)
            lat2rad = math.radians(lat2)
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)

            a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1rad) * math.cos(lat2rad) * math.sin(
                dLon / 2) * math.sin(dLon / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distanceBetweenPoints = R * c

            if (distanceToWalk > distanceBetweenPoints):
                walkable.setLocation(walkable.getTargetLocation())
                walkable.setTargetReached(True)
            else:
                walkable.setTargetReached(False)
                lat1rad = toRadians(lat1)
                lon1rad = toRadians(lon1)

                lat2rad = toRadians(lat2)
                diffLong = toRadians(lon2 - lon1)

                x = math.sin(diffLong) * math.cos(lat2rad)
                y = math.cos(lat1rad) * math.sin(lat2rad) - (math.sin(lat1rad) * math.cos(lat2rad) * math.cos(diffLong))
                initial_bearing = math.atan2(x, y)
                initial_bearing = toDegrees(initial_bearing)
                brng = toRadians((initial_bearing + 360) % 360)

                lat3rad = math.asin(
                    math.sin(lat1rad) * math.cos(d / R) + math.cos(lat1rad) * math.sin(d / R) * math.cos(brng))
                lon3rad = lon1rad + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(lat1rad),
                                               math.cos(d / R) - math.sin(lat1rad) * math.sin(lat2rad))
                lat3 = toDegrees(lat3rad)
                lon3 = toDegrees(lon3rad)

                newLocation = Location(latitude=lat3, longitude=lon3)
                newLocation.setGridCoordinates(int((lat3 - latmin) // latstep), int((lon3 - lonmin) // lonstep))
                walkable.setLocation(newLocation)
        # print("After move-------\n", self.locationsTable.table)

    def getNewRoute(self, walkable):
        return self.map.getRouteBetweenNodes(walkable.getLocation(), self.map.getRandomNode(walkable.getLocation()))

    def getRouteTo(self, walkable, location: Location):
        return self.map.getRouteBetweenNodes(walkable.getLocation(), location)

    def onDayChange(self, person: Person):
        '''
        No activity is needed on day change for this Strategy
        :param person:
        :return:
        '''
        return

    # experimental
    def getNextLocationOnRoute(self, currentLocation, targetLocation, speed):
        def toRadians(degrees):
            return degrees * math.pi / 180

        def toDegrees(radians):
            return radians * 180 / math.pi

        latstep = self.mapGrid.latStep
        latmin = self.mapGrid.latmin
        lonstep = self.mapGrid.lonStep
        lonmin = self.mapGrid.lonmin

        lat1 = currentLocation.getLatitude()
        lon1 = currentLocation.getLongitude()
        lat2 = targetLocation.getLatitude()
        lon2 = targetLocation.getLongitude()
        distanceToWalk = speed  # speed actually

        d = distanceToWalk
        R = 6371000
        lat1rad = math.radians(lat1)
        lat2rad = math.radians(lat2)
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1rad) * math.cos(lat2rad) * math.sin(
            dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distanceBetweenPoints = R * c

        if (distanceToWalk > distanceBetweenPoints):
            return copy.deepcopy(targetLocation), True
        else:
            lat1rad = toRadians(lat1)
            lon1rad = toRadians(lon1)
            lat2rad = toRadians(lat2)
            diffLong = toRadians(lon2 - lon1)

            x = math.sin(diffLong) * math.cos(lat2rad)
            y = math.cos(lat1rad) * math.sin(lat2rad) - (math.sin(lat1rad) * math.cos(lat2rad) * math.cos(diffLong))
            initial_bearing = math.atan2(x, y)
            initial_bearing = toDegrees(initial_bearing)
            brng = toRadians((initial_bearing + 360) % 360)

            lat3rad = math.asin(
                math.sin(lat1rad) * math.cos(d / R) + math.cos(lat1rad) * math.sin(d / R) * math.cos(brng))
            lon3rad = lon1rad + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(lat1rad),
                                           math.cos(d / R) - math.sin(lat1rad) * math.sin(lat2rad))
            lat3 = toDegrees(lat3rad)
            lon3 = toDegrees(lon3rad)

            newLocation = Location(latitude=lat3, longitude=lon3)
            newLocation.setGridCoordinates(int((lat3 - latmin) // latstep), int((lon3 - lonmin) // lonstep))
            return newLocation, False
