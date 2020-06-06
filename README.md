# opcua-sub-to-websocket  
### OPC UA Server -> OPC UA Client / Websocket Server -> Websocket Client   
  
You can use this to Push Data from a OPC UA Subscription over a Websocket to the Browser/Websocket-Client  
  
The OPC UA Subscription Gateway "async_client.py" can support multiple Websocket-Clients and pushes all received Subscription notifications to all Websocket-Clients.
  
Provided is a Sample OPC UA Server which generates random Events and Datachanges  
The timing can be ajusted in opcua_server.py:
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

also provided is a test HTML Page "test.html" with some basic JavaScript to connect/reconnect to a Websockets:   
```
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Andreas Heine</title>
</head>
<body>
<div id="content"> Nothing </div>
<script>
    var content = "";
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
        //data = JSON.parse(event.data);
        console.log(event.data);
        content = event.data + "<br>" + content;
        document.getElementById("content").innerHTML = content;
      }
    }
    connect();
</script>
</body>
</html>
```
  
aswell as an Python based Websocket-Client "ws_client.py":  
  
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
