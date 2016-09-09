import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthesizer.shortcuts import synthesised
from hwtLib.handshaked.reg2 import HandshakedReg2


class HsReg2TC(unittest.TestCase):
    def setUp(self):
        self.u = u = HandshakedReg2(Handshaked)
        synthesised(u)
        self.procs = autoAddAgents(u)

    
    def doSim(self, name, time=130 * Time.ns):
        simUnitVcd(self.u, self.procs,
                    "tmp/hsReg2_" + name + ".vcd",
                    time=time)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("passdata", 120 * Time.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)


# def mkTestbench():
#    from hdl_toolkit.serializer.utils import SimBuilder
#    from hdl_toolkit.serializer.utils import hsWrite, makeTestbenchTemplate
#    from hdl_toolkit.serializer.templates import VHDLTemplates
#    repo = "tmp/"
#    u = HandshakedReg2(Handshaked)
#    serializeAsIpcore(u, repo)
#    
#    
#    def procGen(ctx):
#        s = SimBuilder(ctx)
#        s.wait(50)
#        for i in range(10):
#            s.write(i + 1, u.dataIn.data) 
#            hsWrite(s, u.dataIn)
#        
#        s.wait(None)
#        
#        yield s.mainProc
#        
#        s = SimBuilder(ctx)
#        s.wait(60)
#        for i in range(5):
#            s.write(1, u.dataOut.rd)
#            s.wait(10) 
#        
#        s.write(0, u.dataOut.rd) 
#        s.wait(60)
#
#        for i in range(5):
#            s.write(1, u.dataOut.rd) 
#            s.wait(10)
#        s.write(0, u.dataOut.rd) 
#        
#        
#        yield s.mainProc
#        
#    e, a = makeTestbenchTemplate(u, procGen=procGen)
#    with open(repo + "/hsreg2_tb.vhd", "w") as f:
#        f.write(str(VHDLTemplates.basic_include))
#        f.write(str(e))
#        f.write(str(a))
#
if __name__ == "__main__":
    # mkTestbench()
    
    suite = unittest.TestSuite()
    # suite.addTest(HsRegTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsReg2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
