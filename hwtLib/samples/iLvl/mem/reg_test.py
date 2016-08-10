import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.mem.reg import DReg, DoubleDReg


s = HdlSimulator

class DRegTC(unittest.TestCase):
    def setUpUnit(self, u):
        synthesised(u)
        self.procs = autoAddAgents(u)
        self.u = u
    
    def runSim(self, name, time=100 * s.ns):
        simUnitVcd(self.u, self.procs,
                   "tmp/reg_" + name + ".vcd", time=time)
    
    def testSimple(self):
        self.setUpUnit(DReg())
        
        self.u.din._ag.data = [i % 2 for i in range(6)] + [None, None, 0, 1] 
        expected = [0, 0, 1, 0, 1, 0, 1, None, None, 0]
        
        self.runSim("simple")
        recieved = agInts(self.u.dout)
        # check simulation results
        self.assertSequenceEqual(expected, recieved)
    
    def testDouble(self):
        self.setUpUnit(DoubleDReg())
    
        self.u.din._ag.data = [i % 2 for i in range(6)]  + [None, None, 0, 1] 
        expected = [0, 0, 0, 1, 0, 1, 0, 1, None, None]
        
        self.runSim("double")

        recieved = agInts(self.u.dout)

        # check simulation results
        self.assertSequenceEqual(expected, recieved)
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(DRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
