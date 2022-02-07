import math
from src.common.Location import Location
from typing import List
from src.common.CommonFunctions import CommonFunctions


__com = CommonFunctions()
__m_kHZ = -87.55

def calculate_sinr(
    location: Location,
    gNB,
    other_gNBs: list
) -> float:
    eps = 1
    distance = max(eps, __com.getReal2dDistance(location, gNB.getLocation()))
    # fspl = free_space_path_loss(distance, gNB.Tx_frequency)
    cpl = city_path_loss(distance/1000)
    # print('fspl', fspl)
    # print('cpl', cpl)

    S = (w_to_dbm(gNB.tx_power) - cpl)
    # I = w_to_dbm(1e-19)
    I = 0

    for gNB_inter in other_gNBs:
        if gNB_inter.id == gNB.id:
            continue #skip the one we use

        if gNB_inter.tx_frequency != gNB.tx_frequency:
            #skip even if the frequency is not the same - interference is ~0
            continue

        distance = max(
            eps,
            __com.getReal2dDistance(location, gNB_inter.getLocation())
        )

        if distance <= gNB_inter.association_coverage_radius:
            # fspl = free_space_path_loss(distance, gNB_inter.Tx_frequency)
            cpl = city_path_loss(distance/1000)

            # I += w_to_dbm(gNB_inter.Tx_power) - cpl
            I += dbm_to_w(w_to_dbm(gNB_inter.tx_power) - cpl)

    # k * T  : k - boltzmann constant, T - room temperature in kelvin
    kT = 4.002e-21
    N = w_to_dbm(kT * gNB.bandwidth)
    I = w_to_dbm(I+1e-26)
    return sinr_ltecalc(S, N, I)

def dbm_to_w(inp):
    return math.pow(10,(inp/10))/1000


def w_to_dbm(inp):
    return 10*math.log10((inp*1000))


def sinr_ltecalc(rsrp, noise, interference):
    result = dbm_to_w(rsrp)/(dbm_to_w(noise)+dbm_to_w(interference))
    return w_to_dbm(result/1000)

def free_space_path_loss(distance: float, frequency: float):
    return (20*math.log10(distance) + 20*math.log10(frequency/1000) + __m_kHZ)

def city_path_loss(distance: float):
    #TODO use frequency
    return 128.1+37.6*math.log10(distance)