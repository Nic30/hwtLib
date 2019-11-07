#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import WRITE, READ
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.mem.lutRam import RAM64X1S
from pyMathBitPrecise.bit_utils import selectBit
from pycocotb.constants import CLK_PERIOD


def applyRequests(ram, requests):
    """
    request has to be tuple (WRITE, addr, data) or (READ, addr)
    data can be only 0 or 1 (because width of data port is 1)
    """
    for req in requests:
        m = req[0]
        if m == WRITE:
            data = req[2]
            assert data == 1 or data == 0
            ram.d._ag.data.append(data)
            ram.we._ag.data.append(1)
        elif m == READ:
            ram.we._ag.data.append(0)
        else:
            raise Exception("invalid mode %s" % (repr(req[0])))

        addr = req[1]
        # ram addr has 6 bits
        for i in range(6):
            addrbit = getattr(ram, "a%d" % i)
            addrBitval = selectBit(addr, i)
            addrbit._ag.data.append(addrBitval)


class LutRamTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = RAM64X1S()
        return u

    def test_writeAndRead(self):
        u = self.u

        requests = [(WRITE, 0, 0), (WRITE, 1, 1),
                    (READ, 0), (READ, 1),
                    (READ, 2), (READ, 3), (READ, 2)]
        applyRequests(u, requests)

        self.runSim(8 * CLK_PERIOD)
        self.assertSequenceEqual(valuesToInts(u.o._ag.data),
                                 [0, 0, 0, 1, 0, 0, 0, 0])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(LutRamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
