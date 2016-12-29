#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwt.synthesizer.shortcuts import synthesised
from hwtLib.proc.ssd1306cntrl.code import simpleCodeExample
from hwtLib.proc.ssd1306cntrl.instructions import NOP
from hwtLib.proc.ssd1306cntrl.processor import SSD1306CntrlProc


class SSD1306CntrlProcTC(unittest.TestCase):
    def sim(self, program, name):
        u = SSD1306CntrlProc()
        u.PROGRAM = program
        synthesised(u)
        self.u, self.model, self.procs = simPrepare(u)
        u.dataIn._ag.data = [1, 2, 3, 4]
        # u.dout._ag.enable = False
        
        
        simUnitVcd(self.model, self.procs,
                    "tmp/SSD1306CntrlProc_test_" + name + ".vcd",
                    time=200 * Time.ns)
        
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
