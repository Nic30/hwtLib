#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi3 import Axi3_addr
from hwtLib.amba.axi4 import Axi4_w, Axi4_b
from hwtLib.amba.axi_comp.axi4_rDatapump_test import mkReq
from hwtLib.amba.axi_comp.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiWDatapumpIntf
from hwtLib.amba.interconnect.wStrictOrder import WStrictOrderInterconnect
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from pyMathBitPrecise.bit_utils import mask


class WStrictOrderInterconnecComplex(Unit):

    def _config(self):
        WStrictOrderInterconnect._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dp = Axi_wDatapump(axiAddrCls=Axi3_addr)
            self.ic = WStrictOrderInterconnect()

            self.aw = Axi3_addr()._m()
            self.w = Axi4_w()._m()
            self.b = Axi4_b()
            self.drivers = HObjList(AxiWDatapumpIntf()
                                    for _ in range(int(self.DRIVER_CNT)))

    def _impl(self):
        propagateClkRstn(self)
        dp = self.dp
        ic = self.ic

        self.aw(dp.a)
        self.w(dp.w)
        dp.b(self.b)

        dp.driver(ic.wDatapump)
        ic.drivers(self.drivers)


class WStrictOrderInterconnectComplexTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = WStrictOrderInterconnecComplex()
        u.MAX_TRANS_OVERLAP = cls.MAX_TRANS_OVERLAP = 4
        cls.DATA_WIDTH = u.DATA_WIDTH
        u.DRIVER_CNT = cls.DRIVER_CNT = 3
        return cls.u

    def test_3x128(self, N=128):
        u = self.u
        m = Axi3DenseMem(u.clk, axiAW=u.aw, axiW=u.w, axiB=u.b)
        _mask = mask(self.DATA_WIDTH // 8)
        data = [[self._rand.getrandbits(self.DATA_WIDTH) for _ in range(N)]
                for _ in range(self.DRIVER_CNT)]

        dataAddress = [m.malloc(N * self.DATA_WIDTH // 8)
                       for _ in range(self.DRIVER_CNT)]

        for di, _data in enumerate(data):
            req = u.drivers[di].req._ag
            wIn = u.drivers[di].w._ag
            dataIt = iter(_data)

            addr = dataAddress[di]
            end = False
            while True:
                frameSize = self._rand.getrandbits(4) + 1
                frame = []
                try:
                    for _ in range(frameSize):
                        frame.append(next(dataIt))
                except StopIteration:
                    end = True

                if frame:
                    req.data.append(mkReq(addr, len(frame) - 1))
                    wIn.data.extend([(d, _mask, i == len(frame) - 1)
                                     for i, d in enumerate(frame)])
                    addr += len(frame) * self.DATA_WIDTH // 8
                if end:
                    break

        r = self.randomize
        for d in u.drivers:
            r(d.req)
            r(d.w)
            r(d.ack)

        r(u.aw)
        r(u.w)
        r(u.b)

        self.runSim(self.DRIVER_CNT * N * 40 * Time.ns)
        for i, baseAddr in enumerate(dataAddress):
            inMem = m.getArray(baseAddr, self.DATA_WIDTH // 8, N)
            self.assertValSequenceEqual(inMem, data[i], "driver:%d" % i)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(WStrictOrderInterconnectTC('test_randomized'))
    suite.addTest(unittest.makeSuite(WStrictOrderInterconnectComplexTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
