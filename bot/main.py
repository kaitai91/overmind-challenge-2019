#TODO: Ideas:
# add scouting, reactions for scout info
# use numpy (for faster numeric calculations)
# add upgrades (already in id_map)
# add scouting and save enemy tech / units to counter them
# create array for wanted buildings/units and save goal values there, then use it everywhere (tech, add production...)

#TODO: flags/vars
# put all similar variables into collections (DONE - partially)
# ideas:
# update base locations so bot won't expand in empty bases
# make flags in one variable and reduce everything at once each step (numpy needed for easy implementation)
# change (tag data) variables in to numpy arrays for quicker operations
# make/use heatmap for enemy locations to defend (maybe with connected components)
# use variable to check mineral and gas amount changes within frame (and update it respectively)

#TODO: macro:
# save researched tech somewhere and fetch trainable units from there (for more efficient training esp. with zerg)
# add more production facilities / tech / whatever when close to 200/200 with big resource bank (DONE - simple solution)
# ideas:
# multiple attack/defence groups
# implement anti-air defence (DONE - kinda)
# combine air and ground hp & dps and make defence group based on that
# make priority queue for different macro actions
# decide which actions can be skipped every now and then
# make priority decision based on game state (consider this with/instead of timed functions)
# prioritizing buildings/tech/workers/army <-- implement this (Already have: hard coded limits for workers)

#TODO: micro:
# prioritize low hp/ high dps enemies in the attack range
# make micro more efficient with big army (take nearby units into account when moving)
# ideas:
# add unitType specific micro (in progress)
# anti-air vs anti-ground, counter units in general
# use swarm intelligence to micro squads (?)
# FIXME: make attacking unit to work as well as attacking to point
#  (you wont get removed from attack tags after target dies atm)

import json
from pathlib import Path

import sc2
from sc2.constants import *
from sc2 import Race
from sc2 import position as position_imported


import math

#code snippets for different races
import bot.id_map as id_map
from bot.unit_micro import MICRO_BY_TYPE
import bot.protoss as protoss
import bot.terran as terran
import bot.zerg as zerg

# STATIC VARS:

WORKER_UPPER_LIMIT = 99


# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    """My bot for StarCraft II melee games."""
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        super().__init__()
        self.enemy_att_str_prev = {"hp": 0, "g_dps": 0, "pos": None}
        self.enemy_att_str_curr = {"hp": 0, "g_dps": 0, "pos": None}
        self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": None}
        self.attacking_enemy_units = []

        self.clock = 0
        self.iteration = -1

        # flags
        self.d_task = False #demanding task
        self.racial_macro_flag = 0
        self.expand_flag = 0
        self.w_dist_flag = 0
        self.attack_flag = 0
        self.enemy_att_str_save = 10
        self.def_msg_flag = 0
        self.killed_start_base = 0
        self.tech_flag = 0
        self.repair_flag = 120
        self.check_building_flag = 0
        # self.reset_expansion_cache_flag = 1*60  # for later development

        self.worker_limit = WORKER_UPPER_LIMIT
        self.tech_switch = 0

        self.pend_supply_flag = 0

        # other - collections
        self.attack_force_tags = dict()
        # example: tag[unit.tag] =  # unit tag
        # {"retreat" : retreating (int), # <5 go ahead and fight else retreat
        # "hp_curr":unit.health (int),
        # "hp_prev":unit.health_prev (int),
        # "target": Pos} # attack position

        self.def_force_tags = dict()
        # example: tag[unit.tag] =  # unit tag
        # {"retreat" : retreating (int), # <5 go ahead and fight else retreat
        # "hp_curr":unit.health (int),
        # "hp_prev":unit.health_prev (int),
        # "target": Pos, # defending position / enemy unit position
        # "orig": Pos} # original defending position

        self.tech_goals = dict()  # dictionary of tech goals and units (the first item has priority).
        # goal[building_type] = {"step": (UnitTypeId)", "prod": (UnitTypeId), "count": (int), "unit": (unit_type)}
        # step is used to track tech progress,
        # prod is the goal production building (for specified unit)
        # count is suggested number of production buildings,
        # unit is the type of unit wanted to produce

        # self.expansion_locations = [] #in super, not needed here

    def _prepare_first_step(self):
        # self.expansion_locations()  # pre calculate locations
        return super()._prepare_first_step()

    def set_tech_goal(self, goal_tech, current_tech, goal_prod_building, prod_b_count, goal_unit):
        """Adds (another) tech goal in bot's tech goals."""
        if self.race == Race.Zerg:  # for zerg production is always in hatcheries
            goal_prod_building = self.th_type
        self.tech_goals[goal_tech] = {"step": current_tech,
                                      "prod": goal_prod_building,
                                      "count": prod_b_count,
                                      "unit": goal_unit}

    def on_start(self):
        """Run when game starts."""
        self.th_type = id_map.TOWN_HALL_TYPES[self.race]
        self.w_type = id_map.WORKER_TYPES[self.race]
        self.prod_bs = id_map.PROD_B_TYPES[self.race]
        self.tech_tree = id_map.BUILDING_TECH_TREE[self.race]
        self.gas_type = id_map.GAS_BUILDINGS[self.race]
        self.s_args = id_map.get_supply_args(self.race)  # <- method

        if self.race == Race.Protoss:
            self.macro_bot = protoss.ProtossMacroBot(self)
        elif self.race == Race.Terran:
            self.macro_bot = terran.TerranMacroBot(self)
        else:  # self.race == Race.Zerg:
            self.macro_bot = zerg.ZergMacroBot(self)

    def _on_step_update_timers(self):
        clock_diff = self.get_time_in_seconds() - self.clock
        self.clock = self.get_time_in_seconds()

        # move all flag (time) reductions here
        self.enemy_att_str_save = max(0, self.enemy_att_str_save - clock_diff)
        self.def_msg_flag = max(0, self.def_msg_flag - clock_diff)
        self.attack_flag = max(0, self.attack_flag - clock_diff)
        self.expand_flag = max(0, self.expand_flag - clock_diff)
        self.w_dist_flag = max(0, self.w_dist_flag - clock_diff)
        self.tech_flag = max(0, self.tech_flag - clock_diff)
        self.racial_macro_flag = max(0, self.racial_macro_flag - clock_diff)
        self.repair_flag = max(0, self.repair_flag - clock_diff)
        self.check_building_flag = max(0, self.check_building_flag - clock_diff)
        # self.reset_expansion_cache_flag = max(0, self.reset_expansion_cache_flag-clock_diff)

        return clock_diff

    async def on_step(self, iteration):
        """Make bot's move(s) here - run periodically."""

        #helper vars
        actions = []
        if iteration == self.iteration:
            print(f"Duplicate iterations @ time {self.clock}")
        self.iteration = iteration

        clock_diff = self._on_step_update_timers()

        if self.supply_left < self.townhalls.ready.amount and not self.pend_supply_flag and self.supply_cap < 200:
            self.pend_supply_flag = 1
        else:
            self.pend_supply_flag = 0

        #USUAL TASKS

        rf_action = self.update_enemy_att_str()
        if rf_action:  # reinforce defence if needed
            actions.extend(rf_action)

        # check if it's time to expand
        if self.clock >= 45 and not self.expand_flag and self.minerals > 250 and self.workers.ready.amount > 0:
            await self.expand() #<-- set flag inside the method

        # distribute workers across the bases
        if self.clock >= 60 and not self.w_dist_flag:
            self.w_dist_flag = 0.8
            # dont saturate gas if the gas count is high enough
            skip_gas = self.vespene*1.5 > self.minerals
            await self.distribute_workers(skip_gas)

        else:
            actions.extend(self.manage_idle_workers())  # only needed when distribute workers is on cooldown

        # macro
        if not self.racial_macro_flag:
            actions.extend(await self.macro_boost())
            self.racial_macro_flag = .97 #arbitrary cooldown

        # add workers to gas or build gas extractors if low on vespene
        if (self.minerals > 150) and ((self.vespene / (self.minerals+1)) <= 0.6): #vespene count less than 60% of minerals
            #following snippet adpoted from cyclone_push.py
            for a in self.units(self.gas_type):
                if a.assigned_harvesters < a.ideal_harvesters:
                    w = self.workers.closer_than(5, a)
                    if w.exists:
                        actions.append(w.random.gather(a))

            #specified refinery counts for certain amount of workers
            if (self.minerals >= 800) and ((self.vespene / (self.minerals+1)) <= 0.5):
                await self.check_and_build_gas() #add extra gas if gas-starving

        # bot is ready to start teching up
        supply_pending = 0
        if self.tech_switch:
            # set desired amount of workers based on # of expansion (in between 24, 88)
            self.adjust_worker_limit()
            if not self.tech_flag:
                    await self.check_and_build_gas()
                    # check that bot has pylons (IF PROTOSS) before building stuff (move to other part later(?))
                    if self.race == Race.Protoss:
                        if self.units.of_type(UnitTypeId.PYLON).ready.amount > 0:
                            for tech in self.tech_goals:
                                await self.manage_tech(tech)
                        else:
                            if not self.already_pending(UnitTypeId.PYLON):
                                await self.build_supply()
                                supply_pending = 1
                    else:
                        for tech in self.tech_goals:
                            await self.manage_tech(tech)
                    self.tech_flag = 5

        if not supply_pending:
            await self.build_supply()

        if self.pend_supply_flag != 1:
            if self.workers.amount < (self.worker_limit - self.townhalls.amount):
                actions.extend(await self.train_workers())


        # FOR MICRO
        self.manage_att_def_groups()

        # micro every max(0.1,clock_diff) if you have force
        if len(self.attack_force_tags) > 0 and \
                (min(0.1, clock_diff) <= (self.clock - int(self.clock)) % max(0.1, clock_diff)):  # micro every 0.1s
            await self.attack_unit_micro()

        if len(self.def_force_tags) > 0 and (min(0.1, clock_diff) <= (self.clock - int(self.clock))):
            await self.defend_unit_micro()

        if int(self.clock) % 91 == 57 and clock_diff >= self.clock-int(self.clock)and self.clock > 222:
            await self.chat_send(f"Elapsed game time: {int(self.clock/60)} min, {int(self.clock)%60}s")

        actions.extend(await self.do_attack_decisions())

        # condition to start teching up
        if not self.tech_switch and self.supply_used > 21:
            self.tech_switch = 1
            # print(f"enemy race is {self.enemy_race}")
            self.macro_bot.early_tech()
            await self.chat_send(f"(party) It's party time! (party)")

        if self.supply_used > 190:  # attack when no units attacking and close to max supply
            if len(self.attack_force_tags) < 20:
                self.attack_flag = min(self.attack_flag, 37)  # attack soon
            else:
                self.attack_flag = min(self.attack_flag, 20.2)

        #UNIQUE TASKS
        if iteration == 1:
            await self.chat_send(f"(glhf)")
            await self.chat_send(f"Let's roll dice (random)X(random)X(random)")

            # scout
            target = self.enemy_start_locations[0]
            if self.enemy_race is Race.Terran:
                actions.extend(self.issue_group_attack(self.workers.ready.random_group_of(2), target))
            else:
                actions.append(self.issue_unit_attack(self.workers.ready.random, target))

        await self.do_actions(actions)

    #copied and modified from bot_ai
    async def distribute_workers(self, skip_gas=False):
        """
        Distributes workers across all the bases taken.
        WARNING: This is quite slow when there are lots of workers or multiple bases.
        """

        # TODO:
        # OPTIMIZE: Assign idle workers smarter
        # OPTIMIZE: Never use same worker mutltiple times
        owned_expansions = self.owned_expansions
        worker_pool = []
        actions = []

        for idle_worker in self.workers.idle:
            mf = self.state.mineral_field.closest_to(idle_worker)
            actions.append(idle_worker.gather(mf))

        for location, townhall in owned_expansions.items():
            workers = self.workers.closer_than(20, location)
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue
        for g in self.geysers:
            workers = self.workers.closer_than(1.9995, g)  # these are workers which may be removed from gas
            actual = g.assigned_harvesters
            ideal = g.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue

        if not skip_gas:
            for g in self.geysers:
                actual = g.assigned_harvesters
                ideal = g.ideal_harvesters
                deficit = ideal - actual

                for _ in range(deficit):
                    if worker_pool:
                        w = worker_pool.pop()
                        if len(w.orders) == 1 and w.orders[0].ability.id is AbilityId.HARVEST_RETURN:
                            actions.append(w.move(g))
                            actions.append(w.return_resource(queue=True))
                        else:
                            actions.append(w.gather(g))

        for location, townhall in owned_expansions.items():
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters

            deficit = ideal - actual
            for x in range(0, deficit):
                if worker_pool:
                    w = worker_pool.pop()
                    mf = self.state.mineral_field.closest_to(townhall)
                    if len(w.orders) == 1 and w.orders[0].ability.id is AbilityId.HARVEST_RETURN:
                        actions.append(w.move(townhall))
                        actions.append(w.return_resource(queue=True))
                        actions.append(w.gather(mf, queue=True))
                    else:
                        actions.append(w.gather(mf))

        await self.do_actions(actions)

    async def expand(self):
        # expand
        if (self.units(self.th_type).amount < 8 or self.workers.amount > 75) and self.can_afford(self.th_type):
            self.expand_flag = 5
            if self.already_pending(self.th_type) < 3:  # expand "only" 3 locations at once
                await self.expand_now(closest_to=self.workers.random.position)
                if self.townhalls.amount < 3:
                    await self.chat_send(f"Let's expand! (flex)")
        # not yet
        else:
            self.expand_flag = 1  # <-- try again soon

    #edited snippet from bot_ai
    # async def expand_now(self, building: UnitTypeId = None, max_distance: Union[int, float] = 10,
    #                      location: Optional[Point2] = None, closest_to: Optional[Point2] = None):
    async def expand_now(self, building=None, max_distance=2,
                         location=None, closest_to=None):
        """Takes new expansion."""

        if not building:
            building = self.th_type

        if not location:
            location = await self.get_next_expansion(closest_to)

        if location:
            await self.build(building, near=location, max_distance=max_distance, random_alternative=False,
                             placement_step=1)

    async def get_next_expansion(self, closest_to=None):
        """Find next expansion location."""

        closest = None
        distance = math.inf

        if closest_to:
            startp = closest_to
        else:
            startp = self._game_info.player_start_location

        #FIXME: find out how to do this (recalc valid expansion locations)
        # if not self.reset_expansion_cache_flag:
        #     print(f"deleting exp_loc_cache")
        #     del self.expansion_locations
        #     self.reset_expansion_cache_flag = 3*60  # 3min
        # other way around: save all locations at start and check if there is own base nearby
        # could also save failed attempts for locations to skip bad bases
        for el in self.expansion_locations:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest

    # try using all_units=True by default - not working?
    def already_pending(self, unit_type, all_units=True) -> int:
        """
        Returns a number of buildings or units already in progress, or if a
        worker is en route to build it. This also includes queued orders for
        workers and build queues of buildings.

        If all_units==True, then build queues of other units (such as Carriers
        (Interceptors) or Oracles (Stasis Ward)) are also included.
        """
        return super().already_pending(unit_type, all_units)

    def adjust_worker_limit(self):
        """Sets preferred worker amount depending on owned expansions."""
        self.worker_limit = max(24, min(len(self.owned_expansions) * 24, 88))
        if 3000 <= self.minerals:
            self.worker_limit = 44
        elif self.worker_limit == 44 and self.minerals <= 1000:
            self.worker_limit = 89
        elif self.tech_switch:
            self.worker_limit = max(24, min(len(self.owned_expansions) * 24, 88))


    async def train_workers(self):
        """Train a worker in each idle townhall.

        Trains a drone for each townhall for zerg (if enough larva)"""
        actions = []
        for th in self.townhalls.ready.noqueue:
            if self.can_afford(self.w_type):
                if self.race == Race.Zerg:
                    if self.units(self.s_args[0]).exists:  # if bot has larva
                        actions.append(self.units(self.s_args[0]).random.train(self.w_type))
                else:
                    actions.append(th.train(self.w_type))
        return actions

    def train_units(self, building_type, unit_type, max_amount=None):
        """Train unit in each idle building.

        Uses only idle buildings and considers buildings with reactors.
        Uses larva for zerg."""
        actions = []
        buildings = self.units(building_type).ready
        if self.race == Race.Terran:  # include buildings with reactor and  at most 2 units in production
            reactor_tags = self.units.structure.of_type(id_map.REACTORS).tags #owned reactors and their tags
            buildings_with_reactor = \
                buildings.filter(lambda s: s.add_on_tag in reactor_tags).filter(lambda rb: len(rb.orders) < 2)
            # print(reactor_tags)
            # print(buildings_with_reactor)
            buildings = buildings.noqueue or buildings_with_reactor
        else:
            buildings = buildings.noqueue
        if max_amount:
            buildings = buildings.random_group_of(min(max_amount, buildings.amount))
        for prod_b in buildings:
            if self.can_afford(unit_type):
                if self.race == Race.Zerg:
                    if self.units(self.s_args[0]).exists:  # if bot has larva
                        actions.append(self.units(self.s_args[0]).random.train(unit_type))
                else:
                    actions.append(prod_b.train(unit_type))
        return actions

    def morph_unit(self, target_unit, alt=False):
        """Morph unit into another unit.

        (ling into baneling, hydra into lurker...)
        For overlords the preferred morph is into overseers.
        With alt flag overlords are morphed into transporting overlords."""
        # so far alt is used only for overlord transport morph - not tested
        if alt and target_unit.type_id == UnitTypeId.OVERLORD:  # prevent crashing if trying alt with other units
            return target_unit(id_map.MORPH2[target_unit.type_id])
        return target_unit(id_map.MORPH[target_unit.type_id])

    def morph_units(self, target_units, alt=False):
        """Morph many units at once."""
        actions = []

        for unit in target_units:
            action = self.morph_unit(unit, alt)
            if action:
                actions.append(action)
        return actions

    def morph_by_id(self, type_id, max_amount=0, alt=False):  # max 0 --> all
        """Morph units by UnitTypeId."""
        targets = self.units.of_type(type_id).ready
        if targets.amount < 1:
            return []
        if max_amount:
            targets.random_group_of(min(targets.amount, max_amount))
        return self.morph_units(targets, alt)

    # TODO: return actions and use it in list like all other actions
    async def build_supply(self):
        """Get pylons/supplydepots/overlords."""
        if self.supply_cap == 200:
            return  # no more supply needed / useful
        ths = self.townhalls.ready
        b_buildings = self.units.of_type(self.prod_bs)  # <- returns dict
        if self.race == Race.Zerg:
            amount = len(ths)
        else:
            amount = len(ths) + len(b_buildings)

        if self.iteration % 2300 == 2299:
            await self.chat_send(f"I have {amount} Production buildings")
        if ths.exists:
            near_completion = (71 - id_map.supply_building_time(self.race)) / 71
            ths_about_to_finish = ths.not_ready.filter(lambda t: t.build_progress > near_completion)
            if self.supply_left < len(ths) + 4 and \
                    self.already_pending(self.s_args[1]) < min(4, amount - ths_about_to_finish.amount):
                if self.can_afford(self.s_args[1]):
                    if self.race == Race.Zerg:
                        actions = []
                        if self.units(self.s_args[0]).exists:  # if bot has larva
                            actions.append(self.units(self.s_args[0]).random.train(self.s_args[1]))
                            await self.do_actions(actions)

                    else:
                        th = ths.random
                        await self.build(self.s_args[1], near=th.position.towards(self.game_info.map_center, 8))

                    if self.pend_supply_flag == 1:
                        self.pend_supply_flag = 2

    def geysers_needed(self):
        """Determines the amount of geysers needed based on owned expansions."""
        w_amount = self.workers.amount
        if self.race is not Race.Zerg:
            if w_amount >= 72:
                geyser_amount = (int(self.units.of_type(self.gas_type).amount) + 1)
            elif w_amount >= 50:
                geyser_amount = min(len(self.owned_expansions) * 2, 5)
            elif w_amount >= 44:
                geyser_amount = min(len(self.owned_expansions) * 2, 4)
            elif w_amount >= 36:
                geyser_amount = min(len(self.owned_expansions) * 2, 3)
            elif w_amount >= 24:
                geyser_amount = min(len(self.owned_expansions) * 2, 2)
            elif w_amount >= 7:
                geyser_amount = min(self.townhalls.amount, 1)
            else:
                geyser_amount = 0
        else:
            if w_amount >= 68:
                geyser_amount = (int(self.units.of_type(self.gas_type).amount) + 1)
            elif w_amount >= 58:
                geyser_amount = min(len(self.owned_expansions) * 2, 4)
            elif w_amount >= 52:
                geyser_amount = min(len(self.owned_expansions) * 2, 3)
            elif w_amount >= 41:
                geyser_amount = min(len(self.owned_expansions) * 2, 2)
            elif w_amount >= 32:
                geyser_amount = min(len(self.owned_expansions) * 2, 1)
            elif w_amount >= 7:
                geyser_amount = min(self.townhalls.amount, 1)
            else:
                geyser_amount = 0

        if self.townhalls.amount > 0:
            if geyser_amount - self.geysers.amount - self.already_pending(self.gas_type) > 0:
                return geyser_amount - self.geysers.amount - self.already_pending(self.gas_type)
        return 0

    async def build_gas(self, max_amount=3):
        """Builds gas extracting structures."""
        #following adopted and modified from mass_reaper.py in examples/terran
        actions = []
        own_bases = list(self.owned_expansions.values())
        added = 0
        if self.workers.amount <= 7 or max_amount == 0:
            return []
        for th in own_bases:
            if th.is_ready:
                vgs = self.state.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place(self.gas_type, vg.position) and self.can_afford(self.gas_type):
                        ws = self.workers.gathering
                        if ws.exists:  # same condition as above
                            w = ws.closest_to(vg)
                            # caution: the target for the refinery has to be the vespene geyser, not its position!
                            actions.append(w.build(self.gas_type, vg))
                            added += 1
                    if added >= max_amount:
                        break
                if added >= max_amount:
                    break

        await self.do_actions(actions)

    async def check_and_build_gas(self):
        """Builds more assimilators/refineries/extractors if needed."""
        needed = self.geysers_needed()
        if needed:
            await self.build_gas(needed)

    async def do_attack_decisions(self):
        attack_actions = []

        # killed_base is here, since not used anywhere else.. move if needed
        if not self.killed_start_base:
            shortest_dist = self.units.closest_distance_to(self.enemy_start_locations[0])
            if shortest_dist <= 2:
                # print("killed enemy starting base")
                self.killed_start_base = 1

        if self.supply_used - self.workers.amount > 6 and not self.attack_flag and \
                ((len(self.attack_force_tags) + len(self.def_force_tags)) <
                 (self.units.not_structure.not_flying.amount / 2 + 1)):

            # set new attack_flag
            enemy_buildings = self.known_enemy_structures().not_flying.exclude_type(id_map.CREEP_TUMORS)
            if not self.killed_start_base:
                if enemy_buildings.amount > 0:
                    target = enemy_buildings.random.position
                else:
                    target = self.enemy_start_locations[0]
                self.attack_flag = 90  # seconds
            elif enemy_buildings.not_flying.amount > 0:
                target = self.known_enemy_structures.not_flying.random.position
                self.attack_flag = 60  # seconds
            else:
                possible_targets = list(self.expansion_locations.keys())
                # possible_targets.sort()  # try sorting to ensure same order every time (should save as var and use ref
                number = len(possible_targets)
                target = possible_targets[self.killed_start_base % number]
                self.killed_start_base += 1
                # LCM for base counts 4-13 = 360360
                if self.killed_start_base > 360360 * 2:  # <-not realistic to happen :D
                    self.killed_start_base %= 360360
                self.attack_flag = 10  # seconds

            # attack based on new attack flag
            if self.attack_flag > 20:
                army = self.units.not_structure.exclude_type(
                    [self.w_type, UnitTypeId.OVERLORD, UnitTypeId.MULE, UnitTypeId.QUEEN])
                attack_actions.extend(self.issue_group_attack(army, target))
                if army.amount > 4:
                    attack_actions.extend(self.issue_group_attack(army, target))

                excess_workers = self.workers.amount - min(len(self.owned_expansions) * 29 + 1, 89)
                if excess_workers > 0 and self.workers.amount > 0:
                    attack_actions.extend(self.issue_worker_attack(target, (excess_workers / self.workers.amount)))

            else:  # scout attack location
                # print(f"attacking with: {len(set(self.def_force_tags.keys()).union(set(self.attack_force_tags.keys())))}")
                # print(target)
                army = self.units.not_structure.exclude_type(
                    [self.w_type, UnitTypeId.OVERLORD, UnitTypeId.MULE, UnitTypeId.QUEEN]).\
                    tags_not_in(set(self.def_force_tags.keys()).union(set(self.attack_force_tags.keys())))
                if army.amount > 8:
                    group_size = min(25, max(4, army.amount))  # groups of 4-20 units to scout enemy
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = army.prefer_close_to(target)[:group_size]
                    attack_actions.extend(self.issue_group_attack(random_scout_squad, target))

                elif self.workers.amount > 15:
                    group_size = max(4, int(self.workers.amount * 0.25) + 1)
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = self.workers.filter(lambda w: not w.is_constructing_scv). \
                                             prefer_close_to(target)[:group_size]
                    attack_actions.extend(self.issue_group_attack(random_scout_squad, target))

        return attack_actions

    def calc_enemy_att_str(self):
        """Calculates enemy attack strength.

        Checks if there are enemy units close to completed owned structures."""
        # ground hp, air hp, ground dps, air dps
        enemy_g_hp = 0
        enemy_a_hp = 0
        enemy_g_dps = 0
        # enemy_a_dps = 0  # not relevant for defence in general
        known_g_enemies = self.known_enemy_units.not_structure.not_flying
        known_a_enemies = self.known_enemy_units.not_structure.flying
        # enemy_count = self.known_enemy_units.amount
        enemy_position = None
        closest_dist = math.inf
        self.attacking_enemy_units = []
        bases = self.units.structure.ready
        if not bases:
            bases = self.units.structure
        for enemy in known_g_enemies:
            if enemy.can_attack_ground:
                dist = bases.closest_distance_to(enemy)
                if dist < max(12, enemy.ground_range):
                    if dist < closest_dist:
                        enemy_position = enemy.position
                    self.attacking_enemy_units.append(enemy)
                    enemy_g_hp += enemy.health + enemy.shield
                    enemy_g_dps += enemy.ground_dps

        for enemy in known_a_enemies:
            if enemy.can_attack_ground:
                dist = self.units.structure.closest_distance_to(enemy)
                if dist < max(16, enemy.ground_range):
                    # TODO: take into account when making anti-air
                    # if dist < closest_dist:
                    #     closest_enemy = enemy
                    self.attacking_enemy_units.append(enemy)
                    enemy_a_hp += enemy.health + enemy.shield
                    enemy_g_dps += enemy.ground_dps

        total_hp = enemy_g_hp + enemy_a_hp

        # if enemy has been seen, use the last location as enemy position
        if not enemy_position:  # is none
            if self.enemy_att_str_curr["pos"]:
                enemy_position = self.enemy_att_str_curr["pos"]
            elif self.enemy_att_str_max["pos"]:
                enemy_position = self.enemy_att_str_max["pos"]
        enemy_att_str = {"hp": total_hp, "g_dps": enemy_g_dps, "pos": enemy_position}
        return enemy_att_str

    def manage_att_def_groups(self):
        """Updates unit tags in att/def if needed.

        Makes sure no tag is in both the groups and
        removes one if the tag is no more in tags for all owned units."""
        tags = [unit.tag for unit in self.units.not_structure.ready]  # get tags for units
        diff_a = set(self.attack_force_tags.keys()).difference(set(tags))  # units not in self.units
        diff_d = set(self.def_force_tags.keys()).difference(set(tags))
        if len(self.def_force_tags) > 0 and len(diff_d) > 0:
            for tg in diff_d:
                del (self.def_force_tags[tg])

        if len(self.attack_force_tags) > 0 and len(diff_a) > 0:
            for tg in diff_a:
                del (self.attack_force_tags[tg])
        for tg in set(self.def_force_tags.keys()).intersection(self.attack_force_tags):
            del (self.attack_force_tags[tg])

    def update_enemy_att_str(self):
        # Reinforce defence
        self.enemy_att_str_prev = self.enemy_att_str_curr.copy()
        self.enemy_att_str_curr = self.calc_enemy_att_str()
        enemy_att_got_stronger = self.enemy_att_str_max["hp"] < self.enemy_att_str_curr["hp"] and \
                                 self.enemy_att_str_max["g_dps"] < self.enemy_att_str_curr["g_dps"]

        enemy_is_as_strong = self.enemy_att_str_max["hp"] <= self.enemy_att_str_curr["hp"] and \
                             self.enemy_att_str_max["g_dps"] <= self.enemy_att_str_curr["g_dps"]

        if enemy_att_got_stronger:
            self.enemy_att_str_save = 20

        if not self.enemy_att_str_save:
            # never erase enemy last position (where they did attack last time)
            self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": self.enemy_att_str_max["pos"]}

        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev
        m = self.enemy_att_str_max
        self.enemy_att_str_max["hp"] = max(c["hp"], p["hp"], m["hp"])
        self.enemy_att_str_max["g_dps"] = max(c["g_dps"], p["g_dps"], m["g_dps"])
        if c["pos"]:
            self.enemy_att_str_max["pos"] = c["pos"]  # use most recent position

        # if enemy_att_got_stronger:
        if m["pos"]:
            return self.reinforce_defence()

        return None

    def reinforce_defence(self):
        """Reinforces defence if there is an attack incoming.

        Actual defending units and unit amount depend on calculated attack strength."""

        # shorten names
        m = self.enemy_att_str_max
        if not m["pos"]:
            return

        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev

        # changes: (differences)
        d_hp = max(0, c["hp"]-p["hp"])
        d_g_dps = max(0, c["g_dps"]-p["g_dps"])
        if len(self.attacking_enemy_units) > 0 and (d_hp > 0 or d_g_dps > 0 or len(self.def_force_tags) < 1):
            ad = self.assign_defence(m["hp"], m["g_dps"], m["pos"])
            if ad:
                return ad

    async def assign_def_groups(self, enemy_groups):
        # To be implemented
        pass

    def assign_defence(self, enemy_hp, enemy_dps, enemy_position):
        """Creates defence group to repel an attack.

        No group is created if there is not enough troops to defend."""

        army = self.units.ready.tags_not_in(self.def_force_tags).\
            not_structure.exclude_type([self.w_type, UnitTypeId.QUEEN]).\
                                       filter(lambda u: u.can_attack)
        # sort workers: high hp and close distance preferred
        workers = self.workers.ready.tags_not_in(self.def_force_tags).filter(lambda w: not w.is_constructing_scv).\
            sorted(lambda w: -(w.health+w.shield)).prefer_close_to(enemy_position)

        #TODO: better way to assign and track enemy

        # if len(self.owned_expansions) >= 3:
        if enemy_dps > 20:  # if enemy is too strong, dont suicide all workers
            workers = workers.closer_than(12, enemy_position)  # dont assign workers from other bases to defend
        self.w_dist_flag = 5  # wait for 5s to re distribute workers
        #TODO: just remove this townhall temporarily from worker distribution function
        # (self.units = self.units.exclude_tag(tag_of_building) in the beginning of step)

        if len(army)+len(workers) < 1:
            return

        actions = []

        defenders, own_dps, own_hp = self.create_defence_group(army, enemy_dps, enemy_hp, workers)

        # do we have enough to defend
        if enemy_dps < 10:
            condition = True
        else:
            condition = (own_hp >= enemy_hp and own_dps >= enemy_dps) or self.townhalls.amount < 2  # or self.clock<120
        if condition and len(defenders) > 0:
            actions.extend(self.issue_group_defence(defenders, enemy_position))
            # self.chat_defending_taunt(enemy_position, workers.amount+army.amount, enemy_hp, own_hp, enemy_dps, own_dps)

        # retreat from strong enemy
        else:
            for defender in self.def_force_tags:
                self.def_force_tags[defender]["retreat"] = 5
            # await self.chat_retreating(enemy_position, enemy_hp, enemy_dps)

        if len(actions) > 0:
            return actions

    def create_defence_group(self, army, enemy_dps, enemy_hp, workers):
        """Creates defence group to repel an attack."""
        own_hp = 0
        own_dps = 0
        defenders = []

        # use existing defence first:
        if len(self.def_force_tags) > 0:

            for old_member in self.units.tags_in(set(self.def_force_tags.keys())):

                if own_hp <= (enemy_hp + 1) or own_dps <= (enemy_dps + 1):
                    defenders.append(old_member)
                    own_hp += old_member.health + old_member.shield
                    own_dps += old_member.ground_dps

        if enemy_dps < 4:  # 1 worker or smthing like that
            for asset in army:
                if own_hp <= (enemy_hp + 1) or own_dps <= (enemy_dps + 1):
                    defenders.append(asset)
                    own_hp += asset.health + asset.shield
                    own_dps += asset.ground_dps
                else:
                    break

            for worker in workers:
                if own_hp <= (enemy_hp + 1) or own_dps <= (enemy_dps + 1):
                    defenders.append(worker)
                    own_hp += (worker.health + worker.shield)
                    own_dps += worker.ground_dps
                else:
                    break

        elif enemy_dps < 20:
            for asset in army:
                if own_hp <= (enemy_hp * 1.2 + 1) or own_dps <= (enemy_dps * 1.2 + 1):
                    defenders.append(asset)
                    own_hp += asset.health + asset.shield
                    own_dps += asset.ground_dps
                else:
                    break

            for worker in workers:
                if own_hp <= (enemy_hp * 1.5 + 1) or own_dps <= (enemy_dps * 1.5 + 1):
                    defenders.append(worker)
                    own_hp += (worker.health + worker.shield)
                    own_dps += worker.ground_dps
                else:
                    break

        else:  # enemy_g_dps > 20:
            for asset in army:
                if own_hp <= (enemy_hp * 3 + 1) or own_dps <= (enemy_dps * 2 + 1):
                    defenders.append(asset)
                    own_hp += asset.health + asset.shield
                    own_dps += asset.ground_dps
                else:
                    break

            for worker in workers:
                if own_hp <= (enemy_hp * 3 + 1) or own_dps <= (enemy_dps * 2 + 1):
                    defenders.append(worker)
                    own_hp += (worker.health + worker.shield)
                    own_dps += worker.ground_dps
                else:
                    break
        return defenders, own_dps, own_hp

    # from mass_reaper.py
    # stolen and modified from position.py
    def _neighbors4(self, position, distance=1):
        p = position
        d = distance
        return {
            position_imported.Point2((p.x - d, p.y)),
            position_imported.Point2((p.x + d, p.y)),
            position_imported.Point2((p.x, p.y - d)),
            position_imported.Point2((p.x, p.y + d)),
        }

    # stolen and modified from position.py
    def _neighbors8(self, position, distance=1):
        p = position
        d = distance
        return self._neighbors4(position, distance) | {
            position_imported.Point2((p.x - d, p.y - d)),
            position_imported.Point2((p.x - d, p.y + d)),
            position_imported.Point2((p.x + d, p.y - d)),
            position_imported.Point2((p.x + d, p.y + d)),
        }

    # this checks if a ground unit can walk on a Point2 position
    def _inPathingGrid(self, pos):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[(pos)] != 0

    def ranged_unit_micro(self, unit):
        """General micro for ranged units.

        priorities:
        low_hp_retreat > attack > move/retreat"""
        action = None
        #adopted and modified from mass_reaper.py
        # move to range 15 of closest unit if reaper is below 20 hp and not regenerating
        if unit.is_flying:
            enemyAirThreatsClose = self.known_enemy_units.flying.filter(lambda x: x.can_attack_air).\
                closer_than(15, unit)
            enemyGroundThreatsClose = self.known_enemy_units.not_flying.filter(lambda x: x.can_attack_air).\
                closer_than(15, unit)
        else:
            enemyAirThreatsClose = self.known_enemy_units.flying.filter(lambda x: x.can_attack_ground). \
                closer_than(15, unit)
            enemyGroundThreatsClose = self.known_enemy_units.not_flying.filter(lambda x: x.can_attack_ground). \
                closer_than(15, unit)
        enemyThreatsClose = enemyAirThreatsClose or enemyGroundThreatsClose  # use or to combine selections

        if unit.health_percentage < 2 / 5 and enemyThreatsClose.exists and unit.shield < 1:
            retreatPoints = self._neighbors8(unit.position, distance=2) | self._neighbors8(unit.position, distance=4)
            # filter points that are pathable
            retreatPoints = {x for x in retreatPoints if self._inPathingGrid(x)}
            if retreatPoints:  # maybe this can be done more efficiently (pathing)
                closestEnemy = enemyThreatsClose.closest_to(unit)
                retreatPoint = closestEnemy.position.furthest(list(retreatPoints))  # need indexing in position.py
                action = unit.move(retreatPoint)
                return action  # dont execute any of the following

        # reaper is ready to attack, shoot nearest ground unit
        if unit.can_attack_ground:
            enemyGroundUnits = self.known_enemy_units.not_flying.closer_than(unit.ground_range, unit)
            if unit.weapon_cooldown == 0 and enemyGroundUnits.exists:
                enemyGroundUnits = enemyGroundUnits.sorted(lambda x: x.distance_to(unit))
                closestEnemy = enemyGroundUnits[0]
                action = unit.attack(closestEnemy)
                return action  # dont execute any of the following

        if unit.can_attack_air:
            enemyAirUnits = self.known_enemy_units.flying.closer_than(unit.air_range, unit)
            if unit.weapon_cooldown == 0 and enemyAirUnits.exists:
                enemyAirUnits = enemyAirUnits.sorted(lambda x: x.distance_to(unit))
                closestEnemy = enemyAirUnits[0]
                action = unit.attack(closestEnemy)
                return action  # dont execute any of the following

        # move towards to max unit range if enemy is closer than ??
        if unit.is_flying:
            enemyAirThreatsVeryClose = enemyAirThreatsClose.\
                filter(lambda eu: eu.air_range < unit.air_range).\
                closer_than(min(0, unit.air_range - max(0.5, unit.air_range * 0.1)), unit)
            enemyGroundThreatsVeryClose = enemyGroundThreatsClose.\
                filter(lambda eu: eu.air_range < unit.ground_range).\
                closer_than(min(0, unit.air_range - max(0.5, unit.ground_range * 0.1)), unit)
            # enemyThreatsVeryClose = self.known_enemy_units.filter(lambda x: x.can_attack_air). \
            #     closer_than(unit.ground_range - max(0.5, unit.ground_range*0.1), unit)
        else:
            enemyAirThreatsVeryClose = enemyAirThreatsClose. \
                filter(lambda eu: eu.ground_range < unit.air_range). \
                closer_than(min(0, unit.ground_range - max(0.5, unit.air_range * 0.1)), unit)
            enemyGroundThreatsVeryClose = enemyGroundThreatsClose. \
                filter(lambda eu: eu.ground_range < unit.ground_range). \
                closer_than(min(0, unit.ground_range - max(0.5, unit.ground_range * 0.1)), unit)
            # enemyThreatsVeryClose = enemyThreatsClose.filter(lambda eu: eu.ground_range < unit.ground_range). \
            #     closer_than(min(0, unit.ground_range - max(0.5, unit.ground_range * 0.1)), unit)
        enemyThreatsVeryClose = enemyAirThreatsVeryClose or enemyGroundThreatsVeryClose  # combine selections

        # enemyThreatsVeryClose = self.known_enemy_units.filter(lambda x: x.can_attack_ground).\
        #     closer_than(unit.ground_range - 0.5, unit)  # hardcoded attackrange minus 0.5
        # threats that can attack the reaper
        if unit.weapon_cooldown != 0 and enemyThreatsVeryClose.exists:
            retreatPoints = self._neighbors8(unit.position, distance=2) | self._neighbors8(unit.position, distance=4)
            # filter points that are pathable by a reaper
            retreatPoints = {x for x in retreatPoints if self._inPathingGrid(x)}
            if retreatPoints:
                closestEnemy = enemyThreatsVeryClose.closest_to(unit)
                retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(closestEnemy) - x.distance_to(unit))
                # retreatPoint = closestEnemy.position.furthest(retreatPoints)
                action = unit.move(retreatPoint)
                return action  # don't execute any of the following

        # move to nearest enemy ground unit/building because no enemy unit is closer than 5
        allEnemyGroundUnits = self.known_enemy_units.not_flying or self.known_enemy_structures.not_flying
        if allEnemyGroundUnits.exists:
            closestEnemy = allEnemyGroundUnits.closest_to(unit)
            action = unit.move(closestEnemy)
            return action  # don't execute any of the following

        return action

    def unit_retreat(self, unit, target):
        """General retreat for all units."""
        mf = self.state.mineral_field.closest_to(target)
        if unit.type_id is self.w_type and mf:  # if worker
            if unit.is_carrying_minerals or unit.is_carrying_vespene:
                return unit(AbilityId.SMART, target)
            mf = self.state.mineral_field.closest_to(target)
            return unit.gather(mf)
        else:
            return unit.move(target)

    def general_micro(self, unit_tag, tags, hp_lower_bound=0.1):
        """General micro for all units."""
        action = None
        unit = self.units.by_tag(unit_tag)
        tags[unit_tag]["hp_curr"] = unit.health + unit.shield  # update current hp
        ret = tags[unit_tag]["retreat"]
        hpc = tags[unit_tag]["hp_curr"]
        hpp = tags[unit_tag]["hp_prev"]
        max_hp_sh = unit.health_max + unit.shield_max
        baneling_with_low_hp = (unit.type_id == UnitTypeId.BANELING and hpc < 18)

        if not baneling_with_low_hp:  # dont retreat with low hp banes
            # check if low hp or retreating flag (townhall is retreating point) --> retreat
            no_shield = not unit.shield > unit.health
            if (ret > 4 or (hpc < hp_lower_bound and no_shield)) and self.townhalls.ready.amount > 0:
                if unit.is_burrowed:
                    action = unit(AbilityId.BURROWUP)
                    return action, False
                else:
                    action = self.unit_retreat(unit, self.townhalls.ready.random)
                    return action, True  # tb_removed.append(unit_tag)

            # check if less than 50% hp and lost hp since last tick (townhall is retreating point)
            # --> fall back and come back later
            # if unit has shield use shield as indicator
            hp_less_than_half_more_than_lower_limit = hpc < (max(min(max_hp_sh / 2, unit.health_max), hp_lower_bound))

            if (not no_shield or hp_less_than_half_more_than_lower_limit) and hpc < hpp:
                if self.townhalls.amount > 0:
                    if unit.is_burrowed:
                        action = unit(AbilityId.BURROWUP)
                    else:
                        action = self.unit_retreat(unit, self.townhalls.random)
                    tags[unit_tag]["retreat"] += 1
                    return action, False
                tags[unit_tag]["retreat"] += 1

        if unit.type_id in MICRO_BY_TYPE:
            close_a_enemies = self.known_enemy_units.flying
            close_g_enemies = self.known_enemy_units.not_flying.exclude_type(id_map.CHANGELINGS)
            known_enemies = close_a_enemies or close_g_enemies  # "additive or"
            action = MICRO_BY_TYPE[unit.type_id](unit, known_enemies)
            if action:
                return action, False

        if unit.ground_range >= 1.1:
            action = self.ranged_unit_micro(unit)
            if action:
                return action, False

        return action, False

    async def attack_unit_micro(self):
        """General micro for attacking units."""
        tags = self.attack_force_tags
        actions = []
        tb_removed = []
        min_hp = 11
        if len(tags) >= 3:
            min_hp = 10
        for tg in tags:
            unit = self.units.by_tag(tg)

            # general_micro
            action, remove = self.general_micro(tg, tags, min_hp)
            if remove:
                tb_removed.append(tg)
            if action:
                actions.append(action)
                continue

            # pursue enemy
            close_a_enemies = self.known_enemy_units.flying.closer_than(16, unit.position)
            close_g_enemies = self.known_enemy_units.not_flying.closer_than(16, unit.position).exclude_type(id_map.CHANGELINGS)
            close_enemies = 0
            if unit.can_attack_air:
                close_enemies += close_a_enemies.amount
            if unit.can_attack_ground:
                close_enemies += close_g_enemies.amount

            #get closer to target (location based attack move)
            target = tags[tg]["target"]
            if unit.distance_to(target) >= 25 and close_enemies < 2:
                actions.append(unit.move(target))
            elif (unit.distance_to(target) >= 5) and (tags[tg]["retreat"] < 5):
                actions.append(unit.move(target))
            elif unit.distance_to(target) >= 2 and not self.units.structure.closer_than(2.1, target) and tags[tg]["retreat"] < 5:
                actions.append(unit.attack(target))
            else:
                tb_removed.append(tg)
                if self.townhalls.ready.amount > 0:
                    actions.append(self.unit_retreat(unit, self.townhalls.ready.random))

            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            max_hp_sh = unit.health_max + unit.shield_max
            if ret and hpc > (max_hp_sh/2):
                tags[tg]["retreat"] = 0

            tags[tg]["hp_prev"] = hpc = tags[tg]["hp_curr"]

        for tag in tb_removed:
            del(self.attack_force_tags[tag])

        await self.do_actions(actions)

    async def defend_unit_micro(self):
        """General micro for defending units."""
        tags = self.def_force_tags
        actions = []
        tb_removed = []
        min_hp = 0.1  # TODO: change if needed / create new var for situational min_hp
        for tg in tags:
            unit = self.units.by_tag(tg)

            #general_micro
            action, remove = self.general_micro(tg, tags, min_hp)
            if remove:
                tb_removed.append(tg)
            if action:
                actions.append(action)
                continue

            army = self.units.not_structure.exclude_type(self.w_type).filter(lambda u: u.can_attack_ground)
            workers = self.workers.filter(lambda w: not w.is_constructing_scv)

            #pursue enemy
            orig = tags[tg]["orig_target"]  # for defending at defence location
            close_enemies = self.known_enemy_units.not_flying.closer_than(
                unit.sight_range, unit.position).exclude_type(id_map.CHANGELINGS).sorted_by_distance_to(unit)
            target = tags[tg]["target"]
            if close_enemies.amount > 0:
                #pursue only so far:
                if close_enemies[0].distance_to(orig) < 20:
                    actions.append(unit.attack(close_enemies[0]))  # this enemy is visible
                else:
                    actions.append(unit.attack(orig))
            elif unit.distance_to(target) >= 3:
                actions.append(unit.attack(target))
            else:
                tb_removed.append(tg)
                if self.townhalls.ready.amount > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                    actions.append(unit.gather(mf))

            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            max_hp_sh = unit.health_max + unit.shield_max
            if ret and hpc > (max_hp_sh/2): #hp is back up
                tags[tg]["retreat"] = 0



            tags[tg]["hp_prev"] = hpc = tags[tg]["hp_curr"] + unit.shield

        for tag in tb_removed:
            del(self.def_force_tags[tag])

        await self.do_actions(actions)

