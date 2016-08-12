import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import toRtl
from sp10g.stat.flipReg import FlipRegister


class FlipRegTC(unittest.TestCase):
    def setUp(self):
        self.u = FlipRegister()
        # print(
        toRtl(self.u)
        # )
        self.procs = autoAddAgents(self.u)
        
    def runSim(self, name, time=90 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/flipReg_%s.vcd" % name,
                time=90 * HdlSimulator.ns)
    
    def test_simpleWriteAndSwitch(self):
        u = self.u
        
        u.select_sig._ag.data = [0, 0, 0, 0, 1, 0]
        u.firstIn._ag.data = [1]
        u.secondIn._ag.data = [2]
        
        self.runSim("simpleWriteAndSwitch")

        self.assertSequenceEqual([None, 0, 0, 1, 2, 1, 1, 1, 1], agInts(u.firstOut))
        self.assertSequenceEqual([None, 0, 0, 2, 1, 2, 2, 2, 2], agInts(u.secondOut))

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
