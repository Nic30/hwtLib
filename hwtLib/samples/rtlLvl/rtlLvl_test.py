import unittest

from hwtLib.samples.rtlLvl.arithmetic.counter import Counter, counterExpected
from hwtLib.samples.rtlLvl.arithmetic.leadingZero import LeadingZero, \
    leadingZeroExpected
from hwtLib.samples.rtlLvl.axiReaderCore import AxiReaderCore, \
    axiReaderCoreExpected
from hwtLib.samples.rtlLvl.complexConditions import ComplexConditions, \
    complexConditionsExpected
from hwtLib.samples.rtlLvl.indexOps import IndexOps, indexOpsExpected
from hwtLib.samples.rtlLvl.netlistToRtl import netlistToVhdlStr
from hwtLib.samples.rtlLvl.simpleEnum import SimpleEnum, simpleEnumExpected
from hwtLib.samples.rtlLvl.simpleRegister import SimpleRegister, \
    simpleRegisterExpected
from hwtLib.samples.rtlLvl.simpleWhile import SimpleWhile, simpleWhileExpected
from hwtLib.samples.rtlLvl.switchStatement import SwitchStatement, \
    switchStatementExpected
from hwtLib.tests.statementTrees import StatementTreesTC


class RtlLvlTC(unittest.TestCase):
    def strStructureCmp(self, tmpl, cont):
        return StatementTreesTC.strStructureCmp(self, tmpl, cont)

    def cmp(self, getNetlistFn, expected):
        netlist, interfaces = getNetlistFn()
        self.strStructureCmp(expected, netlistToVhdlStr(getNetlistFn.__name__, netlist, interfaces))

    def test_arithmetic_counter(self):
        self.cmp(Counter, counterExpected)

    def test_arithmetic_leadingZero(self):
        self.cmp(LeadingZero, leadingZeroExpected)

    def test_axiReaderCore(self):
        self.cmp(AxiReaderCore, axiReaderCoreExpected)

    def test_complexConditions(self):
        self.cmp(ComplexConditions, complexConditionsExpected)

    def test_indexOps(self):
        self.cmp(IndexOps, indexOpsExpected)

    def test_simpleEnum(self):
        self.cmp(SimpleEnum, simpleEnumExpected)

    def test_simpleRegister(self):
        self.cmp(SimpleRegister, simpleRegisterExpected)

    def test_simpleWhile(self):
        self.cmp(SimpleWhile, simpleWhileExpected)

    def test_switchStatement(self):
        self.cmp(SwitchStatement, switchStatementExpected)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(RtlLvlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
