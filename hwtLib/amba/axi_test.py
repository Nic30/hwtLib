#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwtLib.amba.constants import BYTES_IN_TRANS


class AxiTC(unittest.TestCase):
    def test_axi_size(self):
        golden = {1:0b000,
                  2:0b001,
                  4:0b010,
                  8:0b011,
                  16:0b100,
                  32:0b101,
                  64:0b110,
                  128:0b111
                  }
        
        for x, res in golden.items():
            self.assertEqual(BYTES_IN_TRANS(x), res, x)
            
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiTC('test_axi_size'))
    suite.addTest(unittest.makeSuite(AxiTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
