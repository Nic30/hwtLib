#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi3 import Axi3_addr
from hwtLib.amba.axi4 import Axi4_w, Axi4_b, Axi4_addr, Axi4
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.amba.datapump.interconnect.wStrictOrder import WStrictOrderInterconnect
from hwtLib.amba.datapump.intf import AxiWDatapumpIntf
from hwtLib.amba.datapump.test import Axi_datapumpTC
from hwtLib.amba.datapump.w import Axi_wDatapump
from pyMathBitPrecise.bit_utils import mask


class WStrictOrderInterconnecComplex(Unit):

    def _config(self):
        WStrictOrderInterconnect._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dp = Axi_wDatapump(axiCls=Axi4)
            self.ic = WStrictOrderInterconnect()
            self.ic.ID_WIDTH = 0

            self.aw = Axi4_addr()._m()
            self.w = Axi4_w()._m()
            self.b = Axi4_b()
            self.drivers = HObjList(AxiWDatapumpIntf()
                                    for _ in range(int(self.DRIVER_CNT)))
            for d in self.drivers:
                d.ID_WIDTH = self.ic.ID_WIDTH

    def _impl(self):
        propagateClkRstn(self)
        dp = self.dp
        ic = self.ic

        self.aw(dp.axi.aw)
        self.w(dp.axi.w)
        dp.axi.b(self.b)

        dp.driver(ic.wDatapump)
        ic.drivers(self.drivers)


class WStrictOrderInterconnectComplexTC(SimTestCase):
    LEN_MAX_VAL = 255

    @classmethod
    def setUpClass(cls):
        u = cls.u = WStrictOrderInterconnecComplex()
        u.MAX_TRANS_OVERLAP = cls.MAX_TRANS_OVERLAP = 4
        cls.DATA_WIDTH = u.DATA_WIDTH
        u.DRIVER_CNT = cls.DRIVER_CNT = 3
        cls.compileSim(u)

    def test_3x128(self, N=128):
        u = self.u
        m = AxiSimRam(axiAW=u.aw, axiW=u.w, axiB=u.b)
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
                    req.data.append(Axi_datapumpTC.mkReq(self, addr, len(frame) - 1))
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
            self.assertValSequenceEqual(inMem, data[i], f"driver:{i:d}")


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(WStrictOrderInterconnectTC('test_randomized'))
    suite.addTest(unittest.makeSuite(WStrictOrderInterconnectComplexTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
