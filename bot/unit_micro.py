# Micro module
# (c) kaitai

from sc2.constants import *
from .racial import TRANSFORM


class MicroBot:
    @staticmethod
    def lurker_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying.closer_than(9, unit)  # 9, not having range while unburrowed
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
            if unit.is_burrowed:
                return unit(AbilityId.BURROWUP)

    @staticmethod
    def viking_micro(unit, enemy_units):
        enemy_ground_units = enemy_units.not_flying.closer_than(6, unit)
        enemy_air_units = enemy_units.flying.closer_than(9, unit) or enemy_ground_units.of_type(UnitTypeId.COLOSSUS)
        if unit.is_flying:
            if not enemy_air_units.exists and enemy_ground_units.exists and unit.health > unit.health_max/2:
                return unit(TRANSFORM[unit.type_id])
        else:
            if enemy_air_units.exists or not enemy_ground_units.exists or unit.health <= unit.health_max/2:
                return unit(TRANSFORM[unit.type_id])


# unit_type: micro_function
MICRO_BY_TYPE = {
    #protoss

    #terran
    UnitTypeId.VIKINGASSAULT: MicroBot.viking_micro, UnitTypeId.VIKINGFIGHTER: MicroBot.viking_micro,

    #zerg
    UnitTypeId.LURKERMP: MicroBot.lurker_micro,
}
