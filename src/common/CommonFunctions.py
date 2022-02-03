
from src.common.Location import Location
from shapely.geometry import Point
import geopy.distance
import math
import time
from random import randint, uniform
import numpy as np
from datetime import datetime, time, timedelta
from src.common.SimulationClock import *

class CommonFunctions:

    def getReal2dDistance(self, first=Location, second=Location):
        coords_1 = (first.getLatitude(), first.getLongitude())
        coords_2 = (second.getLatitude(), second.getLongitude())
        return geopy.distance.geodesic(coords_1, coords_2).m

    # def get2dCoordDistance(self, first=Location, second=Location): #Deprecated
    #     latDifference = first.getLatitude() - second.getLatitude()
    #     lonDifference = first.getLongitude() - second.getLongitude()
    #     coorDistance = math.sqrt(math.pow(latDifference, 2) + math.pow(lonDifference, 2))
    #     return coorDistance

    def getCuda2dDistance(self, first=Location, second=Location):
        # according to: https://www.movable-type.co.uk/scripts/latlong.html
        R = 6371000
        lat1rad = math.radians(first.getLatitude())
        lat2rad = math.radians(second.getLatitude())
        dLat = math.radians(second.getLatitude() - first.getLatitude())
        dLon = math.radians(second.getLongitude() - first.getLongitude())

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1rad) * math.cos(lat2rad) * math.sin(
            dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distanceBetweenPoints = R * c
        return distanceBetweenPoints


    def get3dDistance(self, first=Location, second=Location):
        coords_1 = (first.getLatitude(), first.getLongitude())
        coords_2 = (second.getLatitude(), second.getLongitude())
        landDist = geopy.distance.vincenty(coords_1, coords_2).m;

        heightDifference = abs(first.getHeight() - second.getHeight())
        aerialDistance = math.sqrt(math.pow(landDist, 2) + math.pow(heightDifference, 2))
        return aerialDistance;

    def getBearing(self, first=Location, second=Location):
        lat1 = math.radians(first.getLatitude())
        lat2 = math.radians(second.getLatitude())

        diffLong = math.radians(second.getLongitude() - first.getLongitude())

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing;

    def getLocationFromPathAndDist(self, Xmeters, first=Location, second=Location):
        d = Xmeters
        R = 6370000
        brng = self.getBearing(first, second)

        lat1 = math.radians(first.getLatitude())  # Current lat point converted to radians
        lon1 = math.radians(first.getLongitude())  # Current long point converted to radians

        brng = math.radians(brng)
        lat2 = math.asin(math.sin(lat1) * math.cos(d / R) + math.cos(lat1) * math.sin(d / R) * math.cos(brng))
        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(lat1),
                                 math.cos(d / R) - math.sin(lat1) * math.sin(lat2))

        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)

        newLocation = Location()
        newLocation.setLatitude(lat2)
        newLocation.setLongitude(lon2)
        newLocation.setHeight(first.getHeight())
        return newLocation

    def getTimestamp(self):
        timestr = time.strftime("%Y-%m-%d_%H:%M:%S")
        return timestr

    def appendToFile(self, filename, text):
        with open(filename + ".txt", "a") as myfile:
            myfile.write(text)
        return

    def getPointFromLocation(self, point=Location):
        tpoint = (point.latitude, point.longitude)
        return Point(tpoint)

    def getShortestDistanceFromLocations(self, locations, point=Location):
        shortest = 9999999.9
        for location in locations:
            distance = self.getReal2dDistance(location, point)
            if (distance < shortest):
                shortest = distance

        return shortest

    def getRandomLocationWithinCity(self, latitudeInterval, longitudeInterval, height):
        lat = uniform(latitudeInterval[0], latitudeInterval[1])
        lon = uniform(longitudeInterval[0], longitudeInterval[1])
        location = Location(lat, lon, height)
        return location

    def getClosestActorFromList(self, location, collection):
        closestActor = collection[0]
        shortestDistance = self.getReal2dDistance(location, closestActor.getLocation())

        for actor in collection:
            newDistance= self.getReal2dDistance(location, actor.getLocation())
            if(newDistance < shortestDistance):
                shortestDistance = newDistance
                closestActor = actor
        return closestActor


    def getClosestActorFromListAndDistance(self, location, collection):
        if(len(collection)==0):
            return None, None

        closestActor = collection[0]
        shortestDistance = self.getReal2dDistance(location, closestActor.getLocation())

        for actor in collection:
            newDistance= self.getReal2dDistance(location, actor.getLocation())
            if(newDistance < shortestDistance):
                shortestDistance = newDistance
                closestActor = actor
        return closestActor, shortestDistance

    def getTimeFromNormalDistribution(self, sigma, mu, minutesFromUniform: bool):

        hour =  int(abs(round((np.random.randn(1) * sigma + mu)[0])))
        while (hour>23):
            hour = int(abs(round((np.random.randn(1) * sigma + mu)[0])))

        if (minutesFromUniform):
            minute = randint(0, 59)
        else:
            minute = 0
        return time(hour, minute, 0, 0)

    def getTodaysDaytimeFromTime(self,inputTime):
        global DATETIME
        simulationTime = getDateTime()
        return datetime(simulationTime.year, simulationTime.month, simulationTime.day, inputTime.hour, inputTime.minute, 0, 0)

    def timePlusHoursMinutes(self, startTime, deltaHours=0, deltaMinutes=0):
        tmp_datetime = datetime(2019, 1, 1, startTime.hour, startTime.minute, 0, 0)
        tmp_datetime = tmp_datetime + timedelta(hours=deltaHours, minutes=deltaMinutes)
        return time(tmp_datetime.hour, tmp_datetime.minute,0 , 0)

    def getYesterdaysDate(self, todayDate):
        return todayDate - timedelta(days=1)

    def getTomorrowsDate(self, todayDate):
        return todayDate + timedelta(days=1)

    def printRoutes(self, routes):
        routeIndex = 0
        for route in routes:
            print(f" ---------- route # {routeIndex}")
            locationIndex = 1
            for location in route:
                print(f"{locationIndex}.    |{location.toString()}, route#{routeIndex} step#{locationIndex}")
                locationIndex = locationIndex + 1
            routeIndex = routeIndex + 1
