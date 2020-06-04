'''
Work in progress do not use!

TO DO:
-maybe implement max queuesize
-refactor and beautifying work
'''

import asyncio, websockets, json
from asyncua import Client, ua, Node
from asyncua.common.events import Event

datachange_notification_queue = []
event_notification_queue = []
 
class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        datachange_notification_queue.append((node, val, data))
        # print(node, val)

    def event_notification(self, event: Event):
        """
        called for every event notification from server
        """
        event_notification_queue.append(event)
        # print(event)


async def main():
    url = "opc.tcp://127.0.0.1:4840"
    client = Client(url=url)
    handler = SubscriptionHandler()
    nodes_to_subscribe = ["ns=2;i=2", "ns=0;i=2267", "ns=0;i=2259"] #node-id
    events_to_subscribe = [("ns=2;i=1", "ns=2;i=3")] #(eventtype-node-id, event-node-id)
    subscription = None
    case = 0
    sub_handle_list = []
    while 1:
        if case == 1:
            #connect
            print("connecting...")
            try:
                await client.connect()
                print("connected!")
                case = 2
            except:
                print("connection error!")
                case = 1
                await asyncio.sleep(5)
        elif case == 2:
            #subscribe all nodes and events
            print("subscribing nodes and events...")
            try:
                subscription = await client.create_subscription(50, handler)
                sub_handle_list = []
                if nodes_to_subscribe:
                    for node in nodes_to_subscribe:
                        handle = await subscription.subscribe_data_change(client.get_node(node))
                        sub_handle_list.append(handle)
                if events_to_subscribe:
                    for event in events_to_subscribe:
                        handle = await subscription.subscribe_events(event[0], event[1])
                        sub_handle_list.append(handle)
                print("subscribed!")
                case = 3
            except:
                print("subscription error")
                case = 4
                await asyncio.sleep(0)
        elif case == 3:
            #running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
            try:
                if users == set():
                    datachange_notification_queue.clear()
                    event_notification_queue.clear()
                service_level = await client.get_node("ns=0;i=2267").get_value()
                print(service_level)
                print("datachange_notification_queue ", datachange_notification_queue)
                print("event_notification_queue ", event_notification_queue)
                if service_level >= 200:
                    case = 3
                else:
                    case = 4
                await asyncio.sleep(5)
            except:
                case = 4
        elif case == 4:
            #disconnect clean = unsubscribe, delete subscription then disconnect
            print("disconnecting...")
            try:
                if sub_handle_list:
                    for handle in sub_handle_list:
                        await subscription.unsubscribe(handle)
                await subscription.delete()
                await client.disconnect()
                print("disconnected!")
            except:
                print("disconnection error!")
                subscription = None
                sub_handle_list = []
                client = Client(url=url)
                await asyncio.sleep(0)
            case = 0
        else:
            #wait
            case = 1
            await asyncio.sleep(5)

users = set()
user_id = 0

async def register(websocket):
    global user_id
    users.add(websocket)
    user_id += 1
    # print("USER_ID; ",user_id)
    await websocket.send(json.dumps({
        "registerd": True,
        "id": user_id
    }))
    # print(users)

async def unregister(websocket):
    users.remove(websocket)
    await websocket.send(json.dumps({
        "registerd": False,
    }))
    # print(users)

async def ws_handler(websocket, path):
    await register(websocket)
    try:
        while 1:
            await asyncio.sleep(0)
            if datachange_notification_queue:
                for datachange in datachange_notification_queue:
                    await websocket.send(json.dumps({
                        "type": "datachange",
                        "datachange": str(datachange)
                        }))
                    datachange_notification_queue.pop(0)

            if event_notification_queue:
                for event in event_notification_queue:
                    await websocket.send(json.dumps({
                        "type": "event",
                        "event": str(event), 
                        }))
                    event_notification_queue.pop(0)

    finally:
        await unregister(websocket)

start_server = websockets.serve(ws_handler=ws_handler, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    asyncio.ensure_future(main())
    asyncio.ensure_future(start_server)
    asyncio.get_event_loop().run_forever()