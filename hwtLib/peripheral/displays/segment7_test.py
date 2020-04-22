#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.peripheral.displays.segment7 import Segment7
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class Segment7TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_toVhdl(self):
        self.assert_serializes_as_file(Segment7(), "Segment7.vhd")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(OneHotToBinTC('test_basic'))
    suite.addTest(unittest.makeSuite(Segment7TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
