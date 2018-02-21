from hwt.serializer.vhdl.serializer import VhdlSerializer


def netlistToVhdlStr(name, netlist, interfaces):
    for s in interfaces:
        s._interface = True

    ctx = VhdlSerializer.getBaseContext()
    return "\n".join([VhdlSerializer.asHdl(o, ctx)
                      for o in netlist.synthesize(name, interfaces)
                      ])
