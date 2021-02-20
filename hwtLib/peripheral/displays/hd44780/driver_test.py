#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.displays.hd44780.driver import Hd44780Driver
from hwtSimApi.utils import freq_to_period


class Hd44780Driver8bTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Hd44780Driver()
        u.LCD_FREQ = int(1e6)
        u.FREQ = u.LCD_FREQ * 4
        cls.CLK = int(freq_to_period(u.LCD_FREQ))
        cls.compileSim(u)

    def write_text(self, t):
        self.u.dataIn._ag.data.extend([ord(c) for c in t])

    def test_init(self):
        u = self.u
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 600)
        self.assertEqual(u.dataOut._ag.screen, screen)

    def test_single_char(self):
        u = self.u
        self.write_text("a")
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 600)
        screen[0][0] = 'a'
        self.assertEqual(u.dataOut._ag.screen, screen)

    def test_first_line(self):
        u = self.u
        text = "".join(chr(ord('a') + i) for i in range(u.LCD_COLS))
        self.write_text(text)
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 700)
        screen[0] = [c for c in text]
        self.assertEqual(u.dataOut._ag.screen, screen)

    def test_new_line_first_row(self):
        u = self.u
        text = "ab\ncd"
        self.write_text(text)
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 1000)
        screen[0][0] = 'a'
        screen[0][1] = 'b'
        screen[1][0] = 'c'
        screen[1][1] = 'd'
        self.assertEqual(u.dataOut._ag.screen, screen)

    def test_new_line_last_row(self):
        u = self.u
        text = "ab\ncde\n"
        self.write_text(text)
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 800)
        screen[1][0] = 'c'
        screen[1][1] = 'd'
        screen[1][2] = 'e'
        self.assertEqual(u.dataOut._ag.screen, screen)

    def test_form_feed(self):
        u = self.u
        text = "ab\n\fcd"
        self.write_text(text)
        screen = deepcopy(u.dataOut._ag.screen)
        self.runSim(self.CLK * 1300)
        screen[0][0] = 'c'
        screen[0][1] = 'd'
        self.assertEqual(u.dataOut._ag.screen, screen)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Hd44780Driver8bTC('test_new_line_last_row'))
    suite.addTest(unittest.makeSuite(Hd44780Driver8bTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
