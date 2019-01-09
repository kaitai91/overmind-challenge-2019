import json
from pathlib import Path

import sc2

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")
            actions = []
            for worker in self.workers:
                actions.append(worker.attack(self.enemy_start_locations[0]))
            await self.do_actions(actions)