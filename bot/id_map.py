
# Module for Id collections and management
# (c) kaitai
# Includes Townhalls, Production Buildings, Workers, Tech tree, and more
# TODO: think whether text strings are sensible and maybe remove them
# TODO: more consistent way of using variables vs functions

from sc2 import Race
from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2.ids.upgrade_id import *

# NOTE: race_workers,race_townhalls and race_gas available for bot (following three will complement this file)
TOWN_HALL_TYPES = {Race.Protoss: UnitTypeId.NEXUS, Race.Terran: UnitTypeId.COMMANDCENTER, Race.Zerg: UnitTypeId.HATCHERY}
GAS_BUILDINGS = {Race.Protoss: UnitTypeId.ASSIMILATOR, Race.Terran: UnitTypeId.REFINERY, Race.Zerg: UnitTypeId.EXTRACTOR}
WORKER_TYPES = {Race.Protoss: UnitTypeId.PROBE, Race.Terran: UnitTypeId.SCV, Race.Zerg: UnitTypeId.DRONE}

#TODO: check UnitTypeIds for swarmhost
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

MECHANICALS = [UnitTypeId.SCV, ]
MECHANICALS.extend(list(STARPORT_UNITS.values())+list(FACTORY_UNITS.values()))

# techlab, reactor
BUILD_ADDONS = [AbilityId.BUILD_TECHLAB, AbilityId.BUILD_REACTOR]
REACTORS = {UnitTypeId.BARRACKSREACTOR, UnitTypeId.FACTORYREACTOR,
            UnitTypeId.STARPORTREACTOR, UnitTypeId.REACTOR}
TECHLABS = {UnitTypeId.BARRACKSTECHLAB, UnitTypeId.FACTORYTECHLAB,
            UnitTypeId.STARPORTTECHLAB, UnitTypeId.TECHLAB}
TECHREACTORS = {UnitTypeId.BARRACKSTECHREACTOR, UnitTypeId.FACTORYTECHLAB,
                UnitTypeId.STARPORTTECHREACTOR, UnitTypeId.TECHREACTOR}

ADDON_BUILDING = {
    **dict.fromkeys([UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKSTECHREACTOR],
                    UnitTypeId.BARRACKS),
    **dict.fromkeys([UnitTypeId.FACTORYREACTOR, UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORYTECHREACTOR],
                    UnitTypeId.FACTORY),
    **dict.fromkeys([UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORTTECHREACTOR],
                    UnitTypeId.STARPORT),

}

NEEDS_TECHLAB = {UnitTypeId.MARAUDER, UnitTypeId.GHOST,
                 UnitTypeId.SIEGETANK, UnitTypeId.THOR, UnitTypeId.CYCLONE,
                 UnitTypeId.RAVEN, UnitTypeId.BANSHEE, UnitTypeId.BATTLECRUISER}

CREEP_TUMORS = {UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED,
                UnitTypeId.CREEPTUMORMISSILE, UnitTypeId.CREEPTUMORQUEEN}
CHANGELINGS = {UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGZEALOT,
               UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD,
               UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELINGZERGLINGWINGS}

HATCHERY_UNITS = {"Larva": UnitTypeId.LARVA, "Queen": UnitTypeId.QUEEN}
LARVA_UNITS = {"Drone": UnitTypeId.DRONE, "Overlord": UnitTypeId.OVERLORD, "Mutalisk": UnitTypeId.MUTALISK,
               "Zergling": UnitTypeId.ZERGLING, "Infestor": UnitTypeId.INFESTOR, "Roach": UnitTypeId.ROACH,
               "Swarm Host": UnitTypeId.SWARMHOSTMP, "Hydralisk": UnitTypeId.HYDRALISK, "Viper": UnitTypeId.VIPER,
               "Corruptor": UnitTypeId.CORRUPTOR, "Ultralisk": UnitTypeId.ULTRALISK}
