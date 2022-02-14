from collections import defaultdict
from multiprocessing import connection
from typing import Any, Dict
from NFTAutonomousVehicles.fifo_processing.fifo_processor import ParallelFIFOsProcessing


class RadioConnectionHandler():
    def __init__(
        self,
        uplinks: Dict[Any, ParallelFIFOsProcessing],
        downlinks: Dict[Any, ParallelFIFOsProcessing]
    ) -> None:
        self.uplinks = uplinks
        self.downlinks = downlinks

        self.connections_ue_bs = defaultdict(lambda: None)
        self.connections_bs_ue = defaultdict(lambda: [])

    def connect(self, ue_id, bs_id):
        current_bs_id = self.connections_ue_bs[ue_id]
        if current_bs_id is not None:
            if current_bs_id == bs_id:
                return
            self.disconnect(ue_id, bs_id)

        self.connections_ue_bs[ue_id] = bs_id
        self.connections_bs_ue[bs_id].append(ue_id)

    def disconnect(self, ue_id, bs_id):
        if ue_id in self.connections_ue_bs.keys():
            self.connections_ue_bs.pop(ue_id)
            self.connections_bs_ue[bs_id].remove(ue_id)

    def get_uplink_ue(self, ue_id):
        bs_id = self.connections_ue_bs[ue_id]
        if bs_id is None:
            return None
        return self.uplinks[bs_id]

    def get_downlink_ue(self, ue_id):
        bs_id = self.connections_ue_bs[ue_id]
        if bs_id is None:
            return None
        return self.downlinks[bs_id]

    def get_uplink_bs(self, bs_id):
        return self.uplinks[bs_id]

    def get_downlink_bs(self, bs_id):
        return self.downlinks[bs_id]
