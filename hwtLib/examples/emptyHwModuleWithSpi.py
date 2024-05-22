#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.pyUtils.typingFuture import override
from hwt.synth import to_rtl_str
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.peripheral.spi.intf import Spi


class EmptyHwModuleWithSpi(EmptyHwModule):

    @override
    def hwDeclr(self):
        self.spi = Spi()


class EmptyHwModuleWithSpiTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        self.assert_serializes_as_file(EmptyHwModuleWithSpi(), "EmptyHwModuleWithSpi.vhd")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([EmptyHwModuleWithSpiTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(EmptyHwModuleWithSpiTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    print(to_rtl_str(EmptyHwModuleWithSpi()))
