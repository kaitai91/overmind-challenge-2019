
# Racial macro management module
# (c) kaitai
# Includes Townhalls, Production Buildings and Workers
# TODO: Add unit production

from sc2 import Race
# from sc2.constants import *
from sc2.ids.unit_typeid import *

TOWN_HALL_TYPES = {Race.Protoss: UnitTypeId.NEXUS, Race.Terran: UnitTypeId.COMMANDCENTER, Race.Zerg: UnitTypeId.HATCHERY}

WORKER_TYPES = {Race.Protoss: UnitTypeId.PROBE, Race.Terran: UnitTypeId.SCV, Race.Zerg: UnitTypeId.DRONE}

PROD_B_TYPES = \
    {Race.Protoss: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.ROBOTICSFACILITY, UnitTypeId.STARGATE},
    Race.Terran: {UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT},
    Race.Zerg: {UnitTypeId.HATCHERY, }}
# primary, [secondary]
SUPPLY_UNITS = {Race.Protoss: {UnitTypeId.PYLON, UnitTypeId.NEXUS},
                Race.Terran: {UnitTypeId.SUPPLYDEPOT, UnitTypeId.COMMANDCENTER},
                Race.Zerg: {UnitTypeId.OVERLORD, UnitTypeId.HATCHERY}}


# TODO:
##tech_paths = {Race.Protoss: [UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.ROBOTICSFACILITY, UnitTypeID.STARGATE],
##                Race.Terran: [UnitTypeId.BARRACKS,UnitTypeId.FACTORY, UnitTypeId.STARPORT],
##                Race.Zerg: [UnitTypeId.HATCHERY,]}


####ACTIONS

# TODO: simplify if needed
def train_unit(race, unit, buiding=None):  # <-pass building/larva
    """Action to train units

        For zerg pass larva instead of building
    """
    action = None
    if race == Race.Protoss:
        action = lambda: building.train(unit)
    elif race == Race.Terran:
        action = lambda: building.train(unit)

    elif race == Race.Zerg:
        action = lambda: building.train(unit)  # <-make larva("building") to unit

    return action


def get_supply_args(race):
    if race == Race.Protoss:
        return (UnitTypeId.PROBE, UnitTypeId.PYLON)
    elif race == Race.Terran:
        return (UnitTypeId.SCV, UnitTypeId.SUPPLYDEPOT)
    elif race == Race.Zerg:
        return (UnitTypeId.LARVA, UnitTypeId.OVERLORD)

    return None

