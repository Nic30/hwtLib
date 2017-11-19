from hwt.serializer.vhdl.serializer import VhdlSerializer


def netlistToVhdlStr(name, netlist, interfaces):
    ctx = VhdlSerializer.getBaseContext()
    return "\n".join([VhdlSerializer.asHdl(o, ctx)
                      for o in netlist.synthesize(name, interfaces)
                      ])
