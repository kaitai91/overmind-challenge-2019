#TODO: Ideas:
# add scouting, reactions for scout info
# change iteration to game time references (under testing) <-- game time is a bit off but reasonable atm
# improve tech tree (and add function: get_tech_needed(BUILDING/UNIT) )
# use numpy (after the challenge is over - not supported there)

#TODO: flags/vars
# make __init__ and put object variables in that (DONE)
# put all similar variables into collections
# ideas:
# make flags in one variable and reduce everything at once each step (numpy needed)
# change (tag data) variables in to numpy arrays for quicker operations
# make/use heatmap for enemy locations to defend (maybe with connected components)

#TODO: macro:
# save researched tech somewhere and fetch trainable units from there (for more efficient training esp. with zerg)
# add more production facilities / tech / whatever when close to 200/200 with big resource bank
# make defence better by updating defence calculations and reinforcing when needed
# take air hp into account in enemy att_str_calc
# ideas:
# multiple attack/defence groups
# implement anti-air defence
# make priority queue for different macro actions
# decide which actions can be skipped every now and then
# make priority decision based on game state (consider this with/instead of timed functions)
# prioritizing buildings/tech/workers/army <-- implement this

#TODO: micro:
# IMPORTANT: Viking micro (mode change depending on enemy unit at minimum - air/ground)
# Add constraint to remove attack group once you got to the target point and no enemies available (DONE)
# fix retreat (micro) for other than workers
# add unit micro for ranged units
# prioritize low hp/ high dps enemies in the attack range
# make micro more efficient with big army (take nearby units into account when moving)
# ideas:
# add unitType specific micro
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
if __name__ == '__main__':
    import racial
    import unit_micro
else:
    import bot.racial as racial
    from bot.unit_micro import MICRO_BY_TYPE

# STATIC VARS:

CHANGELING = {UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGZEALOT,
              UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD,
              UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELINGZERGLINGWINGS}

