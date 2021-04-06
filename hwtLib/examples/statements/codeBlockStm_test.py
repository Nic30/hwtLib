from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtSimApi.constants import CLK_PERIOD
from hwtLib.examples.statements.codeBlockStm import BlockStm_complete_override0, \
    BlockStm_complete_override1, BlockStm_complete_override2


class CodeBlokStmTC(SimTestCase, BaseSerializationTC):
    __FILE__ = __file__

    def test_BlockStm_complete_override0(self):
        u = BlockStm_complete_override0()
        self.compileSimAndStart(u)

        a = u.a._ag.data
        b = u.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _b
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(u.c._ag.data, c)

    def test_BlockStm_complete_override1(self):
        u = BlockStm_complete_override1()
        self.compileSimAndStart(u)

        a = u.a._ag.data
        b = u.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                if _b is None:
                    _c = None
                elif _b:
                    _c = 0
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(u.c._ag.data, c)

    def test_BlockStm_complete_override2(self):
        u = BlockStm_complete_override2()
        self.compileSimAndStart(u)

        a = u.a._ag.data
        b = u.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(u.c._ag.data, c)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CodeBlokStmTC('test_resources_SimpleIfStatement2c'))
    suite.addTest(unittest.makeSuite(CodeBlokStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
