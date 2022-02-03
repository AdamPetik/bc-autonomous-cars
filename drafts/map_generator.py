import math
import os
import pickle

import numpy as np
from typing import List, Tuple, Union
from itertools import chain
import networkx as nx
import osmnx as ox
import geopy
# from geopy import distance

from src.common.Location import Location


def create_manhattan_map(
    origin: Location,
    x_dists: List[float],
    y_dists: List[float],
) -> nx.MultiGraph:
    """ Create Manhattan like graph.

    Args:
        origin (Location): Upper left location of the graph.

        x_dists (List[float]): distances between nodes along x axis (East,
                                West).

        y_dists (List[float]): distances between nodes along y axis (North,
                                South).

    Returns:
        nx.MultiGraph: [description]
    """

    E, S = 90, 180  # East, South bearings

    # mandatory arguments for edge with default values (they are not important)
    e_p = dict(oneway=False, highway=False, name=np.nan)

    # crs is mandatory for osmnx
    G = nx.MultiGraph(crs='epsg:4326')

    # nodes count along x,y axis
    x_n_len = len(x_dists) + 1
    y_n_len = len(y_dists) + 1

    # calculate street_count parameter for nodes by their x,y indexis
    def _street_count(x_idx: int, y_idx: int) -> int:
        # at corners condition
        cond = (
            (x_idx == x_n_len or x_idx == 0)
            and
            (y_idx == 0 or y_idx == y_n_len - 1)
        )

        if cond:
            return 2

        # on edge condition
        cond = (
            x_idx == 0 or y_idx == 0
            or y_idx == y_n_len-1 or x_idx == x_n_len-1
        )

        if cond:
            return 3

        # all others
        return 4

    # do 2d list of all nodes ids
    ids = []
    for x in range(x_n_len):
        ids.append([])
        for y in range(y_n_len):
            ids[x].append(y * x_n_len + x)

    # create all nodes
    G.add_nodes_from(list(chain.from_iterable(ids)))

    for y_idx, y_km in enumerate(y_dists):

        # reasign origin location to the next row (next y)
        if y_idx == 0:
            origin_loc = origin
        else:  # y_idx != 0
            n = G.nodes[ids[0][y_idx]]
            origin_loc = Location(latitude=n['y'], longitude=n['x'])

        for x_idx, x_km in enumerate(x_dists):
            # upper left node
            id1 = ids[x_idx][y_idx]
            _set_node_attr(G, id1, origin_loc, _street_count(x_idx, y_idx))

            # upper right node
            # p = distance.distance(kilometers=x_km).destination(
            #     (origin_loc.latitude, origin_loc.longitude),
            #     bearing=E,
            # )
            p = destination_location(origin_loc, E, x_km*1000)
            id2 = ids[x_idx+1][y_idx]
            _set_node_attr(G, id2, p, _street_count(x_idx+1, y_idx))

            # lower right node
            # p = distance.distance(kilometers=y_km).destination(p, bearing=S)
            p = destination_location(p, S, y_km*1000)
            id3 = ids[x_idx+1][y_idx+1]
            _set_node_attr(G, id3, p, _street_count(x_idx+1, y_idx+1))

            # lower left node
            # p = distance.distance(kilometers=y_km).destination(
            #     (origin_loc.latitude, origin_loc.longitude),
            #     bearing=S,
            # )
            p = destination_location(origin_loc, S, y_km*1000)
            id4 = ids[x_idx][y_idx+1]
            _set_node_attr(G, id4, p, _street_count(x_idx, y_idx+1))

            # those two edges certainly don't exist
            G.add_edge(id1, id2, length=x_km*1000,
                       osmid=eosmid(id1, id2), **e_p)
            G.add_edge(id2, id3, length=y_km*1000,
                       osmid=eosmid(id2, id3), **e_p)

            # those may exist
            if not G.has_edge(id1, id4):
                G.add_edge(id1, id4, length=y_km*1000,
                           osmid=eosmid(id1, id4), **e_p)

            if not G.has_edge(id3, id4):
                G.add_edge(id3, id4, length=x_km*1000,
                           osmid=eosmid(id3, id4), **e_p)

            origin_loc = Location(G.nodes[id2]['y'], G.nodes[id2]['x'])
    return G


def _set_node_attr(
    G: nx.MultiGraph,
    node_id: int,
    loc: Union[Location, Tuple[float, float], geopy.Point],
    street_count: int = 1,
    force=False,
) -> None:
    """Set atributes of node

    Args:
        force (bool, optional): whether to override or not if node has params.
                Defaults to False.
    """
    if 'x' in G.nodes[node_id] and not force:
        return

    if isinstance(loc, (Location, geopy.Point)):
        G.nodes[node_id]['x'] = loc.longitude
        G.nodes[node_id]['y'] = loc.latitude
    else:
        G.nodes[node_id]['x'] = loc[1]
        G.nodes[node_id]['y'] = loc[0]

    G.nodes[node_id]['street_count'] = street_count


def eosmid(n1, n2):
    """
    create edge osmid
    n1, n2 - node ids
    """
    return int(f'{n1}{n2}')


def destination_location(
    l: Location, bearing: float, d: float
) -> Location:
    """
    Given a start point, initial bearing, and distance, this will calculate
    the destina­tion point

    Args:
        l (Location): Starting location
        bearing (float): Bearing in degrees
        d (float): Distance in meters

    Returns:
        Location: [description]
    """
    R = 6371000
    dR = d/R
    b_rad = math.radians(bearing)
    lat_rad = math.radians(l.latitude)
    long_rad = math.radians(l.longitude)

    lat_new_rad = math.asin(math.sin(lat_rad) * math.cos(dR) +
                    math.cos(lat_rad) * math.sin(dR) * math.cos(b_rad))

    long_new_rad = long_rad + math.atan2(
        math.sin(b_rad) * math.sin(dR) * math.cos(lat_rad),
        math.cos(dR) - math.sin(lat_rad) * math.sin(lat_new_rad),
    )

    lat_new = math.degrees(lat_new_rad)
    long_new = math.degrees(long_new_rad)

    return Location(lat_new, long_new)

def storeDriveGraphToCache(driveGraph, filename):
    """
    stores drive graph to a cach file located at iism_cache/driveGraphCache/
    (path will be created if it deesn`t exist)
    :param driveGraph: graph to be stored
    :param filename: filename of cache file (based on map characteristics)
    :return: no return value
    """
    cache_dir = os.path.join('iism_cache', 'driveGraphCache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    with open(f'iism_cache/driveGraphCache/{filename}.pkl', 'wb') as outp:
        pickle.dump(driveGraph, outp, pickle.HIGHEST_PROTOCOL)
    fig, ax = ox.plot_graph(driveGraph, figsize=(10, 10), node_size=1.5, edge_linewidth=1.0, save=True,
                            show=False, filepath=f"iism_cache/driveGraphCache/{filename}.png")

print("Generator started")
origin_loc = Location(48.709936, 21.238923)
x_dists = [0.1, 0.1, 0.2, 0.05, 0.1, 0.1]
y_dists = [0.1, 0.1, 0.2, 0.05, 0.1, 0.1]
# import random
# x_dists = random_list(10)
# y_dists = random_list(10)
map_graph = create_manhattan_map(origin_loc, x_dists, y_dists)

print("Generator finished")
storeDriveGraphToCache(map_graph, "middleMap")