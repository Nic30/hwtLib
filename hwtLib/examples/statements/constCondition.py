from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, Clk
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.synthesizer.unit import Unit
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from pycocotb.agents.clk import DEFAULT_CLOCK


class ConstCondition(Unit):

    def _declr(self):
        self.clk = Clk()
        self.a = VectSignal(2)
        self.b = VectSignal(2)
        self.c = Signal()._m()

    def _impl(self):
        one = self._sig('one', Bits(1))
        intermed = self._reg('intermed', Bits(1))
        one(1)
        self.c(intermed)
        If(one._eq(1),
            If(self.a._eq(1),
                intermed(1),
            ),
            If(self.b._eq(1),
                intermed(0),
            ),
            If(self.b._eq(2),
                intermed(1),
            ),
        )


class ConstConditionTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        cls.u = ConstCondition()
        return cls.u

    def test_reg_update(self):
        u = self.u
        u.a._ag.data.extend([0, 1, 0, 0, 0])
        u.b._ag.data.extend([0, 0, 1, 2, 1])
        self.runSim(10 * DEFAULT_CLOCK)
        self.assertValSequenceEqual(u.c._ag.data, [None, None, 1, 0, 1, 0, 0, 0, 0, 0])


def main():
    import unittest
    from hwt.synthesizer.utils import toRtl
    u = ConstCondition()
    print(toRtl(u, serializer=VerilogSerializer))

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConstConditionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == '__main__':
    main()
