from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal, HwIOClk
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD


class ConstCondition(HwModule):
    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self.a = HwIOVectSignal(2)
        self.b = HwIOVectSignal(2)
        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        one = self._sig('one', HBits(1))
        intermed = self._reg('intermed', HBits(1))
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


class ConstConditionTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = ConstCondition()
        cls.compileSim(cls.dut)

    def test_reg_update(self):
        dut = self.dut
        dut.a._ag.data.extend([0, 1, 0, 0, 0])
        dut.b._ag.data.extend([0, 0, 1, 2, 1])
        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.c._ag.data, [None, None, 1, 0, 1, 0, 0, 0, 0, 0])


def main():
    import unittest
    from hwt.synth import to_rtl_str
    
    m = ConstCondition()
    print(to_rtl_str(m))

    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(ConstConditionTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == '__main__':
    main()