#HELPERS

    def manage_idle_workers(self):
        """Returns idle workers back to work."""
        actions = []
        if self.townhalls.ready.exists:
            for w in self.workers.idle:
                th = self.townhalls.ready.closest_to(w)
                mfs = self.state.mineral_field.closer_than(10, th)
                if mfs:
                    mf = mfs.closest_to(w)
                    actions.append(w.gather(mf))
        elif self.townhalls.exists:
            for worker in self.workers.idle:
                th = self.townhalls.closest_to(worker)
                target = th.position
                actions.extend(self.issue_idle_worker_attack(target))
        else:
            self.expand_flag = 0

        return actions

    def get_time_in_seconds(self):
        """Returns real time if game is played on "faster"."""
        return self.state.game_loop * 0.725 * (1 / 16)

    def issue_worker_attack(self, target, percentage=1.0):
        """Attack with workers. (i.e. worker rush)"""
        return self.issue_group_attack(self.workers.random_group_of(
            min(self.workers.amount, int(self.workers.amount*percentage)+1)),
            target)

    def issue_idle_worker_attack(self, target):
        """Attack with idle workers."""
        return self.issue_group_attack(self.workers.idle, target)

    def issue_group_attack(self, group, target):
        """Attack with group of units."""
        actions = []
        for unit in group:
            actions.append(self.issue_unit_attack(unit, target))
        return actions

    def issue_unit_attack(self, unit, target):
        """Attack with single unit."""
        action = unit.attack(target)
        retreating = 0
        health_prev = unit.health
        self.attack_force_tags[unit.tag] = {"retreat": retreating,
                                            "hp_curr": unit.health,
                                            "hp_prev": health_prev,
                                            "target": target}
        return action

    def issue_group_defence(self, group, target):
        """Defend with a group of units."""
        actions = []
        for unit in group:
            actions.append(self.issue_unit_defence(unit, target))
        return actions

    def issue_unit_defence(self, unit, target):
        """Defend with a unit."""
        action = unit.attack(target)
        orig = target
        retreating = 0
        health_prev = unit.health
        self.def_force_tags[unit.tag] = {"retreat": retreating,
                                         "hp_curr": unit.health,
                                         "hp_prev": health_prev,
                                         "target": target,
                                         "orig_target": orig}
        return action

    async def manage_tech(self, tech_goal):
        """Try to advance in given tech.

        (tech must be included in self.tech_goals)"""
        actions = []
        old_step = self.tech_goals[tech_goal]["step"]
        ready_buildings = uniques_by_type_id(self.units.structure.ready)
        ready_types = [b.type_id for b in ready_buildings]
        not_ready_buildings = uniques_by_type_id(self.units.structure.not_ready)

        # check tech progress
        curr_step = self.update_tech_progress(tech_goal, ready_buildings, not_ready_buildings)

        # build advancement in tech
        if curr_step in id_map.MORPH_BUILDINGS:
            pending = self.already_pending(curr_step, all_units=True)
        else:
            pending = self.already_pending(curr_step)

        if not pending and (curr_step not in ready_types):  # or old_step != curr_step:
            if curr_step is self.th_type:  # in case townhall was lost
                await self.expand()
            elif curr_step in id_map.ADDON_BUILDING:  # implicitly isinstance(self.macro_bot, terran.TerranMacroBot)
                building = id_map.ADDON_BUILDING[curr_step]
                # noinspection PyUnresolvedReferences
                acts = await self.macro_bot.build_addons(building, reactor=False, max_amount=1)
                actions.extend(acts)
            elif curr_step not in id_map.MORPH_BUILDINGS:
                if self.workers.ready.collecting.amount > 0:
                    if self.race != Race.Protoss:
                        close_by = self.townhalls.ready.random.position.towards(self.game_info.map_center, 5)
                    else:
                        close_by = self.units.of_type(UnitTypeId.PYLON).ready.random.position
                    await self.build(curr_step, near=close_by)
            else:
                all_units_of_type = self.units.structure.of_type(id_map.MORPH_BUILDINGS[curr_step]).ready.noqueue
                morph_any_of_these = all_units_of_type.random_group_of(all_units_of_type.amount)
                for morph_this in morph_any_of_these:
                    actions.append(self.morph_unit(morph_this))
                    break  # only one

        # tech available
        if curr_step == tech_goal:

            prod_goal = self.tech_goals[tech_goal]["prod"]

            # add enough production buildings
            already_building = self.already_pending(prod_goal)
            already_ready = self.units.structure.ready.of_type(prod_goal).amount
            needed = self.tech_goals[tech_goal]["count"] - already_building - already_ready
            if needed > 0:
                candidates = self.workers.prefer_idle
                if candidates.amount < 1:
                    return
                for builder in candidates.random_group_of(min(needed, candidates.amount)):
                    if self.race != Race.Protoss:
                        close_by = self.units.structure.not_flying.ready.random.position.\
                            towards(self.game_info.map_center, 5)
                    else:
                        close_by = self.units.of_type(UnitTypeId.PYLON).ready.random.position
                    await self.build(prod_goal, near=close_by, unit=builder)
        if len(actions) > 0:
            await self.do_actions(actions)

    def update_tech_progress(self, tech_goal, ready_buildings=None, not_ready_buildings=None):
        """
        Updates tech progress by updating current step in tech path.

        :return: updated curr_step
        """

        if not ready_buildings:
            ready_buildings = uniques_by_type_id(self.units.structure.ready)
        if not not_ready_buildings:
            not_ready_buildings = uniques_by_type_id(self.units.structure.not_ready)
        curr_step = self.tech_goals[tech_goal]["step"]

        progress = self.check_tech_progress(tech_goal, ready_buildings, not_ready_buildings)

        if progress == 2 or progress == 0:  # current step ready or no progress
            whole_path = id_map.get_tech_path_needed(self.race, tech_goal)
            ready_types = [b.type_id for b in ready_buildings]
            available_tech = id_map.get_available_buildings(self.race, ready_types)
            available_new = set(available_tech).difference(ready_types)

            # TODO: make sure the bot wont crash if there is wrong tech goal for Race (such as hydraliskden for protoss)
            available_need = available_new.intersection(whole_path)
            if len(available_need) > 0:
                self.tech_goals[tech_goal]["step"] = available_need.pop()  # assume one path for tech
                curr_step = self.tech_goals[tech_goal]["step"]
            else:  # no more tech to go further // tech reached
                # start building units
                pass

        elif progress == 1:  # tech progressing
            pass

        return curr_step

    def check_tech_progress(self, tech_goal, ready_buildings=None, not_ready_buildings=None):
        """
        Checks if progress has been made in the tech.

        :return: 2,1,0 - tech progress: (step) ready, in progress, no progress
        """
        curr_step = self.tech_goals[tech_goal]["step"]

        if not ready_buildings:
            ready_buildings = set(self.units.structure.ready)

        if not not_ready_buildings:
            not_ready_buildings = set(self.units.structure.not_ready)

        for b in ready_buildings:
            found = compare_building_type(curr_step, b)
            if found:
                return 2

        #exception handling - MORPH_BUILDINGS
        if curr_step in id_map.MORPH_BUILDINGS:
            found = self.check_morphing_tech(curr_step)
            if found:  # could return found as well for this instance
                return 1
        else:
            for b in not_ready_buildings:
                found = compare_building_type(curr_step, b)
                if found:
                    return 1

        return 0

    def check_morphing_tech(self, tech):
        """
        Checks tech progress for tech building which are upgraded for further tech.

        (Such buildings are hatcheries, lairs, spires...)
        Only needed when building is morphing into higher tier.
        :return: 1,0 - tech progress: in progress, no progress
        """
        needed = id_map.MORPH_BUILDINGS[tech]
        # TODO: take dynamically from morph building and assign the right ability too
        #  (latter not currently implemented in racial)
        in_progress = False

        gspire = UnitTypeId.GREATERSPIRE
        hive = UnitTypeId.HIVE
        lair = UnitTypeId.LAIR

        if tech is gspire:
            spires = self.units.of_type(needed).ready
            ability = AbilityId.UPGRADETOGREATERSPIRE_GREATERSPIRE
            in_progress = ability_in_orders_for_any_unit(ability, spires)

        elif tech is hive:
            lairs = self.units.of_type(needed).ready
            ability = AbilityId.UPGRADETOHIVE_HIVE
            in_progress = ability_in_orders_for_any_unit(ability, lairs)

        elif tech is lair:
            hatches = self.units.of_type(needed).ready
            ability = AbilityId.UPGRADETOLAIR_LAIR
            in_progress = ability_in_orders_for_any_unit(ability, hatches)

        else:  # tech exception not implemented
            print(f"WARNING: Trying to check tech {tech} in morphing techs ( - not implemented)")
            print(f"\ttrying to remove {tech} for tech list")
            self.tech_goals.pop(tech)
            in_progress = True  # inform calling function "everything is fine"
            pass

        if in_progress:
            return 1
        else:
            return 0

    async def chat_defending_taunt(self, enemy_position, defender_amount, enemy_hp, own_hp, enemy_dps, own_dps):
        if not self.def_msg_flag:
            if (len(self.def_force_tags) >= defender_amount) and len(self.def_force_tags) > 0:
                await self.chat_send(f"You attack at: {enemy_position}")
                await self.chat_send(f"All Hands On The Deck (flex) (flex)")
            else:  # defend with all
                await self.chat_send(f"Location: {enemy_position}")
                await self.chat_send(f"You Attack with: {len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps")
                await self.chat_send(f"I Defend with: {defender_amount} defenders - {own_hp} total hp, {own_dps} total dps")
            self.def_msg_flag = 2

    async def chat_retreating(self, attack_position, enemy_hp, enemy_dps):
        if len(self.def_force_tags) > 0:
            if not self.def_msg_flag:
                await self.chat_send(f"Your attack is too much atm - Retreating")
                self.def_msg_flag = 8
        elif not self.def_msg_flag:
            await self.chat_send(f"Not defending your attack at {attack_position}")
            self.def_msg_flag = 8

    # TECH GOALS PER RACE:

    def set_air_tech_goal(self):
        """Adds air tech as goal for the bot."""
        #add air tech
        # TODO: find more efficient way to do following operations
        prod_building = list(id_map.AIR_TECH[self.race])[0]  # don't "pop" from racial.AIR_TECH
        if self.race == Race.Terran:
            goal_unit = list(id_map.goal_air_unit(self.race))[1]  # don't "pop"
            goal_building = UnitTypeId.FUSIONCORE
        else:
            goal_unit = list(id_map.goal_air_unit(self.race))[0]
            goal_building = prod_building
        if goal_building not in self.tech_goals:
            self.set_tech_goal(goal_building, self.th_type, prod_building, 2, goal_unit)  # air tech

    # MACRO FOR DIFFERENT RACES:

    async def macro_train_units(self):
        """General method to train available units in tech goals."""
        actions = []
        for goal in self.tech_goals:
            if self.units.structure.ready.of_type(goal).amount > 0: #if the building is ready
                unit = self.tech_goals[goal]["unit"]
                action = await self.macro_bot.train_unit(goal, unit)
                if action:
                    actions.extend(action)
        return actions

    async def macro_boost(self):
        """General method for repetitive macro tasks."""
        actions = []
        # if isinstance(self.macro_bot, terran.TerranMacroBot) \
        #         and self.get_time_in_seconds() > 600 \
        #         and self.macro_bot.save_scans != 2:
        #     curr = self.macro_bot.save_scans
        #     self.macro_bot.save_scans = 2
        #     new = self.macro_bot.save_scans
        #     if curr != new:
        #         print(f"Saving scans changed --> prev: {curr}, new {new}")

        actions.extend(await self.macro_bot.general_macro())

        if self.minerals > 1200 and self.supply_used > 180 or self.race is not Race.Zerg:
            self.set_air_tech_goal()

        if self.minerals > 1450 and self.race is not Race.Zerg:
            for goal in self.tech_goals:
                if goal in {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.BARRACKS}:
                    if self.tech_goals[goal]["count"] < 10:
                        self.tech_goals[goal]["count"] += 1
                elif self.tech_goals[goal]["count"] < 3:
                    self.tech_goals[goal]["count"] += 1

        if self.tech_switch and (self.minerals > 480 or self.supply_used < 60):  # or self.known_enemy_units.not_structure.amount >= 10):
            actions.extend(await self.macro_train_units())

        return actions


