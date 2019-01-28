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
# make unit types other than workers and townhalls (in progress...)
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

import math

#code snippets for different races
if __name__ == '__main__':
    import racial
else:
    import bot.racial as racial



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
        self.expand_flag = 0
        self.w_dist_flag = 0
        self.attack_flag = 0
        self.enemy_att_str_save = 10
        self.def_msg_flag = 0
        self.killed_start_base = 0
        self.kill_move_flag = 0
        self.worker_limit = 120
        self.kill_move_switch = 0

        self.pend_supply_flag = 0

        # other - collections
        self.attack_force_tags = dict()  # example: tag[unit.tag] = {"retreat" : retreating (int), "hp_curr":unit.health (int), "hp_prev":unit.health_prev (int), "target": Pos}
        self.def_force_tags = dict()

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

        #for now, simple goal and winning strategy "mass air" after getting good economy
        goal_building = list(racial.AIR_TECH[self.race])[0]  # don't "pop" or it's not available next time
        goal_unit = list(racial.goal_air_unit(self.race))[0]
        self.set_tech_goal(goal_building, self.th_type, goal_building, 5, goal_unit)

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
        self.kill_move_flag = max(0, self.kill_move_flag - clock_diff)

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

        if self.minerals > 150 and self.vespene / self.minerals <= 0.8: #vespene count is less than 80% of minerals
            #following snippet adpoted from cyclone_push.py
            for a in self.units(self.gas_type):
                if a.assigned_harvesters < a.ideal_harvesters:
                    w = self.workers.closer_than(5, a)
                    if w.exists:
                        actions.append(w.random.gather(a))
            if (self.vespene / self.minerals) <= 0.5 and self.minerals >= 1000:
                await self.build_gas(int(self.units.of_type(self.gas_type).amount/2) + 2) #add extra gas if gas-starving
            # self.d_task = False
            # return

        if self.kill_move_switch:
            # set desired amount of workers based on # of expansion (in between 24, 88)
            self.worker_limit == max(24, min(len(self.owned_expansions) * 24, 88))
            if not self.kill_move_flag:
                    goal_building = list(racial.AIR_TECH[self.race])[0]  # don't "pop" or it's not available next time
                    # goal_unit = list(racial.goal_air_unit(self.race))[0]
                    if self.geysers.amount <= 4:
                        await self.build_gas()
                    # check that bot has pylons (IF PROTOSS) before building stuff (move to other part later(?))
                    if self.race == Race.Protoss:
                        if self.units.of_type(UnitTypeId.PYLON).ready.amount > 0:
                            await self.manage_tech(goal_building)
                        else:
                            await self.build_supply()
                    else:
                        await self.manage_tech(goal_building)
                    self.kill_move_flag = 5
    #                await self.prepare_kill_move(goal_building, goal_unit) #TO BE REMOVED

        await self.build_supply()
        actions.extend(self.manage_idle_workers())
        if self.pend_supply_flag != 1:
            if self.workers.amount < (self.worker_limit - self.townhalls.amount):
                await self.train_workers()
            elif self.minerals > 1000 and self.workers.amount < 160:  #hard coded limit for workers
                await self.train_workers()


        #FOR MICRO
        self.manage_att_def_groups()

        #micro every max(0.1,clock_diff) if you have force
        if len(self.attack_force_tags) > 0 and (min(0.1, clock_diff) <= (self.clock - int(self.clock)) % max(0.1, clock_diff)): #micro every 0.1 second
        #if len(self.attack_force_tags) > 0 and (min(1,clock_diff) <= (self.clock - int(self.clock))):  # micro every second (capping if lags)
            if int(self.clock) % 16 == 15 and clock_diff >= self.clock-int(self.clock):  #max once a second once in 33s
                await self.chat_send(f"Attacking with: {len(self.attack_force_tags)}")

            await self.attack_unit_micro()

        if len(self.def_force_tags) > 0 and (min(1.0, clock_diff) <= (self.clock - int(self.clock))):
            await self.defend_unit_micro()

        if int(self.clock) % 40 == 39 and clock_diff >= self.clock-int(self.clock):
            await self.chat_send(f"Elapsed game time: {int(self.clock/60)} min, {int(self.clock)%60}s")

        #killed_base here, since not used anywhere else.. move if needed
        if not self.killed_start_base:
            shortest_dist = self.units.closest_distance_to(self.enemy_start_locations[0])
            if shortest_dist <= 2:
                # print("killed enemy starting base")
                self.killed_start_base = 1

        if self.supply_used > 110 and not self.attack_flag and \
                ((len(self.attack_force_tags)+len(self.def_force_tags)) <
                 (self.units.not_structure.not_flying.amount/2 + 1)):

            # "fixed": uncomment to have simplest winning strategy! LOL
            # target = None  #not needed
            if not self.killed_start_base:
                target = self.enemy_start_locations[0]
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
                army = self.units.not_structure.filter(lambda w: not w.type_id == self.w_type).\
                                                filter(lambda l: not l.type_id == UnitTypeId.OVERLORD)
                actions.extend(self.issue_group_attack(army, target))
                if self.workers.amount > 20:
                    actions.extend(self.issue_worker_attack(target, 0.35))
            else: #scout attack location
                if self.workers.amount > 15:
                    group_size = max(4, int(self.workers.amount*0.25)+1)
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = self.workers.filter(lambda w: not w.is_constructing_scv).\
                                             prefer_close_to(target)[:group_size]
                    actions.extend(self.issue_group_attack(random_scout_squad, target))

        if not self.kill_move_switch and self.supply_used > 44:
            self.kill_move_switch = 1

            await self.chat_send(f"Initializing kill move procedures")

        if self.supply_used > 190: #attack when no units attacking and close to max supply
            if len(self.attack_force_tags) < 100:
                self.attack_flag = min(self.attack_flag, 50)  #attack soon

        #UNIQUE TASKS
        if iteration == 0:
            await self.chat_send(f"(glhf)")
            # target = self.enemy_start_locations[0]
            # actions.extend(self.issue_worker_attack(target))

        #if iteration == 1:
        #    await self.train_workers()

        # if iteration == 2:
        #     await self.chat_send(f"Main building is {self.townhalls[0].health}")

        if iteration == 5:
            #await self.chat_send(f"Debug args: {self.s_args}")
            #await self.chat_send(f"time: {self.getTimeInSeconds()}")
            await self.chat_send(f"I'm playing {self.race}")

        if iteration == 7:
            #await self.chat_send(f"time:{self.getTimeInSeconds()}")
            await self.chat_send(f"You are {self.enemy_race}")


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

    async def train_units(self, building_type, unit_type, max_amount=None):
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
        await self.do_actions(actions)

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
                        await self.build(self.s_args[1], near=th.position.towards(self.game_info.map_center, 5))

                    if self.pend_supply_flag == 1:
                        self.pend_supply_flag = 2

    async def build_gas(self, max_amount=3):
        #following adopted and modified from mass_reaper.py in examples/terran
        actions = []
        own_bases = list(self.owned_expansions.values())
        for th in own_bases[:max_amount]:
