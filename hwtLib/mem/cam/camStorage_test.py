import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, autoAgents,\
    agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised

from hwtLib.mem.cam.camStorage import CamStorage, CamStorageInIntf
from hdl_toolkit.simulator.agents.signal import SignalAgent

class CamStorageInAgent(SignalAgent):
    def doRead(self, s):
        raise NotImplementedError()
    
    def doWrite(self, s, data):
        addr, dataIn, we = data
        i = self.intf
        s.write(addr, i.addr)
        s.write(dataIn, i.dataIn)
        s.write(we, i.we)
        
class CamStorageTC(unittest.TestCase):
    def testNoMatch(self):
        u = CamStorage()
        u.COLUMNS.set(3)
        u.ROWS.set(2)

        synthesised(u)
        autoAgents[CamStorageInIntf] = CamStorageInAgent
        proc = autoAddAgents(u, autoAgentMap=autoAgents)
        
        
        u.din._ag.data = [(0, 0, 1), (0, 0, 1)]
        
        
        
        s = HdlSimulator
        simUnitVcd(u, proc,
                   "tmp/camStorage_simple.vcd", time=90 * s.ns)
    
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 0], agInts(u.match))

        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CamStorageTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
