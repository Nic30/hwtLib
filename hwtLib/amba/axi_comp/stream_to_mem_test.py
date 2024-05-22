#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.sim.memSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtLib.amba.axi_comp.stream_to_mem import Axi4streamToMem
from hwtSimApi.constants import CLK_PERIOD


class Axi4_streamToMemTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = Axi4streamToMem()

        def mkRegisterMap(dut):
            addrProbe = AddressSpaceProbe(dut.cntrlBus,
                                          lambda hwIO: hwIO.ar.addr)
            cls.regs = AxiLiteMemSpaceMaster(dut.cntrlBus, addrProbe.discovered)

        cls.DATA_WIDTH = 32
        dut.DATA_WIDTH = cls.DATA_WIDTH

        cls.compileSim(dut, onAfterToRtl=mkRegisterMap)

    def test_nop(self):
        dut = self.dut

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(dut.axi.aw._ag.data)
        self.assertEmpty(dut.axi.w._ag.data)

    def test_simpleTransfer(self):
        dut = self.dut
        regs = self.regs
        N = 33

        sampleData = [self._rand.getrandbits(self.DATA_WIDTH) for _ in range(N)]
        m = Axi4SimRam(dut.axi)
        blockPtr = m.malloc(self.DATA_WIDTH // 8 * N)

        dut.dataIn._ag.data.extend(sampleData)

        regs.baseAddr.write(blockPtr)
        regs.control.write(1)

        self.runSim(N * 3 * CLK_PERIOD)

        self.assertValSequenceEqual(m.getArray(blockPtr, self.DATA_WIDTH // 8, N),
                                    sampleData)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4_streamToMemTC("test_endstrbMultiFrame")])
    suite = testLoader.loadTestsFromTestCase(Axi4_streamToMemTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
