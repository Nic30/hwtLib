import os

from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.rtlLvl.arithmetic.counter import Counter
from hwtLib.examples.rtlLvl.arithmetic.leadingZero import LeadingZero
from hwtLib.examples.rtlLvl.axiReaderCore import AxiReaderCore
from hwtLib.examples.rtlLvl.complexConditions import ComplexConditions
from hwtLib.examples.rtlLvl.indexOps import IndexOps
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from hwtLib.examples.rtlLvl.simpleEnum import SimpleEnum
from hwtLib.examples.rtlLvl.simpleRegister import SimpleRegister
from hwtLib.examples.rtlLvl.simpleWhile import SimpleWhile
from hwtLib.examples.rtlLvl.switchStatement import SwitchStatement


class RtlLvlTC(BaseSerializationTC):
    __FILE__ = __file__

    def cmp(self, getNetlistFn, file_name):
        netlist, interfaces = getNetlistFn()
        vhdl = netlistToVhdlStr(getNetlistFn.__name__, netlist, interfaces)
        self.assert_same_as_file(vhdl, file_name)

    def test_arithmetic_counter(self):
        self.cmp(Counter, os.path.join("arithmetic", "Counter.vhd"))

    def test_arithmetic_leadingZero(self):
        self.cmp(LeadingZero, os.path.join("arithmetic", "LeadingZero.vhd"))

    def test_axiReaderCore(self):
        self.cmp(AxiReaderCore, "AxiReaderCore.vhd")

    def test_complexConditions(self):
        self.cmp(ComplexConditions, "ComplexConditions.vhd")

    def test_indexOps(self):
        self.cmp(IndexOps, "IndexOps.vhd")

    def test_simpleEnum(self):
        self.cmp(SimpleEnum, "SimpleEnum.vhd")

    def test_simpleRegister(self):
        self.cmp(SimpleRegister, "SimpleRegister.vhd")

    def test_simpleWhile(self):
        self.cmp(SimpleWhile, "SimpleWhile.vhd")

    def test_switchStatement(self):
        self.cmp(SwitchStatement, "SwitchStatement.vhd")


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RtlLvlTC('test_axiReaderCore'))
    suite.addTest(unittest.makeSuite(RtlLvlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
