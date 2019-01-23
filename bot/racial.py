
# Racial macro management module
# (c) kaitai
# Includes Townhalls, Production Buildings and Workers
# TODO: Add unit production
# TODO: think whether text strings are sensible and maybe remove them
# TODO: more consistent way of using variables vs functions

from sc2 import Race
# from sc2.constants import *
from sc2.ids.unit_typeid import *

#NOTE: race_workers,race_townhalls and race_gas available for bot (following three will complement the file)
TOWN_HALL_TYPES = {Race.Protoss: UnitTypeId.NEXUS, Race.Terran: UnitTypeId.COMMANDCENTER, Race.Zerg: UnitTypeId.HATCHERY}
GAS_BUILDINGS = {Race.Protoss: UnitTypeId.ASSIMILATOR, Race.Terran: UnitTypeId.REFINERY, Race.Zerg: UnitTypeId.EXTRACTOR}
WORKER_TYPES = {Race.Protoss: UnitTypeId.PROBE, Race.Terran: UnitTypeId.SCV, Race.Zerg: UnitTypeId.DRONE}

#TODO: check UnitTypeIds for hellbat and swarmhost
GATE_UNITS = {"Zealot": UnitTypeId.ZEALOT, "Sentry": UnitTypeId.SENTRY, "Stalker": UnitTypeId.STALKER,
              "Adept": UnitTypeId.ADEPT, "High Templar": UnitTypeId.HIGHTEMPLAR, "Dark Templar": UnitTypeId.DARKTEMPLAR}
ROBO_UNITS = {"Observer": UnitTypeId.OBSERVER, "Warp Prism": UnitTypeId.WARPPRISM, "Immortal": UnitTypeId.IMMORTAL,
              "Colossus": UnitTypeId.COLOSSUS, "Disruptor": UnitTypeId.DISRUPTOR}
STARGATE_UNITS = {"Phoenix": UnitTypeId.PHOENIX, "Oracle": UnitTypeId.ORACLE, "Void Ray": UnitTypeId.VOIDRAY,
                  "Tempest": UnitTypeId.TEMPEST, "Carrier": UnitTypeId.CARRIER}

BARRACKS_UNITS = {"Marine": UnitTypeId.MARINE, "Marauder": UnitTypeId.MARAUDER, "Reaper": UnitTypeId.REAPER,
                  "Ghost": UnitTypeId.GHOST}
FACTORY_UNITS = {"Hellion": UnitTypeId.HELLION, "Siege Tank": UnitTypeId.SIEGETANK, "Widow Mine": UnitTypeId.WIDOWMINE,
                 "Hellbat": UnitTypeId.HELLIONTANK, "Thor": UnitTypeId.THOR, "Cyclone": UnitTypeId.CYCLONE}
STARPORT_UNITS = {"Viking": UnitTypeId.VIKINGFIGHTER, "Medivac": UnitTypeId.MEDIVAC, "Raven": UnitTypeId.RAVEN,
                  "Banshee": UnitTypeId.BANSHEE, "Battlecruiser": UnitTypeId.BATTLECRUISER,
                  "Liberator": UnitTypeId.LIBERATOR}

HATCHERY_UNITS = {"Larva": UnitTypeId.LARVA, "Queen": UnitTypeId.QUEEN}
LARVA_UNITS = {"Drone": UnitTypeId.DRONE, "Overlord": UnitTypeId.OVERLORD, "Mutalisk": UnitTypeId.MUTALISK,
               "Zergling": UnitTypeId.ZERGLING, "Infestor": UnitTypeId.INFESTOR, "Roach": UnitTypeId.ROACH,
               "Swarm Host": UnitTypeId.SWARMHOSTMP, "Hydralisk": UnitTypeId.HYDRALISK, "Viper": UnitTypeId.VIPER,
               "Corruptor": UnitTypeId.CORRUPTOR, "Ultralisk": UnitTypeId.ULTRALISK}
# what (zerg) unit morphs into which unit
MORPH_UNITS = {UnitTypeId.OVERLORD: UnitTypeId.OVERSEER, UnitTypeId.ZERGLING: UnitTypeId.BANELING,
               UnitTypeId.ROACH: UnitTypeId.RAVAGER, UnitTypeId.HYDRALISK: UnitTypeId.LURKERMP,
               UnitTypeId.CORRUPTOR: UnitTypeId.BROODLORD}
MORPH_BUILDINGS = {UnitTypeId.HIVE: UnitTypeId.LAIR, UnitTypeId.LAIR: UnitTypeId.HATCHERY,
                   UnitTypeId.SPIRE: UnitTypeId.GREATERSPIRE}

UNITS_BY_FACILITY = \
    {Race.Protoss: {UnitTypeId.GATEWAY: GATE_UNITS, UnitTypeId.WARPGATE: GATE_UNITS,
                    UnitTypeId.ROBOTICSFACILITY: ROBO_UNITS, UnitTypeId.STARGATE: STARGATE_UNITS},
     Race.Terran: {UnitTypeId.BARRACKS: BARRACKS_UNITS, UnitTypeId.FACTORY: FACTORY_UNITS, UnitTypeId.STARPORT: STARPORT_UNITS},
     Race.Zerg: {UnitTypeId.HATCHERY: HATCHERY_UNITS, UnitTypeId.LARVA: LARVA_UNITS}}
# add these if needed UnitTypeId.LAIR: HATCHERY_UNITS, UnitTypeId.HIVE: HATCHERY_UNITS,

PROD_B_TYPES = \
    {Race.Protoss: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.ROBOTICSFACILITY, UnitTypeId.STARGATE},
    Race.Terran: {UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT},
    Race.Zerg: {UnitTypeId.HATCHERY, }}
