from src.placeable.movable.Vehicles.Vehicle import Vehicle


class Car(Vehicle):

    def __init__(self):
        super(Car, self).__init__()

    def walk(self):
        super(Car, self).walk()
        self.updatePassangersLocation()

        return
