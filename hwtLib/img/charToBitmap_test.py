#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.agentConnector import valToInt
from hwtLib.img.charToBitmap import asciiArtOfChar, addCharToBitmap


A = """#   ####
 ### ###
 ### ###
     ###
 ### ###
 ### ###
########
########"""

dot = """########
########
########
########
########
# ######
########
########"""

six = """##  ####
# ######
#   ####
 ### ###
 ### ###
#   ####
########
########"""

a_inverted = """########
########
#    ###
 ### ###
 ##  ###
#  # ###
########
########"""


class CharToBitmapTC(unittest.TestCase):
    def test_A(self):
        self.assertEqual(asciiArtOfChar("A"), A)

    def test_dot(self):
        self.assertEqual(asciiArtOfChar("."), dot)

    def test_6(self):
        self.assertEqual(asciiArtOfChar("6"), six)

    def test_a_inverted(self):
        self.assertEqual(asciiArtOfChar("a", inverted=True), a_inverted)

    def test_dot_in_hw(self):
        dot_golden = [255, 255, 255, 255, 255, 0b10111111, 255, 255]
        a = addCharToBitmap()
        for i, item in enumerate(dot_golden):
            self.assertEqual(valToInt(a[ord(".") * 8 + i]), item, i)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ArrayBuff_writer_TC('test_fullFill_withoutAck'))
    suite.addTest(unittest.makeSuite(CharToBitmapTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
