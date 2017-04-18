#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.amba.axi3 import Axi3_addr
from hwtLib.amba.axi4 import Axi4_w, Axi4_b
from hwtLib.amba.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwtLib.amba.interconnect.wStrictOrder import WStrictOrderInterconnect
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem


class WStrictOrderInterconnecComplex(Unit):
    def _config(self):
        WStrictOrderInterconnect._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dp = Axi_wDatapump(axiAddrCls=Axi3_addr)
            self.ic = WStrictOrderInterconnect()

            self.aw = Axi3_addr()
            self.aw.LOCK_WIDTH = 2
            self.w = Axi4_w()
            self.b = Axi4_b()
            self.drivers = AxiWDatapumpIntf(multipliedBy=self.DRIVER_CNT)

    def _impl(self):
        propagateClkRstn(self)
        dp = self.dp
        ic = self.ic

        self.aw ** dp.a
        self.w ** dp.w
        dp.b ** self.b

        dp.driver ** ic.wDatapump

        ic.drivers ** self.drivers


class WStrictOrderInterconnectComplexTC(SimTestCase):
    def setUp(self):
        super(WStrictOrderInterconnectComplexTC, self).setUp()
        self.u = WStrictOrderInterconnecComplex()
        self.MAX_TRANS_OVERLAP = 4
        self.u.MAX_TRANS_OVERLAP.set(self.MAX_TRANS_OVERLAP)
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val

        self.DRIVER_CNT = 3
        self.u.DRIVER_CNT.set(self.DRIVER_CNT)
        self.prepareUnit(self.u)

    def test_3x128(self, N=128):
        u = self.u
        m = Axi3DenseMem(u.clk, axiAW=u.aw, axiW=u.w, axiB=u.b)
        _mask = mask(self.DATA_WIDTH // 8)
        data = [[self._rand.getrandbits(self.DATA_WIDTH) for _ in range(N)]
                for _ in range(self.DRIVER_CNT)]

        dataAddress = [m.malloc(N * self.DATA_WIDTH // 8) for _ in range(self.DRIVER_CNT)]

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
                    req.data.append(req.mkReq(addr, len(frame) - 1))
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

        self.doSim(self.DRIVER_CNT * N * 50 * Time.ns)
        for i, baseAddr in enumerate(dataAddress):
            inMem = m.getArray(baseAddr, self.DATA_WIDTH // 8, N)
            self.assertValSequenceEqual(inMem, data[i], "driver:%d" % i)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(WStrictOrderInterconnectTC('test_randomized'))
    suite.addTest(unittest.makeSuite(WStrictOrderInterconnectComplexTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
