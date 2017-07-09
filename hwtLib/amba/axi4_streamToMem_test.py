from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi4_streamToMem import Axi4streamToMem
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster


class Axi4_streamToMemTC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)

        u = self.u = Axi4streamToMem()

        def mkRegisterMap(u, modelCls):
            addrProbe = AddressSpaceProbe(u.cntrlBus,
                                          lambda intf: intf.ar.addr)
            self.regs = AxiLiteMemSpaceMaster(u.cntrlBus, addrProbe.discovered)

        self.DATA_WIDTH = 32
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=mkRegisterMap)

    def test_nop(self):
        u = self.u

        self.doSim(100 * Time.ns)

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
        
        self.doSim(N * 30 * Time.ns) 

        self.assertValSequenceEqual(m.getArray(blockPtr, self.DATA_WIDTH // 8, N), sampleData)
        
        

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_streamToMemTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(Axi4_streamToMemTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
