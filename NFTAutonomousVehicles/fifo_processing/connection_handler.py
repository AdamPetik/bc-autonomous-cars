from collections import defaultdict
from multiprocessing import connection
from typing import Any, Callable, Dict
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor, ParallelFIFOsProcessing


_HandlerCon = Callable[['RadioConnectionHandler', Any, Any], FIFOProcessor]
_HandlerDiscon = Callable[['RadioConnectionHandler', Any, Any], None]


class RadioConnectionHandler():
    def __init__(
        self,
        uplinks: Dict[Any, ParallelFIFOsProcessing],
        downlinks: Dict[Any, ParallelFIFOsProcessing],
        on_connect_uplink: _HandlerCon,
        on_connect_downlink: _HandlerCon,
        on_disconnect: _HandlerDiscon = None,
    ) -> None:
        self.uplinks = uplinks
        self.downlinks = downlinks

        self.connections_ue_bs = defaultdict(lambda: None)
        self.connections_bs_ue = defaultdict(lambda: [])

        self.on_connect_uplink = on_connect_uplink
        self.on_connect_downlink = on_connect_downlink
        self.on_disconnect = on_disconnect

    def connect(self, ue_id, bs_id):
        current_bs_id = self.connections_ue_bs[ue_id]
        if current_bs_id is not None:
            if current_bs_id == bs_id:
                return
            self.disconnect(ue_id)

        self.connections_ue_bs[ue_id] = bs_id
        self.connections_bs_ue[bs_id].append(ue_id)

        self.uplinks[bs_id].fifos[ue_id] = self.on_connect_uplink(
                                                            self, ue_id, bs_id)
        self.downlinks[bs_id].fifos[ue_id] = self.on_connect_downlink(
                                                            self, ue_id, bs_id)

    def disconnect(self, ue_id):
        if ue_id in self.connections_ue_bs.keys():
            bs_id = self.connections_ue_bs[ue_id]
            self.connections_ue_bs.pop(ue_id)
            self.connections_bs_ue[bs_id].remove(ue_id)

            self.uplinks[bs_id].fifos.pop(ue_id)
            self.downlinks[bs_id].fifos.pop(ue_id)

            if self.on_disconnect is not None:
                self.on_disconnect(self, ue_id, bs_id)

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
