# Protoss macro management module
# (c) kaitai

from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2.ids.buff_id import *

from sc2 import position as position_imported

import bot.racial as racial
from bot.race_interface import Race_macro

class ProtossMacroBot(Race_macro):

    # GENERAL METHODS
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller

    async def train_unit(self, building_type, unit_type):
        controller = self.controller
        facility = controller.tech_goals[building_type]["prod"]
        action = controller.train_units(facility, unit_type)
        return action

    async def general_macro(self):
        controller = self.controller

        actions = []
        actions.extend(self.spam_chronoboost())
        if controller.units.of_type(UnitTypeId.OBSERVER).amount < 2 and controller.units.of_type(
                UnitTypeId.ROBOTICSFACILITY).amount > 0:
            ao = self.request_observer()
            if ao:
                actions.append(ao)
        return actions

    def early_tech(self):
        controller = self.controller

        # zealots
        controller.set_tech_goal(UnitTypeId.GATEWAY, controller.th_type, UnitTypeId.GATEWAY, 2, UnitTypeId.ZEALOT)

        # immortals
        # controller.set_tech_goal(UnitTypeId.ROBOTICSFACILITY, controller.th_type, UnitTypeId.ROBOTICSFACILITY, 2, UnitTypeId.IMMORTAL)

        # colossi
        controller.set_tech_goal(UnitTypeId.ROBOTICSBAY, controller.th_type, UnitTypeId.ROBOTICSFACILITY, 2,
                                 UnitTypeId.COLOSSUS)

    def mid_tech(self):
        pass

    def late_tech(self):
        pass

    def air_tech(self):
        pass

    # RACE SPECIFIC METHODS:

    def request_observer(self):
        """Requests observer to be built."""
        controller = self.controller

        observer = UnitTypeId.OBSERVER
        robo = UnitTypeId.ROBOTICSFACILITY
        buildings = controller.units(robo).ready.filter(lambda b: len(b.orders) <= 2)
        if buildings.exists:
            if controller.can_afford(observer):
                return buildings.random.train(observer)

    def request_power(self):
        # self.units.structure.filter(lambda s: not s.is_powered)
        pass

    # chrono boost buildings with queued production
    # adopted from warpgate_push.py
    def chronoboost(self, nexus=None, target=None):
        """Uses nexus chronoboost on given target."""
        controller = self.controller

        if not nexus:
            nexus = controller.townhalls.of_type(UnitTypeId.NEXUS).filter(lambda n: n.energy >= 50).random

        if not target:
            target = controller.units.structure.ready.filter(lambda s: not s.noqueue). \
                filter(lambda s1: not s1.has_buff(BuffId.CHRONOBOOSTENERGYCOST)).random

        if nexus and target:
            return nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)

    def spam_chronoboost(self, nexi=None, targets=None):
        """Uses nexus chronoboosts on given targets."""
        controller = self.controller

        actions = []
        if not nexi:
            nexi = controller.townhalls.of_type(UnitTypeId.NEXUS).filter(lambda n: n.energy >= 50)

        if not targets:
            targets = controller.units.structure.ready.filter(lambda s: not s.noqueue). \
                filter(lambda s1: not s1.has_buff(BuffId.CHRONOBOOSTENERGYCOST))

        for nexus in nexi:
            if targets:
                target = targets.pop()
                action = self.chronoboost(nexus, target)
                if action:
                    actions.append(action)
            else:
                break
        return actions

#HELPERS

