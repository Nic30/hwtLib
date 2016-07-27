import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.samples.iLvl.operators.indexing import SimpleIndexingSplit, SimpleIndexingJoin

ns = HdlSimulator.ns

class IndexingTC(unittest.TestCase):
    def setUpSplit(self):
        self.u = SimpleIndexingSplit()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
    
    def setUpJoin(self):
        self.u = SimpleIndexingJoin()
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
    
        
    def runSim(self, name, time=80 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/indexing_%s.vcd" % name,
                time=time)
            
    def test_split(self):
        self.setUpSplit()
        u = self.u
        
        u.a._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        
        self.runSim("split")
        
        self.assertSequenceEqual([0, 1, 0, 1, None, 1, 0, 1], agInts(u.b))
        self.assertSequenceEqual([0, 0, 1, 1, None, 1, 1, 0], agInts(u.c))

    def test_join(self):
        self.setUpJoin()
        u = self.u
        
        u.b._ag.data = [0, 1, 0, 1, None, 1, 0, 1]
        u.c._ag.data = [0, 0, 1, 1, None, 1, 1, 0]
        
        self.runSim("join")
        
        self.assertSequenceEqual([0, 1, 2, 3, None, 3, 2, 1], agInts(u.a))
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(IndexingTC('test_join'))
    suite.addTest(unittest.makeSuite(IndexingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
