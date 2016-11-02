#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time, NOP
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream
from hdl_toolkit.interfaces.utils import addClkRstn


class SynchronizedSimpleUnitAxiStream(SimpleUnitAxiStream):
    """
    Unit with reference clk added
    """
    def _declr(self):
        SimpleUnitAxiStream._declr(self)
        with self._asExtern():
            addClkRstn(self)

class SimpleUnitAxiStream_TC(unittest.TestCase):
    def setUp(self):
        self.u = SynchronizedSimpleUnitAxiStream()
        _, self.model, self.procs = simPrepare(self.u)
    
    def getTestName(self):
        className, testName = self.id().split(".")[-2:]
        return "%s_%s" % (className, testName)
    
    def doSim(self, time):
        simUnitVcd(self.model, self.procs,
                    "tmp/" + self.getTestName() + ".vcd",
                    time=time)
    
        
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.b._ag.data), 0)
        
    def test_pass(self):
        u = self.u
        
        u.a._ag.data.extend([(11, mask(u.a.strb._dtype.bit_length()), 1),
                             NOP,
                             (12, mask(u.a.strb._dtype.bit_length()), 1)
                            ])
        
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.b._ag.data), 2)
        
            


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimpleUnitAxiStream_TC('test_nop'))
    suite.addTest(unittest.makeSuite(SimpleUnitAxiStream_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

