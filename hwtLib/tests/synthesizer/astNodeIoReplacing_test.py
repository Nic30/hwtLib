import unittest

from hwt.code import If, Switch
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


class AstNodeIoReplacingTC(unittest.TestCase):

    def sigs_by_n(self, n):
        nl = RtlNetlist()
        sigs = [nl.sig(chr(ord("a") + i)) for i in range(n)]
        for s in sigs:
            s._isUnnamedExpr = False
        return nl, sigs

    def test_If_simple_replace_input(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        If(a,
           b(1)
        ).Else(
           b(0)
        )
        self.assertEqual(stm._inputs, [a])
        self.assertTrue(stm._replace_input((a, c)))
        stm_ref = If(c,
                      b(1)
                  ).Else(
                      b(0)
                  )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertEqual(a._rtlEndpoints, [])
        self.assertEqual(c._rtlEndpoints, [stm, stm_ref])
        self.assertEqual(stm._inputs, [c])

    def test_If_elif_replace_input(self):
        _, (a, b, c, d) = self.sigs_by_n(4)
        stm = \
        If(a,
           b(1)
        ).Elif(c & a,
           b(0)
        ).Else(
           c(0)
        )

        self.assertTrue(stm._replace_input((a, d)))

        stm_ref = If(d,
                      b(1)
                  ).Elif(c & d,
                      b(0)
                  ).Else(
                      c(0)
                  )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertEqual(a._rtlEndpoints, [(c & a).singleDriver(),
                                       a._isOn().singleDriver()])
        self.assertEqual(c._rtlEndpoints, [(c & a).singleDriver(),
                                       (c & d).singleDriver()])
        self.assertEqual(stm._inputs, [d, c & d])
        self.assertEqual(stm._outputs, [b, c])

    def test_If_nested(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        If(a,
            If(c,
               b(c & a)
            ).Else(
               b(c | a)
            )
        ).Else(
           b(0)
        )
        self.assertEqual(stm._inputs, [a, c, c & a, c | a])
        self.assertTrue(stm._replace_input((a, c)))
        stm_ref = \
        If(c,
            If(c,
                b(c)
            ).Else(
                b(c)
            )
        ).Else(
            b(0)
        )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertEqual(stm._inputs, [c, ])
        self.assertNotIn(stm, a._rtlEndpoints)
        self.assertIn(stm, c._rtlEndpoints)
    
    def test_If_nested_withExpr(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        If(a,
            If(c,
               b(c & a)
            ).Else(
               b(c | a)
            )
        ).Else(
           b(0)
        )

        self.assertTrue(stm._replace_input((a, ~c)))
        stm_ref = \
        If(~c,
            If(c,
                b(0)
            ).Else(
                b(1)
            )
        ).Else(
            b(0)
        )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertNotIn(stm, a._rtlEndpoints)
        self.assertIn(stm, (~c)._rtlEndpoints)
        self.assertIn(stm, c._rtlEndpoints)

    def test_Switch_simple(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        Switch(a)\
        .Case(0,
            b(1)
        ).Default(
            b(0)
        )

        self.assertTrue(stm._replace_input((a, c)))
        stm_ref = \
        Switch(c)\
        .Case(0,
            b(1)
        ).Default(
            b(0)
        )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertNotIn(stm, a._rtlEndpoints)
        self.assertIn(stm, c._rtlEndpoints)


if __name__ == '__main__':
    import sys
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(AstNodeIoReplacingTC)
    runner = unittest.TextTestRunner(verbosity=3)
    sys.exit(not runner.run(suite).wasSuccessful())
