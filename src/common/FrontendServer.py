import asyncio
import websockets


# simple websocket "server" according to https://websockets.readthedocs.io/en/stable/intro.html
class FrontendServer():

    def __init__(self):
        self.queue = []
        self.start_server = websockets.serve(self.jsonSend, '127.0.0.1', 5678)

    async def jsonSend(self, websocket, path):
        while True:
            while len(self.queue) > 0:
                msg = self.queue[0]
                await websocket.send(msg)
                self.queue.pop(0)

            await asyncio.sleep(0)

    def addMessageToQueue(self, msg):
        self.queue.append(msg)
        return
