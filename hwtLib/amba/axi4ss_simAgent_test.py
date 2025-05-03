from typing import List, Deque, Tuple, Union

from hwt.hdl.const import HConst
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4SSegmented import Axi4StreamSegmented, \
    Axi4StreamSegmentedFrameUtils
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axis_comp.reg import Axi4SReg
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4StreamFrameUtils
from hwtSimApi.utils import freq_to_period


class _Axi4StreamSegmentedReg(HwModule):

    def hwConfig(self) -> None:
        Axi4StreamSegmented.hwConfig(self)

    def hwDeclr(self) -> None:
        addClkRstn(self)
        with self._hwParamsShared():
            self.rx = Axi4StreamSegmented()
            self.tx = Axi4StreamSegmented()._m()

    def hwImpl(self) -> None:
        tx = Axi4SBuilder(self, self.rx).buff().end
        self.tx(tx)
        propagateClkRstn(self)


class BaseAxi4SPktInPktOutTC(SimTestCase):
    """
    Base class for tests which test component which takes 1 frame and produces 1 frame
    Input port should be named "rx", output port should be named "tx"
    """
    StreamFrameUtils = Axi4StreamFrameUtils

    def _test(self, dut: HwModule, refFramesIn: List[List[int]], refFramesOut: List[List[int]], freq=int(1e6),
              rtlSimTimeMultiplier=2.0,
              ):
        """
        test optimizer IR, MIR and RTL
        """
        dut.CLK_FREQ = freq

        self.compileSimAndStart(dut)
        rxFu = self.StreamFrameUtils.from_HwIO(dut.rx)
        for refFrame in refFramesIn:
            rxFu.send_bytes(refFrame, dut.rx._ag.data)

        t = int(freq_to_period(freq) * (len(dut.rx._ag.data) + 10) * rtlSimTimeMultiplier)
        self.runSim(t)

        txFu = self.StreamFrameUtils.from_HwIO(dut.tx)
        for frame in refFramesOut:
            offset, data = txFu.receive_bytes(dut.tx._ag.data)
            self.assertEqual(offset, 0)
            self.assertValSequenceEqual(data, frame)

        self.assertEqual(len(dut.tx._ag.data), 0)

class Axi4StreamSegmentedAgent_TC(BaseAxi4SPktInPktOutTC):

    class StreamFrameUtils(Axi4StreamSegmentedFrameUtils):

        @override
        def receive_bytes(self, ag_data:Deque[Tuple[HBitsConst, HConst]]) -> Tuple[int, List[Union[int, HBitsConst]]]:
            # convert from (startSegmentIndex, dataBytes, err) to (offset, dataBytes) format
            _, dataBytes, err = Axi4StreamSegmentedFrameUtils.receive_bytes(self, ag_data)
            assert not err
            return (0, dataBytes)

    def _test(self, DATA_WIDTH:int, SEGMENT_CNT:int, FRAME_LENGTHS:List[int], PACK_SEGMENT_BITS:bool=False,
        freq=int(1e6)):

        dut = _Axi4StreamSegmentedReg()
        dut.DATA_WIDTH = DATA_WIDTH
        dut.SEGMENT_CNT = SEGMENT_CNT
        dut.PACK_SEGMENT_BITS = PACK_SEGMENT_BITS

        refFrames = []
        for frameLen in FRAME_LENGTHS:
            data = [i for i in range(1, frameLen + 1)]
            # data = [self._rand.getrandbits(8) for _ in range(frameLen)]
            refFrames.append(data)

        BaseAxi4SPktInPktOutTC._test(self, dut, refFrames, refFrames, freq=freq)

    def test_2x2B(self):
        PKT_CNT = 6
        self._test(16, 2, [self._rand.randint(1, 7) for _ in range(PKT_CNT)])

    def test_2x2B_PACK_SEGMENT_BITS(self):
        PKT_CNT = 6
        self._test(16, 2, [self._rand.randint(1, 7) for _ in range(PKT_CNT)], PACK_SEGMENT_BITS=True)


if __name__ == "__main__":
    m = Axi4SReg(hwIOCls=Axi4StreamSegmented)
    m.SEGMENT_CNT = 2
    m.PACK_SEGMENT_BITS = False
    from hwt.synth import to_rtl_str

    print(to_rtl_str(m))

    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4StreamSegmentedAgent_TC("test_WriteFsmPrequel")])
    suite = testLoader.loadTestsFromTestCase(Axi4StreamSegmentedAgent_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
