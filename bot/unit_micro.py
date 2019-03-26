# Micro module
# (c) kaitai

from sc2.constants import *
from .id_map import TRANSFORM


class MicroBot:
    r = 1
    @staticmethod
    def lurker_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying.closer_than(9 + MicroBot.r, unit)  # 9, not having range while unburrowed
        # print(unit.ground_range)
        if enemy_ground_units.exists:
            # print("ground unit spotted")
            if unit.is_burrowed:
                if unit.weapon_cooldown == 0 and enemy_ground_units.exists:
                    enemy_ground_units = enemy_ground_units.sorted(lambda x: x.distance_to(unit))
                    closest_enemy = enemy_ground_units[0]
                    action = unit.attack(closest_enemy)
                    return action
            else:
                return unit(AbilityId.BURROWDOWN)
        else:
            if unit.type_id == UnitTypeId.LURKERMPBURROWED:
                return unit(AbilityId.BURROWUP)

    @staticmethod
    def viking_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying
        enemy_colossi = enemy_ground_units.of_type(UnitTypeId.COLOSSUS).closer_than(9, unit)
        enemy_ground_units = enemy_ground_units.closer_than(6 + MicroBot.r, unit)
        enemy_air_units = enemy_units.flying.closer_than(9, unit) or enemy_colossi
        if unit.is_flying:
            if not enemy_air_units.exists and enemy_ground_units.exists and unit.health > unit.health_max/2:
                return unit(TRANSFORM[unit.type_id])
        else:
            if enemy_air_units.exists or not enemy_ground_units.exists or unit.health <= unit.health_max/2:
                return unit(TRANSFORM[unit.type_id])

    @staticmethod
    def hel_lion_bat_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying
        enemy_ground_units = enemy_ground_units.closer_than(8 + MicroBot.r, unit)
        if unit.type_id == UnitTypeId.HELLIONTANK:
            if enemy_ground_units.amount < 2:
                return unit(TRANSFORM[unit.type_id])  # transform into quick unit
        else:
            if enemy_ground_units.amount > 2:  #
                return unit(TRANSFORM[unit.type_id])  # transform to slow unit

    @staticmethod
    def tank_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying
        # enemy_colossi = enemy_ground_units.of_type(UnitTypeId.COLOSSUS).closer_than(11, unit)
        enemy_ground_units = enemy_ground_units.closer_than(11 + MicroBot.r, unit)
        too_close = enemy_ground_units.closer_than(3, unit)
        # enemy_air_units = enemy_units.flying.closer_than(9, unit) or enemy_colossi
        if unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            # if less than 3 in siege tank siege range (should always be positive integer)
            if enemy_ground_units.amount - too_close.amount < 3:
                return unit(TRANSFORM[unit.type_id])  # unsiege
        else:
            if enemy_ground_units.amount - too_close.amount >= 5 or too_close == 0 and enemy_ground_units.amount > 1: #siege if at least 5 in siege range
                return unit(TRANSFORM[unit.type_id])  # siege



# unit_type: micro_function
MICRO_BY_TYPE = {
    #protoss

    #terran
    UnitTypeId.VIKINGASSAULT: MicroBot.viking_micro, UnitTypeId.VIKINGFIGHTER: MicroBot.viking_micro,
    UnitTypeId.SIEGETANK: MicroBot.tank_micro, UnitTypeId.SIEGETANKSIEGED: MicroBot.tank_micro,
    UnitTypeId.HELLION: MicroBot.hel_lion_bat_micro, UnitTypeId.HELLIONTANK: MicroBot.hel_lion_bat_micro,

    #zerg
    UnitTypeId.LURKERMP: MicroBot.lurker_micro, UnitTypeId.LURKERMPBURROWED: MicroBot.lurker_micro,
}
