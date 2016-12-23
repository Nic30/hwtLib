import unittest
from hwt.synthesizer.shortcuts import toRtl
from hwt.synthesizer.exceptions import TypeConversionErr, IntfLvlConfErr
from hwtLib.samples.iLvl.errors.invalidTypeConnetion import InvalidTypeConnetion
from hwtLib.samples.iLvl.errors.unconsistentIntfDirection import UncosistentIntfDirection
from hwtLib.samples.iLvl.errors.multipleDriversOfChildNet import MultipleDriversOfChildNet,\
    MultipleDriversOfChildNet2
from hwt.serializer.exceptions import SerializerException
from hwt.synthesizer.rtlLevel.signalUtils.exceptions import MultipleDriversExc

class ErrorsTC(unittest.TestCase):
    def test_invalidTypeConnetion(self):
        u = InvalidTypeConnetion()
        with self.assertRaises(TypeConversionErr):
            toRtl(u)
      
    def test_uncosistentIntfDirection(self):
        u = UncosistentIntfDirection()
        with self.assertRaises(IntfLvlConfErr):
            toRtl(u)
      
    def test_multipleDriversOfChildNet(self):
        u = MultipleDriversOfChildNet()
        with self.assertRaises(SerializerException):
            toRtl(u) 
            
    def test_multipleDriversOfChildNet2(self):
        u = MultipleDriversOfChildNet2()
        with self.assertRaises(MultipleDriversExc):
            toRtl(u) 
            
if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ErrorsTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(ErrorsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)