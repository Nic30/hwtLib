import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, autoAgents
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import toRtl
from hwtLib.proc.ssd1306cntrl.code import simpleCodeExample
from hwtLib.proc.ssd1306cntrl.instructions import NOP
from hwtLib.proc.ssd1306cntrl.processor import SSD1306CntrlProc
 

class SSD1306CntrlProcTC(unittest.TestCase):
    def sim(self, program, name):
        u = self.u = SSD1306CntrlProc()
        u.PROGRAM = program
        toRtl(u)
        
        ns = HdlSimulator.ns
        
        agents = {}
        agents.update(autoAgents)
        # [TODO] agent for OledIntf
        
        procs = autoAddAgents(u)
        u.dataIn._ag.data = [1, 2, 3, 4]
        # u.dout._ag.enable = False
        
        
        simUnitVcd(u, procs,
                    "tmp/SSD1306CntrlProc_test_" + name + ".vcd",
                    time=200 * HdlSimulator.ns)
        
        return u
        
    def test_nops(self):
        u = self.sim([NOP for _ in range(100)], "nops")
        self.assertSequenceEqual([], u.oled.spi._ag.dataOut)
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(SSD1306CntrlProcTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
