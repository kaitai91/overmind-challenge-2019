# Terran macro management module
# (c) kaitai


from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2 import position as position_imported

import bot.racial as racial
from bot.race_interface import Race_macro


class TerranMacroBot(Race_macro):

    # GENERAL METHODS
    def __init__(self, controller):
        self.controller = controller

    async def train_unit(self, goal, unit):
        facility = self.controller.tech_goals[goal]["prod"]
        if unit not in racial.NEEDS_TECHLAB:
            action = self.controller.train_units(facility, unit)
        else:
            buildings = self.controller.units.structure.of_type(facility).noqueue.filter(lambda st: st.add_on_tag != 0)
            if buildings.exists:  # noqueue makes sure the addon is also finished
                action = []
                for b in buildings:
                    a = b.train(unit)
                    if a:
                        action.append(a)
            else:
                action = await self.build_addons(facility, False)

        return action

    async def general_macro(self):
        controller = self.controller
        actions = []
        actions.extend(self.morph_orbital())
        actions.extend(self.drop_mules(save_scans=0))
        a = self.do_repairs()
        if a:
            actions.append(a)
        if not controller.check_building_flag:
            actions.extend(self.continue_building())
            actions.extend(await self.build_addons({UnitTypeId.BARRACKS}))  # build tech labs UnitTypeId.BARRACKSFLYING?
            controller.check_building_flag = 5
        return actions

    def early_tech(self):
        controller = self.controller
        # marines
        controller.set_tech_goal(UnitTypeId.BARRACKS, controller.th_type, UnitTypeId.BARRACKS, 4, UnitTypeId.MARINE)

        # hellbats
        # controller.set_tech_goal(UnitTypeId.ARMORY, self.th_type, UnitTypeId.FACTORY, 2,
        #                    UnitTypeId.HELLIONTANK)

        # tanks #TODO: make building techlab possible (DONE)
        controller.set_tech_goal(UnitTypeId.FACTORY, controller.th_type, UnitTypeId.FACTORY, 2,
                                 UnitTypeId.SIEGETANK)

    def mid_tech(self):
        pass

    def late_tech(self):
        pass

    def air_tech(self):
        pass

    # RACE SPECIFIC METHODS:
    def continue_building(self):
        controller = self.controller
        actions = []
        buildings = controller.units.structure.not_ready.exclude_type(
            set(racial.TECHLABS).union(racial.REACTORS).union(racial.TECHREACTORS))
        builders = controller.workers.filter(lambda w: w.is_constructing_scv)
        # for b in builders:
        #     print(f"{b.orders}")
        # example:
        # [UnitOrder(AbilityData(name=CommandCenter), x: 58.5 y: 149.5 , 0.0)]
        # TODO: maybe this can be optimized by checking if any building scv has order to build specific building
        #  this seems to be fine for now
        available = controller.workers.collecting
        for building in buildings:
            if available.exists and not builders.closer_than(4, building):  # 5 for cc are big
                a = available.random_group_of(int(max(available.amount / 4, 1))).prefer_close_to(building)
                ab = a[0](AbilityId.SMART, building)
                if ab:
                    actions.append(ab)
        return actions

    # make orbitals and drop mules (from mass_reaper.py)
    # morph commandcenter to orbitalcommand
    def morph_orbital(self):
        controller = self.controller
        actions = []
        if controller.units(UnitTypeId.BARRACKS).ready.exists and controller.can_afford(
                UnitTypeId.ORBITALCOMMAND):  # check if orbital is affordable
            for cc in controller.units(UnitTypeId.COMMANDCENTER).idle:  # .idle filters idle command centers
                actions.append(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

        return actions

    def drop_mules(self, mf=None, save_scans=1):
        controller = self.controller
        # TODO: make possible to save more than 1 scan per oc (exact amounts)
        actions = []
        if not mf:
            for oc in controller.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                if save_scans:
                    save_scans -= 1
                    if oc.energy < 100:
                        continue
                mfs = controller.state.mineral_field.closer_than(10, oc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    actions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
        else:
            for oc in controller.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                if save_scans:
                    save_scans -= 1
                    if oc.energy < 100:
                        continue
                actions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))

        return actions

    def do_repairs(self, scv=None, target=None, no_checks=False):
        controller = self.controller
        if (controller.repair_flag or controller.workers.amount < 8) and not no_checks:  # dont repair if more income is needed
            return
        # print("in do_repairs")
        if not scv:
            scvs = controller.workers.filter(lambda w: not w.is_constructing_scv)
            if scvs.amount > 0:
                scv = scvs.random
            # print(scv)
            else:
                return
        if not target:
            targets = controller.units.ready.tags_not_in({scv, }).closer_than(10, scv)
            # hard limit of 10 might be bad in some cases
            if targets.amount > 0:
                targets = check_if_mechanical(targets).filter(lambda u: u.health_percentage < 1)
                if targets.amount > 0:
                    target = targets[0]
                    # print(target.health)

        if target and scv:
            # autocast not available atm
            # print(f"doing some repairs")
            controller.repair_flag = 1
            return scv.repair(target)
        else:
            controller.repair_flag = 0.34

    async def build_addon(self, building, reactor=True, location=None):
        action = None
        if not location:
            if not building.is_flying:
                # print("not flying")
                can_place = await self.can_place_addon(building)
                if can_place:
                    if reactor:
                        action = building(racial.BUILD_ADDONS[1])
                    else:
                        action = building(racial.BUILD_ADDONS[0])
                else:
                    building(AbilityId.LIFT)
            # else:  #not working
            #     print("flying")
            #     if reactor:
            #         action = building(racial.BUILD_ADDONS[1])
            #     else:
            #         action = building(racial.BUILD_ADDONS[0])
        # else: # to be implemented: (lift off, place addon to specified location - must be done in different steps)

        return action

    async def can_place_addon(self, building):
        addon_offset = position_imported.Point2((2, 0))
        can_place = await self.controller.can_place(UnitTypeId.SUPPLYDEPOT, building.position.offset(addon_offset))
        if can_place:
            return True
        else:
            return False

    async def build_addons(self, type_id, reactor=True, max_amount=0):
        buildings = self.controller.units.structure.of_type(type_id).noqueue.filter(lambda st: st.add_on_tag == 0)
        actions = []
        count = 0
        if buildings.exists:
            for b in buildings:
                a = await self.build_addon(b, reactor)
                if a:
                    actions.append(a)
                    count += 1
                    if count >= max_amount:
                        break
        return actions

#HELPERS
def check_if_mechanical(unit_list):

    is_mech = unit_list.structure
    is_mech.extend(unit_list.not_structure.of_type(racial.MECHANICALS))
    return is_mech
