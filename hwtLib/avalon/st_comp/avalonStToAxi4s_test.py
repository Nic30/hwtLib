#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.avalon.st import AvalonST
from hwtLib.avalon.st_comp.avalonStBuilder import AvalonSTBuilder
from hwtSimApi.constants import CLK_PERIOD


class _TestAvalonStToAxi4streamAndBack(HwModule):

    @override
    def hwConfig(self) -> None:
        AvalonST.hwConfig(self)

    def hwDeclr(self) -> None:
        addClkRstn(self)  # only for sim purposes
        with self._hwParamsShared():
            self.dataIn = AvalonST()
            self.dataOut = AvalonST()._m()

    def hwImpl(self) -> None:
        end = AvalonSTBuilder(self, self.dataIn)\
            .to_axis()\
            .to_avalonSt().end
        self.dataOut(end)


class AvalonStToAxi4streamAndBack_TC(SimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = _TestAvalonStToAxi4streamAndBack()
        cls.dut.DATA_WIDTH = 8
        cls.compileSim(cls.dut)

    def formatData(self, data: list[int]) -> list[tuple[int, int]]:
        return [(d, 1, 1) for d in data]

    def test_normalOp(self, TIME_MULTIPLIER=1):
        # FifoTC.test_normalOp
        dut = self.dut

        expected = self.formatData(list(range(10)))
        dut.dataIn._ag.data.extend(expected)
        for i in (dut.dataIn, dut.dataOut):
            i._ag.presetBeforeClk = True

        self.runSim(int((len(expected) + 4) * TIME_MULTIPLIER * self.CLK))

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

    def test_randomized(self, randIn=True, randOut=True, LEN=20, TIME_MULTIPLIER=5):
        dut = self.dut
        ref = self.formatData([i + 1 for i in range(LEN)])
        dut.dataIn._ag.data.extend(ref)
        if randIn:
            self.randomize(dut.dataIn)
        if randOut:
            self.randomize(dut.dataOut)
        for i in (dut.dataIn, dut.dataOut):
            i._ag.presetBeforeClk = True

        self.runSim(int(TIME_MULTIPLIER * LEN * self.CLK))

        collected = [tuple(int(d) for d in word) for word in dut.dataOut._ag.data]
        self.assertSequenceEqual(collected, ref)


if __name__ == "__main__":
    import unittest
    from hwt.synth import to_rtl_str

    m = _TestAvalonStToAxi4streamAndBack()
    print(to_rtl_str(m))

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AvalonStCastReadyLatencyAndAllowance_l1a1_TC("test_normalOp")])
    suite = testLoader.loadTestsFromTestCase(AvalonStToAxi4streamAndBack_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
