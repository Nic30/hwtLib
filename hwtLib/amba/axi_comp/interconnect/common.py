from itertools import chain
from typing import Optional

from hwt.hwIOs.utils import addClkRstn
from hwt.hObjList import HObjList
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwtLib.abstract.busInterconnect import BusInterconnect


class AxiInterconnectCommon(BusInterconnect):

    def __init__(self, hwIOCls, hdl_name_override:Optional[str]=None):
        self.hwIOCls = hwIOCls
        super(AxiInterconnectCommon, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        super(AxiInterconnectCommon, self)._config()
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.MAX_TRANS_OVERLAP = HwParam(16)
        self.hwIOCls._config(self)

    def _declr(self, has_r=True, has_w=True):
        addClkRstn(self)
        AXI = self.hwIOCls
        with self._hwParamsShared():
            self.s = HObjList([AXI() for _ in self.MASTERS])

        with self._hwParamsShared(exclude=({}, {"ADDR_WIDTH"})):
            self.m = HObjList([AXI()._m() for _ in self.SLAVES])

        for i in chain(self.m, self.s):
            i.HAS_W = has_w
            i.HAS_R = has_r

        for s, (_, size) in zip(self.m, self.SLAVES):
            s.ADDR_WIDTH = log2ceil(size - 1)
