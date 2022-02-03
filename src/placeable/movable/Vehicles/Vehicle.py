from src.placeable.movable.Movable import Movable
from src.placeable.movable.Person import Person


class Vehicle(Movable):

    def __init__(self):
        '''
        creates vehicle that can carry persons as passengers
        '''
        super(Vehicle, self).__init__()
        self.passangers = []
        self.passangerCount = 0

    def addPerson(self, person=Person):
        '''
        adds Person to the vehicle
        @param person: Person object to be inserted into car
        @return: no return
        '''
        person.location = self.location
        person.setInVehicle(True)
        self.passangers.append(person)
        self.passangerCount = self.passangerCount + 1

    def updatePassangersLocation(self):
        '''
        updates passangers' locations to match the location of car
        @return:
        '''
        for person in self.passangers:
            person.location = self.location

    def getGeoJson(self):
        '''
        returns structure of data needed when creating geoJSON representation of this object
        @return: structure with object details, use json.dumps(obj.getGeoJson()) to obtain JSON
        '''
        data = {}
        data['id'] = self.id
        data['type'] = "Features"

        properties = {}
        properties['type'] = self.__class__.__name__
        properties['passangers'] = self.passangerCount
        data['properties'] = properties

        geometry = {}
        geometry['type'] = "Point"
        geometry['coordinates'] = [self.location.longitude, self.location.latitude, self.location.height]
        data['geometry'] = geometry

        json_data = data
        return json_data