# what (zerg) unit morphs into which (specified) unit
MORPH_UNITS = {UnitTypeId.OVERSEER: UnitTypeId.OVERLORD, UnitTypeId.BANELING: UnitTypeId.ZERGLING,
               UnitTypeId.RAVAGER: UnitTypeId.ROACH, UnitTypeId.LURKERMP: UnitTypeId.HYDRALISK,
               UnitTypeId.BROODLORD: UnitTypeId.CORRUPTOR}
MORPH_BUILDINGS = {UnitTypeId.HIVE: UnitTypeId.LAIR, UnitTypeId.LAIR: UnitTypeId.HATCHERY,
                   UnitTypeId.GREATERSPIRE: UnitTypeId.SPIRE}

MORPH = {
    # protoss
    UnitTypeId.DARKTEMPLAR: AbilityId.ARCHON_WARP_TARGET, UnitTypeId.HIGHTEMPLAR: AbilityId.ARCHON_WARP_TARGET,

    # terran
    UnitTypeId.COMMANDCENTER: AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,

    # zerg
    UnitTypeId.HATCHERY: AbilityId.UPGRADETOLAIR_LAIR, UnitTypeId.LAIR: AbilityId.UPGRADETOHIVE_HIVE,
    UnitTypeId.SPIRE: AbilityId.UPGRADETOGREATERSPIRE_GREATERSPIRE,

    UnitTypeId.OVERLORD: AbilityId.MORPH_OVERSEER, UnitTypeId.ZERGLING: AbilityId.MORPHZERGLINGTOBANELING_BANELING,
    UnitTypeId.ROACH: AbilityId.MORPHTORAVAGER_RAVAGER, UnitTypeId.HYDRALISK: AbilityId.MORPH_LURKER,
    UnitTypeId.CORRUPTOR: AbilityId.MORPHTOBROODLORD_BROODLORD, UnitTypeId.OVERLORDTRANSPORT: AbilityId.MORPH_OVERSEER
}
#secondary morph command(s) for units with more morph abilities (such as overlord)
MORPH2 = {
    # protoss

    # terran

    # zerg
    UnitTypeId.OVERLORD: AbilityId.MORPH_OVERLORDTRANSPORT
}

#commands to change mode (such as siegetank siege mode, observer stationary mode, prism phasing mode etc.
TRANSFORM = {
    # protoss
    UnitTypeId.GATEWAY: AbilityId.MORPH_WARPGATE, UnitTypeId.WARPGATE: AbilityId.MORPH_GATEWAY,

    UnitTypeId.OBSERVER: AbilityId.MORPH_SURVEILLANCEMODE,
    UnitTypeId.WARPPRISM: AbilityId.MORPH_WARPPRISMPHASINGMODE,

    UnitTypeId.OBSERVERSIEGEMODE: AbilityId.MORPH_OBSERVERMODE,
    UnitTypeId.WARPPRISMPHASING: AbilityId.MORPH_WARPPRISMTRANSPORTMODE,

    # terran ##TODO: test thor
    UnitTypeId.SUPPLYDEPOT: AbilityId.MORPH_SUPPLYDEPOT_LOWER, UnitTypeId.HELLION: AbilityId.MORPH_HELLBAT,
    UnitTypeId.SIEGETANK: AbilityId.SIEGEMODE_SIEGEMODE, UnitTypeId.THOR: AbilityId.MORPH_THORHIGHIMPACTMODE,
    UnitTypeId.LIBERATOR: AbilityId.MORPH_LIBERATORAGMODE, UnitTypeId.VIKINGFIGHTER: AbilityId.MORPH_VIKINGASSAULTMODE,

    UnitTypeId.SUPPLYDEPOTLOWERED: AbilityId.MORPH_SUPPLYDEPOT_RAISE, UnitTypeId.HELLIONTANK: AbilityId.MORPH_HELLION,
    UnitTypeId.SIEGETANKSIEGED: AbilityId.UNSIEGE_UNSIEGE, UnitTypeId.THORAP: AbilityId.MORPH_THOREXPLOSIVEMODE,
    UnitTypeId.LIBERATORAG: AbilityId.MORPH_LIBERATORAAMODE, UnitTypeId.VIKINGASSAULT: AbilityId.MORPH_VIKINGFIGHTERMODE,

    # zerg
    UnitTypeId.OVERSEER: AbilityId.MORPH_OVERSIGHTMODE,

    UnitTypeId.OVERSEERSIEGEMODE: AbilityId.MORPH_OVERSEERMODE,
}

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

