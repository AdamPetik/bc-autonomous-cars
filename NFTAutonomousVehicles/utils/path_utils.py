from datetime import datetime, timedelta
import math
from typing import Any, Callable, Dict, Generator, Tuple, Union, List
import functools
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt

from src.city.Map import Map
from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from . import map_utils
from src.common.SimulationClock import getDateTime

_com = CommonFunctions()


def _cache(fun):
    """Cache decorator for normalize_edge_between function"""
    cache: Dict[str, List] = {}

    def make_id(l1: Location, l2: Location, dist: float):
        return (
            f'{l1.latitude}-{l1.longitude}-'
            f'{l2.latitude}-{l2.longitude}-'
            f'{dist}'
        )

    @functools.wraps(fun)
    def wrapper(l1, l2, dist, *args, **kwargs):
        # create cache ids. (also in reverse order)
        id1, id2 = make_id(l1, l2, dist), make_id(l2, l1, dist)

        # if in cache -> return
        if id1 in cache.keys():
            return cache[id1][:]

        # if not in cache, call the function
        res = fun(l1, l2, dist, *args, **kwargs)
        # save result (also in reverse order)
        rev = res[:]
        rev.reverse()
        cache[id1] = res
        cache[id2] = rev
        return res[:]
    return wrapper


@_cache
def normalize_edge_between_locs(
    l1: Location, l2: Location, dist: float
) -> List[Location]:
    """
    Add and distribute the nodes along the edge between l1 and l2 nodes by
    distance dist.

    Args:
        l1 (Location): Location 1
        l2 (Location): Location 2
        dist (float): distance between "normalized" nodes

    Returns:
        List[Location]: Normalized path.
    """
    d = _com.getCuda2dDistance(l1, l2)

    if d <= dist:
        return [l1, l2]

    normalized = []

    bearing = _com.getBearing(l1, l2)
    slices = round(d / dist)
    slice_d = (d / slices) * 0.001

    for s in range(1, slices):
        l = map_utils.destination_location(l1, bearing, slice_d*s*1000)
        normalized.append(l)

    return normalized


def normalize_path(path: List[Location], dist: float) -> List[Location]:
    """Add and distribute the nodes along the edges of the path by
    distance dist ("normalized" path includes nodes from the original path).

    Args:
        path (List[Location]): Path.
        dist (float): distance between "normalized" nodes

    Returns:
        List[Location]: Normalized path.
    """
    path_len = len(path)

    if path_len < 2:
        return path[:]

    normalized_path = []

    for index in range(path_len - 1):
        l1, l2 = path[index], path[index+1]
        normalized_path.append(l1)

        normalized_path += normalize_edge_between_locs(l1, l2, dist)

    normalized_path.append(path[-1])
    return normalized_path


def path_time(map: Map, path, speed, weight='length') -> float:
    length = nx.path_weight(map.driveGraph, path, weight=weight)
    return length / speed


def break_condition_time(
    max_t: float,
    speed: float
) -> Callable[[Map, list], bool]:
    def fun(map: Map, path: list) -> bool:
        t = path_time(map, path, speed)
        return t > max_t
    return fun


def _convert_path(map: Map, path) -> List[Location]:
    """Convert nx path to "list of locations path" """
    nodes = map.gdfNodes.loc[path]
    loc_list = []
    for i in range(0, len(nodes.index)): # preco bolo od 1??
        node = nodes.iloc[i]
        loc = Location()
        loc.setLatitude(node['y'])
        loc.setLongitude(node['x'])
        loc.osmnxNode = nodes.index.get_level_values(0).values[i]
        loc_list.append(loc)
    return loc_list


def to_raw_path(locs: List[Location]) -> list:
    """Convert to nx path (list of nodes ids)"""
    result = []
    for l in locs:
        result.append(l.osmnxNode)
    return result


def get_shortest_path(
    map: Map, orig: Location, dest: Location
) -> Union[List[Location], list]:
    """Get the shortest path between two nodes"""
    orig_node = map.getNearestNode(orig)
    dest_node = map.getNearestNode(dest)

    p = ox.shortest_path(map.driveGraph, orig_node, dest_node)
    return _convert_path(map, p), p


def get_shortest_paths(
    map: Map,
    orig: Location,
    dest: Location,
    break_condition=None,
    k=None
) -> Generator[Tuple[List[Location], list], None, None]:
    """Get shortest paths from origin to destination.

    Args:
        map (Map): Map.
        orig (Location): Origin location.
        dest (Location): Destination location.
        break_condition ([type], optional): Function that defines break
            condition. Defaults to None.
        k ([type], optional): [description]. Max number of paths to be yielded.

    Yields:
        Generator[Tuple[List[Location], list], None, None]:
            The next shortest path
    """
    orig_node = map.getNearestNode(orig)
    dest_node = map.getNearestNode(dest)

    for path in ox.k_shortest_paths(map.driveGraph, orig_node, dest_node, k=k):

        if break_condition is not None and break_condition(map, path):
            break

        yield _convert_path(map, path), path


def location_from_path_generator(
    path: List[Location],
    dist: float
) -> Generator[Location, None, None]:
    """
    Generate locations with distance 'dist' between each other along the
    path.
    """
    if len(path) == 0:
        return

    yield path[0]

    l1s = path[:-1]
    l2s = path[1:]
    for l1, l2 in zip(l1s, l2s):
        d = _com.getCuda2dDistance(l1, l2)

        if d <= dist:
            yield l2
            continue

        bearing = _com.getBearing(l1, l2)
        slices = math.ceil(d / dist)

        for s in range(1, slices):
            l = map_utils.destination_location(l1, bearing, dist*s)
            yield l

        yield l2


def get_loc_with_time(
    path: List[Location],
    dist_dt: float,
    dt: float,
    initial_datetime: datetime
) -> Dict[datetime, Location]:
    """Create chain of locations at particular time"""
    dict_ = {}
    timestamp = initial_datetime

    for l in location_from_path_generator(path, dist_dt):
        dict_[timestamp] = l
        timestamp += timedelta(seconds=dt)

    return dict_


def plot_routes(map: Map, routes: list, filepath='routes.png', c=['r']):
    raw_paths = [to_raw_path(r) for r in routes]
    if len(routes) == 1:
        ox.plot_graph_route(
            map.driveGraph,
            routes[0],
            route_color=c[0],
            save=True,
            filepath=filepath
        )
    else:
        fig, ax = ox.plot_graph_routes(
            map.driveGraph,
            raw_paths,
            save=True,
            filepath='routes.png',
            route_colors=c
        )
    plt.close(fig)
