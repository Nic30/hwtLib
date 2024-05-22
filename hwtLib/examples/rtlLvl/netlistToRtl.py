from io import StringIO
from typing import Dict

from hdlConvertorAst.translate.common.name_scope import NameScope
from hwt.hdl.portItem import HdlPortItem
from hwt.serializer.store_manager import SaveToStream
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from ipCorePackager.constants import DIRECTION


def netlistToVhdlStr(name: str, netlist: RtlNetlist,
                     hwIOs: Dict[RtlSignal, DIRECTION]):
    name_scope = NameScope(None, name, True)
    buff = StringIO()
    store_manager = SaveToStream(Vhdl2008Serializer, buff)
    netlist.create_HdlModuleDec(name, store_manager, {})
    netlist.hwIOs = hwIOs
    for s, d in hwIOs.items():
        s._hwIO = True
        pi = HdlPortItem.fromSignal(s, netlist, d)
        # port of current top component
        s.name = name_scope.checked_name(s.name, s)
        pi.connectInternSig(s)
        netlist.ent.ports.append(pi)
    netlist.ent.ports.sort(key=lambda x: x.name)
    netlist.create_HdlModuleDef(DummyPlatform(), store_manager)
    store_manager.write(netlist.arch)
    return buff.getvalue()
