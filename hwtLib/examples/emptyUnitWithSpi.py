#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwt.synthesizer.utils import to_rtl_str
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.peripheral.spi.intf import Spi


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        self.spi = Spi()


class EmptyUnitWithSpiTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        self.assert_serializes_as_file(EmptyUnitWithSpi(), "EmptyUnitWithSpi.vhd")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(EmptyUnitWithSpiTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    print(to_rtl_str(EmptyUnitWithSpi()))
