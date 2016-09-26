import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import agInts, valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.axi.simpleAxiRegs import SimpleAxiRegs
from hdl_toolkit.bitmask import Bitmask


allMask = Bitmask.mask(64)
        
class SimpleAxiRegsTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(SimpleAxiRegs())
        
    def runSim(self, name, time=250 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/SimpleAxiRegs_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_nop(self):
        u = self.u
        
        self.runSim("nop")
        
        self.assertEqual(len(u.axi._ag.r.data), 0)
        self.assertEqual(len(u.axi._ag.b.data), 0)

    
    def test_falseWrite(self):
        u = self.u
        axi = u.axi._ag
        
        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim("falseWrite")

        self.assertEqual(len(axi.w.data), 2)
        self.assertEqual(len(u.axi._ag.r.data), 0)
        self.assertEqual(len(u.axi._ag.b.data), 0)
        
        
    def test_write(self):
        u = self.u
        axi = u.axi._ag
        
        axi.aw.data += [0, 4]
        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim("write")
        
        self.assertEqual(len(axi.aw.data), 0)
        self.assertEqual(len(axi.w.data), 0)
        self.assertEqual(len(u.axi._ag.r.data), 0)
        self.assertEqual(len(u.axi._ag.b.data), 0)
        
        model = self.model
        
        self.assertEqual(valuesToInts([model.reg0._oldVal, model.reg1._oldVal]), [11, 37])
        
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(SimpleAxiRegsTC('test_write'))
    # suite.addTest(unittest.makeSuite(SimpleAxiRegsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
