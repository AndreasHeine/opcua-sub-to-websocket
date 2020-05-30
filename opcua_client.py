from opcua import Client, ua
import asyncio, websockets, json

loop = asyncio.get_event_loop()

class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another 
    thread if you need to do such a thing
    """
    def __init__(self):
        """
        called once
        """
        self.node = None
        self.val = None
        self.data = None
        self.event = None
        self.status = None

    def datachange_notification(self, node, val, data):
        """
        called for every datachange notification from server
        """
        self.node = node
        self.val = val
        self.data = data
        print(val)
    
    def event_notification(self, event):
        """
        called for every event notification from server
        """
        self.event = event

    def status_change_notification(self, status):
        """
        called for every status change notification from server
        """
        self.status = status

url = "opc.tcp://127.0.0.1:4840"
client = Client(url)
handler = SubHandler()
subscription = None
nodes_to_subscribe = ["ns=2;i=2", "ns=0;i=2267", "ns=0;i=2259"]

async def connect(client):
    print("Connecting...")
    client.connect()
    print(f"Connected to: {url}!")

async def disconnect(client, subscription, sub_handle_list):
    await unsubscribe(client, subscription, sub_handle_list)
    subscription.delete()
    client.disconnect()
    print(f"Disconnected!")

async def subscribe(client, subscription, nodes_to_subscribe, handler):
    print("Subscribe all nodes!")
    subscription = client.create_subscription(500, handler)
    sub_handle_list = []
    for node in nodes_to_subscribe:
        handle = subscription.subscribe_data_change(client.get_node(node))
        sub_handle_list.append(handle)
    return sub_handle_list

async def unsubscribe(client, subscription, sub_handle_list):
    print("Unsubscribe all nodes!")
    for handle in sub_handle_list:
        subscription.unsubscribe(handle)

async def get_service_level(client, case):
    service_level = client.get_node("ns=0;i=2267").get_value()
    #print("Servicelevel", service_level)
    if service_level >= 200:
        return 3
    else:
        return 4

async def main(client, subscription, nodes_to_subscribe, handler):
    case = 0
    sub_handle_list = []
    while 1:
        if case == 1:
            #connect
            try:
                await connect(client=client)
                case = 2
            except:
                case = 1
                await asyncio.sleep(0)
        elif case == 2:
            #subscribe
            try:
                sub_handle_list = await subscribe(client=client, subscription=subscription, nodes_to_subscribe=nodes_to_subscribe, handler=handler)
                case = 3
            except:
                case = 4
                await asyncio.sleep(0)
        elif case == 3:
            #running
            try:
                case = await get_service_level(client=client, case=case)
                await asyncio.sleep(2)
            except:
                case = 4
        elif case == 4:
            #disconnect clean+
            try:
                await disconnect(client=client, subscription=subscription, sub_handle_list=sub_handle_list)
            except:
                await asyncio.sleep(0)
            case = 0
        else:
            case = 1
            await asyncio.sleep(5)

async def ws_handler(websocket, path):
    while 1:
        await asyncio.sleep(0)
        if handler.node:
            await websocket.send(json.dumps({
                "id": str(handler.node.nodeid), 
                "browsname": str(handler.node.get_browse_name()), 
                "value": str(handler.val)
                }))
            handler.node = None

start_server = websockets.serve(ws_handler=ws_handler, host="127.0.0.1", port=8000)

asyncio.ensure_future(start_server, loop=loop)
asyncio.ensure_future(main(client=client, subscription=subscription, nodes_to_subscribe=nodes_to_subscribe, handler=handler), loop=loop)
loop.run_forever()