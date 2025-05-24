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
        cls.dut = dut = Hd44780Driver()
        dut.LCD_FREQ = int(1e6)
        dut.CLK_FREQ = dut.LCD_FREQ * 4
        cls.CLK = int(freq_to_period(dut.LCD_FREQ))
        cls.compileSim(dut)

    def write_text(self, t):
        self.dut.dataIn._ag.data.extend([ord(c) for c in t])

    def test_init(self):
        dut = self.dut
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 600)
        self.assertEqual(dut.dataOut._ag.screen, screen)

    def test_single_char(self):
        dut = self.dut
        self.write_text("a")
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 600)
        screen[0][0] = 'a'
        self.assertEqual(dut.dataOut._ag.screen, screen)

    def test_first_line(self):
        dut = self.dut
        text = "".join(chr(ord('a') + i) for i in range(dut.LCD_COLS))
        self.write_text(text)
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 700)
        screen[0] = [c for c in text]
        self.assertEqual(dut.dataOut._ag.screen, screen)

    def test_new_line_first_row(self):
        dut = self.dut
        text = "ab\ncd"
        self.write_text(text)
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 1000)
        screen[0][0] = 'a'
        screen[0][1] = 'b'
        screen[1][0] = 'c'
        screen[1][1] = 'd'
        self.assertEqual(dut.dataOut._ag.screen, screen)

    def test_new_line_last_row(self):
        dut = self.dut
        text = "ab\ncde\n"
        self.write_text(text)
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 800)
        screen[1][0] = 'c'
        screen[1][1] = 'd'
        screen[1][2] = 'e'
        self.assertEqual(dut.dataOut._ag.screen, screen)

    def test_form_feed(self):
        dut = self.dut
        text = "ab\n\fcd"
        self.write_text(text)
        screen = deepcopy(dut.dataOut._ag.screen)
        self.runSim(self.CLK * 1300)
        screen[0][0] = 'c'
        screen[0][1] = 'd'
        self.assertEqual(dut.dataOut._ag.screen, screen)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Hd44780Driver8bTC("test_new_line_last_row")])
    suite = testLoader.loadTestsFromTestCase(Hd44780Driver8bTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
