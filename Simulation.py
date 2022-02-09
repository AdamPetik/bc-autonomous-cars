from NFTAutonomousVehicles.iisMotionCustomInterface.IISMotion import IISMotion
from NFTAutonomousVehicles.resultCollectors.MainCollector import MainCollector
from NFTAutonomousVehicles.utils.sinr_map import SINRMap
from src.city.ZoneType import ZoneType
from src.common.Location import Location
from src.common.CommonFunctions import CommonFunctions
from src.common.SimulationClock import *
import asyncio
import time

from src.movement.LocationPredictor import LocationPredictor
from src.movement.movementStrategies.MovementStrategyType import MovementStrategyType

fun = CommonFunctions()

# Setting location that will be simulated
location = Location()
location.setLatitude(48.709936)
location.setLongitude(21.238923)
location.setAltitude(0)
radius = 200  # radius around the location that will be included

oneway = False  # oneways are disabled so agents will not get stuck at the edges of simulated area
guiEnabled = False  # gui enabled, to see the agents, open /frontend/index.html in your browser while simulation running
guiTimeout = 3.2  # in seconds, sleep between simulations steps (gui is unable to keep up with updates at full speed)
intersectionCheck = True  # check whether agents are located at the intersection nodes
gridRows = 5  # grid that world is split into (used to find closest pairs of agents when needed)

secondsPerTick = 1  # each iteration will increment clock by 1 second
processing_iteration_duration_seconds = 0.1
noOfTicks = 100000  # number of iterations simulation will take



iismotion = IISMotion(radius=radius,
                      location=location,
                      oneWayEnabled=oneway,
                      guiEnabled=guiEnabled,
                      gridRows=gridRows,
                      secondsPerTick=secondsPerTick,
                      removeDeadends=True
                      )  # initialize IISMotion

map_grid = iismotion.mapGrid

sinr_map = SINRMap(
    x_size=130,
    y_size=130,
    latmin=map_grid.latmin,
    latmax=map_grid.latmax,
    lonmin=map_grid.lonmin,
    lonmax=map_grid.lonmax,
)


logger = MainCollector()

nftVehicles = iismotion\
    .createActorCollection("nftVehicles", True, MovementStrategyType.PRELOADED_LOCATIONS_STRATEGY) \
    .addAutonomousVehicles(10, False, 0) \
    .setGuiEnabled(guiEnabled)

basicVehicles = iismotion\
    .createActorCollection("basicVehicles", True, MovementStrategyType.RANDOM_WAYPOINT_CITY) \
    .addAutonomousVehicles(1, False, 1) \
    .setGuiEnabled(guiEnabled)

nftVehicles.sinr_map = sinr_map
basicVehicles.sinr_map = sinr_map

taskSolvers = iismotion\
    .createActorCollection("taskSolvers", False, MovementStrategyType.DRONE_MOVEMENT_CUDA) \
    .setGuiEnabled(guiEnabled)

iismotion.getActorCollection("taskSolvers").generateTaskSolvers(50, 50)
print(" - solvers generated")
# iismotion.getActorCollection("taskSolvers").storeTaskSolvers("middleMap.json")
# taskSolvers.loadTaskSolversFromFile("middleMap.json")
# iismotion.getActorCollection("taskSolvers").loadTaskSolversFromFile("smallV1_2_50.json")
iismotion.getActorCollection("taskSolvers").setSolversProcessingIterationDurationInSeconds(processing_iteration_duration_seconds)




# method that moves agents for desired number of iterations
# async because of "GUI"
async def simulate():
    print("=================== Simulation started ===================")
    start = time.time()
    for step in range(0, noOfTicks):
        newDay = updateSimulationClock(secondsPerTick)
        print(f"---------------- step: {step} ---------------- dateTime : {getDateTime()} ----------------")
        stepStart = time.time()

        basicVehicles.planRoutesForNonNFTVehicles(newDay)
        nftVehicles.planRoutesForNFTVehicles(['taskSolvers'], logger)
        iismotion.stepAllCollections(newDay, logger)

        nftVehicles.generateAndSendNFTTasks(logger)
        basicVehicles.generateAndSendNonNFTTasks(['taskSolvers'], logger)
        taskSolvers.solveTasks(logger)

        stepEnd = time.time()
        print("step took ", stepEnd - stepStart)
        global DATETIME
        if (guiEnabled == True):
            await asyncio.sleep(guiTimeout)
        end = time.time()

    elapsed = end - start
    print("================== Simulation finished ===================")
    print("elapsed time:", elapsed)


#main method that will execute simulation based on guiEnabled param
def main():
    if (guiEnabled):
        loop = asyncio.get_event_loop()
        loop.create_task(simulate())
        loop.run_until_complete(iismotion.frontend.start_server)
        loop.run_forever()
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate())

if __name__ == '__main__':
    main()
    logger.closeCollector()
    # cProfile.run('main()')
