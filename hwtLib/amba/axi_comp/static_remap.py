from hwt.code import connect
from hwtLib.abstract.busStaticRemap import BusStaticRemap
from hwtLib.amba.axi4 import Axi4
from hwt.synthesizer.param import Param


class AxiStaticRemap(BusStaticRemap):
    """
    :class:`.BusStaticRemap` implementation for AXI3/4 interfaces
    :note: this component only remaps some memory regions, but it does not preform the address checking
    
    .. hwt-schematic:: _example_AxiStaticRemap
    """

    def __init__(self, intfCls=Axi4):
        self.intfCls = intfCls
        super(AxiStaticRemap, self).__init__()

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        BusStaticRemap._config(self)
        self.intfCls._config(self)

    def _impl(self):
        # for each remaped region substitute the address offset
        connect(self.m, self.s, exclude={self.m.ar.addr, self.m.aw.addr})
        MM = self.MEM_MAP
        self.translate_addr_signal(
            MM, self.m.ar.addr, self.s.ar.addr)
        self.translate_addr_signal(
            MM, self.m.aw.addr, self.s.aw.addr)

def _example_AxiStaticRemap():
    u = AxiStaticRemap()
    u.MEM_MAP = [(0x0, 0x1000, 0x1000),
                 (0x1000, 0x1000, 0x0),
                 ]
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiStaticRemap()
    print(toRtl(u))
