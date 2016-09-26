import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.axi.simpleAxiRegs import SimpleAxiRegs


class SimpleAxiRegsTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(SimpleAxiRegs())
        
    def runSim(self, name, time=200 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/SimpleAxiRegs_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_readAndWrite(self):
        u = self.u
        
        self.runSim("readAndWrite")
        #self.assertSequenceEqual([0, 0, 1, 2, 3, 4, 0, 1, 2], agInts(u.dout))
       
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimpleAxiRegs('test_readAndWrite'))
    suite.addTest(unittest.makeSuite(SimpleAxiRegsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
