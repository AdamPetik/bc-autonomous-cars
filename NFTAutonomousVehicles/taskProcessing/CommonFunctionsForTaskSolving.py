from src.common.Location import Location
from src. common.CommonFunctions import CommonFunctions

class CommonFunctionsForTaskSolving:

    def __init__(self):
        self.com = CommonFunctions()

    def getConnectionSpeedInMegabytesPerSecond(self, distance):
        return 110 - (3 * distance)

    # def getConnectionSpeedInMegabytesPerSecond(self, location_a: Location, location_b: Location):
    #     return self.getConnectionSpeedInMegabytesPerSecond(self.com.getReal2dDistance(location_a, location_b))

    def getTransferTimeInSeconds(self, location_a: Location, location_b: Location, task_size_in_megabytes):
        speed = self.getConnectionSpeedInMegabytesPerSecond(self.com.getReal2dDistance(location_a, location_b))
        return task_size_in_megabytes / speed

    def getEffectiveDistanceOfConnection(self, solving_time, time_limit, task_size_in_megabytes):
        time_limit_for_single_transfer = (time_limit - solving_time) / 2
        effective_distance = (100 - (task_size_in_megabytes / time_limit_for_single_transfer)) / 3
        # print(f"getEffectiveDistanceOfConnection:  time_limit_for_single_transfer={time_limit_for_single_transfer}, effective_distance={effective_distance}  ")
        return effective_distance
