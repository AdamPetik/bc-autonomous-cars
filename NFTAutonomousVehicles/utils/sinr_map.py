from typing import Deque, Dict, List
import numpy as np
import numpy.typing as npt
from collections import defaultdict, deque
import seaborn as sns
import matplotlib.pylab as plt


class SINRMap:
    """Grid SINR map"""
    def __init__(
        self,
        x_size: int,
        y_size: int,
        update_param: float = 0.5,
        cache_capacity: int = 100,
        lovest_sinr_val: float = -100
    ) -> None:
        self.x_size = x_size
        self.y_size = y_size
        self.update_param = update_param
        self.lovest_sinr_val = lovest_sinr_val
        self.init_sinr_val = lovest_sinr_val - 1
        self._map = np.full((x_size, y_size), fill_value=self.init_sinr_val)
        self._ue_cache: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=self.cache_capacity)
        )
        self.cache_capacity = cache_capacity
        self._bs_maps: Dict[str, npt.ArrayLike] = defaultdict(
            lambda: np.full(
                (x_size, y_size),
                fill_value=self.init_sinr_val,
            )
        )

        # {
        #   'ue_id': {
        #       'bs_id': [<cached values>]
        #   },
        # ...
        # }
        self._ue_bs_cache: Dict[str, Dict[str, Deque[float]]] = defaultdict(
            lambda: defaultdict(
                lambda: deque(maxlen=self.cache_capacity)
            )
        )

    def update(self, x: int, y: int, value: float, ue_id=None) -> None:
        """Updates global map"""

        value = max(self.lovest_sinr_val, value)
        if self._map[x, y] == self.init_sinr_val:
            self._map[x, y] = value
        else:
            self._map[x, y] = (1 - self.update_param) * \
                self._map[x, y] + self.update_param * value

        if ue_id is not None:
            # if provided with ue ID, sinr value is cached

            self._ue_cache[ue_id].append(value)

    def get_ue_cache(self, ue_id: str) -> List[float]:
        return list(self._ue_cache[ue_id])

    def get(self, x: int, y: int) -> float:
        return self._map[x, y]

    def get_from_bs_map(self, x: int, y: int, bs_id: str) -> float:
        return self._bs_maps[bs_id][x, y]

    def get_ue_bs_cache(self, ue_id: str, bs_id: str) -> List[float]:
        return list(self._ue_bs_cache[ue_id][bs_id])

    def update_bs_map(
        self,
        x: int,
        y: int,
        value: float,
        bs_id: str,
        ue_id: str = None,
    ) -> None:
        """Update base station specific map"""

        value = max(self.lovest_sinr_val, value)

        if self._bs_maps[bs_id][x, y] == self.init_sinr_val:
            self._bs_maps[bs_id][x, y] = value
        else:
            curr_value = self._bs_maps[bs_id][x, y]

            self._bs_maps[bs_id][x, y] = (
                (1 - self.update_param) * curr_value
                + self.update_param * value
            )

        if ue_id is not None:
            """if ue_id is provided, value is cached"""
            self._ue_bs_cache[ue_id][bs_id].append(value)

    def save_global_heat_map(self,
        filename = 'sinr_heatmap.png',
        smooth_size=None,
    ) -> None:
        if smooth_size is None:
            heatmap = self._map
        else:
            # dooing max pool where size, stride = smooth_size
            M, N = self._map.shape
            K,L = smooth_size, smooth_size

            MK = M // K
            NL = N // L
            heatmap = self._map[:MK*K, :NL*L].reshape(MK, K, NL, L).max(axis=(1, 3))

        my_fig, (my_ax, my_cbar_ax) = plt.subplots(
                ncols=2, figsize=(8, 6), gridspec_kw={'width_ratios': [10, 1]})

        ax = sns.heatmap(np.flip(heatmap, 0), linewidths=0,
                ax=my_ax, cbar_ax=my_cbar_ax)
        plt.savefig(filename)

    def __repr__(self) -> str:
        global_map = f'global SINR map:\n{self._map}'
        maps = []
        maps.append(global_map)
        for bs_id, map in self._bs_maps.items():
            maps.append(f'bs {bs_id}:\n{map}')
        return '\n'.join(maps)
