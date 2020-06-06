# opcua-sub-to-websocket  
### OPC UA Server -> OPC UA Client / Websocket Server -> Websocket Client   
  
You can use this to push data from a "OPC UA Subscription" over a websocket to the browser/websocket-client  
  
"opcua-sub-to-websocket" can support multiple websocket-clients and pushes all received subscription-notifications to all websocket-clients.
  
Provided is a sample "OPC UA Server" which generates random events and datachanges!  
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

also provided is a test HTML-Page with some basic JavaScript to connect/reconnect to websockets:   
```
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Andreas Heine</title>
</head>
<body>
<div id="content"> Data is logged to the console ! </div>
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
        console.log(event.data);
        //content = event.data + "<br>" + content;
        //document.getElementById("content").innerHTML = content;
      }
    }
    connect();
</script>
</body>
</html>
```
  
aswell as an python based websocket-client :  
  
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
