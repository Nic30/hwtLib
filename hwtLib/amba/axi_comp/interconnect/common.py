from itertools import chain
from typing import Optional

from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.abstract.busInterconnect import BusInterconnect


class AxiInterconnectCommon(BusInterconnect):

    def __init__(self, intfCls, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AxiInterconnectCommon, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        super(AxiInterconnectCommon, self)._config()
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
