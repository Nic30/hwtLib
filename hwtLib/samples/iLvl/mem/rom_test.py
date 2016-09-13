import unittest

from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.mem.rom import SimpleRom
from hdl_toolkit.hdlObjects.specialValues import Time



class RomTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(SimpleRom())
        
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/rom_%s.vcd" % name,
                time=time)
            
    def test_allData(self):
        u = self.u
        
        u.addr._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        
        self.runSim("allData")
        
        self.assertSequenceEqual([1, 2, 3, 4, None, 4, 3, 2], agInts(u.dout))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(RomTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
