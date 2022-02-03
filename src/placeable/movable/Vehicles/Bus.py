from copy import deepcopy

from src.placeable.movable.Vehicles.Vehicle import Vehicle
from src.common.Location import Location


class Bus(Vehicle):

    def __init__(self):
        """
        Bus instance drives around the route determined by added bus-stops
        """
        super(Bus, self).__init__()
        self.stops = []

    def addStop(self, point=Location):
        '''
        adds GPS Location point to the bus route
        @param point: Location of point
        @return: no return
        '''
        self.stops.append(point)
        if (len(self.stops) > 1):
            self.makeRouteFromStops()

    def addStops(self, points):
        '''
        adds GPS Location pointa to the bus route
        @param points: list of Location objects
        @return: no return
        '''
        self.stops.extend(points)
        if (len(self.stops) > 1):
            self.makeRouteFromStops()

    def makeRouteFromStops(self):
        '''
        makes route from the given list of bus-stop locations
        @return: no return value
        '''
        # print("making route from stops called, initial location is: ", self.stops[0].toJson())
        self.route = []
        self.locationRoute = []
        points = len(self.stops)
        i = 0
        while (i < (points - 1)):
            self.route.extend(self.city.getRoute(self.stops[i], self.stops[i + 1]))
            i = i + 1
        self.route.extend(self.city.getRoute(self.stops[points - 1], self.stops[0]))
        self.locationRoute = self.city.routeToLocations(self.route)
        self.location = self.locationRoute[0]
        return;

    def walk(self):
        '''
        Overrides Walkable method, moves Bus around defined route
        @return:
        '''
        self.drive()


    def drive(self):
        '''
        Drives Bus around defined route repeatedly
        @return: no return
        '''
        # print(">>Drive called by Bus with ID: ", self.id)
        # print("(so far made ", self.movementsMade, "movements)")
        # print("Current location: " + self.location.toJson(), " (becoming origin location)")
        self.originLocation = deepcopy(self.location)
        distanceToWalk = self.speed
        # print("Going to drive ", distanceToWalk, " meters")

        while (distanceToWalk > 0):
            # print("while| ", distanceToWalk, "m still remaining")

            self.destinationLocation = self.locationRoute[0]
            # print("destination to walk is: " + self.destinationLocation.toJson())
            distanceToDestination = self.com.getReal2dDistance(self.location, self.destinationLocation)
            # print("distance to given location is: ", distanceToDestination)
            if (distanceToDestination < distanceToWalk):
                # print("it was closer than planned drive this iteration, therfore")
                distanceToWalk = distanceToWalk - distanceToDestination
                self.location = self.destinationLocation
                # print("moving to new location ", self.location)
                # print("with remaining distance to drive this iteration: ", distanceToWalk)
                self.locationRoute.append(self.locationRoute[0])
                self.locationRoute.pop(0)
            else:
                self.location = self.com.getLocationFromPathAndDist(distanceToWalk, self.location,
                                                                    self.destinationLocation)
                # print("Managed to move desired distance, my new location is: ", self.location.toJson())
                distanceToWalk = 0

        self.movementsMade = self.movementsMade + 1
        self.updatePassangersLocation()
