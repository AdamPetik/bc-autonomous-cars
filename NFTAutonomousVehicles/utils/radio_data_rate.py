import math
from typing import Tuple
import pandas as pd


class RadioDataRate:
    # http://anisimoff.org/eng/lte_mcs.html
    __sinr_table: pd.DataFrame = None
    __modulation_schemes = {"QPSK":2, "16QAM":4, "64QAM":6, "256QAM": 8}
    fake_symbol_rate = 0.168 # 1 000 000 RE per RB per second 12 * 7 * 2000

    @classmethod
    def init_sinr_table(cls, path_sinr_table: str = './sinr.csv') -> None:
        cls.__sinr_table = pd.read_csv(path_sinr_table, sep=',')

    @classmethod
    def get_v_and_code_rate(cls, sinr_value: float) -> Tuple[int, float]:
        """
        By SINR value selects the number of bits pre symbol - v (by modulation
        scheme) and code rate.

        Args:
            sinr_value (float): SINR value

        Returns:
            Tuple[int, float]: v, code rate
        """
        if cls.__sinr_table is None:
            cls.init_sinr_table() # init with default path if not loaded
        select = (cls.__sinr_table['SINR']-sinr_value).abs().argsort()[:1]
        df_sort = cls.__sinr_table.iloc[select]

        #index of 1st appearance - closest value
        index = df_sort.index.tolist()[0]

        modulation = cls.__sinr_table.iloc[index]["Modulation"]
        v = cls.__modulation_schemes[modulation]
        code_rate = cls.__sinr_table.iloc[index]["CodeRate"]
        return v, code_rate

    @staticmethod
    def calculate_avgrb(
        sinr_value: float,
        resource_blocks: int,
        connected_devices: int,
    ) -> float:
        """Resource blocks are averaged among all UEs

        Args:
            sinr_value (float): SINR value.
            resource_blocks (int): Total number of resource blocks at the
                    particular BS.
            connected_devices (int):

        Returns:
            float: data rate in mbps
        """
        v, code_rate = RadioDataRate.get_v_and_code_rate(sinr_value)
        return RadioDataRate.datarate_formula(
            v=v,
            ro=code_rate,
            nRB=resource_blocks,
            nR=connected_devices,
            symbol_rate=RadioDataRate.fake_symbol_rate
        )

    @staticmethod
    def calculate(sinr_value: float, used_resource_blocks: int) -> float:
        """
        Calculate the data rate by SINR value and number of resource
        blocks.

        Args:
            sinr_value (float): SINR value
            used_resource_blocks (int): Number of resource blocks
                    that are assigned to the UE.

        Returns:
            float: data rate i mbps
        """
        v, code_rate = RadioDataRate.get_v_and_code_rate(sinr_value)
        return RadioDataRate.datarate_formula(
            v=v,
            ro=code_rate,
            nRB=used_resource_blocks,
            nR=1,
            symbol_rate=RadioDataRate.fake_symbol_rate
        )

    @staticmethod
    def get_rb_count(sinr_value: float, required_datarate: float) -> int:
        """
        Calculate the required number of resource blocks for meeting the data
        rate requirements.

        Args:
            sinr_value (float): SINR value.
            required_datarate (float): Data rate requirement.

        Returns:
            int: Number of resource blocks.
        """
        v, code_rate = RadioDataRate.get_v_and_code_rate(sinr_value)

        return RadioDataRate.rb_formula(
            required_datarate, v, code_rate, RadioDataRate.fake_symbol_rate)

    @staticmethod
    def rb_formula(datarate, v, ro, symbol_rate) -> int:
        """
        Args:
            datarate : Data rate
            v : bits per symbol
            ro : code rate
            symbol_rate : symbol_rate

        Returns:
            int: Number of resource blocks.
        """
        return math.ceil(datarate / (v * ro * symbol_rate))

    @staticmethod
    def datarate_formula(v, ro, nRB, nR, symbol_rate) -> float:
        """
        Args:
            v : bits per symbol
            ro : code rate
            nRB : number of resource blocks
            nR : number of connected ues
            symbol_rate : symbol_rate

        Returns:
            float: data rate
        """
        if nR == 0:
            nR = 1
        return v*ro*nRB/nR * symbol_rate