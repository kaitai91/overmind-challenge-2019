# Zerg macro management module
# (c) kaitai

from sc2 import Race
from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2.ids.buff_id import *

from sc2 import position as position_imported

import bot.racial as racial
from bot.race_interface import Race_macro

class ZergMacroBot(Race_macro):
    def __init__(self, controller):
        self.controller = controller

    def train_unit(self, goal, unit):
        pass

    async def general_macro(self):
        controller = self.controller
        actions = []
        actions.extend(self.queens_spawn())
        actions.extend(self.queens_inject())
        if controller.get_time_in_seconds() % 6 and controller.minerals > 400 and controller.vespene > 250 \
                and controller.units.of_type(UnitTypeId.OVERSEER).amount + \
                controller.already_pending(UnitTypeId.OVERSEER, all_units=True) < 2:
            a = controller.morph_overseer()
            if a:
                actions.append(a)

        if controller.supply_used > 120 or (controller.enemy_race is Race.Zerg and controller.supply_used > 170):
            controller.zerg_tech_mid()

        if \
                controller.enemy_race is Race.Zerg and \
                UnitTypeId.SPAWNINGPOOL in controller.tech_goals and \
                controller.supply_used > 62:

            controller.tech_goals.pop(UnitTypeId.SPAWNINGPOOL)

        return actions

    def early_tech(self):
        controller = self.controller
        # lings
        controller.set_tech_goal(UnitTypeId.SPAWNINGPOOL, controller.th_type, None, 2,
                           UnitTypeId.ZERGLING)

        # banelings
        if controller.enemy_race is not Race.Protoss:
            controller.set_tech_goal(UnitTypeId.BANELINGNEST, controller.th_type, None, 2,
                               UnitTypeId.BANELING)

        # roaches
        controller.set_tech_goal(UnitTypeId.ROACHWARREN, controller.th_type, None, 1,
                           UnitTypeId.ROACH)

        # hydras
        if controller.enemy_race is not Race.Zerg:
            controller.set_tech_goal(UnitTypeId.HYDRALISKDEN, controller.th_type, None, 1,
                               UnitTypeId.HYDRALISK)

    def mid_tech(self):
        controller = self.controller

        # hydras
        if UnitTypeId.HYDRALISKDEN not in controller.tech_goals:
            # print("adding hydraden")
            controller.set_tech_goal(UnitTypeId.HYDRALISKDEN, controller.th_type, None, 1,
                               UnitTypeId.HYDRALISK)

        # lurkers
        if UnitTypeId.LURKERDENMP not in controller.tech_goals:
            # print("adding lurkerden")
            controller.set_tech_goal(UnitTypeId.LURKERDENMP, controller.th_type, None, 1, UnitTypeId.LURKERMP)

    def late_tech(self):
        pass

    def air_tech(self):
        pass

    # RACE SPECIFIC METHODS:

    # following ones adopted (and modified) from hydralisk_push.py

    def queen_spawn(self, townhall):
        controller = self.controller

        if controller.units(UnitTypeId.SPAWNINGPOOL).ready.exists:
            close_queens = controller.units.of_type(UnitTypeId.QUEEN).closer_than(8, townhall)
            if close_queens.amount < 1 and townhall.is_ready and townhall.noqueue:  # no queens nearby
                if controller.can_afford(UnitTypeId.QUEEN):
                    return townhall.train(UnitTypeId.QUEEN)

    def queens_spawn(self, townhalls=None):
        actions = []
        if not townhalls:
            townhalls = self.controller.townhalls.ready
        for th in townhalls:
            action = self.queen_spawn(th)
            if action:
                actions.append(action)

        return actions

    def queen_inject(self, queen, townhall):
        # abilities = await self.get_available_abilities(queen)
        if queen.energy >= 25:  # inject cost is 25
            return queen(AbilityId.EFFECT_INJECTLARVA, townhall)

    def queens_inject(self, queens=None, townhalls=None, stacking=False):
        controller = self.controller

        actions = []
        if not queens:
            queens = controller.units.of_type(UnitTypeId.QUEEN)
        if not townhalls:
            townhalls = controller.townhalls.ready
        for queen in queens:
            if queen.energy >= 25:  # lambda x: x.energy >= 50
                ths = townhalls.ready.closer_than(8, queen)
                if not stacking:  # don't stack larva injects
                    ths = ths.filter(lambda t: not t.has_buff(BuffId.QUEENSPAWNLARVATIMER))
                    # inject not needed if spawning larva already
                if ths.exists:
                    action = self.queen_inject(queen, ths.closest_to(queen.position))
                    if action:
                        actions.append(action)
        return actions

    def morph_overseer(self, overlord=None):
        controller = self.controller

        if overlord:
            return controller.morph_unit(overlord)
        if controller.townhalls.of_type({UnitTypeId.LAIR, UnitTypeId.HIVE}).amount > 0:
            ovls = controller.units.of_type(UnitTypeId.OVERLORD)
            if ovls.amount > 0:
                # print(f"trying to create overseer")
                return controller.morph_unit(ovls.random)

# HELPERS
