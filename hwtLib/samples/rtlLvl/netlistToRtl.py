from hwt.serializer.vhdl.formater import formatVhdl


def netlistToVhdlStr(name, netlist, interfaces):
    return formatVhdl("\n".join([str(o)
                                 for o in netlist.synthesize(name, interfaces)
                                 ])
                      )
