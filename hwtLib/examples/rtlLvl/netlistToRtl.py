from io import StringIO
from typing import List

from hwt.serializer.vhdl.serializer import Vhdl2008Serializer
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.serializer.store_manager import SaveToStream


def netlistToVhdlStr(name: str, netlist: RtlNetlist, interfaces: List[RtlSignal]):
    for s in interfaces:
        s._interface = True
    buff = StringIO()
    store_manager = SaveToStream(Vhdl2008Serializer, buff)
    netlist.create_HdlModuleDec(name, store_manager, {})
    netlist.create_HdlModuleDef(name, DummyPlatform(), store_manager)
    store_manager.write(netlist.arch)
    return buff.getvalue()
