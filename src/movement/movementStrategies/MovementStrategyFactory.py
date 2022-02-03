from src.movement.movementStrategies.DroneMovementCuda import DroneMovementCuda
from src.movement.movementStrategies.PreloadedLocationsStrategy import PreloadedLocationsStrategy
from src.movement.movementStrategies.RandomWaypointBlankEnvCuda import RandomWaypointBlankEnvCuda
from src.movement.movementStrategies.RandomWaypointCity import RandomWaypointCity
from src.movement.movementStrategies.RandomWaypointCityCuda import RandomWaypointCityCuda
from src.movement.movementStrategies.RandomIntersectionWaypointCityCuda import RandomIntersectionWaypointCityCuda

from src.movement.movementStrategies.PersonBehaviorCityCuda import PersonBehaviourCityCuda
from src.movement.movementStrategies.MovementStrategyType import MovementStrategyType


class MovementStrategyFactory:
    def getStrategy(self, type: MovementStrategyType, locationsTable, actorSet, map, mapGrid):

        if (type == MovementStrategyType.RANDOM_WAYPOINT_CITY_CUDA):
            return RandomWaypointCityCuda(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.RANDOM_WAYPOINT_CITY):
            return RandomWaypointCity(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.RANDOM_WAYPOINT_BLANK_ENV_CUDA):
            return RandomWaypointBlankEnvCuda(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.DRONE_MOVEMENT_CUDA):
            return DroneMovementCuda(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.PERSON_BEHAVIOUR_CITY_CUDA):
            return PersonBehaviourCityCuda(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.RANDOM_INTERSECTION_WAYPOINT_CITY_CUDA):
            return RandomIntersectionWaypointCityCuda(locationsTable, actorSet, map, mapGrid, type)

        if (type == MovementStrategyType.PRELOADED_LOCATIONS_STRATEGY):
            return PreloadedLocationsStrategy(locationsTable, actorSet, map, mapGrid, type)
        return None
