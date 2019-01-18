#TODO: Ideas:
# change iteration to game time references (under testing) <-- game time is a bit off but reasonable atm
# add tech tree

#TODO: flags/vars
# make flags in one variable and reduce everything at once each step (numpy)
# make __init__ and put object variables in that
# change (tag data) variables in to numpy arrays for quicker operations
# ideas:
# make/use heatmap for enemy locations to defend (maybe with connected components)

#TODO: macro:
# make unit types other than workers and townhalls
# make defence better by updating defence calculations and reinforcing when needed
# take air hp into account in enemy att_str_calc
# ideas:
# multiple attack/defence groups
# make priority queue for different macro actions
# decide which actions can be skipped every now and then
# make priority decision based on game state

#TODO: micro:
# ADD constraint to remove attack group once you got to the target point and no enemies available !!!IMPORTANT!!!
# prioritize low hp/ high dps enemies
# make micro more efficient with big army (take nearby units into account when moving)
# ideas:
# anti-air vs anti-ground, counter units in general
# use swarm intelligence to micro squads (?)
# FIXME: make attacking unit to work as well as attacking to point
#  (you wont get deleted from attack after target dies atm)

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
        self.enemy_att_str_prev = {"hp": 0, "g_dps": 0, "pos": 0}
        self.enemy_att_str_curr = {"hp": 0, "g_dps": 0, "pos": 0}
        self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": 0}
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

        self.pend_supply_flag = 0

        self.attack_force_tags = dict()  # example: tag[unit.tag] = {"retreat" : retreating (int), "hp_curr":unit.health (int), "hp_prev":unit.health_prev (int), "target": Pos}
        self.def_force_tags = dict()

        #self.expansion_locations = [] #in super, not needed here

    def _prepare_first_step(self):
        self.expansion_locations
        #print(self.expansion_locations.keys())
        return super()._prepare_first_step()

    def on_start(self):
        self.th_type = racial.TOWN_HALL_TYPES[self.race]
        self.w_type = racial.WORKER_TYPES[self.race]
        self.prod_bs = racial.PROD_B_TYPES[self.race]
        self.s_args = racial.get_supply_args(self.race) #<- method

    async def on_step(self, iteration):

        #helper vars
        actions = []

        self.iteration = iteration

        clock_diff = self.getTimeInSeconds() - self.clock
        self.clock = self.getTimeInSeconds()

        #TODO: move all flag (time) reductions here
        self.enemy_att_str_save = max(0, self.enemy_att_str_save - clock_diff)
        self.def_msg_flag = max(0, self.def_msg_flag - clock_diff)
        self.attack_flag = max(0, self.attack_flag - clock_diff)


        # if self.d_task:  # wait task to finish to avoid timeouts (does this actually work?)
        #     return

        # Reinforce defence

        self.enemy_att_str_prev = self.enemy_att_str_curr.copy()
        self.enemy_att_str_curr = self.calc_enemy_att_str()
        enemy_att_got_stronger = self.enemy_att_str_prev["hp"] > self.enemy_att_str_curr["hp"] and \
                                self.enemy_att_str_prev["g_dps"] > self.enemy_att_str_curr["g_dps"]

        enemy_is_as_strong = self.enemy_att_str_prev["hp"] >= self.enemy_att_str_curr["hp"] and \
                                self.enemy_att_str_prev["g_dps"] >= self.enemy_att_str_curr["g_dps"]


        if enemy_is_as_strong:
            self.enemy_att_str_save = 30
            #print("max att preserved")


        if not self.enemy_att_str_save:
            if self.enemy_att_str_max["hp"] > 0.9:
                print("max reset")
            self.enemy_att_str_max = {"hp": 0, "g_dps": 0, "pos": 0}

        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev
        m = self.enemy_att_str_max
        self.enemy_att_str_max["hp"] = max(c["hp"], p["hp"], m["hp"])
        self.enemy_att_str_max["g_dps"] = max(c["g_dps"], p["g_dps"], m["g_dps"])
        self.enemy_att_str_max["pos"] = c["pos"]  # use most recent position

        if enemy_att_got_stronger:
            await self.reinforce_defence()

        if self.supply_left < self.townhalls.ready.amount and not self.pend_supply_flag and self.supply_cap < 200:
            self.pend_supply_flag = 1
        else:
            self.pend_supply_flag = 0

        #USUAL TASKS


        # check expand on it's own iteration
        if self.clock >= 45 and not self.expand_flag and self.minerals > 250:
            # self.d_task = True
            await self.expand() #<-- set flag inside that method
            # self.d_task = False
            return
        else:
            self.expand_flag = max(0, self.expand_flag-clock_diff)

        if self.clock >= 60 and not self.w_dist_flag:
            self.w_dist_flag = 0.8
            # self.d_task = True
            await self.distribute_workers()
            # self.d_task = False
            return
        else:
            self.w_dist_flag = max(0, self.w_dist_flag-clock_diff)

        await self.build_supply()
        actions.extend(self.manage_idle_workers())
        if self.pend_supply_flag != 1:
            await self.build_workers()

        #FOR MICRO
        self.manage_att_def_groups()

        #micro every max(0.1,clock_diff) if you have force
        if len(self.attack_force_tags) > 0 and (min(0.1, clock_diff) <= (self.clock - int(self.clock)) % max(0.1, clock_diff)): #micro every 0.1 second
        #if len(self.attack_force_tags) > 0 and (min(1,clock_diff) <= (self.clock - int(self.clock))):  # micro every 1 second (capping if lags)
            if int(self.clock) % 16 == 15 and clock_diff >= self.clock-int(self.clock):  #max once a second once in 33s
                await self.chat_send(f"Attacking with: {len(self.attack_force_tags)}")

            await self.attack_unit_micro()

        if len(self.def_force_tags) > 0 and (min(1, clock_diff) <= (self.clock - int(self.clock))):
            await self.defend_unit_micro()

        if int(self.clock) % 40 == 39 and clock_diff >= self.clock-int(self.clock):
            await self.chat_send(f"Elapsed game time: {int(self.clock/60)} min, {int(self.clock)%60}s")

        #killed_base here, since not used anywhere else.. move if needed
        if not self.killed_start_base:
            shortest_dist = self.units.closest_distance_to(self.enemy_start_locations[0])
            if shortest_dist <= 2:
                print("killed enemy starting base")
                self.killed_start_base = 1

        if self.supply_used > 110 and not self.attack_flag and len(self.attack_force_tags) < 100:

            # FIXME: uncomment to have simplest winning strategy! LOL
            target = None
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
                actions.extend(self.issue_worker_attack(target))
            else: #scout attack location
                if len(self.workers) > 15:
                    await self.chat_send(f"You can run, but You can't hide! (devil)")
                    random_scout_squad = self.workers.filter(lambda w: not w.is_constructing_scv).\
                                             prefer_close_to(target)[:4]
                    actions.extend(self.issue_group_attack(random_scout_squad, target))

        if self.supply_used > 190: #attack when no units attacking and close to max supply
            if len(self.attack_force_tags) < 100:
                self.attack_flag = min(self.attack_flag, 50)  #attack soon

        #UNIQUE TASKS
        if iteration == 0:
            await self.chat_send(f"(glhf)")
            # target = self.enemy_start_locations[0]
            # actions.extend(self.issue_worker_attack(target))

        #if iteration == 1:
        #    await self.build_workers()

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
        if (self.units(self.th_type).amount < 5 or self.workers.amount > 75) and self.can_afford(self.th_type):
            self.expand_flag = 5
            await self.expand_now(closest_to=self.workers.random.position)
            if self.townhalls.amount < 5:
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

    async def build_workers(self):
        actions = []
        for th in self.units(self.th_type).ready.noqueue:
            if self.can_afford(self.w_type):
                if self.race == Race.Zerg:
                    if self.units(self.s_args[0]).exists:  # if bot has larva
                        actions.append(self.units(self.s_args[0]).random.train(self.w_type))
                else:
                    actions.append(th.train(self.w_type))
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

    def calc_enemy_att_str(self):  # calculate enemy attack strength
        # ground hp, air hp, ground dps, air dps
        enemy_g_hp = 0
        enemy_a_hp = 0
        enemy_g_dps = 0
        known_g_enemies = self.known_enemy_units.not_structure.not_flying
        known_a_enemies = self.known_enemy_units.not_structure.flying
        # enemy_count = self.known_enemy_units.amount
        enemy_position = None
        closest_dist = 9999999
        self.attacking_enemy_units = []
        for enemy in known_g_enemies:
            if enemy.can_attack_ground:
                dist = self.units.structure.closest_distance_to(enemy)
                if dist < max(12, enemy.ground_range):  # max(16, enemy.radar_range, (enemy.ground_range) + 5):
                    if dist < closest_dist:
                        enemy_position = enemy.position
                    self.attacking_enemy_units.append(enemy)
                    enemy_g_hp += enemy.health + enemy.shield
                    enemy_g_dps += enemy.ground_dps

        for enemy in known_a_enemies:
            if enemy.can_attack_ground:
                dist = self.units.structure.closest_distance_to(enemy)
                if dist < max(12, enemy.ground_range):
                    # TODO: take into account when making anti-air
                    # if dist < closest_dist:
                    #     closest_enemy = enemy
                    self.attacking_enemy_units.append(enemy)
                    # enemy_a_hp += enemy.health + enemy.shield
                    enemy_g_dps += enemy.ground_dps

        total_hp = enemy_g_hp + enemy_a_hp
        enemy_att_str = {"hp": total_hp, "g_dps": enemy_g_dps, "pos": enemy_position}
        return enemy_att_str

    def manage_att_def_groups(self):
        tags = [unit.tag for unit in self.units(self.w_type)]  # get tags for workers TODO: include army units
        diff_a = set(self.attack_force_tags.keys()).difference(set(tags))  # units not in self.units
        diff_d = set(self.def_force_tags.keys()).difference(set(tags))
        if len(self.def_force_tags) > 0 and len(diff_d) > 0:
            for tg in diff_d:
                del (self.def_force_tags[tg])

        if len(self.attack_force_tags) > 0 and len(diff_a) > 0:
            for tg in diff_a:
                del (self.attack_force_tags[tg])
        # prioritize defence over attack (this shouldnt happen tho)
        for tg in set(self.def_force_tags.keys()).intersection(self.attack_force_tags):
            del (self.attack_force_tags[tg])


    async def reinforce_defence(self):

        #shorten names
        c = self.enemy_att_str_curr
        p = self.enemy_att_str_prev

        #changes: (differences)
        d_hp = max(0, c["hp"]-p["hp"])
        d_g_dps = max(0, c["g_dps"]-p["g_dps"])
        position = c["pos"]
        if len(self.attacking_enemy_units) > 0 and (d_hp > 0 or d_g_dps > 0):
            await self.assign_defence(d_hp, d_g_dps, position)

        # #not working (is_attacking) maybe only with own units...
        # if closest_enemy:
        #     if closest_enemy.is_attacking:
        #         await self.chat_send(f"Enemy{closest_enemy.type_id()}is attacking!")


    async def assign_def_groups(self, enemy_groups):
        #To be implemented
        pass

    async def assign_defence(self, enemy_hp, enemy_dps, enemy_position):

        army = self.units.not_structure.exclude_type(self.w_type).filter(lambda u: u.can_attack_ground)
        #sort workers: high hp and close distance preferred
        workers = self.workers.filter(lambda w: not w.is_constructing_scv).\
            prefer_close_to(enemy_position).sorted(lambda w: -(w.health+w.shield))
        #combined_tags = set(self.attack_force_tags.keys()).union(set(self.def_force_tags.keys()))

        #TODO: better way to assign and track enemy

        if len(army)+len(workers) < 1:
            print("no army or workers")
            return

        actions = []
        if enemy_dps < 4:  #1 worker or smthing like that
            for asset in army:
                if asset.tag not in self.def_force_tags: #and asset.tag not in self.attack_force_tags:
                    actions.append(self.issue_unit_defence(asset, enemy_position))
                    break
            else: #<-no assets found //end for
                for asset in workers:
                    if asset.tag not in self.def_force_tags: #and asset.tag not in self.attack_force_tags:
                        actions.append(self.issue_unit_defence(asset, enemy_position))
                        break
                else:
                    pass  #no units available :(
        elif enemy_dps < 10:
            own_hp = 0
            own_dps = 0
            defenders = []
            # more_needed = own_hp < (enemy_hp + 1) or own_dps < (enemy_dps + 1) #try it out
            for asset in army:
                if own_hp < (enemy_hp + 1) or own_dps < (enemy_dps + 1):
                    defenders.append(asset)
                    own_hp += asset.health + asset.shield
                    own_dps += asset.ground_dps

            for worker in workers:
                if own_hp < (enemy_hp*1.5 + 1) or own_dps < (enemy_dps*1.5 + 1):
                    defenders.append(worker)
                    own_hp += (worker.health + worker.shield)
                    own_dps += worker.ground_dps

            if own_hp >= enemy_hp and own_dps > enemy_dps:
                actions.extend(self.issue_group_defence(defenders, enemy_position))
                actions.append(self.chat_send(f"Location:{enemy_position}"))
                actions.append(self.chat_send(f"You Attack with:{len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps"))
                actions.append(self.chat_send(f"I Defend with:{len(defenders)} defenders - {own_hp} total hp, {own_dps} total dps"))

            # retreat from strong enemy
            else:
                if len(self.def_force_tags) > 0:
                    for def_tag in self.def_force_tags:
                        self.def_force_tags[def_tag]["retreating"] = 5
                    actions.append(self.chat_send(f"Your attack is too much atm - Retreating"))
                elif not self.def_msg_flag:
                    actions.append(self.chat_send(f"Not defending your attack at {enemy_position}"))
                    self.def_msg_flag = 8

        else:  #enemy_g_dps < 4:
            own_hp = 0
            own_dps = 0
            defenders = []
            for asset in army:
                if own_hp < (enemy_hp * 3 + 1) or own_dps < (enemy_dps * 2 + 1):
                    defenders.append(asset)
                    own_hp += asset.health+asset.shield
                    own_dps += asset.ground_dps

            for worker in workers:
                if own_hp < (enemy_hp * 3 + 1) or own_dps < (enemy_dps * 2 + 1):
                    defenders.append(worker)
                    own_hp += (worker.health+worker.shield)
                    own_dps += worker.ground_dps

            if own_hp >= enemy_hp and own_dps > enemy_dps:
                actions.extend(self.issue_group_defence(defenders, enemy_position))
                actions.append(self.chat_send(f"Location:{enemy_position}"))
                actions.append(self.chat_send(f"You Attack with:{len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps"))
                actions.append(self.chat_send(f"I Defend with:{len(defenders)} defenders - {own_hp} total hp, {own_dps} total dps"))

            #retreat from strong enemy
            else:
                if len(self.def_force_tags) > 0:
                    for def_tag in self.def_force_tags:
                        self.def_force_tags[def_tag]["retreating"] = 5
                    actions.append(self.chat_send(f"Your attack is too much atm - Retreating"))
                elif not self.def_msg_flag:
                    actions.append(self.chat_send(f"Not defending your attack at {enemy_position}"))
                    self.def_msg_flag = 8
        #print(f"def_actions with{len(self.def_force_tags)} out of {len(workers)}")
        await self.do_actions(actions)

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
            if unit.distance_to(target) >= 25 and self.known_enemy_units.amount < 3:
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
        min_hp = 6
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
                mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                actions.append(unit.gather(mf))
                continue
            if hpc < (max(min(max_hp_sh/2, unit.health_max), min_hp)) and hpc < hpp:
                if len(self.townhalls) > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.random)
                    actions.append(unit.gather(mf))

                tags[tg]["retreat"] += 1
                continue

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

            if ret and hpc > (max_hp_sh/2):
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

    def getTimeInSeconds(self):
        # returns real time if game is played on "faster"
        return self.state.game_loop * 0.725 * (1 / 16)

    def issue_worker_attack(self, target):
        if len(self.workers) >= 100:
            return self.issue_group_attack(self.workers.random_group_of(int(self.workers.amount*0.9)+1), target)
        else:
            return self.issue_group_attack(self.workers, target)

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

