import unittest

from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.simulator.agentConnector import autoAddAgents, agInts
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.simulator.shortcuts import simUnitVcd
from hdl_toolkit.synthetisator.shortcuts import synthesised
from hwtLib.handshaked.reg import HandshakedReg


class HsRegTC(unittest.TestCase):
    def setUp(self):
        self.u = u = HandshakedReg(Handshaked)
        synthesised(u)
        self.procs = autoAddAgents(u)

    
    def doSim(self, name, time=80 * HdlSimulator.ns):
        simUnitVcd(self.u, self.procs,
                    "tmp/hsReg_" + name + ".vcd",
                    time=time)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("passdata", 120 * HdlSimulator.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([ 2, 3, 4, 5, 6], collected) # 1 was in reset
        self.assertSequenceEqual([], u.dataIn._ag.data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsRegTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
