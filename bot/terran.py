# Terran macro management module
# (c) kaitai


from sc2.ids.unit_typeid import *
from sc2.ids.ability_id import *
from sc2 import position as position_imported

import bot.id_map as id_map
from bot.race_interface import RaceMacro


class TerranMacroBot(RaceMacro):

    # GENERAL METHODS
    def __init__(self, controller):
        super().__init__(controller)
        self.__save_scans = 0

    async def train_unit(self, building_type, unit_type):
        facility = self.controller.tech_goals[building_type]["prod"]
        if unit_type not in id_map.NEEDS_TECHLAB:
            action = self.controller.train_units(facility, unit_type)
        else:
            buildings = self.controller.units.structure.of_type(facility).noqueue.filter(lambda st: st.add_on_tag != 0)
            if buildings.exists:  # noqueue makes sure the addon is also finished
                action = []
                for b in buildings:
                    a = b.train(unit_type)
                    if a:
                        action.append(a)
            else:
                action = await self.build_addons(facility, False)

        return action

    async def general_macro(self):
        controller = self.controller
        actions = []
        actions.extend(self.morph_orbital())
        actions.extend(self.drop_mules(save_scans=self.save_scans))
        a = self.do_repairs()
        if a:
            actions.append(a)
        if not controller.check_building_flag:
            actions.extend(self.continue_building())
            # actions.extend(await self.build_addons({UnitTypeId.BARRACKS}))  # build tech labs UnitTypeId.BARRACKSFLYING?
            controller.check_building_flag = 5
        return actions

    def early_tech(self):
        controller = self.controller
        # marines
        # controller.set_tech_goal(UnitTypeId.BARRACKS, controller.th_type, UnitTypeId.BARRACKS, 4, UnitTypeId.MARINE)

        # marauders
        controller.set_tech_goal(UnitTypeId.BARRACKSTECHLAB, controller.th_type, UnitTypeId.BARRACKS, 2, UnitTypeId.MARAUDER)


        # hellbats
        # controller.set_tech_goal(UnitTypeId.ARMORY, self.th_type, UnitTypeId.FACTORY, 2,
        #                    UnitTypeId.HELLIONTANK)

        # tanks
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
        """Sends SCV to build unfinished building with no SCV."""
        controller = self.controller
        actions = []
        buildings = controller.units.structure.not_ready.exclude_type(
            set(id_map.TECHLABS).union(id_map.REACTORS).union(id_map.TECHREACTORS))
        builders = controller.workers.filter(lambda w: w.is_constructing_scv)

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
        """Turns all idle Command Centers into Orbital Commands."""
        controller = self.controller
        actions = []
        if controller.units(UnitTypeId.BARRACKS).ready.exists and controller.can_afford(
                UnitTypeId.ORBITALCOMMAND):  # check if orbital is affordable
            for cc in controller.units(UnitTypeId.COMMANDCENTER).idle:  # .idle filters idle command centers
                actions.append(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

        return actions

    def drop_mules(self, mf=None, save_scans=None):
        """Drops mules from Orbital Commands to nearby mineral field."""
        controller = self.controller
        actions = []
        if not save_scans:
            save_scans = self.save_scans
        if not mf:
            for oc in controller.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                if save_scans:
                    save_scans -= 1
                    if oc.energy < 100:
                        continue
                    elif oc.energy < 150 and save_scans > 0:
                        save_scans -= 1
                        continue
                    else:  # save max 2 scans in each orbital
                        save_scans -= 1
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
        """Repairs damaged unit with SCV."""
        controller = self.controller
        if (controller.repair_flag or controller.workers.amount < 8) and not no_checks:  # dont repair if more income is needed
            return
        if not scv:
            scvs = controller.workers.filter(lambda w: not w.is_constructing_scv)
            if scvs.amount > 0:
                scv = scvs.random
            else:
                return
        if not target:
            targets = controller.units.ready.tags_not_in({scv, }).closer_than(10, scv)
            # hard limit of 10 might be bad in some cases
            if targets.amount > 0:
                targets = check_if_mechanical(targets).filter(lambda u: u.health_percentage < 1)
                if targets.amount > 0:
                    target = targets[0]

        if target and scv:
            controller.repair_flag = 1
            return scv.repair(target)
        else:
            controller.repair_flag = 0.34

    async def build_addon(self, building, reactor=True, location=None):
        """Builds an addon for building."""
        action = None
        if not location:
            if not building.is_flying:
                can_place = await self.can_place_addon(building)
                if can_place:
                    if reactor:
                        action = building(id_map.BUILD_ADDONS[1])
                    else:
                        action = building(id_map.BUILD_ADDONS[0])
                else:
                    building(AbilityId.LIFT)
        return action

    async def can_place_addon(self, building):
        """Checks if there is room for addon."""
        addon_offset = position_imported.Point2((2, 0))
        can_place = await self.controller.can_place(UnitTypeId.SUPPLYDEPOT, building.position.offset(addon_offset))
        if can_place:
            return True
        else:
            return False

    async def build_addons(self, type_id, reactor=True, max_amount=0):
        """Builds addons for buildings with given UnitTypeId."""
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

    @property
    def save_scans(self):
        return self.__save_scans

    @save_scans.setter
    def save_scans(self, save_scans):
        self.__save_scans = save_scans


#HELPERS
def check_if_mechanical(unit_list):
    """Returns repairable (Terran) units and structures in given list."""

    is_mech = unit_list.structure
    is_mech.extend(unit_list.not_structure.of_type(id_map.MECHANICALS))
    return is_mech
