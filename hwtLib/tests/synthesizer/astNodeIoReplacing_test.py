import unittest

from hwt.code import If, Switch
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


class AstNodeIoReplacingTC(unittest.TestCase):

    def sigs_by_n(self, n):
        nl = RtlNetlist()
        sigs = [nl.sig(chr(ord("a") + i)) for i in range(n)]
        for s in sigs:
            s.hidden = False
        return nl, sigs

    def test_If_simple_replace_input(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        If(a,
           b(1)
        ).Else(
           b(0)
        )

        stm._replace_input(a, c)
        stm_ref = If(c,
                      b(1)
                  ).Else(
                      b(0)
                  )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertEqual(a.endpoints, [])
        self.assertEqual(c.endpoints, [stm, stm_ref])

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

        stm._replace_input(a, d)

        stm_ref = If(d,
                      b(1)
                  ).Elif(c & d,
                      b(0)
                  ).Else(
                      c(0)
                  )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertEqual(a.endpoints, [a._isOn().singleDriver()])
        self.assertEqual(c.endpoints, [(c & a).singleDriver(),
                                       (c & d).singleDriver()])

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

        stm._replace_input(a, c)
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
        self.assertNotIn(stm, a.endpoints)
        self.assertIn(stm, c.endpoints)

    def test_Switch_simple(self):
        _, (a, b, c) = self.sigs_by_n(3)
        stm = \
        Switch(a)\
        .Case(0,
            b(1)
        ).Default(
            b(0)
        )

        stm._replace_input(a, c)
        stm_ref = \
        Switch(c)\
        .Case(0,
            b(1)
        ).Default(
            b(0)
        )
        self.assertTrue(stm.isSame(stm_ref), [stm, stm_ref])
        self.assertNotIn(stm, a.endpoints)
        self.assertIn(stm, c.endpoints)


if __name__ == '__main__':
    import sys
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AstNodeIoReplacingTC))
    # suite.addTest(AstNodeIoReplacingTC("test_If_elif_replace_input"))
    runner = unittest.TextTestRunner(verbosity=3)
    sys.exit(not runner.run(suite).wasSuccessful())
