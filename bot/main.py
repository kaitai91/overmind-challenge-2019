#TODO: change iteration to game time references

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
        #self.init_race = str(self.race)
        self.th_type = racial.TOWN_HALL_TYPES[self.race]
        self.w_type = racial.WORKER_TYPES[self.race]
        self.prod_bs = racial.PROD_B_TYPES[self.race]
        self.s_args = racial.get_supply_args(self.race) #<- method

        self.d_task = False #demanding task
        self.expand_flag = 0
        self.w_dist_flag = 0
        self.attack_flag = 0
        self.attack_force_tags = dict() #example: tag[unit.tag] = {"retreat" : retreating (int), "hp_curr":unit.health (int), "hp_prev":unit.health_prev (int)}


    async def on_step(self, iteration):
    #USUAL TASKS
        self.iteration = iteration

        if self.d_task: #wait task to finish to avoid timeouts (does this work?)
            return
        # check expand on it's own iteration
        if self.iteration >= 3000 and not self.expand_flag:
            self.d_task = True
            await self.expand() #<-- set flag inside that method
            self.d_task = False
            return
        else:
            self.expand_flag = max(0, self.expand_flag-1)

        if iteration >= 2000 and not self.w_dist_flag:
            self.w_dist_flag = 49
            self.d_task = True
            await self.distribute_workers()
            self.d_task = False
            return
        else:
            self.w_dist_flag = max(0, self.w_dist_flag-1)

        await self.build_supply()
        await self.do_actions(self.manage_idle_workers())
        await self.build_workers()

        if len(self.attack_force_tags) > 0 and (iteration % 17 == 0):
            if iteration % 17*20 == 0 and iteration > 123:
                await self.chat_send(f"Attacking with: {len(self.attack_force_tags)}")
            tags = [unit.tag for unit in self.units(self.w_type)] #get tags for workers
            diff = set(self.attack_force_tags.keys()).difference(set(tags)) #units not in self.units
            for tg in diff:
                del(self.attack_force_tags[tg])
            await self.unit_micro()

        if self.supply_used > 110 and not self.attack_flag:

            # FIXME: uncomment to have simplest winning strategy! LOL
            actions = []
            for worker in self.workers:
                actions.append(worker.attack(self.enemy_start_locations[0]))
                worker.retreating = 0
                worker.health_prev = worker.health
                self.attack_force_tags[worker.tag] = {"retreat": worker.retreating,
                                                      "hp_curr": worker.health,
                                                      "hp_prev": worker.health_prev}
            self.attack_flag = 3000
            await self.do_actions(actions)


        else:
            self.attack_flag = max(0, self.attack_flag - 1)

        #UNIQUE TASKS
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")
            actions = []
            for worker in self.workers:
                actions.append(worker.attack(self.enemy_start_locations[0]))
                worker.retreating = 0
                worker.health_prev = worker.health
                self.attack_force_tags[worker.tag] = {"retreat": worker.retreating,
                                                      "hp_curr": worker.health,
                                                      "hp_prev": worker.health_prev}
            await self.do_actions(actions)

        if iteration == 1:
            await self.build_workers()

        if iteration == 2:
            await self.chat_send(f"Main building is {self.townhalls[0].health}")

        if iteration == 5:
            #await self.chat_send(f"Debug args: {self.s_args}")
            await self.chat_send(f"I'm playing {self.race}")

        if iteration == 7:
            await self.chat_send(f"You are {self.enemy_race}")


    async def expand(self):
        # expand
        if (self.units(self.th_type).amount < 5 or self.workers.amount > 75) and self.can_afford(self.th_type):
            self.expand_flag = 300  # <-- 5 seconds?
            await self.expand_now()
            await self.chat_send(f"Trying to expand!")
        # not yet
        else:
            self.expand_flag = 60  # <-- try again soon


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

        # amount= self.race ? Race.Zerg : len(ths) ? len(ths)+len(b_buildings)
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
                            # await self.units(self.s_args[0]).(self.s_args[1], near=cc.position.towards(self.game_info.map_center, 5))
                    else:
                        await self.build(self.s_args[1], near=th.position.towards(self.game_info.map_center, 5))

    async def unit_micro(self, target=None):
        """"""
        if target is None:
            target = self.enemy_start_locations[0]
        tags = self.attack_force_tags
        actions = []
        tb_removed = []
        for tg in tags:
            unit = self.units.by_tag(tg)
            tags[tg]["hp_curr"] = unit.health #update current hp
            ret = tags[tg]["retreat"]
            hpc = tags[tg]["hp_curr"]
            hpp = tags[tg]["hp_prev"]

            if (ret > 4 or hpc < 6) and len(self.townhalls.ready) > 0:
                tb_removed.append(tg)
                mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                actions.append(unit.gather(mf))
                continue
            if hpc < (unit.health_max/2) and hpc < hpp:
                mf = self.state.mineral_field.closest_to(self.townhalls.ready.random)
                actions.append(unit.gather(mf))
                tags[tg]["retreat"] += 1

            else:
                actions.append(unit.attack(target))

            if ret and hpc > (unit.health_max/2):
                tags[tg]["retreat"] = 0

            tags[tg]["hp_prev"] = hpc = tags[tg]["hp_curr"]
            #worker.health_prev = worker.health

        for tag in tb_removed:
            del(self.attack_force_tags[tag])

        await self.do_actions(actions)

#HELPERS

    def manage_idle_workers(self):
        actions = []
        if self.townhalls.exists:
            for w in self.workers.idle:
                th = self.townhalls.ready.closest_to(w)
                mfs = self.state.mineral_field.closer_than(10, th)
                if mfs:
                    mf = mfs.closest_to(w)
                    actions.append(w.gather(mf))
        return actions

