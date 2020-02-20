from itertools import chain

from hwt.code import log2ceil
from hwt.hdl.types.defs import BIT
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.abstract.busInterconnect import BusInterconnect


def apply_name(unit_instance, sig, name):
    """
    Wrap signal or value in signal of specified name
    """
    if isinstance(sig, (int, bool)):
        t = BIT
    else:
        t = sig._dtype
    s = unit_instance._sig(name, t)
    s(sig)
    return s


class AxiInterconnectCommon(BusInterconnect):

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiInterconnectCommon, self).__init__()

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.MAX_TRANS_OVERLAP = Param(16)
        self.intfCls._config(self)

    def _declr(self, has_r=True, has_w=True):
        addClkRstn(self)
        AXI = self.intfCls
        with self._paramsShared():
            self.s = HObjList([AXI() for _ in self.MASTERS])

        with self._paramsShared(exclude=({}, {"ADDR_WIDTH"})):
            self.m = HObjList([AXI()._m() for _ in self.SLAVES])

        for i in chain(self.m, self.s):
            i.HAS_W = has_w
            i.HAS_R = has_r

        for s, (_, size) in zip(self.m, self.SLAVES):
            s.ADDR_WIDTH = log2ceil(size - 1)
