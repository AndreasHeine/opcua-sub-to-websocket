from opcua import Client
from opcua import ua, common
import asyncio
import websockets
import json

loop = asyncio.get_event_loop()

class SubHandler(object):
    def __init__(self):
        self.node = None
        self.val = None
        self.data = None

    def datachange_notification(self, node, val, data):
        self.node = node
        self.val = val
        self.data = data
        
url = "opc.tcp://127.0.0.1:4840"
client = Client(url)

client.connect()
print(f"Connected to: {url}")

handler = SubHandler()
sub = client.create_subscription(500, handler)

nodes_to_subscribe = ["ns=2;i=2", "ns=0;i=2267"]
sub_handle_list = []
for node in nodes_to_subscribe:
    handle = sub.subscribe_data_change(client.get_node(node))
    sub_handle_list.append(handle)

async def response(websocket, path):
    while 1:
        await asyncio.sleep(0)
        if handler.node:
            await websocket.send(json.dumps({
                "id": str(handler.node.nodeid), 
                "browsname": str(handler.node.get_browse_name()), 
                "value": str(handler.val)
                }))
            handler.node = None

start_server = websockets.serve(ws_handler=response, host="127.0.0.1", port=8000)

asyncio.ensure_future(start_server, loop=loop)
loop.run_forever()