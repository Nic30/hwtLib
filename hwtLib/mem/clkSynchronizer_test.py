import unittest

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd, oscilate, pullDownAfter
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.mem.clkSynchronizer import ClkSynchronizer


s = HdlSimulator
CLK_PERIOD = 10 * s.ns
        
class ClkSynchronizerTC(unittest.TestCase):
    def setUp(self):
        self.u = u = ClkSynchronizer()
        u.DATA_TYP = vecT(32)
        synthesised(u)
    
    def doSim(self, dataInStimul, name, time=100 * s.ns): 
        collected = []

        u = self.u
                
        def dataCollector(s):
            while True:
                d = s.read(u.outData)
                collected.append(d)
                # print(s.env.now)
                yield s.wait(CLK_PERIOD)
        
        simUnitVcd(u, [oscilate(u.inClk, CLK_PERIOD),
                       oscilate(u.outClk, CLK_PERIOD, initWait=CLK_PERIOD / 4),
                       pullDownAfter(u.rst, CLK_PERIOD * 2),
                       dataCollector,
                       dataInStimul], "tmp/clkSynchronizer_" + name + ".vcd", time=100 * s.ns)   
        return collected
    
    def test_normalOp(self):
        u = self.u

        expected = [0, 0, 0, None, 0, 1, 2, 3, 4]
        
        def dataInStimul(s):
            yield s.wait(3 * CLK_PERIOD)
            for i in range(127):
                s.write(i, u.inData)
                yield s.wait(CLK_PERIOD)
                
        collected = self.doSim(dataInStimul, "normalOp")
        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_invalidData(self):
        u = self.u
    
        CLK_PERIOD = 10 * s.ns
        expected = [0, 0, 0, None, None, None, None, None, None]
        
        def dataInStimul(s):
            yield s.wait(3 * CLK_PERIOD)
            for _ in range(127):
                yield s.wait(CLK_PERIOD)
                s.write(None, u.inData)
        
        collected = self.doSim(dataInStimul, "invalidData")
        self.assertSequenceEqual(expected, valuesToInts(collected))

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ClkSynchronizerTC('test_invalidData'))
    suite.addTest(unittest.makeSuite(ClkSynchronizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
