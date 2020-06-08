"""
TO DO:
-performance enhancements

"""

import asyncio, websockets, json
from asyncua import Client, ua, Node
from asyncua.common.events import Event
from datetime import datetime


####################################################################################
# Globals:
####################################################################################

# OPC UA Client
server_url = "opc.tcp://127.0.0.1:4840"
datachange_notification_queue = []
event_notification_queue = []
status_change_notification_queue = []
nodes_to_subscribe =    [  
                        "ns=2;i=2", 
                        "ns=0;i=2267", 
                        "ns=0;i=2259",
                        ] #node-id
events_to_subscribe =   [
                        ("ns=2;i=1", "ns=2;i=3")
                        ] #(eventtype-node-id, event-node-id)

# WebSocketServer:
ws_ip = "127.0.0.1"
ws_port = 8000
users = set()
user_id = 0


####################################################################################
# OpcUaClient:
####################################################################################

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

    def event_notification(self, event: Event):
        """
        called for every event notification from server
        """
        event_dict = event.get_event_props_as_fields_dict()
        event_notification_queue.append(event_dict)
    
    def status_change_notification(self, status):
        """
        called for every status change notification from server
        """
        status_change_notification_queue.append(status)


async def opcua_client():
    """
    -handles connect/disconnect/reconnect/subscribe/unsubscribe
    -connection-monitoring with cyclic read of the service-level
    """
    client = Client(url=server_url)
    handler = SubscriptionHandler()

    subscription = None
    case = 0
    subscription_handle_list = []
    while 1:
        if case == 1:
            #connect
            print("connecting...")
            try:
                await client.connect()
                await client.load_type_definitions()
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
                subscription_handle_list = []
                if nodes_to_subscribe:
                    for node in nodes_to_subscribe:
                        handle = await subscription.subscribe_data_change(client.get_node(node))
                        subscription_handle_list.append(handle)
                if events_to_subscribe:
                    for event in events_to_subscribe:
                        handle = await subscription.subscribe_events(event[0], event[1])
                        subscription_handle_list.append(handle)
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
                if service_level >= 200:
                    case = 3
                else:
                    case = 4
                await asyncio.sleep(5)
            except:
                case = 4
        elif case == 4:
            #disconnect clean = unsubscribe, delete subscription then disconnect
            print("unsubscribing...")
            try:
                if subscription_handle_list:
                    for handle in subscription_handle_list:
                        await subscription.unsubscribe(handle)
                await subscription.delete()
                print("unsubscribed!")
            except:
                print("unsubscribing error!")
                subscription = None
                subscription_handle_list = []
                await asyncio.sleep(0)
            print("disconnecting...")
            try:
                await client.disconnect()
            except:
                print("disconnection error!")
            case = 0
        else:
            #wait
            case = 1
            await asyncio.sleep(5)


####################################################################################
# Websocketserver:
####################################################################################

async def register(websocket):
    """
    registers the websocket and return a message with an user id and registerd = True
    """
    global user_id
    users.add(websocket)
    user_id += 1
    await websocket.send(json.dumps({
        "registerd": True,
        "id": user_id
    }))

async def unregister(websocket):
    """
    unregisters the websocket and return a message with registerd = False
    """
    users.remove(websocket)
    await websocket.send(json.dumps({
        "registerd": False,
    }))

async def ws_handler(websocket, path):
    """
    ws_handler handles all incoming websocket connections and send a keep-alive to the client
    """
    await register(websocket)
    try:
        while 1:
            await websocket.send(json.dumps({"type": "keep-alive"}))
            await asyncio.sleep(10)
    finally:
        await unregister(websocket)

start_server = websockets.serve(ws_handler=ws_handler, host=ws_ip, port=ws_port)

async def notifier():
    """
    if at leat one user has been registered, the notifier will send all registered clients the queued messages
    """
    while 1:
        if users:
            if datachange_notification_queue:
                for datachange in datachange_notification_queue:
                    message = json.dumps({
                        "ws_send": str(datetime.now()),
                        "topic": "datachange notification",
                        "payload": {
                                    "node": str(datachange[0]),
                                    "value": str(datachange[1]),
                                    "data": str(datachange[2]),
                                    },
                        })
                    await asyncio.wait([user.send(message) for user in users])
                    datachange_notification_queue.pop(0)

            if event_notification_queue:
                for event in event_notification_queue:
                    message = json.dumps({
                        "ws_send": str(datetime.now()),
                        "topic": "event notification",
                        "payload": str(event),
                        })
                    await asyncio.wait([user.send(message) for user in users])
                    event_notification_queue.pop(0)

            if status_change_notification_queue:
                for status in status_change_notification_queue:
                    message = json.dumps({
                        "ws_send": str(datetime.now()),
                        "topic": "status change notification",
                        "payload": str(status),
                        })
                    await asyncio.wait([user.send(message) for user in users])
                    status_change_notification_queue.pop(0)
        await asyncio.sleep(0)


####################################################################################
# Run:
####################################################################################

if __name__ == "__main__":
    asyncio.ensure_future(opcua_client())
    asyncio.ensure_future(notifier())
    asyncio.ensure_future(start_server)
    asyncio.get_event_loop().run_forever()