from enum import Enum

class MovementStrategyType(Enum):
    RANDOM_WAYPOINT_CITY_CUDA = "RandomWaypointCityCuda"
    RANDOM_WAYPOINT_CITY = "RandomWaypointCity"
    RANDOM_WAYPOINT_BLANK_ENV_CUDA = "RandomWaypointBlankEnvCuda"
    DRONE_MOVEMENT_CUDA = "DroneMovementCuda"
    PERSON_BEHAVIOUR_CITY_CUDA = "PersonBehaviourCityCuda"
    RANDOM_INTERSECTION_WAYPOINT_CITY_CUDA = "RandomIntersectionWaypointCityCuda"
    PRELOADED_LOCATIONS_STRATEGY = "PreloadedLocationsStrategy"
