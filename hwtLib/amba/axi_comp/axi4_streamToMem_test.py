#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi_comp.axi4_streamToMem import Axi4streamToMem
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from pycocotb.constants import CLK_PERIOD


class Axi4_streamToMemTC(SimTestCase):
    @classmethod
    def setUpClass(cls):
        SimTestCase.setUpClass()

        u = cls.u = Axi4streamToMem()

        def mkRegisterMap(u):
            addrProbe = AddressSpaceProbe(u.cntrlBus,
                                          lambda intf: intf.ar.addr)
            cls.regs = AxiLiteMemSpaceMaster(u.cntrlBus, addrProbe.discovered)

        cls.DATA_WIDTH = 32
        u.DATA_WIDTH = cls.DATA_WIDTH

        cls.prepareUnit(u, onAfterToRtl=mkRegisterMap)

    def test_nop(self):
        u = self.u

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(u.axi.ar._ag.data)
        self.assertEmpty(u.axi.aw._ag.data)
        self.assertEmpty(u.axi.w._ag.data)

    def test_simpleTransfer(self):
        u = self.u
        regs = self.regs
        N = 33

        sampleData = [self._rand.getrandbits(self.DATA_WIDTH) for _ in range(N)]
        m = Axi3DenseMem(u.clk, u.axi)
        blockPtr = m.malloc(self.DATA_WIDTH // 8 * N)

        u.dataIn._ag.data.extend(sampleData)

        regs.baseAddr.write(blockPtr)
        regs.control.write(1)

        self.runSim(N * 3 * CLK_PERIOD)

        self.assertValSequenceEqual(m.getArray(blockPtr, self.DATA_WIDTH // 8, N),
                                    sampleData)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_streamToMemTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(Axi4_streamToMemTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
