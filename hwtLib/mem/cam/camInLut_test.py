import unittest

from hdl_toolkit.simulator.agentConnector import autoAddAgents, autoAgents
from hdl_toolkit.simulator.agents.handshaked import HandshakedAgent
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.mem.cam.camInLUT import CamInLUT
from hwtLib.mem.cam.interfaces import AddrDataHs


# class CamInLut_Model():
#     def __init__(self, size):
#         self.data = [None for _ in range(size)]
#         self.size = size
#         
#     def write(self, addr, data):
#         self.data[addr] = data
#     
#     def match(self, data):
#         match = 0
#         for d in reversed(self.data):
#             
#             if d is None:
#                 m = 0
#             else:
#                 m = d == data
#             match <<= 1
#             match |= m
#         
#         return match 
class AddrDataHs_agent(HandshakedAgent):

    def doRead(self, s):
        """
        Collect tuples (addr, data, mask)
        """
        intf = self.intf
        a = s.read(intf.addr)
        d = s.read(intf.data)
        m = s.read(intf.mask)
        return (a, d, m)

    def doWrite(self, s, data):
        intf = self.intf    
        if data is None:
            s.w(None, intf.addr)
            s.w(None, intf.data)
            s.w(None, intf.mask)
        else:
            s.w(data[0], intf.addr)
            s.w(data[1], intf.data)
            s.w(data[2], intf.mask)
            
class CamInLutTC(unittest.TestCase):
    def testSimple(self):
        u = CamInLUT()
        u.ITEMS.set(16)
        
        synthesised(u)
        autoAgents[AddrDataHs] = AddrDataHs_agent
        
        proc = autoAddAgents(u, autoAgentMap=autoAgents)
        
        s = HdlSimulator
        simUnitVcd(u, proc,
                   "tmp/camInLut_simple.vcd",
                   time=90 * s.ns)
    
        # # check simulation results
        # self.assertEqual(len(expected), len(recieved), recieved)
        # for exp, rec in zip(expected, recieved):
        #    self.assertTrue(rec.vldMask)
        #    self.assertEqual(exp, rec.val, (exp, rec))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CamInLutTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