def ability_in_orders_for_any_unit(ability, units):
    """Checks if any given unit  has given ability in their orders."""
    for u in units:
        if not u.noqueue:
            if u.orders[0].ability.id is ability:
                return True
    return False


def ability_in_orders_for_all_units(ability, units):
    """Checks if every given unit  has given ability in their orders."""
    for u in units:
        if not u.noqueue:
            if u.orders[0].ability.id is ability:
                continue
        break
    else:
        return True
    return False


def check_building_type_similarity(b_type, buildings):
    """Checks if any one given building is also of given building type."""
    for b in buildings:
        found = compare_building_type(b_type, b)
        if found:
            return True
    else:  # not found
        return False


def compare_building_type(building_type, building):
    """Compares UnitTypeId with given building."""
    if building_type == building.type_id:
        return True
    if building.unit_alias:
        if building_type is building.unit_alias:
            return True
    if building.tech_alias:
        if building_type in building.tech_alias:
            return True
    return False


def uniques_by_type_id(unit_list):
    """Returns list of units with different (unique) UnitTypeId for each."""

    # getting unique attribute idea from:
    # https://stackoverflow.com/questions/17347678/list-of-objects-with-a-unique-attribute
    return dict((obj.type_id, obj) for obj in unit_list).values()


def check_if_mechanical(unit_list):
    """Returns repairable (Terran) units and structures in given list."""

    is_mech = unit_list.structure
    is_mech.extend(unit_list.not_structure.of_type(id_map.MECHANICALS))
    return is_mech

