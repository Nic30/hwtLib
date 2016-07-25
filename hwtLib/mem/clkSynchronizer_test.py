import unittest

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd, oscilate, pullDownAfter
from hdl_toolkit.synthetisator.shortcuts import toRtl

from hwtLib.mem.clkSynchronizer import ClkSynchronizer
from hdl_toolkit.simulator.agentConnector import valuesToInts


s = HdlSimulator

class ClkSynchronizerTC(unittest.TestCase):
    
    def test_normalOp(self):
        u = ClkSynchronizer()
        u.DATA_TYP = vecT(32)
        toRtl(u)
        
        s = HdlSimulator
    
        CLK_PERIOD = 10 * s.ns
        expected = [0, 0, 0, 0, 0, 0, 1, 2, 3]
        collected = []
        
        def dataInStimul(s):
            yield s.wait(3 * CLK_PERIOD)
            for i in range(127):
                yield s.wait(CLK_PERIOD)
                s.write(i, u.inData)
        
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
                       dataInStimul], "tmp/clkSynchronizer.vcd", time=100 * s.ns)
        
    
        self.assertSequenceEqual(expected, valuesToInts(collected))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(ClkSynchronizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
