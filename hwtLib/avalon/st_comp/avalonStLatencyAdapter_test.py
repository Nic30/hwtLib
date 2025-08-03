#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.avalon.st import AvalonST
from hwtLib.avalon.st_comp.avalonStBuilder import AvalonSTBuilder
from hwtSimApi.constants import CLK_PERIOD


class _TestAvalonStCastReadyLatencyAndAllowance_wire(HwModule):

    @override
    def hwConfig(self) -> None:
        self.internal_readyLatency:int = HwParam(0)
        self.internal_readyAllowance: Optional[int] = HwParam(None)
        self.dataBitsPerSymbol:int = HwParam(8)
        self.DATA_WIDTH:int = HwParam(8)

    def hwDeclr(self) -> None:
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = AvalonST()
            self.dataOut = AvalonST()._m()

    def hwImpl(self) -> None:
        end = AvalonSTBuilder(self, self.dataIn)\
            .castReadyLatencyAndAllowance(self.internal_readyLatency, self.internal_readyAllowance)\
            .castReadyLatencyAndAllowance(0, 0).end
        self.dataOut(end)


class AvalonStCastReadyLatencyAndAllowance_l0a0_TC(SimTestCase):
    internal_readyLatency = 0
    internal_readyAllowance = 0
    IN_CLK = CLK_PERIOD
    OUT_CLK = CLK_PERIOD
    CLK = max(IN_CLK, OUT_CLK)  # clock used for resolving of sim duration

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = _TestAvalonStCastReadyLatencyAndAllowance_wire()
        dut.internal_readyAllowance = cls.internal_readyAllowance
        dut.internal_readyLatency = cls.internal_readyLatency
        cls.compileSim(cls.dut)

    def formatData(self, data: list[int]) -> list[tuple[int, int]]:
        return [(d, 1, 1) for d in data]

    def test_fifoSingleWord(self):
        # FifoTC.test_fifoSingleWord(self)
        dut = self.dut

        expected = self.formatData([1])
        dut.dataIn._ag.data.extend(expected)

        self.runSim(9 * self.CLK)

        collected = dut.dataOut._ag.data
        self.assertValSequenceEqual(collected, expected)

    def test_normalOp(self, TIME_MULTIPLIER=1):
        # FifoTC.test_normalOp
        dut = self.dut

        expected = self.formatData(list(range(10)))
        dut.dataIn._ag.data.extend(expected)
        for i in (dut.dataIn, dut.dataOut):
            i._ag.presetBeforeClk = True

        self.runSim(int((len(expected) + 4) * TIME_MULTIPLIER * self.CLK))

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

    def test_randomizedIn(self):
        self._test_randomized(True, False)

    def test_randomizedOut(self):
        self._test_randomized(False, True)

    def test_randomizedAll(self, TIME_MULTIPLIER=4):
        self._test_randomized(True, True, TIME_MULTIPLIER=TIME_MULTIPLIER)

    def _test_randomized(self, randIn, randOut, LEN=80, TIME_MULTIPLIER=2):
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


class AvalonStCastReadyLatencyAndAllowance_l1a1_TC(AvalonStCastReadyLatencyAndAllowance_l0a0_TC):
    internal_readyLatency = 1
    internal_readyAllowance = 1

    def test_normalOp(self, TIME_MULTIPLIER=1.1):
        super().test_normalOp(TIME_MULTIPLIER)

    def test_randomizedAll(self, TIME_MULTIPLIER=2.5):
        super().test_randomizedAll(TIME_MULTIPLIER)


class AvalonStCastReadyLatencyAndAllowance_l0a1_TC(AvalonStCastReadyLatencyAndAllowance_l0a0_TC):
    internal_readyLatency = 0
    internal_readyAllowance = 1

    def test_randomizedAll(self, TIME_MULTIPLIER=2.5):
        super().test_randomizedAll(TIME_MULTIPLIER)


class AvalonStCastReadyLatencyAndAllowance_l1a2_TC(AvalonStCastReadyLatencyAndAllowance_l0a0_TC):
    internal_readyLatency = 1
    internal_readyAllowance = 2

    def test_normalOp(self, TIME_MULTIPLIER=1.1):
        super().test_normalOp(TIME_MULTIPLIER)

    def test_randomizedAll(self, TIME_MULTIPLIER=2.5):
        super().test_randomizedAll(TIME_MULTIPLIER)


class AvalonStCastReadyLatencyAndAllowance_l2a2_TC(AvalonStCastReadyLatencyAndAllowance_l0a0_TC):
    internal_readyLatency = 2
    internal_readyAllowance = 2

    def test_normalOp(self, TIME_MULTIPLIER=1.1):
        super().test_normalOp(TIME_MULTIPLIER)

    def test_randomizedAll(self, TIME_MULTIPLIER=2.5):
        super().test_randomizedAll(TIME_MULTIPLIER)


class AvalonStCastReadyLatencyAndAllowance_l3a3_TC(AvalonStCastReadyLatencyAndAllowance_l0a0_TC):
    internal_readyLatency = 3
    internal_readyAllowance = 3

    def test_normalOp(self, TIME_MULTIPLIER=1.2):
        super().test_normalOp(TIME_MULTIPLIER)

    def test_randomizedAll(self, TIME_MULTIPLIER=3):
        super().test_randomizedAll(TIME_MULTIPLIER)


AvalonStCastReadyLatencyAndAllowance_TCs = [
    AvalonStCastReadyLatencyAndAllowance_l0a0_TC,
    AvalonStCastReadyLatencyAndAllowance_l0a1_TC,
    AvalonStCastReadyLatencyAndAllowance_l1a1_TC,
    AvalonStCastReadyLatencyAndAllowance_l1a2_TC,
    AvalonStCastReadyLatencyAndAllowance_l2a2_TC,
    AvalonStCastReadyLatencyAndAllowance_l3a3_TC,
]

if __name__ == "__main__":
    import unittest
    from hwt.synth import to_rtl_str

    m = _TestAvalonStCastReadyLatencyAndAllowance_wire()
    m.internal_readyLatency = 2
    m.internal_readyAllowance = 2
    print(to_rtl_str(m))

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AvalonStCastReadyLatencyAndAllowance_l1a1_TC("test_normalOp")])
    # suite = testLoader.loadTestsFromTestCase(AvalonStCastReadyLatencyAndAllowance_l0a1_TC)
    suite = unittest.TestSuite([testLoader.loadTestsFromTestCase(tc) for tc in AvalonStCastReadyLatencyAndAllowance_TCs])
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
