try:
    from opcua import ua, uamethod, Server
    import asyncio
    import random
except ImportError as e:
    print(e)


"""
OPC-UA-Server Setup
"""
server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4840")
server.set_server_name("OPCUA-Test")
address_space = server.register_namespace("testnamespace")

"""
OPC-UA-Modeling
"""
root_node = server.get_root_node()
object_node = server.get_objects_node()
server_node = server.get_server_node()

parameter_obj = object_node.add_object(address_space, "Parameter")
random_node = parameter_obj.add_variable(address_space, "random", ua.Variant(0, ua.VariantType.UInt64))


"""
OPC-UA-VarUpdater
"""

#for me async eventloop works just fine, you could also use threads for that!

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
        await asyncio.sleep(random.randint(1,10))
        random_node.set_value(ua.DataValue(ua.Variant(random.randint(70,90), ua.VariantType.UInt64)))
            
loop = asyncio.get_event_loop()
asyncio.ensure_future(servicelevel_updater(server.get_node("ns=0;i=2267")))
asyncio.ensure_future(random_updater(random_node))

"""
OPC-UA-Server Start
"""
if __name__ == "__main__":
    try:
        server.start()
        loop.run_forever()            
    except KeyboardInterrupt:
        loop.close()
        server.stop()