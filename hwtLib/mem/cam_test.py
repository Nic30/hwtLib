import unittest

from hdl_toolkit.hdlObjects.specialValues import Time, NOP
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.mem.cam import Cam


class CamTC(unittest.TestCase):

    def test_writeAndMatchTest(self):
        u, model, procs = simPrepare(Cam())

        u.write._ag.data = [(0, 1, -1),
                            (1, 3, -1),
                            (7, 11, -1)]
        
        u.match._ag.data = [NOP, NOP, NOP, 1, 2, 3, 5, 11, 12]

        simUnitVcd(model, procs,
                   "tmp/cam_simple.vcd", time=160 * Time.ns)
        self.assertSequenceEqual(valuesToInts(u.out._ag.data),
                                 [1, 0, 2, 0, 128, 0])

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
