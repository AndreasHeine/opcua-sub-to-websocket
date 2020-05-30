'''
Client:
'''
import asyncio
import websockets

async def request():
    uri = "ws://127.0.0.1:8000"
    async with websockets.connect(uri) as websocket:
        while 1:
            msg = await websocket.recv()
            print(msg)

asyncio.get_event_loop().run_until_complete(request())