import unittest

from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit
from hdl_toolkit.hdlObjects.statements import IfContainer
from hdl_toolkit.synthetisator.rtlLevel.rtlSignal import RtlSignal
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.hdlObjects.types.defs import BIT

class StatementsTC(unittest.TestCase):
    def testIfContSimEval(self):
        for a_in, b_in in [(0, 0),
                           (0, 1),
                           (1, 0),
                           (1, 1)]:
            resT = vecT(2)
            res = RtlSignal("res", dtype=resT)
            a = RtlSignal("a", BIT)
            b = RtlSignal("b", BIT)
            
            w = lambda val: res._assignFrom(resT.fromPy(val))
            a._val = hBit(a_in)
            b._val = hBit(b_in)
            
            
            stm = IfContainer(set([a & b,]),
                       ifTrue=[w(0),],
                       elIfs=[([a,], [w(1),]),
                              ], 
                       ifFalse=[w(2),]
                  )
            if a_in and b_in:
                expected = 0
            elif a_in:
                expected = 1
            else:
                expected = 2
            

            simulator = HdlSimulator()
            results = list(stm.simEval(simulator))
            
            self.assertEqual(len(results), 1)
            r = results[0]
            self.assertIs(r[0], res)
            self.assertEqual(r[1].val, expected)
            self.assertEqual(r[1].vldMask, 3)

      
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatementsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
