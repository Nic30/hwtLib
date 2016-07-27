from copy import copy
import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.mem.fifo import Fifo


class FifoTC(unittest.TestCase):
    def setUp(self):
        self.u = u = Fifo()
        u.DATA_WIDTH.set(8)
        u.DEPTH.set(4)
        synthesised(u)
        self.procs = autoAddAgents(u)

    
    def doSim(self, name, time=80 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                    "tmp/fifo_" + name + ".vcd",
                    time=time)
    
    
    
    def test_fifoWritterDisable(self):
        u = self.u
        
        data = [1, 2, 3, 4]
        u.dataIn._ag.data = copy(data)
        u.dataIn._ag.enable = False

        self.doSim("fifoWritterDisable")
        
        self.assertSequenceEqual([], u.dataOut._ag.data)
        self.assertSequenceEqual(data, u.dataIn._ag.data)
        
        
    
    def test_normalOp(self):
        u = self.u
        
        expected = [1, 2, 3, 4]
        u.dataIn._ag.data = copy(expected)

        self.doSim("normalOp", 90 * HdlSimulator.ns)
        
        collected = u.dataOut._ag.data

        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_tryMore(self):
        u = self.u
        
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]
        u.dataOut._ag.enable = False
        
        self.doSim("tryMore", 120 * HdlSimulator.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4], valuesToInts(u.mem._val))
        self.assertSequenceEqual(collected, [])
        self.assertSequenceEqual(u.dataIn._ag.data, [5, 6])

    def test_doloop(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("doloop", 120 * HdlSimulator.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(FifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
