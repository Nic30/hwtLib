from itertools import chain
from typing import Optional

from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwtLib.abstract.busInterconnect import BusInterconnect


class AxiInterconnectCommon(BusInterconnect):

    def __init__(self, hwIOCls, hdlName:Optional[str]=None):
        self.hwIOCls = hwIOCls
        super(AxiInterconnectCommon, self).__init__(hdlName=hdlName)

    def hwConfig(self):
        super(AxiInterconnectCommon, self).hwConfig()
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.MAX_TRANS_OVERLAP = HwParam(16)
        self.hwIOCls.hwConfig(self)

    def hwDeclr(self, has_r=True, has_w=True):
        addClkRstn(self)
        AXI = self.hwIOCls
        with self._hwParamsShared():
            self.s = HwIOArray(AXI() for _ in self.MASTERS)

        with self._hwParamsShared(exclude=({}, {"ADDR_WIDTH"})):
            self.m = HwIOArray(AXI() for _ in self.SLAVES)._m()

        for i in chain(self.m, self.s):
            i.HAS_W = has_w
            i.HAS_R = has_r

        for s, (_, size) in zip(self.m, self.SLAVES):
            s.ADDR_WIDTH = log2ceil(size - 1)
