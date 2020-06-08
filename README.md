# opcua-sub-to-websocket  
### OPC UA Server -> OPC UA Client / WebSocket Server -> WebSocket Client   
  
You can use this to push data from a "OPC UA Subscription" over a WebSocket to the Browser/WebSocket-Client  
  
"opcua-sub-to-websocket" can support multiple WebSocket-Clients and pushes all received subscription-notifications to all WebSocket-Clients.
  
Provided is a sample "OPC UA Server" which generates random events and datachanges!  
The timing can be adjusted in opcua_server.py:
```
async def random_updater(random_node):
    while True:
        await asyncio.sleep(random.randint(1,10)/10) #<-------------
        random_node.set_value(ua.DataValue(ua.Variant(random.randint(70,90), ua.VariantType.UInt64)))
        print(datetime.now(), "datachange")

async def event_gen(myevgen):
        count = 0
        while 1:
            await asyncio.sleep(random.randint(1,10)/10) #<-------------
            myevgen.event.Message = ua.LocalizedText("MyFirstEvent %d" % count)
            myevgen.event.Severity = count
            myevgen.event.MyNumericProperty = count
            myevgen.event.MyStringProperty = "Property " + str(count)
            myevgen.trigger()
            count += 1
            print(datetime.now(), "event")
```

also provided is a test HTML-Page with some basic JavaScript to connect/reconnect to WebSockets:   
```
    var content = {}
    let data
    function connect() {
      let url = "ws://127.0.0.1:8000";
      let s = new WebSocket(url);
      s.onopen = function(event) {
        console.log(event);
      }
      s.onclose = function(event) {
        console.log(event);
        setTimeout(function() {
          connect();
        }, 2000);
      }
      s.onerror = function(event) {
        console.log(event);
      }
      s.onmessage = function(event){
        data = JSON.parse(event.data);
        //console.log(data);
        if (data.topic == "datachange notification"){
          content[data.payload.node] = {
            value: data.payload.value,
            data: data.payload.data,
          };
        }
        if (data.topic == "event notification"){
          content["Event"] = data;
        }
        if (data.topic == "status change notification"){
          content["Status"] = data;
        }
        document.getElementById("content").innerHTML = JSON.stringify(content);
      }
    }
    connect();
```
  
aswell as an python based WebSocket Client :  
  
```
import asyncio, websockets

async def request():
    uri = "ws://127.0.0.1:8000"
    async with websockets.connect(uri) as websocket:
        while 1:
            msg = await websocket.recv()
            print(msg)

asyncio.get_event_loop().run_until_complete(request())
```
  
  
  
Interested? Contact me: info@andreas-heine.net
