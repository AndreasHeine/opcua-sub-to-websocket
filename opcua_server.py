from opcua import ua, Server
import asyncio, random, time
from datetime import datetime

server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4840")
server.set_server_name("OPCUA-Test")
address_space = server.register_namespace("http://andreas-heine.net/UA")

root_node = server.get_root_node()
object_node = server.get_objects_node()
server_node = server.get_server_node()

parameter_obj = object_node.add_object(address_space, "Parameter")
random_node = parameter_obj.add_variable(address_space, "random", ua.Variant(0, ua.VariantType.UInt64))

etype = server.create_custom_event_type(address_space, 'MyFirstEvent', ua.ObjectIds.BaseEventType, [('MyNumericProperty', ua.VariantType.Float), ('MyStringProperty', ua.VariantType.String)])
myevgen = server.get_event_generator(etype, parameter_obj)

vars_obj = object_node.add_object(address_space, "Vars")
var_list = []
for i in range(100):
    var = vars_obj.add_variable(ua.NodeId.from_string(f'ns={address_space};s=DB_DATA.Test.var{i}'), f'Test.var{i}', 0)
    var.set_writable(True)
    var_list.append(var)

async def servicelevel_updater(servicelevel_node):
    value = 0
    while True:
        await asyncio.sleep(1)
        #no redundant servers!
        if value < 200:
            value = 250
            servicelevel_node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Byte)))

async def random_updater(random_node):
    while True:
        await asyncio.sleep(random.randint(1,100)/10) #<-------------
        random_node.set_value(ua.DataValue(ua.Variant(random.randint(70,90), ua.VariantType.UInt64)))
        print(datetime.now(), "datachange")

async def event_gen(myevgen):
        count = 0
        while 1:
            await asyncio.sleep(random.randint(1,100)/100) #<-------------
            myevgen.event.Message = ua.LocalizedText("MyFirstEvent %d" % count)
            myevgen.event.Severity = count
            myevgen.event.MyNumericProperty = count
            myevgen.event.MyStringProperty = "Property " + str(count)
            myevgen.trigger()
            count += 1
            print(datetime.now(), "event")

async def vars_updater(var_list):
        while 1:
            for each in var_list:
                each.set_value(random.randint(1,100))
            print(datetime.now(), "bulk datachange")
            await asyncio.sleep(random.randint(1,100)/10)

async def status_updater(status_node):
    while True:
        status_node.set_value(ua.DataValue(ua.Variant(ua.ServerState.Running, ua.VariantType.Int32)))
        await asyncio.sleep(10)
        status_node.set_value(ua.DataValue(ua.Variant(ua.ServerState.Suspended, ua.VariantType.Int32)))
        await asyncio.sleep(10)
        
      
loop = asyncio.get_event_loop()
asyncio.ensure_future(servicelevel_updater(server.get_node("ns=0;i=2267")))
asyncio.ensure_future(random_updater(random_node))
asyncio.ensure_future(event_gen(myevgen))
asyncio.ensure_future(status_updater(server.get_node("ns=0;i=2259")))
asyncio.ensure_future(vars_updater(var_list))

if __name__ == "__main__":
    try:
        server.start()
        loop.run_forever()            
    except KeyboardInterrupt:
        loop.close()
        server.stop()
