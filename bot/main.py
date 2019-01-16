#TODO: change iteration to game time references (under testing)
#TODO: make defence better
#TODO: change tag data variables in to numpy arrays for quicker operations
import json
from pathlib import Path

import sc2
from sc2.constants import *
from sc2 import Race

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

    def on_start(self):
        self.th_type = racial.TOWN_HALL_TYPES[self.race]
        self.w_type = racial.WORKER_TYPES[self.race]
        self.prod_bs = racial.PROD_B_TYPES[self.race]
        self.s_args = racial.get_supply_args(self.race) #<- method

        self.clock = 0

        self.d_task = False #demanding task
        self.expand_flag = 0
        self.w_dist_flag = 0
        self.attack_flag = 0

        self.pend_supply_flag = 0

        self.attack_force_tags = dict() #example: tag[unit.tag] = {"retreat" : retreating (int), "hp_curr":unit.health (int), "hp_prev":unit.health_prev (int), "target": Pos}
        self.def_force_tags = dict()

        self.attacking_enemy_units = []

    async def on_step(self, iteration):

        #helper vars
        self.iteration = iteration

        clock_diff = self.getTimeInSeconds() - self.clock
        self.clock = self.getTimeInSeconds()

        if self.d_task:  # wait task to finish to avoid timeouts (does this actually work?)
            return

        #Reinforce defence
        self.reinforce_defence()

        if self.supply_left < self.townhalls.ready.amount and not self.pend_supply_flag:
            self.pend_supply_flag = 1
        else:
            self.pend_supply_flag = 0

        #USUAL TASKS


        # check expand on it's own iteration
        if self.clock >= 45 and not self.expand_flag:
            self.d_task = True
            await self.expand() #<-- set flag inside that method
            self.d_task = False
            return
        else:
            self.expand_flag = max(0, self.expand_flag-clock_diff)

        if self.clock >= 60 and not self.w_dist_flag:
            self.w_dist_flag = 0.8
            self.d_task = True
            await self.distribute_workers()
            self.d_task = False
            return
        else:
            self.w_dist_flag = max(0, self.w_dist_flag-clock_diff)

        await self.build_supply()
        await self.do_actions(self.manage_idle_workers())
        if self.pend_supply_flag != 1:
            await self.build_workers()

        tags = [unit.tag for unit in self.units(self.w_type)]  # get tags for workers
        diff_a = set(self.attack_force_tags.keys()).difference(set(tags))  # units not in self.units
        diff_d = set(self.def_force_tags.keys()).difference(set(tags))
        for tg in diff_d:
            del (self.def_force_tags[tg])
        for tg in diff_a:
            del (self.attack_force_tags[tg])
        # prioritize defence over attack
        for tg in set(self.def_force_tags.keys()).intersection(self.attack_force_tags):
            del (self.attack_force_tags[tg])

        #if len(self.attack_force_tags) > 0 and (clock_diff <= (self.clock - int(self.clock)) % max(0.3, clock_diff)): #micro every 0.3 second
        if len(self.attack_force_tags) > 0 and (min(1,clock_diff) <= (self.clock - int(self.clock))):  # micro every 1 second (capping if lags)
            if int(self.clock) % 59 == 58 and clock_diff >= self.clock-int(self.clock):  #max once a second once a minute
                await self.chat_send(f"Attacking with: {len(self.attack_force_tags)}")

            await self.attack_unit_micro()

        if len(self.def_force_tags) > 0 and (min(1, clock_diff) <= (self.clock - int(self.clock))):
            await self.defend_unit_micro()

        if self.supply_used > 190: #init attack when no units attacking and close to max supply
            if len(self.attack_force_tags) < 100:
                self.attack_flag = 0

        if self.supply_used > 110 and not self.attack_flag:

            # FIXME: uncomment to have simplest winning strategy! LOL
            target = self.enemy_start_locations[0]
            actions = self.issue_worker_attack(target)
            self.attack_flag = 120  # 2 min
            await self.do_actions(actions)


        else:
            self.attack_flag = max(0, self.attack_flag - clock_diff)

        #UNIQUE TASKS
        if iteration == 0:
            await self.chat_send(f"(glhf)")
            target = self.enemy_start_locations[0]
            actions = self.issue_worker_attack(target)
            await self.do_actions(actions)

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

        if int(self.clock) % 40 == 39 and clock_diff >= self.clock-int(self.clock):
            await self.chat_send(f"Elapsed game time: {int(self.clock/60)} min, {int(self.clock)%60}s")

    async def expand(self):
        # expand
        if (self.units(self.th_type).amount < 5 or self.workers.amount > 75) and self.can_afford(self.th_type):
            self.expand_flag = 5
            await self.expand_now()
            await self.chat_send(f"Trying to expand!")
        # not yet
        else:
            self.expand_flag = 1  # <-- try again soon


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

    async def reinforce_defence(self):
        #ground hp, air hp, ground dps, air dps
        enemy_g_hp = 0
        enemy_a_hp = 0
        enemy_g_dps = 0
        known_g_enemies = self.known_enemy_units.not_structure.not_flying
        known_a_enemies = self.known_enemy_units.not_structure.flying
        #enemy_count = self.known_enemy_units.amount
        closest_enemy = None
        closest_dist = 9999999
        self.attacking_enemy_units = []
        for enemy in known_g_enemies:
                if enemy.can_attack_ground:
                    dist = self.units.structure.closest_distance_to(enemy)
                    if dist < max(12, enemy.radar_range, (enemy.ground_range) + 5):
                        if dist < closest_dist:
                            closest_enemy = enemy
                        self.attacking_enemy_units.append(enemy)
                        enemy_g_hp += enemy.health + enemy.shield
                        enemy_g_dps += enemy.ground_dps

        for enemy in known_a_enemies:
                if enemy.can_attack_ground:
                    dist = self.units.structure.closest_distance_to(enemy)
                    if dist < max(12, enemy.radar_range, (enemy.ground_range) + 5):
                        #TODO: take into account when making anti-air
                        # if dist < closest_dist:
                        #     closest_enemy = enemy
                        # self.attacking_enemy_units.append(enemy)
                        # enemy_a_hp += enemy.health + enemy.shield
                        enemy_g_dps += enemy.ground_dps

        if len(self.def_force_tags) < 1 and len(self.attacking_enemy_units) > 0:
            await self.assing_defence(enemy_g_hp, enemy_g_dps, closest_enemy)
        #not working (is_attacking) maybe only with own units...
        if closest_enemy:
            if closest_enemy.is_attacking:
                await self.chat_send(f"Enemy{closest_enemy.type_id()}is attacking!")

    async def assing_defence(self, enemy_hp, enemy_dps, enemy):
        army = self.units.not_structure.exclude_type(self.w_type).filter(lambda u: u.can_attack_ground)
        workers = self.workers.filter(lambda w: not w.is_constructing_scv).sorted(lambda w: w.health+w.shield, reverse = True).sorted(lambda w: w.distance_to(enemy))
        #combined_tags = set(self.attack_force_tags.keys()).union(set(self.def_force_tags.keys()))

        #TODO: better way to assign and track enemy
        if len(army)+len(workers) < 1:
            return

        if enemy_dps < 4:  #1 worker or smthing like that
            for asset in army:
                if asset.tag not in self.def_force_tags and asset.tag not in self.attack_force_tags:
                    self.issue_unit_defence(asset, enemy)
                    break
            else: #<-no assets found //end for
                for asset in workers:
                    if asset.tag not in self.def_force_tags and asset.tag not in self.attack_force_tags:
                        self.issue_unit_defence(asset, enemy)
                        break
                else:
                    pass  #no units available :(
        else:  #enemy_g_dps < 50:
            own_hp = 0
            own_dps = 0
            defenders = []
            for asset in army:
                if own_hp < (enemy_hp * 3 + 1) or own_dps < (enemy_dps * 2 + 1):
                    defenders.append(asset)
                    own_hp += asset.health+asset.shield
                    own_dps += max(asset.ground_dps, asset.air_dps)

            for worker in workers:
                if own_hp < (enemy_hp * 3 + 1) or own_dps < (enemy_dps * 2 + 1):
                    defenders.append(worker)
                    own_hp += (worker.health+worker.shield)
                    own_dps += worker.ground_dps/2

            if own_hp >= enemy_hp and own_dps > enemy_dps:
                self.issue_group_defence(defenders, enemy)
                await self.chat_send(f"You Attack with:{len(self.attacking_enemy_units)} Units - {enemy_hp} total hp, {enemy_dps} total dps")
                await self.chat_send(f"I Defend with:{len(defenders)} defenders - {own_hp} total hp, {own_dps} total dps")

            #TODO: FIX functionality so that following can be run
            else:
                if len(self.def_force_tags) > 0:
                    for def_tag in self.def_force_tags:
                        self.def_force_tags[def_tag]["retreating"] = 5  #retreat
                    await self.chat_send(f"Your attack is too much atm - Retreating")


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
                if len(self.townhalls) > 0:
                    mf = self.state.mineral_field.closest_to(self.townhalls.random)
                    actions.append(unit.gather(mf))

                tags[tg]["retreat"] += 1

            else:
                if unit.distance_to(target) >= 4:
                    actions.append(unit.attack(target))

                else:
                    if self.known_enemy_units.exists:
                        unit.attack(self.known_enemy_units.closest_to(unit).position)
                    else:
                        tb_removed.append(tg)

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
        min_hp = 6
        for tg in tags:
            unit = self.units.by_tag(tg)
            tags[tg]["hp_curr"] = unit.health + unit.shield #update current hp
            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            hpp = tags[tg]["hp_prev"]
            target = tags[tg]["target"]
            orig = tags[tg]["orig_target"]
            if not target.is_visible:
                target = orig
                tags[tg]["target"] = tags[tg]["orig_target"]
            else:
                target = target.position
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

            else:
                close_enemies = self.known_enemy_units.not_flying.closer_than(unit.sight_range, unit.position).sorted_by_distance_to(unit)
                if len(close_enemies) > 0:
                    actions.append(unit.attack(close_enemies[0]))
                elif unit.distance_to(target) >= 3:
                    actions.append(unit.attack(target))
                else:
                    tb_removed.append(tg)

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
                actions = self.issue_worker_attack(target)

        else:
            self.expand_flag = 0


        return actions

    def getTimeInSeconds(self):
        # returns real time if game is played on "faster"
        return self.state.game_loop * 0.725 * (1 / 16)

    def issue_worker_attack(self, target):
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

    def issue_unit_defence(self,unit,target):
        action = unit.attack(target)
        orig = target.position
        retreating = 0
        unit.health_prev = unit.health
        self.def_force_tags[unit.tag] = {"retreat": retreating,
                                         "hp_curr": unit.health,
                                         "hp_prev": unit.health_prev,
                                         "target": target,
                                         "orig_target" : orig}
        return action