WORKER_UPPER_LIMIT = 99

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        super().__init__()
        self.enemy_att_str_prev = {"hp": 0, "g_dps": 0, "pos": None}
        self.enemy_att_str_curr = {"hp": 0, "g_dps": 0, "pos": None}
        self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": None}
        self.attacking_enemy_units = []

        self.clock = 0

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
        # goal[building_type] = {"count": (int), "unit": (unit_type)}
        # goal[building_type] = {"step": (UnitTypeId)", "prod": (UnitTypeId), "count": (int), "unit": (unit_type)}
        # step is used to track tech progress,
        # prod is the goal production building (for specified unit)
        # count is suggested number of production buildings,
        # unit is the type of unit wanted from


        # self.expansion_locations = [] #in super, not needed here

    def _prepare_first_step(self):
        self.expansion_locations
        #print(self.expansion_locations.keys())
        return super()._prepare_first_step()

    def set_tech_goal(self, goal_tech, current_tech, goal_prod_building, prod_b_count, goal_unit):
        if self.race == Race.Zerg: #for zerg production is always in hatcheries
            goal_prod_building = self.th_type
        self.tech_goals[goal_tech] = {"step": current_tech,
                                      "prod": goal_prod_building,
                                      "count": prod_b_count,
                                      "unit": goal_unit}

    def on_start(self):
        self.th_type = racial.TOWN_HALL_TYPES[self.race]
        self.w_type = racial.WORKER_TYPES[self.race]
        self.prod_bs = racial.PROD_B_TYPES[self.race]
        self.s_args = racial.get_supply_args(self.race) #<- method
        self.tech_tree = racial.TECH_TREE[self.race]
        self.gas_type = racial.GAS_BUILDINGS[self.race]

        # print(self.tech_goals)

    async def on_step(self, iteration):

        #helper vars
        actions = []

        self.iteration = iteration

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
        self.repair_flag = max(0, self.repair_flag-clock_diff)

        # if self.d_task:  # wait task to finish to avoid timeouts (does this actually work?)
        #     return

        # Reinforce defence
        self.enemy_att_str_prev = self.enemy_att_str_curr.copy()
        self.enemy_att_str_curr = self.calc_enemy_att_str()
        enemy_att_got_stronger = self.enemy_att_str_max["hp"] < self.enemy_att_str_curr["hp"] and \
                                self.enemy_att_str_max["g_dps"] < self.enemy_att_str_curr["g_dps"]

        enemy_is_as_strong = self.enemy_att_str_max["hp"] <= self.enemy_att_str_curr["hp"] and \
                                self.enemy_att_str_max["g_dps"] <= self.enemy_att_str_curr["g_dps"]

        if enemy_att_got_stronger:
            self.enemy_att_str_save = 20
            # print("max att preserved")

        if not self.enemy_att_str_save:
            # if self.enemy_att_str_max["hp"] > 0.9:
                # print("max reset")
            #never erase enemy last position (where they did attack last time)
            self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": self.enemy_att_str_max["pos"]}

        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev
        m = self.enemy_att_str_max
        self.enemy_att_str_max["hp"] = max(c["hp"], p["hp"], m["hp"])
        self.enemy_att_str_max["g_dps"] = max(c["g_dps"], p["g_dps"], m["g_dps"])
        if c["pos"]:
           # print(self.enemy_att_str_max)
            self.enemy_att_str_max["pos"] = c["pos"]  # use most recent position

        # if enemy_att_got_stronger:
        if m["pos"]:
            await self.reinforce_defence()

        if self.supply_left < self.townhalls.ready.amount and not self.pend_supply_flag and self.supply_cap < 200:
            self.pend_supply_flag = 1
        else:
            self.pend_supply_flag = 0

        #USUAL TASKS


        # check expand on it's own iteration
        if self.clock >= 45 and not self.expand_flag and self.minerals > 250 and self.workers.ready.amount > 0:
            # self.d_task = True
            await self.expand() #<-- set flag inside that method
            # self.d_task = False
            # return

        if self.clock >= 60 and not self.w_dist_flag:
            self.w_dist_flag = 0.8
            # self.d_task = True
            await self.distribute_workers()
            # self.d_task = False
            # return

        if not self.racial_macro_flag:
            actions.extend(self.macro_boost(self.race))
            self.racial_macro_flag = .97 #arbitrary cooldown

        if self.minerals > 150 and (self.vespene / (self.minerals+1)) <= 0.6: #vespene count less than 60% of minerals
            #following snippet adpoted from cyclone_push.py
            for a in self.units(self.gas_type):
                if a.assigned_harvesters < a.ideal_harvesters:
                    w = self.workers.closer_than(5, a)
                    if w.exists:
                        actions.append(w.random.gather(a))

            #specified refinery counts for certain amount of workers
            if (self.vespene / (self.minerals+1)) <= 0.5 and self.minerals >= 800:
                await self.check_and_build_gas() #add extra gas if gas-starving


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
                    else:
                        for tech in self.tech_goals:
                            await self.manage_tech(tech)
                    self.tech_flag = 5

        await self.build_supply()
        actions.extend(self.manage_idle_workers())
        if self.pend_supply_flag != 1:
            if self.workers.amount < (self.worker_limit - self.townhalls.amount):
                await self.train_workers()
            # elif self.minerals > 1000 and self.workers.amount < WORKER_UPPER_LIMIT:  #hard coded limit for workers
            #     await self.train_workers()


        #FOR MICRO
        self.manage_att_def_groups()

        #micro every max(0.1,clock_diff) if you have force
        if len(self.attack_force_tags) > 0 and (min(0.1, clock_diff) <= (self.clock - int(self.clock)) % max(0.1, clock_diff)): #micro every 0.1 second
        #if len(self.attack_force_tags) > 0 and (min(1,clock_diff) <= (self.clock - int(self.clock))):  # micro every second (capping if lags)
            # if int(self.clock) % 16 == 15 and clock_diff >= self.clock-int(self.clock):  #max once a second once in 33s
            #     await self.chat_send(f"Attacking with: {len(self.attack_force_tags)}")

            await self.attack_unit_micro()

        if len(self.def_force_tags) > 0 and (min(0.1, clock_diff) <= (self.clock - int(self.clock))):
            await self.defend_unit_micro()

        if int(self.clock) % 61 == 57 and clock_diff >= self.clock-int(self.clock):
            await self.chat_send(f"Elapsed game time: {int(self.clock/60)} min, {int(self.clock)%60}s")

        #killed_base here, since not used anywhere else.. move if needed
        if not self.killed_start_base:
            shortest_dist = self.units.closest_distance_to(self.enemy_start_locations[0])
            if shortest_dist <= 2:
                # print("killed enemy starting base")
                self.killed_start_base = 1

        if self.supply_used - self.workers.amount > 6 and not self.attack_flag and \
                ((len(self.attack_force_tags)+len(self.def_force_tags)) <
                 (self.units.not_structure.not_flying.amount/2 + 1)):

            # "fixed": uncomment to have simplest winning strategy! LOL
            # target = None  #not needed
            if not self.killed_start_base:
                target = self.enemy_start_locations[0]
                enemy_buildings = self.known_enemy_structures().not_flying
                if enemy_buildings.amount > 0:
                    target = enemy_buildings.closest_to(self.townhalls.random.position).position
                self.attack_flag = 120  # seconds
            elif len(self.known_enemy_structures.not_flying) > 0:
                target = self.known_enemy_structures.not_flying[0].position
                self.attack_flag = 60  # seconds
            else:
                possible_targets = list(self.expansion_locations.keys())
                number = len(possible_targets)
                #print(number)
                target = possible_targets[self.killed_start_base % number]
                #print(target)
                self.killed_start_base += 1
                #LCM for base counts 4-13 = 360360
                if self.killed_start_base > 360360*2:#<-not realistic to happen :D
                    self.killed_start_base %= 360360
                self.attack_flag = 10  # seconds
            if self.attack_flag > 20:
                army = self.units.not_structure.exclude_type([self.w_type, UnitTypeId.OVERLORD, UnitTypeId.MULE, UnitTypeId.QUEEN])
                actions.extend(self.issue_group_attack(army, target))
                if army.amount > 4:
                    actions.extend(self.issue_group_attack(army, target))

                excess_workers = self.workers.amount - min(len(self.owned_expansions) * 29 + 1, 89)
                if excess_workers > 0 and self.workers.amount > 0:
                    actions.extend(self.issue_worker_attack(target, (excess_workers / self.workers.amount)))
            else: #scout attack location

                army = self.units.not_structure.exclude_type([self.w_type, UnitTypeId.OVERLORD, UnitTypeId.MULE, UnitTypeId.QUEEN])
                if army.amount > 8:
                    group_size = max(4, army.amount)
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = army.prefer_close_to(target)[:group_size]
                    actions.extend(self.issue_group_attack(random_scout_squad, target))

                elif self.workers.amount > 15:
                    group_size = max(4, int(self.workers.amount*0.25)+1)
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = self.workers.filter(lambda w: not w.is_constructing_scv).\
                                             prefer_close_to(target)[:group_size]
                    actions.extend(self.issue_group_attack(random_scout_squad, target))

        if not self.tech_switch and self.supply_used > 21:
            self.tech_switch = 1
            self.set_racial_tech_goals(self.race)

            await self.chat_send(f"Initializing tech advancement procedures")

        if self.supply_used > 170: #attack when no units attacking and close to max supply
            if len(self.attack_force_tags) < 70:
                self.attack_flag = min(self.attack_flag, 37)  #attack soon
            else:
                self.attack_flag = min(self.attack_flag, 20.2)

        #UNIQUE TASKS
        if iteration == 1:
            await self.chat_send(f"(glhf)")

            # scout
            target = self.enemy_start_locations[0]
            actions.extend(self.issue_group_attack(self.workers.ready.random_group_of(2), target))
            # print(self.workers.random.ground_range)

        #if iteration == 1:
        #    await self.train_workers()

        # if iteration == 2:
        #     await self.chat_send(f"Main building is {self.townhalls[0].health}")

        # if iteration == 5:
        #     #await self.chat_send(f"Debug args: {self.s_args}")
        #     #await self.chat_send(f"time: {self.getTimeInSeconds()}")
        #     # await self.chat_send(f"I'm playing {self.race}")
        #
        # if iteration == 7:
        #     #await self.chat_send(f"time:{self.getTimeInSeconds()}")
        #     await self.chat_send(f"You are {self.enemy_race}")

        await self.do_actions(actions)

    async def expand(self):
        # expand
        if (self.units(self.th_type).amount < 8 or self.workers.amount > 75) and self.can_afford(self.th_type):
            self.expand_flag = 5
            if self.already_pending(self.th_type) < 3:  # expand "only" 3 locations at once
                await self.expand_now(closest_to=self.workers.random.position)
                if self.townhalls.amount < 4:
                    await self.chat_send(f"Trying to expand!")
        # not yet
        else:
            self.expand_flag = 1  # <-- try again soon

    #edited snippet from bot_ai
    # async def expand_now(self, building: UnitTypeId = None, max_distance: Union[int, float] = 10,
    #                      location: Optional[Point2] = None, closest_to: Optional[Point2] = None):
    async def expand_now(self, building=None, max_distance=10,
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
        for el in self.expansion_locations:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if closest_to:
                startp = closest_to
            else:
                startp = self._game_info.player_start_location
            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest

    def adjust_worker_limit(self):
        self.worker_limit = max(24, min(len(self.owned_expansions) * 24, 88))
        if 3000 <= self.minerals:
            self.worker_limit = 44
        elif self.worker_limit == 44 and self.minerals <= 1000:
            self.worker_limit = 89
        elif self.tech_switch:
            self.worker_limit = max(24, min(len(self.owned_expansions) * 24, 88))


    async def train_workers(self):
        actions = []
        for th in self.townhalls.ready.noqueue:
            if self.can_afford(self.w_type):
                if self.race == Race.Zerg:
                    if self.units(self.s_args[0]).exists:  # if bot has larva
                        actions.append(self.units(self.s_args[0]).random.train(self.w_type))
                else:
                    actions.append(th.train(self.w_type))
        await self.do_actions(actions)

    def train_units(self, building_type, unit_type, max_amount=None):
        actions = []
        if max_amount:
            buildings = self.units(building_type).ready.noqueue.random_group_of(max_amount)
        else:
            buildings = self.units(building_type).ready.noqueue
        for prod_b in buildings:
            if self.can_afford(unit_type):
                if self.race == Race.Zerg:
                    if self.units(self.s_args[0]).exists:  # if bot has larva
                        actions.append(self.units(self.s_args[0]).random.train(unit_type))
                else:
                    actions.append(prod_b.train(unit_type))
        return actions

    def morph_unit(self, target_unit, alt=False):
        #so far alt is used only for overlord transport morph - not tested
        if alt:
            return target_unit(racial.MORPH2[target_unit.type_id])
        return target_unit(racial.MORPH[target_unit.type_id])

    def morph_units(self, target_units):
        actions = []

        for unit in target_units:
            action = self.morph_unit(unit)
            if action:
                actions.append(action)
        return actions

    def morph_by_id(self, type_id, max_amount=0): #max 0 --> all
        targets = self.units.of_type(type_id).ready
        if targets.amount < 1:
            return []
        if max_amount:
            targets.random_group_of(min(targets.amount, max_amount))
        return self.morph_units(targets)

    async def build_supply(self):
        if self.supply_cap == 200:
            return #no more supply needed / useful
        ths = self.townhalls.ready
        b_buildings = self.units.of_type(self.prod_bs)  # <- returns dict
        if self.race == Race.Zerg:
            amount = len(ths)
        else:
            amount = len(ths) + len(b_buildings)

        if self.iteration % 2300 == 2299:
            await self.chat_send(f"I have {amount} Production buildings")
        if ths.exists:
            th = ths.first
            if self.supply_left < len(ths) + 4 and self.already_pending(self.s_args[1]) < min(4, amount):
                if self.can_afford(self.s_args[1]):
                    if self.race == Race.Zerg:
                        actions = []
                        if self.units(self.s_args[0]).exists:  # if bot has larva
                            actions.append(self.units(self.s_args[0]).random.train(self.s_args[1]))
                            await self.do_actions(actions)

                    else:
                        await self.build(self.s_args[1], near=th.position.towards(self.game_info.map_center, 8))

                    if self.pend_supply_flag == 1:
                        self.pend_supply_flag = 2

    def geysers_needed(self):
        w_amount = self.workers.amount
        if self.race is not Race.Zerg:
            if w_amount >= 66:
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
                return geyser_amount
        return 0

    async def build_gas(self, max_amount=3):
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
                            # actions.append(self.units(self.s_args[0]).random.train(unit_type))
                            # await self.build(self.gas_type, vg)
                            actions.append(w.build(self.gas_type, vg))
                            added +=1
                            #w.build
                    if added >=max_amount:
                        break
                if added >= max_amount:
                    break

        await self.do_actions(actions)
        #print(actions)
        #return actions

    async def check_and_build_gas(self):
        needed = self.geysers_needed()
        if needed:
            await self.build_gas(needed)

    def calc_enemy_att_str(self):  # calculate enemy attack strength
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
                if dist < max(12, enemy.ground_range):  # max(16, enemy.radar_range, (enemy.ground_range) + 5):
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

        #if enemy has been seen, use the last location as enemy position
        if not enemy_position: #is none
            if self.enemy_att_str_curr["pos"]:
                enemy_position = self.enemy_att_str_curr["pos"]
            elif self.enemy_att_str_max["pos"]:
                enemy_position = self.enemy_att_str_max["pos"]
                # print("enemy position taken from max")
        enemy_att_str = {"hp": total_hp, "g_dps": enemy_g_dps, "pos": enemy_position}
        return enemy_att_str

    def manage_att_def_groups(self):
        tags = [unit.tag for unit in self.units.not_structure.ready]  # get tags for units TODO: include army units
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


    async def reinforce_defence(self):

        #shorten names
        m = self.enemy_att_str_max
        if not m["pos"]:
            # print("no position available - reinforce defence later")
            return

        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev

        #changes: (differences)
        d_hp = max(0, c["hp"]-p["hp"])
        d_g_dps = max(0, c["g_dps"]-p["g_dps"])

        #d_hp = m["hp"]-max(c["hp"], p["hp"])
        #d_g_dps = m["g_dps"]-max(c["g_dps"], p["g_dps"])
        position = c["pos"]
        if len(self.attacking_enemy_units) > 0 and (d_hp > 0 or d_g_dps > 0 or len(self.def_force_tags) < 1):
            #await self.assign_defence(d_hp, d_g_dps, position)
            await self.assign_defence(m["hp"], m["g_dps"], m["pos"])

        # #not working (is_attacking) maybe only with own units...
        # if closest_enemy:
        #     if closest_enemy.is_attacking:
        #         await self.chat_send(f"Enemy{closest_enemy.type_id()}is attacking!")


    async def assign_def_groups(self, enemy_groups):
        #To be implemented
        pass

    async def assign_defence(self, enemy_hp, enemy_dps, enemy_position):

        #print("trying to assign defence")
        army = self.units.ready.tags_not_in(self.def_force_tags).\
            not_structure.exclude_type([self.w_type, UnitTypeId.QUEEN]).\
                                       filter(lambda u: u.can_attack)
        #sort workers: high hp and close distance preferred
        workers = self.workers.ready.tags_not_in(self.def_force_tags).filter(lambda w: not w.is_constructing_scv).\
            sorted(lambda w: -(w.health+w.shield)).prefer_close_to(enemy_position)
        #combined_tags = set(self.attack_force_tags.keys()).union(set(self.def_force_tags.keys()))

        #TODO: better way to assign and track enemy

        if len(self.owned_expansions) >= 3:
            workers = workers.closer_than(10, enemy_position)  # dont assign workers to defend
            self.w_dist_flag = 10  # wait for 10s to re distribute workers
            #TODO: just remove this townhall temporarily from worker distribution function
            # (self.units = self.units.exclude_tag(tag_of_building) in the beginning of step)

        if len(army)+len(workers) < 1:
            # print("no army or workers")
            return

        actions = []

        defenders, own_dps, own_hp = self.create_defence_group(army, enemy_dps, enemy_hp, workers)

        #do we have enough to defend
        if enemy_dps < 10:
            condition = True
        else:
            condition = (own_hp >= enemy_hp and own_dps >= enemy_dps) or self.townhalls.amount < 2  # or self.clock<120
        if condition and len(defenders) > 0:
            actions.extend(self.issue_group_defence(defenders, enemy_position))
            # await self.chat_defending_taunt(enemy_position, workers.amount+army.amount, enemy_hp, own_hp, enemy_dps, own_dps)

        # retreat from strong enemy
        else:
            for defender in self.def_force_tags:
                self.def_force_tags[defender]["retreat"] = 5
            # await self.chat_retreating(enemy_position, enemy_hp, enemy_dps)

        if len(actions) > 0:
            await self.do_actions(actions)

    def create_defence_group(self, army, enemy_dps, enemy_hp, workers):
        own_hp = 0
        own_dps = 0
        defenders = []
        if enemy_dps < 4:  # 1 worker or smthing like that
            # defenders, own_hp, own_dps = self.create_army_group(army, enemy_hp, enemy_dps)
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
            # more_needed = own_hp < (enemy_hp + 1) or own_dps < (enemy_dps + 1) #try it out
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
    def neighbors4(self, position, distance=1):
        p = position
        d = distance
        return {
            position_imported.Point2((p.x - d, p.y)),
            position_imported.Point2((p.x + d, p.y)),
            position_imported.Point2((p.x, p.y - d)),
            position_imported.Point2((p.x, p.y + d)),
        }

    # stolen and modified from position.py
    def neighbors8(self, position, distance=1):
        p = position
        d = distance
        return self.neighbors4(position, distance) | {
            position_imported.Point2((p.x - d, p.y - d)),
            position_imported.Point2((p.x - d, p.y + d)),
            position_imported.Point2((p.x + d, p.y - d)),
            position_imported.Point2((p.x + d, p.y + d)),
        }

    # this checks if a ground unit can walk on a Point2 position
    def inPathingGrid(self, pos):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[(pos)] != 0

    def ranged_unit_micro(self, unit):
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

        if unit.health_percentage < 2 / 5 and enemyThreatsClose.exists:
            retreatPoints = self.neighbors8(unit.position, distance=2) | self.neighbors8(unit.position, distance=4)
            # filter points that are pathable
            retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
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

        # attack is on cooldown, check if grenade is on cooldown, if not then throw it to furthest enemy in range 5
        # use this for different units' special attacks and abilities
        # reaperGrenadeRange = self._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
        # enemyGroundUnitsInGrenadeRange = self.known_enemy_units.not_structure.not_flying.exclude_type(
        #     [UnitTypeId.LARVA, UnitTypeId.EGG]).closer_than(reaperGrenadeRange, unit)
        # if enemyGroundUnitsInGrenadeRange.exists and (unit.is_attacking or unit.is_moving):
        #     # if AbilityId.KD8CHARGE_KD8CHARGE in abilities, we check that to see if the reaper grenade is off cooldown
        #     abilities = (await self.get_available_abilities(unit))
        #     enemyGroundUnitsInGrenadeRange = enemyGroundUnitsInGrenadeRange.sorted(lambda x: x.distance_to(unit),
        #                                                                            reverse=True)
        #     furthestEnemy = None
        #     for enemy in enemyGroundUnitsInGrenadeRange:
        #         if await self.can_cast(unit, AbilityId.KD8CHARGE_KD8CHARGE, enemy, cached_abilities_of_unit=abilities):
        #             furthestEnemy = enemy
        #             break
        #     if furthestEnemy:
        #         self.combinedActions.append(unit(AbilityId.KD8CHARGE_KD8CHARGE, furthestEnemy))
        #         return  # continue for loop, don't execute any of the following


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
            retreatPoints = self.neighbors8(unit.position, distance=2) | self.neighbors8(unit.position, distance=4)
            # filter points that are pathable by a reaper
            retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
            if retreatPoints:
                closestEnemy = enemyThreatsVeryClose.closest_to(unit)
                retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(closestEnemy) - x.distance_to(unit))
                # retreatPoint = closestEnemy.position.furthest(retreatPoints)
                action = unit.move(retreatPoint)
                return action  # don't execute any of the following

        # move to nearest enemy ground unit/building because no enemy unit is closer than 5
        allEnemyGroundUnits = self.known_enemy_units.not_flying
        if allEnemyGroundUnits.exists:
            closestEnemy = allEnemyGroundUnits.closest_to(unit)
            action = unit.move(closestEnemy)
            return action  # don't execute any of the following

        # move to enemy start location if no enemy buildings have been seen
        # TODO: do something else (return None and do stuff in general micro (just move for example)
        #action = unit.move(target)  # consider using random.choise
        return action

    def unit_retreat(self, unit, target):
            mf = self.state.mineral_field.closest_to(target)
            if unit.type_id is self.w_type and mf:  # if worker
                if unit.is_carrying_minerals or unit.is_carrying_vespene:
                    return unit(AbilityId.SMART, target)
                mf = self.state.mineral_field.closest_to(target)
                return unit.gather(mf)
            else:
                return unit.move(target)

    def general_micro(self, unit_tag, tags, hp_lower_bound=0.1):
        action = None
        unit = self.units.by_tag(unit_tag)
        tags[unit_tag]["hp_curr"] = unit.health + unit.shield  # update current hp
        ret = tags[unit_tag]["retreat"]
        hpc = tags[unit_tag]["hp_curr"]
        hpp = tags[unit_tag]["hp_prev"]
        max_hp_sh = unit.health_max + unit.shield_max

        # check if low hp or retreating flag (townhall is retreating point) --> retreat
        no_shield = not unit.shield > unit.health
        if (ret > 4 or (hpc < hp_lower_bound and no_shield)) and self.townhalls.ready.amount > 0:
            if unit.is_burrowed:
                action = unit(AbilityId.BURROWUP)
            else:
                action = self.unit_retreat(unit, self.townhalls.ready.random)
            return action, True  # tb_removed.append(unit_tag)

        # check if less than 50% hp and lost hp since last tick (townhall is retreating point)
        # --> fall back and come back later
        # if unit has shield use shield as indicator
        hp_less_than_half_more_than_lower_limit = hpc < (max(min(max_hp_sh / 2, unit.health_max), hp_lower_bound))

        if (not no_shield or hp_less_than_half_more_than_lower_limit) and hpc < hpp:
            # if hpc < (max(min(max_hp_sh/2, unit.health_max), min_hp)) and hpc < hpp:
            if self.townhalls.amount > 0:
                if unit.is_burrowed:
                    action = unit(AbilityId.BURROWUP)
                else:
                    action = self.unit_retreat(unit, self.townhalls.random)
                tags[unit_tag]["retreat"] += 1
                return action, False
            tags[unit_tag]["retreat"] += 1

        # find out a good way for this..
        # action = None

        if unit.type_id in MICRO_BY_TYPE:
            # print("using specific micro function")
            close_a_enemies = self.known_enemy_units.flying
            close_g_enemies = self.known_enemy_units.not_flying.exclude_type(CHANGELING)
            known_enemies = close_a_enemies or close_g_enemies
            # TODO: find out why this bugs units
            # if not known_enemies.exists:
            #     known_enemies = self.known_enemy_structures.not_flying
            action = MICRO_BY_TYPE[unit.type_id](unit, known_enemies)# or close_enemy_structures)  # "additive or"
            # print(action)
            if action:
                return action, False

        if unit.ground_range >= 1.1:
            action = self.ranged_unit_micro(unit)
            if action:
                return action, False

        return action, False

    async def attack_unit_micro(self):
        """"""
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
            close_g_enemies = self.known_enemy_units.not_flying.closer_than(16, unit.position).exclude_type(CHANGELING)
            close_enemies = 0
            if unit.can_attack_air:
                close_enemies += close_a_enemies.amount
            if unit.can_attack_ground:
                close_enemies += close_g_enemies.amount

            #get closer to target (location based attack move)
            target = tags[tg]["target"]
            if unit.distance_to(target) >= 25 and close_enemies < 2:
                actions.append(unit.move(target))
            elif (unit.distance_to(target) >= 2 and tags[tg]["retreat"] < 5): #or len(close_enemies) > 0:
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
            #worker.health_prev = worker.health

        for tag in tb_removed:
            del(self.attack_force_tags[tag])

        await self.do_actions(actions)

    async def defend_unit_micro(self):
        """"""
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
            close_enemies = self.known_enemy_units.not_flying.closer_than(unit.sight_range, unit.position).exclude_type(CHANGELING).sorted_by_distance_to(unit)
            target = tags[tg]["target"]
            if close_enemies.amount > 0:
                #pursue only so far:
                if close_enemies[0].distance_to(orig) < 20: #changed this
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

            # test - removing this maybe not needed
            # if len(self.def_force_tags) >= workers.amount + army.amount:
            #     tags[tg]["retreat"] = 0  #dont retreat when everyone is needed in defence

            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            max_hp_sh = unit.health_max + unit.shield_max
            if ret and hpc > (max_hp_sh/2): #hp is back up
                tags[tg]["retreat"] = 0



            tags[tg]["hp_prev"] = hpc = tags[tg]["hp_curr"] + unit.shield
            #worker.health_prev = worker.health

        for tag in tb_removed:
            del(self.def_force_tags[tag])

        await self.do_actions(actions)

