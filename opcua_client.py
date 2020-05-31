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

    def datachange_notification(self, node, val, data):
        """
        called for every datachange notification from server
        """
        self.node = node
        self.val = val
        self.data = data
        print(node, val, data)
    
    def event_notification(self, event):
        """
        called for every event notification from server
        """
        self.event = event
        print(event)

url = "opc.tcp://127.0.0.1:4840"
client = Client(url)
handler = SubHandler()
subscription = None
nodes_to_subscribe = ["ns=2;i=2", "ns=0;i=2267", "ns=0;i=2259"] #node-id
events_to_subscribe = [("ns=2;i=1", "ns=2;i=3")] #(eventtype-node-id, event-node-id)

async def connect(client):
    print("Connecting...")
    client.connect()
    print(f"Connected to: {url}!")

async def disconnect(client, subscription, sub_handle_list):
    await unsubscribe(client, subscription, sub_handle_list)
    subscription.delete()
    client.disconnect()
    print(f"Disconnected!")

async def subscribe(client, subscription, nodes_to_subscribe, events_to_subscribe, handler):
    print("Subscribe nodes and events!")
    subscription = client.create_subscription(500, handler)
    sub_handle_list = []
    if nodes_to_subscribe:
        for node in nodes_to_subscribe:
            handle = subscription.subscribe_data_change(client.get_node(node))
            sub_handle_list.append(handle)
    if events_to_subscribe:
        for event in events_to_subscribe:
            handle = subscription.subscribe_events(event[0], event[1])
            sub_handle_list.append(handle)
    return sub_handle_list

async def unsubscribe(client, subscription, sub_handle_list):
    print("Unsubscribe all nodes!")
    if sub_handle_list:
        for handle in sub_handle_list:
            subscription.unsubscribe(handle)

async def check_service_level(client):
    service_level = client.get_node("ns=0;i=2267").get_value()
    if service_level >= 200:
        return 3
    else:
        return 4

async def main(client, subscription, nodes_to_subscribe, events_to_subscribe, handler):
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
            #subscribe all nodes and events
            try:
                sub_handle_list = await subscribe(client=client, subscription=subscription, nodes_to_subscribe=nodes_to_subscribe, events_to_subscribe=events_to_subscribe, handler=handler)
                case = 3
            except:
                case = 4
                await asyncio.sleep(0)
        elif case == 3:
            #running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
            try:
                case = await check_service_level(client=client)
                await asyncio.sleep(2)
            except:
                case = 4
        elif case == 4:
            #disconnect clean = unsubscribe, delete subscription then disconnect
            try:
                await disconnect(client=client, subscription=subscription, sub_handle_list=sub_handle_list)
            except:
                await asyncio.sleep(0)
            case = 0
        else:
            #wait
            case = 1
            await asyncio.sleep(5)

async def ws_handler(websocket, path):
    while 1:
        await asyncio.sleep(0)
        if handler.node:
            await websocket.send(json.dumps({
                "type": "datachange",
                "id": str(handler.node.nodeid), 
                "browsname": str(handler.node.get_browse_name()), 
                "value": str(handler.val)
                }))
            handler.node = None
            handler.val = None
            handler.data = None
        if handler.event:
            await websocket.send(json.dumps({
                "type": "event",
                "event": str(handler.event)
                }))
            handler.event = None

start_server = websockets.serve(ws_handler=ws_handler, host="127.0.0.1", port=8000)

asyncio.ensure_future(start_server, loop=loop)
asyncio.ensure_future(main(client=client, subscription=subscription, nodes_to_subscribe=nodes_to_subscribe, events_to_subscribe=events_to_subscribe, handler=handler), loop=loop)
loop.run_forever()