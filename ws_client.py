import asyncio, websockets, json
from datetime import datetime

async def request():
    uri = "ws://127.0.0.1:8000"
    async with websockets.connect(uri) as websocket:
        while 1:
            msg = await websocket.recv()
            data = json.loads(msg)
            try:
                if data["type"] == "keep-alive":
                    pass
                else:
                    print("ws_recv", datetime.now(), msg)
            except:
                pass

asyncio.get_event_loop().run_until_complete(request())