# primary, [secondary]
SUPPLY_UNITS = {Race.Protoss: {UnitTypeId.PYLON, UnitTypeId.NEXUS},
                Race.Terran: {UnitTypeId.SUPPLYDEPOT, UnitTypeId.COMMANDCENTER},
                Race.Zerg: {UnitTypeId.OVERLORD, UnitTypeId.HATCHERY}}

AIR_TECH = \
    {Race.Protoss: {UnitTypeId.STARGATE},
     Race.Terran: {UnitTypeId.STARPORT},
     Race.Zerg: {UnitTypeId.SPIRE}}

#
BUILDING_TECH_TREE = {
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
                UnitTypeId.BARRACKSTECHLAB: None,
                UnitTypeId.BUNKER: None,
                UnitTypeId.FACTORY: {
                    UnitTypeId.FACTORYTECHLAB: None,
                    UnitTypeId.ARMORY: None,
                    UnitTypeId.GHOSTACADEMY: None,
                    UnitTypeId.STARPORT: {
                        UnitTypeId.STARPORTTECHLAB: None,
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

##BUILDING_ABILITIES
#protoss
NEXUS = {UnitTypeId.NEXUS: {AbilityId.NEXUSTRAIN_PROBE, AbilityId.NEXUSTRAINMOTHERSHIP_MOTHERSHIP, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST}}

#terran

#zerg

##UNIT ABILITIES
# TODO: test spell abilities
SPELL1 = {
    # protoss
    UnitTypeId.ZEALOT: AbilityId.EFFECT_CHARGE, UnitTypeId.ADEPT: AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT,
    UnitTypeId.SENTRY: AbilityId.FORCEFIELD_FORCEFIELD, UnitTypeId.STALKER: AbilityId.EFFECT_BLINK_STALKER,
    UnitTypeId.DARKTEMPLAR: AbilityId.EFFECT_SHADOWSTRIDE, UnitTypeId.HIGHTEMPLAR: AbilityId.FEEDBACK_FEEDBACK,
    UnitTypeId.DISRUPTOR: AbilityId.EFFECT_PURIFICATIONNOVA, UnitTypeId.VOIDRAY: AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT,
    UnitTypeId.PHOENIX: AbilityId.GRAVITONBEAM_GRAVITONBEAM, UnitTypeId.ORACLE: AbilityId.ORACLEREVELATION_ORACLEREVELATION,
    UnitTypeId.MOTHERSHIP: AbilityId.EFFECT_MASSRECALL_MOTHERSHIP, UnitTypeId.SHIELDBATTERY: AbilityId.RESTORESHIELDS_RESTORESHIELDS,

    # terran
    UnitTypeId.SCV: AbilityId.EFFECT_REPAIR_SCV, UnitTypeId.MULE: AbilityId.EFFECT_REPAIR_MULE,
    UnitTypeId.MARINE: AbilityId.EFFECT_STIM_MARINE, UnitTypeId.REAPER: AbilityId.KD8CHARGE_KD8CHARGE,
    UnitTypeId.MARAUDER: AbilityId.EFFECT_STIM_MARAUDER, UnitTypeId.GHOST: AbilityId.TACNUKESTRIKE_NUKECALLDOWN,
    UnitTypeId.CYCLONE: AbilityId.LOCKON_LOCKON, UnitTypeId.MEDIVAC: AbilityId.MEDIVACHEAL_HEAL,
    UnitTypeId.RAVEN: AbilityId.RAVENBUILD_AUTOTURRET, UnitTypeId.BATTLECRUISER: AbilityId.YAMATO_YAMATOGUN,
    UnitTypeId.BANSHEE: AbilityId.BEHAVIOR_CLOAKON_BANSHEE,
    # UnitTypeId.COMMANDCENTER: AbilityId.LOADALL_COMMANDCENTER,
    # UnitTypeId.PLANETARYFORTRESS: AbilityId.LOADALL_COMMANDCENTER, UnitTypeId.BUNKER: AbilityId.LOAD_BUNKER,

    # zerg #nyduscanal == nydusworm?
    UnitTypeId.BANELING: AbilityId.EXPLODE_EXPLODE, UnitTypeId.QUEEN: AbilityId.BUILD_CREEPTUMOR_QUEEN,
    UnitTypeId.RAVAGER: AbilityId.EFFECT_CORROSIVEBILE, UnitTypeId.OVERSEER: AbilityId.SPAWNCHANGELING_SPAWNCHANGELING,
    UnitTypeId.SWARMHOSTMP: AbilityId.SWARMHOSTSPAWNLOCUSTS_LOCUSTMP, UnitTypeId.INFESTOR: AbilityId.INFESTEDTERRANSLAYEGG_INFESTEDTERRANS,
    UnitTypeId.VIPER: AbilityId.VIPERCONSUMESTRUCTURE_VIPERCONSUME,

}
SPELL2 = {
    # protoss
    UnitTypeId.SENTRY: AbilityId.GUARDIANSHIELD_GUARDIANSHIELD, UnitTypeId.HIGHTEMPLAR: AbilityId.PSISTORM_PSISTORM,
    UnitTypeId.ORACLE: AbilityId.ORACLESTASISTRAP_ORACLEBUILDSTASISTRAP, UnitTypeId.MOTHERSHIP: AbilityId.EFFECT_TIMEWARP,

    # terran
    UnitTypeId.GHOST: AbilityId.EFFECT_GHOSTSNIPE, UnitTypeId.MEDIVAC: AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS,
    UnitTypeId.RAVEN: AbilityId.EFFECT_INTERFERENCEMATRIX, UnitTypeId.BATTLECRUISER: AbilityId.EFFECT_TACTICALJUMP,
    UnitTypeId.BANSHEE: AbilityId.BEHAVIOR_CLOAKOFF_BANSHEE,
    # UnitTypeId.COMMANDCENTER: AbilityId.UNLOADALL_COMMANDCENTER,
    # UnitTypeId.PLANETARYFORTRESS: AbilityId.UNLOADALL_COMMANDCENTER, UnitTypeId.BUNKER: AbilityId.UNLOADALL_BUNKER,

    # zerg
    UnitTypeId.QUEEN: AbilityId.EFFECT_INJECTLARVA, UnitTypeId.OVERSEER: AbilityId.CONTAMINATE_CONTAMINATE,
    UnitTypeId.INFESTOR: AbilityId.FUNGALGROWTH_FUNGALGROWTH, UnitTypeId.VIPER: AbilityId.EFFECT_ABDUCT,

}
SPELL3 = {
    # protoss #TODO: different sentry hallucinations (idea: sentry[UnitTypeId.Zealot: AbilityId.hallucination_zealot)
    UnitTypeId.SENTRY: AbilityId.HALLUCINATION_PHOENIX, UnitTypeId.ORACLE: AbilityId.BEHAVIOR_PULSARBEAMON,

    # terran
    UnitTypeId.GHOST: AbilityId.EMP_EMP, UnitTypeId.MEDIVAC: AbilityId.UNLOADALLAT_MEDIVAC,
    UnitTypeId.RAVEN: AbilityId.EFFECT_ANTIARMORMISSILE,

    # zerg
    UnitTypeId.QUEEN: AbilityId.TRANSFUSION_TRANSFUSION, UnitTypeId.INFESTOR: AbilityId.NEURALPARASITE_NEURALPARASITE,
    UnitTypeId.VIPER: AbilityId.BLINDINGCLOUD_BLINDINGCLOUD,

}
SPELL4 = {
    # protoss
    UnitTypeId.ORACLE: AbilityId.BEHAVIOR_PULSARBEAMOFF,

    # terran
    UnitTypeId.GHOST: AbilityId.BEHAVIOR_CLOAKON_GHOST,

    # zerg
    UnitTypeId.VIPER: AbilityId.PARASITICBOMB_PARASITICBOMB,
}
SPELL5 = {
    # protoss

    # terran
    UnitTypeId.GHOST: AbilityId.BEHAVIOR_CLOAKOFF_GHOST,

    # zerg
}

SPELL_LIST = [SPELL1, SPELL2, SPELL3, SPELL4, SPELL5]

def get_spells(type_id):
    """Returns AbilityIds for spells available for given unit type."""
    available = []
    for spell in SPELL_LIST:
        if type_id in spell:
            available.append(spell[type_id])
        else:  # spells are in order, once found nothing, there will be no more spells
            break
    return available

#TODO: test upgrades

#protoss
P_AIR_ATTACK = {UpgradeId.PROTOSSAIRWEAPONSLEVEL1, UpgradeId.PROTOSSAIRWEAPONSLEVEL2, UpgradeId.PROTOSSAIRWEAPONSLEVEL3}
P_AIR_ARMOR = {UpgradeId.PROTOSSAIRARMORSLEVEL1, UpgradeId.PROTOSSAIRARMORSLEVEL2, UpgradeId.PROTOSSAIRARMORSLEVEL3}
P_AIR = {*P_AIR_ATTACK, *P_AIR_ARMOR}

P_GROUND_ATTACK = {UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3}
P_GROUND_ARMOR = {UpgradeId.PROTOSSGROUNDARMORSLEVEL1, UpgradeId.PROTOSSGROUNDARMORSLEVEL2, UpgradeId.PROTOSSGROUNDARMORSLEVEL3}
P_GROUND = {*P_GROUND_ATTACK, *P_GROUND_ARMOR}

P_SHIELD_UPG = {UpgradeId.PROTOSSSHIELDSLEVEL1, UpgradeId.PROTOSSSHIELDSLEVEL2, UpgradeId.PROTOSSSHIELDSLEVEL3}
WARPGATE = UpgradeId.WARPGATERESEARCH

#terran
T_VEHICLE_ATTACK = {UpgradeId.TERRANVEHICLEWEAPONSLEVEL1, UpgradeId.TERRANVEHICLEWEAPONSLEVEL2, UpgradeId.TERRANVEHICLEWEAPONSLEVEL3}
T_SHIP_ATTACK = {UpgradeId.TERRANSHIPWEAPONSLEVEL1, UpgradeId.TERRANSHIPWEAPONSLEVEL2, UpgradeId.TERRANSHIPWEAPONSLEVEL3}
T_PLATING = {UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1, UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2, UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3}

T_INFANTRY_ATTACK = {UpgradeId.TERRANINFANTRYWEAPONSLEVEL1, UpgradeId.TERRANINFANTRYWEAPONSLEVEL2, UpgradeId.TERRANINFANTRYWEAPONSLEVEL3}
T_INFANTRY_ARMOR = {UpgradeId.TERRANINFANTRYARMORSLEVEL1, UpgradeId.TERRANINFANTRYARMORSLEVEL2, UpgradeId.TERRANINFANTRYARMORSLEVEL3}
BUILDING_UPGS = {UpgradeId.HISECAUTOTRACKING, UpgradeId.NEOSTEELFRAME}

#zerg
Z_MELEE_UPGS = {UpgradeId.ZERGMELEEWEAPONSLEVEL1, UpgradeId.ZERGMELEEWEAPONSLEVEL2, UpgradeId.ZERGMELEEWEAPONSLEVEL3}
Z_MISSILE_UPGS = {UpgradeId.ZERGMISSILEWEAPONSLEVEL1, UpgradeId.ZERGMISSILEWEAPONSLEVEL2, UpgradeId.ZERGMISSILEWEAPONSLEVEL3}
Z_CARAPACE_UPGS = {UpgradeId.ZERGGROUNDARMORSLEVEL1, UpgradeId.ZERGGROUNDARMORSLEVEL2, UpgradeId.ZERGGROUNDARMORSLEVEL3}

Z_FLYER_ATTACK = {UpgradeId.ZERGFLYERWEAPONSLEVEL1, UpgradeId.ZERGFLYERWEAPONSLEVEL2, UpgradeId.ZERGFLYERWEAPONSLEVEL3}
Z_FLYER_ARMOR = {UpgradeId.ZERGFLYERARMORSLEVEL1, UpgradeId.ZERGFLYERARMORSLEVEL2, UpgradeId.ZERGFLYERARMORSLEVEL3}
BURROW_UPG = UpgradeId.BURROW
# which unit benefits which upgrades:
UNIT_UPGRADES = {

    # protoss
    UnitTypeId.PROBE: {}, UnitTypeId.ZEALOT: {UpgradeId.CHARGE},
    UnitTypeId.ADEPT: {UpgradeId.ADEPTPIERCINGATTACK}, UnitTypeId.SENTRY: {},
    UnitTypeId.STALKER: {UpgradeId.BLINKTECH}, UnitTypeId.DARKTEMPLAR: {UpgradeId.DARKTEMPLARBLINKUPGRADE},
    UnitTypeId.HIGHTEMPLAR: {UpgradeId.PSISTORMTECH}, UnitTypeId.ARCHON: {},
    UnitTypeId.WARPPRISM: {UpgradeId.GRAVITICDRIVE}, UnitTypeId.OBSERVER: {UpgradeId.OBSERVERGRAVITICBOOSTER},
    UnitTypeId.IMMORTAL: {}, UnitTypeId.COLOSSUS: {UpgradeId.EXTENDEDTHERMALLANCE},
    UnitTypeId.DISRUPTOR: {}, UnitTypeId.PHOENIX: {UpgradeId.PHOENIXRANGEUPGRADE},
    UnitTypeId.VOIDRAY: {}, UnitTypeId.ORACLE: {},
    UnitTypeId.CARRIER: {}, UnitTypeId.TEMPEST: {},
    UnitTypeId.MOTHERSHIP: {},

    # terran
    UnitTypeId.SCV: {}, UnitTypeId.MARINE: {UpgradeId.STIMPACK, UpgradeId.SHIELDWALL},
    UnitTypeId.REAPER: {}, UnitTypeId.MARAUDER: {UpgradeId.STIMPACK, UpgradeId.PUNISHERGRENADES},
    UnitTypeId.GHOST: {UpgradeId.PERSONALCLOAKING},
    # for different transformation modes of units:
    **dict.fromkeys([UnitTypeId.HELLION, UnitTypeId.HELLIONTANK], {UpgradeId.INFERNALPREIGNITERS, UpgradeId.SMARTSERVOS}),
    UnitTypeId.WIDOWMINE: {UpgradeId.DRILLCLAWS}, UnitTypeId.SIEGETANK: {},
    UnitTypeId.CYCLONE: {UpgradeId.MAGFIELDLAUNCHERS},
    **dict.fromkeys([UnitTypeId.THOR, UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT], {UpgradeId.SMARTSERVOS}),
    UnitTypeId.MEDIVAC: {UpgradeId.NAPALMFUELTANKS}, UnitTypeId.LIBERATOR: {UpgradeId.LIBERATORAGRANGEUPGRADE},
    UnitTypeId.RAVEN: {UpgradeId.RAVENCORVIDREACTOR}, UnitTypeId.BATTLECRUISER: {UpgradeId.YAMATOCANNON},
    UnitTypeId.BANSHEE: {UpgradeId.BANSHEECLOAK, UpgradeId.BANSHEESPEED},

    # zerg
    UnitTypeId.DRONE: {}, UnitTypeId.ZERGLING: {UpgradeId.ZERGLINGMOVEMENTSPEED, UpgradeId.ZERGLINGATTACKSPEED},
    UnitTypeId.BANELING: {UpgradeId.CENTRIFICALHOOKS}, UnitTypeId.ROACH: {UpgradeId.GLIALRECONSTITUTION, UpgradeId.TUNNELINGCLAWS},
    UnitTypeId.RAVAGER: {}, UnitTypeId.HYDRALISK: {UpgradeId.EVOLVEGROOVEDSPINES, UpgradeId.EVOLVEMUSCULARAUGMENTS},
    UnitTypeId.LURKERMP: {UpgradeId.LURKERRANGE}, UnitTypeId.VIPER: {},
    UnitTypeId.MUTALISK: {}, UnitTypeId.CORRUPTOR: {},
    UnitTypeId.SWARMHOSTMP: {}, UnitTypeId.INFESTOR: {UpgradeId.INFESTORENERGYUPGRADE, UpgradeId.NEURALPARASITE},
    UnitTypeId.ULTRALISK: {UpgradeId.CHITINOUSPLATING,  UpgradeId.ANABOLICSYNTHESIS}, UnitTypeId.BROODLORD: {},
    **dict.fromkeys([UnitTypeId.OVERLORD, UnitTypeId.OVERSEER], {UpgradeId.OVERLORDSPEED}),
    UnitTypeId.QUEEN: {},

}

# from which building the upgrade is researched
UPGRADING_BUILDING = {

    # protoss
    **dict.fromkeys([*P_GROUND, *P_SHIELD_UPG], UnitTypeId.FORGE),
    **dict.fromkeys([*P_AIR, UpgradeId.WARPGATERESEARCH], UnitTypeId.CYBERNETICSCORE),
    **dict.fromkeys([UpgradeId.OBSERVERGRAVITICBOOSTER, UpgradeId.GRAVITICDRIVE, UpgradeId.EXTENDEDTHERMALLANCE], UnitTypeId.ROBOTICSBAY),
    **dict.fromkeys([UpgradeId.PHOENIXRANGEUPGRADE, ], {UnitTypeId.FLEETBEACON}),
    **dict.fromkeys([UpgradeId.CHARGE, UpgradeId.BLINKTECH, UpgradeId.ADEPTPIERCINGATTACK], UnitTypeId.TWILIGHTCOUNCIL),
    **dict.fromkeys([UpgradeId.PSISTORMTECH, ], UnitTypeId.TEMPLARARCHIVE),
    **dict.fromkeys([UpgradeId.DARKTEMPLARBLINKUPGRADE, ], UnitTypeId.DARKSHRINE),

    # terran
    **dict.fromkeys([UpgradeId.SHIELDWALL, UpgradeId.STIMPACK, UpgradeId.PUNISHERGRENADES], UnitTypeId.BARRACKSTECHLAB),
    **dict.fromkeys([UpgradeId.INFERNALPREIGNITERS, UpgradeId.MAGFIELDLAUNCHERS, UpgradeId.DRILLCLAWS,
                     UpgradeId.SMARTSERVOS], UnitTypeId.FACTORYTECHLAB),
    **dict.fromkeys([*T_VEHICLE_ATTACK, *T_SHIP_ATTACK, *T_PLATING], UnitTypeId.ARMORY),
    **dict.fromkeys([UpgradeId.PERSONALCLOAKING, ], UnitTypeId.GHOSTACADEMY),
    **dict.fromkeys([UpgradeId.NAPALMFUELTANKS, UpgradeId.RAVENCORVIDREACTOR, UpgradeId.BANSHEECLOAK,
                     UpgradeId.BANSHEESPEED, UpgradeId.LIBERATORAGRANGEUPGRADE], UnitTypeId.STARPORTTECHLAB),
    **dict.fromkeys([UpgradeId.YAMATOCANNON, ], UnitTypeId.FUSIONCORE),

    # zerg
    **dict.fromkeys([UpgradeId.OVERLORDSPEED, UpgradeId.BURROW], UnitTypeId.HATCHERY),
    **dict.fromkeys([*Z_MELEE_UPGS, *Z_MISSILE_UPGS, *Z_CARAPACE_UPGS], UnitTypeId.EVOLUTIONCHAMBER),
    **dict.fromkeys([UpgradeId.ZERGLINGMOVEMENTSPEED, UpgradeId.ZERGLINGATTACKSPEED], UnitTypeId.SPAWNINGPOOL),
    **dict.fromkeys([UpgradeId.CENTRIFICALHOOKS, ], UnitTypeId.BANELINGNEST),
    **dict.fromkeys([UpgradeId.GLIALRECONSTITUTION, UpgradeId.TUNNELINGCLAWS], UnitTypeId.ROACHWARREN),
    **dict.fromkeys([UpgradeId.EVOLVEGROOVEDSPINES, UpgradeId.EVOLVEMUSCULARAUGMENTS], UnitTypeId.HYDRALISKDEN),
    **dict.fromkeys([UpgradeId.LURKERRANGE, ], UnitTypeId.LURKERDENMP),
    **dict.fromkeys([*Z_FLYER_ATTACK, *Z_FLYER_ARMOR], UnitTypeId.SPIRE),
    **dict.fromkeys([UpgradeId.INFESTORENERGYUPGRADE, UpgradeId.NEURALPARASITE], UnitTypeId.INFESTATIONPIT),
    **dict.fromkeys([UpgradeId.CHITINOUSPLATING, UpgradeId.ANABOLICSYNTHESIS], UnitTypeId.ULTRALISKCAVERN),

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
    """Returns air units for air tech goal."""
    goal_units = None
    if race == Race.Protoss:
        goal_units = (STARGATE_UNITS["Void Ray"], STARGATE_UNITS["Carrier"])
    elif race == Race.Terran:
        goal_units = (STARPORT_UNITS["Viking"], STARPORT_UNITS["Battlecruiser"])
    elif race == Race.Zerg:
        goal_units = (LARVA_UNITS["Mutalisk"], LARVA_UNITS["Mutalisk"])  # mutas are good

    return goal_units


def get_supply_args(race):
    """Returns arguments which can be provided to increase supply count."""
    if race == Race.Protoss:
        return UnitTypeId.PROBE, UnitTypeId.PYLON
    elif race == Race.Terran:
        return UnitTypeId.SCV, UnitTypeId.SUPPLYDEPOT
    elif race == Race.Zerg:
        return UnitTypeId.LARVA, UnitTypeId.OVERLORD

    return None


def supply_building_time(race):
    """Returns ingame time required for supply units to be built/trained."""
    if race == Race.Terran:
        return 21  # ingame seconds
    else:
        return 18


# example: get_available_buildings(Race.Protoss,[UnitTypeId.NEXUS, UnitTypeId.GATEWAY])
def get_available_buildings(race, buildings_ready):
    """Returns all buildings currently available to be built."""
    tree = BUILDING_TECH_TREE[race]
    building_set = set(buildings_ready)
    return search_tree(tree, building_set)


# recursive dict search tree "all children of the keys"
def search_tree(dict_tree, keys):
    """Returns list of all children (keys) of given keys in dictionary search tree"""
    found_keys = []
    for k in set(dict_tree.keys()):
        if dict_tree[k]:
            if k in set(keys):
                found_keys.extend(search_tree(dict_tree[k], keys))
    found_keys.extend(list(dict_tree.keys()))

    return found_keys


def get_tech_path_needed(race, building):
    """Returns tech path for given building or none if no tech path available/defined."""
    tree = BUILDING_TECH_TREE[race]
    found, path = search_path(tree, building)
    if found:
        return path
    else:
        return None


# returns 2 GREATERSPIREs since it has two required tech paths
def search_path(dict_tree, key):
    """Returns if the path is found and path to the key in dictionary search tree."""
    found_keys = []
    found = False
    for k in set(dict_tree.keys()):
        path = []
        if k == key:
            found_keys.append(k)
        elif dict_tree[k]:
            _, path = search_path(dict_tree[k], key)
            if len(path) > 0:
                found_keys.append(k)
                found_keys.extend(path)
                # could use break statement if there was only one path to certain tech
                # however, greater spire needs two routes
                # (tech trees are small, I don't think the optimization is needed atm)
    if len(found_keys) > 0:
        found = True
    #print(found_keys)

    return found, found_keys