# TECH_B_TYPES = \
#     {Race.Protoss: {UnitTypeId.NEXUS, UnitTypeId.PYLON, UnitTypeId.GATEWAY, UnitTypeId.CYBERNETICSCORE,
#                     UnitTypeId.ROBOTICSFACILITY, UnitTypeId.STARGATE, UnitTypeId.TWILIGHTCOUNCIL },
#     Race.Terran: {UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT},
#     Race.Zerg: {UnitTypeId.HATCHERY, }}
# primary, [secondary]
SUPPLY_UNITS = {Race.Protoss: {UnitTypeId.PYLON, UnitTypeId.NEXUS},
                Race.Terran: {UnitTypeId.SUPPLYDEPOT, UnitTypeId.COMMANDCENTER},
                Race.Zerg: {UnitTypeId.OVERLORD, UnitTypeId.HATCHERY}}

AIR_TECH = \
    {Race.Protoss: {UnitTypeId.STARGATE},
     Race.Terran: {UnitTypeId.STARPORT},
     Race.Zerg: {UnitTypeId.SPIRE}}
#TODO: tech tree other way around ("what to build now if I want to build XX later?")
# or could do this dynamically from tech tree
#
TECH_TREE = {
    Race.Protoss: {
        UnitTypeId.NEXUS: {
            UnitTypeId.FORGE: {
                UnitTypeId.PHOTONCANNON: None
            },
            UnitTypeId.GATEWAY: {
                UnitTypeId.CYBERNETICSCORE: {
                    UnitTypeId.ROBOTICSFACILITY: {
                        UnitTypeId.ROBOTICSBAY: None
                    },
                    UnitTypeId.STARGATE: {
                        UnitTypeId.FLEETBEACON: None
                    },
                    UnitTypeId.TWILIGHTCOUNCIL: {
                        UnitTypeId.TEMPLARARCHIVE: None,
                        UnitTypeId.DARKSHRINE: None
                    },
                },
            },
        },
    },
    Race.Terran: {
        UnitTypeId.COMMANDCENTER: {
            UnitTypeId.ENGINEERINGBAY: {
                UnitTypeId.MISSILETURRET: None,
                UnitTypeId.SENSORTOWER: None},
        },
        UnitTypeId.SUPPLYDEPOT: {
            UnitTypeId.BARRACKS: {
                UnitTypeId.BUNKER: None,
                UnitTypeId.FACTORY: {
                    UnitTypeId.ARMORY: None,
                    UnitTypeId.GHOSTACADEMY: None,
                    UnitTypeId.STARPORT: {
                        UnitTypeId.FUSIONCORE: None
                    },
                },
            },
        },
    },
    Race.Zerg: {
        UnitTypeId.HATCHERY: {
            UnitTypeId.EVOLUTIONCHAMBER: None,
            UnitTypeId.SPAWNINGPOOL: {
                UnitTypeId.ROACHWARREN: None,
                UnitTypeId.BANELINGNEST: None,
                UnitTypeId.SPINECRAWLER: None,
                UnitTypeId.SPORECRAWLER: None,
                UnitTypeId.LAIR: {
                    UnitTypeId.NYDUSNETWORK: None,
                    UnitTypeId.HYDRALISKDEN: {
                        UnitTypeId.LURKERDENMP: None,
                    },
                    UnitTypeId.SPIRE: {
                        UnitTypeId.GREATERSPIRE: None,  # NOTE: in 2 places
                    },
                    UnitTypeId.INFESTATIONPIT: {
                        UnitTypeId.HIVE: {
                            UnitTypeId.GREATERSPIRE: None,  # NOTE: in 2 places
                            UnitTypeId.ULTRALISKCAVERN: None,
                        },
                    },

                },
            },
        },
    },  #MORE RACES
}


####ACTIONS

# TODO: simplify if needed
def train_unit(race, unit, building):  # <-pass building/larva
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

def goal_air_unit(race):
    goal_units = None
    if race == Race.Protoss:
        goal_units = (STARGATE_UNITS["Void Ray"], STARGATE_UNITS["Carrier"])
    elif race == Race.Terran:
        goal_units = (STARPORT_UNITS["Viking"], STARPORT_UNITS["Battlecruiser"])
    elif race == Race.Zerg:
        goal_units = (LARVA_UNITS["Mutalisk"], LARVA_UNITS["Mutalisk"])  # mutas are good

    return goal_units

def get_supply_args(race):
    if race == Race.Protoss:
        return (UnitTypeId.PROBE, UnitTypeId.PYLON)
    elif race == Race.Terran:
        return (UnitTypeId.SCV, UnitTypeId.SUPPLYDEPOT)
    elif race == Race.Zerg:
        return (UnitTypeId.LARVA, UnitTypeId.OVERLORD)

    return None

#example: get_available_buildings(Race.Protoss,[UnitTypeId.NEXUS, UnitTypeId.GATEWAY])
def get_available_buildings(race, buildings_ready):
    tree = TECH_TREE[race]
    building_set = set(buildings_ready)
    return search_tree(tree, building_set)

#recursive dict search tree
def search_tree(dict_tree,keys):
    found_keys = []
    #print(set(keys))
    for k in set(dict_tree.keys()):
        #print(k)
        if dict_tree[k]:
            if k in set(keys):
                found_keys.extend(search_tree(dict_tree[k], keys))
            # else:
            #     found_keys.extend(dict_tree[k].keys())
    found_keys.extend(list(dict_tree.keys()))

    return found_keys