#HELPERS

    def manage_idle_workers(self):
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
                actions.extend(self.issue_worker_attack(target))
        else:
            self.expand_flag = 0

        return actions

    def get_time_in_seconds(self):
        # returns real time if game is played on "faster"
        return self.state.game_loop * 0.725 * (1 / 16)

    def issue_worker_attack(self, target, percentage=1.0):
        return self.issue_group_attack(self.workers.random_group_of(
            min(self.workers.amount, int(self.workers.amount*percentage)+1)),
            target)

    def issue_idle_worker_attack(self, target):
        return self.issue_group_attack(self.workers.idle, target)

    def issue_group_attack(self, group, target):
        actions = []
        for unit in group:
            actions.append(self.issue_unit_attack(unit, target))
        return actions

    def issue_unit_attack(self, unit, target):
        action = unit.attack(target)
        retreating = 0
        unit.health_prev = unit.health
        self.attack_force_tags[unit.tag] = {"retreat": retreating,
                                            "hp_curr": unit.health,
                                            "hp_prev": unit.health_prev,
                                            "target": target}
        return action

    def issue_group_defence(self, group, target):
        actions = []
        for unit in group:
            actions.append(self.issue_unit_defence(unit, target))
        return actions

    def issue_unit_defence(self, unit, target):
        action = unit.attack(target)
        orig = target
        retreating = 0
        unit.health_prev = unit.health
        self.def_force_tags[unit.tag] = {"retreat": retreating,
                                         "hp_curr": unit.health,
                                         "hp_prev": unit.health_prev,
                                         "target": target,
                                         "orig_target": orig}
        return action

    async def manage_tech(self, tech_goal):
        actions = []
        old_step = self.tech_goals[tech_goal]["step"]
        ready_buildings = uniques_by_type_id(self.units.structure.ready)
        ready_types = [b.type_id for b in ready_buildings]
        not_ready_buildings = uniques_by_type_id(self.units.structure.not_ready)

        # check tech progress
        curr_step = self.update_tech_progress(tech_goal, ready_buildings, not_ready_buildings)

        # build advancement in tech
        if curr_step in racial.MORPH_BUILDINGS:
            pending = self.already_pending(curr_step, all_units=True)
        else:
            pending = self.already_pending(curr_step)

        if not pending and (curr_step not in ready_types) and self.workers.ready.collecting.amount > 0:  # or old_step != curr_step:
            # print(f"getting {curr_step}")
            # FIXME: might not have any townhalls if the last one got killed (build townhall then) (DONE?)
            if curr_step is self.th_type:  # in case townhall was lost
                await self.expand()
            elif curr_step not in racial.MORPH_BUILDINGS:
                if self.race != Race.Protoss:
                    await self.build(curr_step, near=self.townhalls.ready.random.position.towards(self.game_info.map_center, 5))
                else:
                    await self.build(curr_step, near=self.units.of_type(UnitTypeId.PYLON).ready.random)
            else:
                all_units_of_type = self.units.structure.of_type(racial.MORPH_BUILDINGS[curr_step]).ready.noqueue
                morph_any_of_these = all_units_of_type.random_group_of(all_units_of_type.amount)
                # print(all_units_of_type)
                # print(morph_any_of_these)
                for morph_this in morph_any_of_these:
                    actions.append(self.morph_unit(morph_this))
                    # print(f"morphing{morph_this} into {curr_step}")
                    # print(f"{morph_this.build_progress}")
                    break #only one


        # tech available
        if curr_step == tech_goal:

            prod_goal = self.tech_goals[tech_goal]["prod"]
            # start unit production
            #TODO: remove??
            goal_unit = self.tech_goals[tech_goal]["unit"]
            if goal_unit in racial.MORPH_UNITS:
                goal_unit_prod = racial.MORPH_UNITS[goal_unit]
                # print(goal_unit)
                # print(goal_unit_prod)
            else:
                goal_unit_prod = goal_unit
            # if self.units.of_type(prod_goal).ready.amount > 0:
            #     # start producing units
            #     # for building in self.units.of_type(self.tech_goals[tech_goal]["prod"]).ready:
            #     #     #if building in racial.PROD_B_TYPES[self.race]:  # this check shouldn't be needed
            #     #     await self.train_units(building, goal_unit)
            #
            #     if prod_goal in racial.PROD_B_TYPES[self.race]:  # non-zerg
            #         actions.extend(self.train_units(prod_goal, goal_unit_prod))
            #     else:  # zerg
            #         actions.extend(self.train_units(self.th_type, goal_unit_prod))

            #morph units into goal units if needed
            #TODO: do it in different part
            if goal_unit is not goal_unit_prod:
                actions.extend(self.morph_by_id(goal_unit_prod, 1))

            # add enough production buildings
            already_building = self.already_pending(prod_goal)
            already_ready = self.units.structure.ready.of_type(prod_goal).amount
            needed = self.tech_goals[tech_goal]["count"] - already_building - already_ready
            if needed > 0:
                # print(f"""adding {prod_goal}""")
                candidates = self.workers.prefer_idle
                if candidates.amount < 1:
                    return
                for builder in candidates.random_group_of(min(needed, candidates.amount)):
                    if self.race != Race.Protoss:
                        await self.build(prod_goal, near=self.units.structure.not_flying.ready.random.position.towards(self.game_info.map_center, 5),
                                         unit=builder)
                    else:
                        await self.build(prod_goal, near=self.units.of_type(UnitTypeId.PYLON).ready.random, unit=builder)
        if len(actions) > 0:
            await self.do_actions(actions)

    def update_tech_progress(self, tech_goal, ready_buildings=None, not_ready_buildings=None):
        """
        Updates tech progress by updating current step in tech path
        :param tech_goal: Building to be built
        :return: updated current step
        """

        if not ready_buildings:
            ready_buildings = uniques_by_type_id(self.units.structure.ready)
        if not not_ready_buildings:
            not_ready_buildings = uniques_by_type_id(self.units.structure.not_ready)
        curr_step = self.tech_goals[tech_goal]["step"]

        progress = self.check_tech_progress(tech_goal, ready_buildings, not_ready_buildings)

        if progress == 2 or progress == 0:  # current step ready or no progress
            whole_path = racial.get_tech_path_needed(self.race, tech_goal)
            ready_types = [b.type_id for b in ready_buildings]
            available_tech = racial.get_available_buildings(self.race, ready_types)
            available_new = set(available_tech).difference(ready_types)
            available_need = available_new.intersection(whole_path)
            if len(available_need) > 0:
                self.tech_goals[tech_goal]["step"] = available_need.pop()  # assume one path for tech
                curr_step = self.tech_goals[tech_goal]["step"]
            else:  # no more tech to go further // tech reached
                # print(f"Reached limit in tech {tech_goal} at step {curr_step}")
                # start building units
                pass

        elif progress == 1:  # tech progressing
            pass

        return curr_step

    def check_tech_progress(self, tech_goal, ready_buildings=None, not_ready_buildings=None):
        """

        :param tech_goal:
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
        if curr_step in racial.MORPH_BUILDINGS:
            found = self.check_morphing_tech(curr_step)
            if found: #could return found as well for this instance
                return 1
        else:
            for b in not_ready_buildings:
                found = compare_building_type(curr_step, b)
                if found:
                    return 1

        return 0

    def check_morphing_tech(self, tech):
        needed = racial.MORPH_BUILDINGS[tech]
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

        else:
            pass  #tech exception not implemented

        if in_progress:
            return 1
        else:
            return 0


    async def get_tech(self, tech_goal):
        """
        Tries to progress towards specified tech

        :return:    0: unable to progress towards tech
                    1: progressing towards tech
                    2: tech available
        """

        ready_buildings = self.units.structure.ready
        for b in ready_buildings:
            if tech_goal == b.type_id:
                return 2
            if b.tech_alias:
                if tech_goal in b.tech_alias:
                    return 2

        not_ready_buildings = self.units.structure.not_ready
        #print(f"ready: {ready_buildings}")
        #print(f"not ready: {not_ready_buildings}")
        for b in not_ready_buildings:
            if tech_goal == b.type_id:
                return 1
            if b.tech_alias:
                if tech_goal in b.tech_alias:
                    return 1

        building_types = set()
        for b in ready_buildings:
            building_types.add(b.type_id)
            if b.tech_alias:
                building_types.union(b.tech_alias)

        unfinished_types = set()
        for b in not_ready_buildings:
            unfinished_types.add(b.type_id)
            if b.tech_alias:
                unfinished_types.union(b.tech_alias)

        available_tech = racial.get_available_buildings(self.race, building_types)
        tech_path = racial.get_tech_path_needed(self.race, tech_goal)
        not_having = (set(available_tech).intersection(tech_path)-building_types)-unfinished_types
        # print(not_having)
        if tech_goal not in not_having:
            for b_type in not_having:
                if b_type not in racial.MORPH_BUILDINGS:
                    await self.build(b_type, near=self.townhalls.random)
                else:
                    morph_this = self.units.structure.of_type(racial.MORPH_BUILDINGS[b_type]).ready.random
                    if morph_this:
                        await self.do(morph_this.build(b_type))
                        # print(f"morphing{morph_this} into {b_type}")
                        # print(f"{morph_this.build_progress}")
                    else:
                        break
            else:
                return 1  # all buildings built, progressing towards tech
            return 0  # not sure if progress has been made
        else:
            if tech_goal in racial.PROD_B_TYPES[self.race]: #if we want to high production of units
                for i in range(4):
                    await self.build(tech_goal, near=self.townhalls.random)
                else:
                    return 1

            else:
                await self.build(tech_goal, near=self.townhalls.random)
                return 1
        return 0

    async def chat_defending_taunt(self, enemy_position, defender_amount, enemy_hp, own_hp, enemy_dps, own_dps):
        if not self.def_msg_flag:
            if (len(self.def_force_tags) >= defender_amount) and len(self.def_force_tags) > 0:  # and \
                # (own_hp/max(0.1, enemy_dps) > enemy_hp/max(0.1, own_dps) or self.townhalls.amount <= 2):
                await self.chat_send(f"You attack at: {enemy_position}")
                await self.chat_send(f"All Hands On The Deck (flex) (flex)")
            else:  # defend with all
                await self.chat_send(f"Location: {enemy_position}")
                await self.chat_send(f"You Attack with: {len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps")
                # await self.chat_send(f"I Defend with: {defender_amount} defenders - {own_hp} total hp, {own_dps} total dps")
            self.def_msg_flag = 8

    async def chat_retreating(self, attack_position, enemy_hp, enemy_dps):
        if len(self.def_force_tags) > 0:
            for def_tag in self.def_force_tags:
                self.def_force_tags[def_tag]["retreating"] = 5
            if not self.def_msg_flag:
                await self.chat_send(f"Your attack is too much atm - Retreating")
                self.def_msg_flag = 8
        elif not self.def_msg_flag:
            # await self.chat_send(f"You Attack with: {len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps")
            await self.chat_send(f"Not defending your attack at {attack_position}")
            self.def_msg_flag = 8

    # TECH GOALS PER RACE:

    def set_racial_tech_goals(self, race):
        # some tech
        if race == Race.Protoss:
            self.protoss_tech()
        if race == Race.Terran:
            self.terran_tech()
        if race == Race.Zerg:
            self.zerg_tech_initial()

    def set_air_tech_goal(self):
        #and finally air tech
        goal_building = list(racial.AIR_TECH[self.race])[0]  # don't "pop" from racial.AIR_TECH
        goal_unit = list(racial.goal_air_unit(self.race))[0]
        if goal_building not in self.tech_goals:
            self.set_tech_goal(goal_building, self.th_type, goal_building, 5, goal_unit)  # air tech


    # MACRO FOR DIFFERENT RACES:

    def macro_train_units(self):
        actions = []
        for goal in self.tech_goals:
            if self.units.structure.ready.of_type(goal).amount > 0: #if we have building ready
                unit = self.tech_goals[goal]["unit"]
                if self.race is Race.Zerg:
                    if unit in racial.MORPH_UNITS:
                        unit = racial.MORPH_UNITS[unit]
                    action = self.train_units(self.th_type, unit)

                else:
                    facility = self.tech_goals[goal]["prod"]
                    action = self.train_units(facility, unit)
                if action:
                    actions.extend(action)
        # print(actions)
        return actions

    def macro_boost(self, race):

        actions = []
        if self.minerals > 1200 and self.supply_used > 180 or self.race is not Race.Zerg:
            self.set_air_tech_goal()

        if self.minerals > 1250 and self.race is not Race.Zerg:
            for goal in self.tech_goals:
                if goal in {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.BARRACKS}:
                    if self.tech_goals[goal]["count"] < 10:
                        self.tech_goals[goal]["count"] += 1
                elif self.tech_goals[goal]["count"] < 3:
                    self.tech_goals[goal]["count"] += 1

        if self.enemy_race is Race.Zerg and UnitTypeId.SPAWNINGPOOL in self.tech_goals and self.supply_used > 62:
            self.tech_goals.pop(UnitTypeId.SPAWNINGPOOL)

        if self.tech_switch and (self.minerals > 480 or self.supply_used < 60):
            actions.extend(self.macro_train_units())

        if race == Race.Protoss:
            actions.extend(self.protoss_macro())
        if race == Race.Terran:
            actions.extend(self.terran_macro())
        if race == Race.Zerg:
            actions.extend(self.zerg_macro())
        return actions

    # PROTOSS:

    def protoss_tech(self):
        # zealots
        self.set_tech_goal(UnitTypeId.GATEWAY, self.th_type, UnitTypeId.GATEWAY, 2, UnitTypeId.ZEALOT)

        # immortals
        # self.set_tech_goal(UnitTypeId.ROBOTICSFACILITY, self.th_type, UnitTypeId.ROBOTICSFACILITY, 2, UnitTypeId.IMMORTAL)

        # colossi
        self.set_tech_goal(UnitTypeId.ROBOTICSBAY, self.th_type, UnitTypeId.ROBOTICSFACILITY, 2,
                           UnitTypeId.COLOSSUS)

    def protoss_macro(self):
        actions = []
        actions.extend(self.spam_chronoboost())
        return actions

    # chrono boost buildings with queued production

    # adopted from warpgate_push.py

    def chronoboost(self, nexus=None, target=None):
        if not nexus:
            nexus = self.townhalls.of_type(UnitTypeId.NEXUS).filter(lambda n: n.energy >= 50).random

        if not target:
            target = self.units.structure.ready.filter(lambda s: not s.noqueue). \
                filter(lambda s1: not s1.has_buff(BuffId.CHRONOBOOSTENERGYCOST)).random

        if nexus and target:
            return nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)

    def spam_chronoboost(self, nexi=None, targets=None):
        actions = []
        if not nexi:
            nexi = self.townhalls.of_type(UnitTypeId.NEXUS).filter(lambda n: n.energy >= 50)

        if not targets:
            targets = self.units.structure.ready.filter(lambda s: not s.noqueue). \
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

    # TERRAN:

    def terran_tech(self):
        # marines
        self.set_tech_goal(UnitTypeId.BARRACKS, self.th_type, UnitTypeId.BARRACKS, 4, UnitTypeId.MARINE)

        # hellbats
        self.set_tech_goal(UnitTypeId.ARMORY, self.th_type, UnitTypeId.FACTORY, 2,
                           UnitTypeId.HELLIONTANK)

        # tanks #TODO: make building techlab possible
        # self.set_tech_goal(UnitTypeId.TECHLAB, self.th_type, UnitTypeId.FACTORY, 2,
        #                    UnitTypeId.HELLIONTANK)

    #make orbitals and drop mules (from mass_reaper.py)

    # morph commandcenter to orbitalcommand
    def terran_macro(self):
        actions = []
        actions.extend(self.morph_orbital())
        actions.extend(self.drop_mules())
        a = self.do_repairs()
        if a:
            actions.append(a)
        return actions

    def morph_orbital(self):
        actions = []
        if self.units(UnitTypeId.BARRACKS).ready.exists and self.can_afford(UnitTypeId.ORBITALCOMMAND):  # check if orbital is affordable
            for cc in self.units(UnitTypeId.COMMANDCENTER).idle:  # .idle filters idle command centers
                actions.append(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

        return actions

    def drop_mules(self, mf=None):
        actions = []
        if not mf:
            for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                mfs = self.state.mineral_field.closer_than(10, oc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    actions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
        else:
            for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                actions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))

        return actions

    def do_repairs(self, scv=None, target=None, no_checks=False):

        if (self.repair_flag or self.workers.amount < 8) and not no_checks:
            return
        # print("in do_repairs")
        if not scv:
            scvs = self.workers.filter(lambda w: not w.is_constructing_scv)
            if scvs.amount > 0:
                scv = scvs.random
            # print(scv)
            else:
                return
        if not target:
            targets = self.units.tags_not_in({scv, }).closer_than(10, scv)
            if targets.amount > 0:
                targets = check_if_mechanical(targets).filter(lambda u: u.health_percentage < 1)
                if targets.amount > 0: #dont repair if more income is needed
                    target = targets[0]
                    # print(target.health)

        if target and scv:
            # autocast not available atm
            # print(f"doing some repairs")
            self.repair_flag = 1
            return scv.repair(target)
        else:
            self.repair_flag = 0.34
    # ZERG:
    # make queens and inject larvae

    def zerg_tech_initial(self):
        # lings
        self.set_tech_goal(UnitTypeId.SPAWNINGPOOL, self.th_type, None, 2,
                           UnitTypeId.ZERGLING)

        # banelings
        if self.enemy_race is not Race.Protoss:
            self.set_tech_goal(UnitTypeId.BANELINGNEST, self.th_type, None, 2,
                               UnitTypeId.BANELING)

        # roaches
        self.set_tech_goal(UnitTypeId.ROACHWARREN, self.th_type, None, 1,
                           UnitTypeId.ROACH)

        # hydras
        if self.enemy_race is not Race.Zerg:
            self.set_tech_goal(UnitTypeId.HYDRALISKDEN, self.th_type, None, 1,
                               UnitTypeId.HYDRALISK)

        # lurkers
        # self.set_tech_goal(UnitTypeId.LURKERDENMP, self.th_type, None, 1,
        #                    UnitTypeId.LURKERMP)

    def zerg_tech_mid(self):
        if UnitTypeId.HYDRALISKDEN not in self.tech_goals:
            # print("adding hydraden")
            self.set_tech_goal(UnitTypeId.HYDRALISKDEN, self.th_type, None, 1,
                               UnitTypeId.HYDRALISK)

        # lurkers
        if UnitTypeId.LURKERDENMP not in self.tech_goals:
            # print("adding lurkerden")
            self.set_tech_goal(UnitTypeId.LURKERDENMP, self.th_type, None, 1, UnitTypeId.LURKERMP)

    def zerg_macro(self):
        actions = []
        actions.extend(self.queens_spawn())
        actions.extend(self.queens_inject())
        if self.get_time_in_seconds() % 6 and self.minerals > 400 and self.vespene > 250 \
                and self.units.of_type(UnitTypeId.OVERSEER).amount + \
                self.already_pending(UnitTypeId.OVERSEER, all_units=True) < 2:
            a = self.morph_overseer()
            if a:
                actions.append(a)

        if self.race is Race.Zerg:
            if self.supply_used > 120 or (self.enemy_race is Race.Zerg and self.supply_used > 170):
                self.zerg_tech_mid()

        return actions

    #following ones adopted (and modified) from hydralisk_push.py

    def queen_spawn(self, townhall):
        if self.units(UnitTypeId.SPAWNINGPOOL).ready.exists:
            close_queens = self.units.of_type(UnitTypeId.QUEEN).closer_than(8, townhall)
            if close_queens.amount < 1 and townhall.is_ready and townhall.noqueue: #no queens nearby
                if self.can_afford(UnitTypeId.QUEEN):
                    return townhall.train(UnitTypeId.QUEEN)

    def queens_spawn(self, townhalls=None):
        actions = []
        if not townhalls:
            townhalls = self.townhalls.ready
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
        actions = []
        if not queens:
            queens = self.units.of_type(UnitTypeId.QUEEN)
        if not townhalls:
            townhalls = self.townhalls.ready
        for queen in queens:
            if queen.energy >= 25:  #lambda x: x.energy >= 50
                ths = townhalls.ready.closer_than(8, queen)
                if not stacking: # don't stack larva injects
                    ths = ths.filter(lambda t: not t.has_buff(BuffId.QUEENSPAWNLARVATIMER))
                    # inject not needed if spawning larva already
                if ths.exists:
                    action = self.queen_inject(queen, ths.closest_to(queen.position))
                    if action:
                        actions.append(action)
        return actions

    def morph_overseer(self, overlord=None):
        if overlord:
            return self.morph_unit(overlord)
        if self.townhalls.of_type({UnitTypeId.LAIR, UnitTypeId.HIVE}).amount > 0:
            ovls = self.units.of_type(UnitTypeId.OVERLORD)
            if ovls.amount > 0:
                # print(f"trying to create overseer")
                return self.morph_unit(ovls.random)

def ability_in_orders_for_any_unit(ability, units):
    for u in units:
        if not u.noqueue:
            if u.orders[0].ability.id is ability:
                return True
    return False


def check_building_type_similarity(b_type, buildings):
    for b in buildings:
        found = compare_building_type(b_type, b)
        if found:
            return True
    else:  # not found
        return False


def compare_building_type(building_type, building):
    if building_type == building.type_id:
        return True
    if building.unit_alias:
        if building_type in building.tech_alias:
            return True
    if building.tech_alias:
        if building_type in building.tech_alias:
            return True
    return False


def uniques_by_type_id(unit_list):

    # getting unique attribute idea from:
    # https://stackoverflow.com/questions/17347678/list-of-objects-with-a-unique-attribute
    # dict((obj.thing, obj) for obj in object_list).values()
    return dict((obj.type_id, obj) for obj in unit_list).values()

def check_if_mechanical(unit_list):
    #only terran units
    mechanicals = [UnitTypeId.SCV, ]
    mechanicals.extend(list(racial.STARPORT_UNITS.values())+list(racial.FACTORY_UNITS.values()))

    is_mech = unit_list.structure
    is_mech.extend(unit_list.not_structure.of_type(mechanicals))
    return is_mech