#            for th in self.townhalls.random_group_of(max_amount):
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
                        #w.build

        await self.do_actions(actions)
        #print(actions)
        #return actions

    def calc_enemy_att_str(self):  # calculate enemy attack strength
        # ground hp, air hp, ground dps, air dps
        enemy_g_hp = 0
        enemy_a_hp = 0
        enemy_g_dps = 0
        known_g_enemies = self.known_enemy_units.not_structure.not_flying
        known_a_enemies = self.known_enemy_units.not_structure.flying
        # enemy_count = self.known_enemy_units.amount
        enemy_position = None
        closest_dist = math.inf
        self.attacking_enemy_units = []
        for enemy in known_g_enemies:
            if enemy.can_attack_ground:
                dist = self.units.structure.ready.closest_distance_to(enemy)
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
                    # enemy_a_hp += enemy.health + enemy.shield
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
        army = self.units.ready.tags_not_in(self.def_force_tags).not_structure.exclude_type(self.w_type).filter(lambda u: u.can_attack_ground)
        #sort workers: high hp and close distance preferred
        workers = self.workers.ready.tags_not_in(self.def_force_tags).filter(lambda w: not w.is_constructing_scv).\
            sorted(lambda w: -(w.health+w.shield)).prefer_close_to(enemy_position)
        #combined_tags = set(self.attack_force_tags.keys()).union(set(self.def_force_tags.keys()))

        #TODO: better way to assign and track enemy

        if len(army)+len(workers) < 1:
            # print("no army or workers")
            return

        actions = []

        defenders, own_dps, own_hp = await self.create_defence_group(army, enemy_dps, enemy_hp, workers)

        #do we have enough to defend
        if enemy_dps < 10:
            condition = True
        else:
            condition = (own_hp >= enemy_hp and own_dps >= enemy_dps) or self.townhalls.amount <= 2  # or self.clock<120
        if condition:
            actions.extend(self.issue_group_defence(defenders, enemy_position))
            await self.chat_defending_taunt(enemy_position, workers.amount+army.amount, enemy_hp, own_hp, enemy_dps, own_dps)

        # retreat from strong enemy
        else:
            for defender in self.def_force_tags:
                self.def_force_tags[defender]["retreat"] = 5
            await self.chat_retreating(enemy_position, enemy_hp, enemy_dps)

        if len(actions) > 0:
            await self.do_actions(actions)

    async def create_defence_group(self, army, enemy_dps, enemy_hp, workers):
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
                if own_hp <= (enemy_hp * 1.5 + 1) or own_dps <= (enemy_dps * 1.5 + 1):
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

    #TODO: implement the micro function

    # async def micro_viking(self, viking, tags):
    #     """"""
    #     tag = viking.tag
    #     actions = []
    #     tb_removed = False
    #     min_hp = 22
    #     tags["hp_curr"] = viking.health + viking.shield #update current hp
    #     ret = tags["retreat"]
    #     hpc = tags["hp_curr"]
    #     hpp = tags["hp_prev"]
    #     target = tags["target"]
    #     max_hp_sh = viking.health_max + viking.shield_max
    #
    #     if (ret > 4 or hpc < min_hp) and len(self.townhalls.ready) > 0:
    #         tb_removed.append(tag)
    #         retreat_point = self.state.mineral_field.closest_to(self.townhalls.ready.random)
    #         actions.append(viking.move(retreat_point))
    #         return
    #
    #     if hpc < (max(min(max_hp_sh/2, viking.health_max), min_hp)) and hpc < hpp:
    #         if len(self.townhalls.ready) > 0:
    #             mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
    #             actions.append(viking.gather(mf))
    #         tags["retreat"] += 1
    #
    #
    #     # else:
    #     #     if unit.distance_to(target) >= 4:
    #     #         actions.append(unit.attack(target))
    #     #
    #     #     else:
    #     #         if self.known_enemy_units.exists:
    #     #             unit.attack(self.known_enemy_units.closest_to(unit).position)
    #     #         else:
    #     #             tb_removed.append(tg)
    #
    #     # pursue enemy
    #     close_enemies = self.known_enemy_units.not_flying.closer_than(viking.radar_range, viking.position).sorted_by_distance_to(unit)
    #     if viking.distance_to(target) >= 25 and close_enemies.amount < 3:
    #         actions.append(viking.move(target))
    #
    #     elif (viking.distance_to(target) >= 2 and tags[tg]["retreat"] < 5): #or len(close_enemies) > 0:
    #         actions.append(viking.attack(target))
    #     else:
    #         tb_removed.append(tag)
    #         if self.townhalls.ready.amount > 0:
    #             mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
    #             actions.append(unit.gather(mf))
    #
    #     if ret and hpc > (max_hp_sh/2):
    #         tags[tg]["retreat"] = 0
    #
    #     # if unit.distance_to(target) < 3:
    #     #     actions.append(unit.attack(target))
    #     # else:
    #     #     tb_removed.append(tg)
    #
    #     tags[tg]["hp_prev"] = hpc = tags[tg]["hp_curr"]
    #     #worker.health_prev = worker.health
    #
    #     for tag in tb_removed:
    #         del(self.attack_force_tags[tag])
    #
    #     await self.do_actions(actions)

    async def attack_unit_micro(self):
        """"""
        tags = self.attack_force_tags
        actions = []
        tb_removed = []
        min_hp = 6
        if len(tags) >= 3:
            min_hp = 11
        for tg in tags:
            unit = self.units.by_tag(tg)
            tags[tg]["hp_curr"] = unit.health + unit.shield #update current hp
            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            hpp = tags[tg]["hp_prev"]
            target = tags[tg]["target"]
            max_hp_sh = unit.health_max + unit.shield_max

            if (ret > 4 or hpc < min_hp) and len(self.townhalls.ready) > 0:
                tb_removed.append(tg)
                mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                actions.append(unit.gather(mf))
                continue

            if hpc < (max(min(max_hp_sh/2, unit.health_max), min_hp)) and hpc < hpp:
                if len(self.townhalls.ready) > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                    actions.append(unit.gather(mf))
                tags[tg]["retreat"] += 1


            # else:
            #     if unit.distance_to(target) >= 4:
            #         actions.append(unit.attack(target))
            #
            #     else:
            #         if self.known_enemy_units.exists:
            #             unit.attack(self.known_enemy_units.closest_to(unit).position)
            #         else:
            #             tb_removed.append(tg)

            # pursue enemy
            close_enemies = self.known_enemy_units.not_flying.closer_than(unit.radar_range, unit.position).sorted_by_distance_to(unit)
            if unit.distance_to(target) >= 25 and close_enemies.amount < 3:
                actions.append(unit.move(target))

            elif (unit.distance_to(target) >= 2 and tags[tg]["retreat"] < 5): #or len(close_enemies) > 0:
                actions.append(unit.attack(target))
            else:
                tb_removed.append(tg)
                if self.townhalls.ready.amount > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                    actions.append(unit.gather(mf))

            if ret and hpc > (max_hp_sh/2):
                tags[tg]["retreat"] = 0

            # if unit.distance_to(target) < 3:
            #     actions.append(unit.attack(target))
            # else:
            #     tb_removed.append(tg)

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
        min_hp = 0.1 #TODO: change if needed / create new var for situational min_hp
        for tg in tags:
            unit = self.units.by_tag(tg)
            tags[tg]["hp_curr"] = unit.health + unit.shield #update current hp
            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            hpp = tags[tg]["hp_prev"]
            target = tags[tg]["target"]
            orig = tags[tg]["orig_target"]


            max_hp_sh = unit.health_max + unit.shield_max

            #TODO: fix this for non-workers
            if (ret > 4 or hpc < min_hp) and len(self.townhalls.ready) > 0:
                tb_removed.append(tg)
                if unit.is_carrying_minerals or unit.is_carrying_vespene:
                    actions.append(unit.return_resource(self.townhalls.ready.random))
                else:
                    mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                    actions.append(unit.gather(mf))
                continue
            if hpc < (max(min(max_hp_sh/2, unit.health_max), min_hp)) and hpc < hpp:
                if len(self.townhalls) > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.random)
                    actions.append(unit.gather(mf))

                tags[tg]["retreat"] += 1
                continue

            army = self.units.not_structure.exclude_type(self.w_type).filter(lambda u: u.can_attack_ground)
            workers = self.workers.filter(lambda w: not w.is_constructing_scv)

            #pursue enemy
            close_enemies = self.known_enemy_units.not_flying.closer_than(unit.sight_range, unit.position).sorted_by_distance_to(unit)
            if close_enemies.amount > 0:
                #pursue only so far:
                if close_enemies[0].distance_to(orig) > 20:
                    actions.append(unit.attack(close_enemies[0].position))
                else:
                    actions.append(unit.attack(orig))
            elif unit.distance_to(target) >= 3:
                actions.append(unit.attack(target))
            else:
                tb_removed.append(tg)
                if self.townhalls.ready.amount > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                    actions.append(unit.gather(mf))

            if len(self.def_force_tags) >= workers.amount + army.amount:
                tags[tg]["retreat"] = 0  #dont retreat when everyone is needed in defence
            elif ret and hpc > (max_hp_sh/2):
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
        return self.issue_group_attack(self.workers.random_group_of(int(self.workers.amount*percentage)+1), target)

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

    async def prepare_kill_move(self, goal_building, goal_unit):
        """

        """
        if self.geysers.amount < 2:
            await self.build_gas()

        progress = await self.get_tech(goal_building)
        if not progress:
            # print(f"tech progress ?")
            self.kill_move_flag = 3  # try again soon
        elif progress == 1:
            # print(f"tech progress 1")
            self.kill_move_flag = 15 #try again after building finish (every building should take more than 30s)
        elif progress == 2:  # tech available
            # print(f"tech available")
            # print(goal_building)
            # print(goal_unit)
            if goal_building in racial.PROD_B_TYPES[self.race]:  #this check shouldn't be needed
                await self.train_units(goal_building, goal_unit)
            else:  # zerg
                await self.train_units(self.th_type, goal_unit)
            self.kill_move_flag = 5
        else:
            pass
            # print(f"something weird happened")

    async def manage_tech(self, tech_goal):
        old_step = self.tech_goals[tech_goal]["step"]
        ready_buildings = uniques_by_attr(self.units.structure.ready)
        ready_types = [b.type_id for b in ready_buildings]
        not_ready_buildings = uniques_by_attr(self.units.structure.not_ready)

        # check tech progress
        curr_step = self.update_tech_progress(tech_goal, ready_buildings, not_ready_buildings)

        # build advancement in tech
        if curr_step in racial.MORPH_BUILDINGS:
            pending = self.already_pending(curr_step, all_units=True)
        else:
            pending = self.already_pending(curr_step)

        #FIXME: currently build always new highest tech building unless already building one (DONE)
        if not pending and (curr_step not in ready_types):  # or old_step != curr_step:
            # print(f"getting {curr_step}")
            if curr_step not in racial.MORPH_BUILDINGS:
                if self.race != Race.Protoss:
                    await self.build(curr_step, near=self.townhalls.ready.random)
                else:
                    await self.build(curr_step, near=self.units.of_type(UnitTypeId.PYLON).ready.random)
            else:
                all_units_of_type = self.units.structure.of_type(racial.MORPH_BUILDINGS[curr_step]).ready
                morph_any_of_these = all_units_of_type.random_group_of(all_units_of_type.amount)
                #print(all_units_of_type)
                #print(morph_any_of_these)
                for morph_this in morph_any_of_these:
                    if morph_this.noqueue:
                        await self.do(morph_this.build(curr_step))
                        # print(f"morphing{morph_this} into {curr_step}")
                        # print(f"{morph_this.build_progress}")
                        break #only one


        # tech available
        if curr_step == tech_goal:

            prod_goal = self.tech_goals[tech_goal]["prod"]
            # start unit production
            goal_unit = self.tech_goals[tech_goal]["unit"]
            if self.units.of_type(prod_goal).ready.amount > 0:
                # start producing units
                # for building in self.units.of_type(self.tech_goals[tech_goal]["prod"]).ready:
                #     #if building in racial.PROD_B_TYPES[self.race]:  # this check shouldn't be needed
                #     await self.train_units(building, goal_unit)

                if prod_goal in racial.PROD_B_TYPES[self.race]:  # non-zerg
                    await self.train_units(prod_goal, goal_unit)
                else:  # zerg
                    await self.train_units(self.th_type, goal_unit)

            # add enough production buildings
            already_building = self.already_pending(prod_goal)
            already_ready = self.units.structure.ready.of_type(prod_goal).amount
            needed = self.tech_goals[tech_goal]["count"] - already_building - already_ready
            if needed > 0:
                # print(f"""adding {prod_goal}""")
                for builder in self.workers.prefer_idle.random_group_of(needed):
                    if self.race != Race.Protoss:
                        await self.build(prod_goal, near=self.units.structure.not_flying.ready.random,
                                         unit=builder)
                    else:
                        await self.build(prod_goal, near=self.units.of_type(UnitTypeId.PYLON).ready.random, unit=builder)


    def update_tech_progress(self, tech_goal, ready_buildings=None, not_ready_buildings=None):
        """
        Updates tech progress by updating current step in tech path
        :param tech_goal: Building to be built
        :return: updated current step
        """

        if not ready_buildings:
            ready_buildings = uniques_by_attr(self.units.structure.ready)
        if not  not_ready_buildings:
            not_ready_buildings = uniques_by_attr(self.units.structure.not_ready)
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
        # if curr_tech in self.units.structure.ready:
        #     return 2  # tech has progressed
        # elif curr_tech in self.units.structure.not_ready:
        #     return 1  # tech in in progress
        # else:
        #     return 0  # tech has been lost

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



    async def get_tech(self,tech_goal):
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
            if (len(self.def_force_tags) >= defender_amount):  # and \
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

def ability_in_orders_for_any_unit(ability, units):
    for u in units:
        if not u.noqueue:
            if u.orders[0].ability.id is ability:
                return True
    return False

def check_building_type_similarity(b_type, buildings):
    for b in buildings:
        found = compare_building_type(b_type,b)
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

def uniques_by_attr(unit_list):

    # getting unique attribute idea from:
    # https://stackoverflow.com/questions/17347678/list-of-objects-with-a-unique-attribute
    # dict((obj.thing, obj) for obj in object_list).values()
    return dict((obj.type_id, obj) for obj in unit_list).values()
