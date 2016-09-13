import unittest

from hdl_toolkit.hdlObjects.statements import IfContainer
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit
from hdl_toolkit.hdlObjects.types.defs import BIT
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


class StatementsTC(unittest.TestCase):
    def testIfContSimEval(self):
        for a_in, b_in in [(0, 0),
                           (0, 1),
                           (1, 0),
                           (1, 1)]:
            resT = vecT(2)
            nl = RtlNetlist()
            
            res = nl.sig("res", resT)
            a = nl.sig("a", BIT)
            b = nl.sig("b", BIT)
            
            w = lambda val: res ** val
            a._val = hBit(a_in)
            b._val = hBit(b_in)
            
            
            stm = IfContainer(set([a & b, ]),
                       ifTrue=w(0),
                       elIfs=[([a, ], w(1)),
                              ],
                       ifFalse=w(2)
                  )
            
            if a_in and b_in:
                expected = 0
            elif a_in:
                expected = 1
            else:
                expected = 2
            

            stm.seqEval()
            
            newVal = res._val
            
            self.assertEqual(newVal.val, expected)
            self.assertEqual(newVal.vldMask, 3)

      
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatementsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
