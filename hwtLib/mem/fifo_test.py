from copy import copy
import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.mem.fifo import Fifo


class FifoTC(unittest.TestCase):
    def setUp(self):
        u = Fifo()
        u.DATA_WIDTH.set(8)
        u.DEPTH.set(4)
        self.u, self.model, self.procs = simPrepare(u)
    
    def doSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
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

        self.doSim("normalOp", 90 * Time.ns)
        
        collected = u.dataOut._ag.data

        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_tryMore(self):
        u = self.u
        
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]
        u.dataOut._ag.enable = False
        
        self.doSim("tryMore", 120 * Time.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4], valuesToInts(self.model.memory._val))
        self.assertSequenceEqual(collected, [])
        self.assertSequenceEqual(u.dataIn._ag.data, [5, 6])

    def test_doloop(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("doloop", 120 * Time.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(FifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
