import unittest

from hwt.synthesizer.exceptions import TypeConversionErr, IntfLvlConfErr
from hwt.synthesizer.rtlLevel.signalUtils.exceptions import \
    MultipleDriversErr, NoDriverErr
from hwt.synthesizer.utils import toRtl
from hwtLib.examples.errors.accessingSubunitInternalIntf import \
    AccessingSubunitInternalIntf
from hwtLib.examples.errors.inconsistentIntfDirection import \
    InconsistentIntfDirection
from hwtLib.examples.errors.invalidTypeConnetion import InvalidTypeConnetion
from hwtLib.examples.errors.multipleDriversOfChildNet import \
    MultipleDriversOfChildNet, MultipleDriversOfChildNet2
from hwtLib.examples.errors.unusedSubunit import UnusedSubunit, UnusedSubunit2


class ErrorsTC(unittest.TestCase):
    def test_invalidTypeConnetion(self):
        u = InvalidTypeConnetion()
        with self.assertRaises(TypeConversionErr):
            toRtl(u)

    def test_inconsistentIntfDirection(self):
        u = InconsistentIntfDirection()
        with self.assertRaises(IntfLvlConfErr):
            toRtl(u)

    def test_multipleDriversOfChildNet(self):
        u = MultipleDriversOfChildNet()
        with self.assertRaises((MultipleDriversErr, NoDriverErr)):
            toRtl(u)

    def test_multipleDriversOfChildNet2(self):
        u = MultipleDriversOfChildNet2()
        with self.assertRaises(MultipleDriversErr):
            toRtl(u)

    def test_unusedSubunit(self):
        u = UnusedSubunit()
        with self.assertRaises(NoDriverErr):
            toRtl(u)

    def test_unusedSubunit2(self):
        u = UnusedSubunit2()
        with self.assertRaises(NoDriverErr):
            toRtl(u)

    def test_accessingSubunitInternalIntf(self):
        u = AccessingSubunitInternalIntf()
        with self.assertRaises(AssertionError):
            toRtl(u)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ErrorsTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(ErrorsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
