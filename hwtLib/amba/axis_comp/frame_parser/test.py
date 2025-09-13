#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from math import inf
import os
from typing import Tuple

from hwt.constants import Time
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structUtils import HdlType_select
from hwt.hwIO import HwIO
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.pyUtils.testUtils import TestMatrix
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4sSimFrameUtils import axi4s_receive_bytes, Axi4StreamSimFrameUtils
from hwtLib.amba.axis_comp.frame_deparser.test_types import unionOfStructs, unionSimple
from hwtLib.amba.axis_comp.frame_parser import Axi4S_frameParser
from hwtLib.amba.axis_comp.frame_parser.test_types import structManyInts, \
    ref0_structManyInts, ref1_structManyInts, ref_unionOfStructs0, \
    ref_unionOfStructs2, ref_unionOfStructs1, ref_unionOfStructs3, \
    ref_unionSimple0, ref_unionSimple1, ref_unionSimple2, ref_unionSimple3
from hwtLib.types.ctypes import uint16_t, uint8_t
from hwtSimApi.constants import CLK_PERIOD


TEST_DW = [
    15, 16, 32, 51, 64,
    128, 512
]
RAND_FLAGS = [
    False,
    True
]

testMatrix = TestMatrix(TEST_DW, RAND_FLAGS)


class Axi4S_frameParserTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def randomizeIntf(self, hwIO: HwIO):
        if isinstance(hwIO, HwIOStruct):
            for cHwIO in hwIO._hwIOs:
                self.randomizeIntf(cHwIO)
        else:
            self.randomize(hwIO)

    def mySetUp(self, dataWidth: int, structTemplate: HdlType, randomize=False,
                use_strb=False, use_keep=False) -> Tuple[Axi4S_frameParser, Axi4StreamSimFrameUtils]:
        dut = Axi4S_frameParser(structTemplate)
        dut.USE_STRB = use_strb
        dut.USE_KEEP = use_keep
        dut.DATA_WIDTH = dataWidth
        if self.DEFAULT_BUILD_DIR is not None:
            # because otherwise files gets mixed in parallel test execution
            test_name = self.getTestName()
            u_name = dut._getDefaultName()
            unique_name = f"{test_name:s}_{u_name:s}_dw{dataWidth:d}_r{randomize:d}"
            build_dir = os.path.join(self.DEFAULT_BUILD_DIR,
                                     self.getTestName() + unique_name)
        else:
            unique_name = None
            build_dir = None
        self.compileSimAndStart(dut, unique_name=unique_name,
                                build_dir=build_dir)
        # because we want to prevent reusing of this class in TestCase.setUp()
        self.__class__.rtl_simulator_cls = None
        if randomize:
            self.randomizeIntf(dut.dataIn)
            self.randomizeIntf(dut.dataOut)
        fu = Axi4StreamSimFrameUtils(dataWidth, USE_STRB=use_strb, USE_KEEP=use_keep)
        return dut, fu

    def test_pack_frame(self):
        t = structManyInts
        for DW in TEST_DW:
            d1 = t.from_py(ref0_structManyInts)
            fu = Axi4StreamSimFrameUtils(DW)
            f = deque(fu.pack_frame(d1))
            d2 = fu.unpack_frame(t, f)

            for k in ref0_structManyInts.keys():
                self.assertEqual(getattr(d1, k), getattr(d2, k), (DW, k))

    def runMatrixSim(self, time: int, dataWidth: int, randomize: bool):
        test_name = self.getTestName()
        vcd_name = f"{test_name:s}_dw{dataWidth:d}_r{randomize:d}.vcd"
        self.runSim(time, name=os.path.join(self.DEFAULT_LOG_DIR, vcd_name))

    @testMatrix
    def test_structManyInts_nop(self, dataWidth: int, randomize: bool):
        dut, _ = self.mySetUp(dataWidth, structManyInts, randomize)

        self.runMatrixSim(30 * CLK_PERIOD, dataWidth, randomize)
        for hwIO in dut.dataOut._hwIOs:
            self.assertEmpty(hwIO._ag.data)

    @testMatrix
    def test_structManyInts_2x(self, dataWidth: int, randomize: bool):
        t = structManyInts
        dut, fu = self.mySetUp(dataWidth, t, randomize)

        dut.dataIn._ag.data.extend(fu.pack_frame(t.from_py(ref0_structManyInts)))
        dut.dataIn._ag.data.extend(fu.pack_frame(t.from_py(ref1_structManyInts)))

        if randomize:
            # {DW: t}
            ts = {
                15: 300,
                16: 240,
                32: 300,
                51: 160,
                64: 160,
                128: 110,
                512: 90,
            }
            t = ts[dataWidth] * CLK_PERIOD
        else:
            t = int(((8 * 64) / dataWidth) * 8 * CLK_PERIOD)
        self.runMatrixSim(t, dataWidth, randomize)

        for hwIO in dut.dataOut._hwIOs:
            n = hwIO._name
            d = [ref0_structManyInts[n], ref1_structManyInts[n]]
            self.assertValSequenceEqual(hwIO._ag.data, d, n)

    @testMatrix
    def test_unionOfStructs_nop(self, dataWidth: int, randomize: bool):
        t = unionOfStructs
        dut, _ = self.mySetUp(dataWidth, t, randomize)
        t = 15 * CLK_PERIOD

        self.runMatrixSim(t, dataWidth, randomize)
        for hwIO in [dut.dataOut.frameA, dut.dataOut.frameB]:
            for cHwIO in hwIO._hwIOs:
                self.assertEmpty(cHwIO._ag.data)

    @testMatrix
    def test_unionOfStructs_noSel(self, dataWidth: int, randomize: bool):
        t = unionOfStructs
        dut, fu = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionOfStructs0, ref_unionOfStructs2]:
            dut.dataIn._ag.data.extend(fu.pack_frame(t.from_py(d)))

        t = 15 * CLK_PERIOD
        self.runMatrixSim(t, dataWidth, randomize)

        for hwIO in [dut.dataOut.frameA, dut.dataOut.frameB]:
            for cHwIO in hwIO._hwIOs:
                self.assertEmpty(cHwIO._ag.data)

    @testMatrix
    def test_unionOfStructs(self, dataWidth: int, randomize: bool):
        t = unionOfStructs
        dut, fu = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionOfStructs0, ref_unionOfStructs2,
                  ref_unionOfStructs1, ref_unionOfStructs3]:
            dut.dataIn._ag.data.extend(fu.pack_frame(t.from_py(d)))
        dut.dataOut._select._ag.data.extend([0, 1, 0, 1])

        if randomize:
            # {DW: t}
            ts = {
                15: 200,
                16: 280,
                32: 200,
                51: 90,
                64: 100,
                128: 130,
                512: 50,
            }
            t = ts[dataWidth] * CLK_PERIOD
        else:
            t = 50 * CLK_PERIOD
        self.runMatrixSim(t, dataWidth, randomize)

        for hwIO in [dut.dataOut.frameA, dut.dataOut.frameB]:
            if hwIO._name == "frameA":
                v0 = ref_unionOfStructs0[1]
                v1 = ref_unionOfStructs1[1]
            else:
                v0 = ref_unionOfStructs2[1]
                v1 = ref_unionOfStructs3[1]

            for cHwIO in hwIO._hwIOs:
                n = cHwIO._name
                vals = v0[n], v1[n]
                self.assertValSequenceEqual(cHwIO._ag.data, vals, (hwIO._name, n))

    @testMatrix
    def test_simpleUnion(self, dataWidth: int, randomize: bool):
        t = unionSimple
        dut, fu = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionSimple0, ref_unionSimple2,
                  ref_unionSimple1, ref_unionSimple3]:
            dut.dataIn._ag.data.extend(fu.pack_frame(t.from_py(d)))
        dut.dataOut._select._ag.data.extend([0, 1, 0, 1])

        t = 300 * Time.ns
        if randomize:
            # {DW: t}
            ts = {
                15: 80,
                16: 55,
                32: 85,
                51: 45,
                64: 70,
                128: 20,
                512: 65,
            }
            t = ts[dataWidth] * 2 * CLK_PERIOD
        self.runMatrixSim(t, dataWidth, randomize)

        for i in [dut.dataOut.a, dut.dataOut.b]:
            if i._name == "a":
                v0 = ref_unionSimple0[1]
                v1 = ref_unionSimple1[1]
            else:
                v0 = ref_unionSimple2[1]
                v1 = ref_unionSimple3[1]

            self.assertValSequenceEqual(i._ag.data, [v0, v1], i._name)

    def runMatrixSim2(self, t, dataWidth: int, frame_len: int, randomize: bool, name_extra: str=""):
        test_name = self.getTestName()
        vcd_name = f"{test_name:s}_dw{dataWidth:d}_len{frame_len:d}_r{randomize:d}{name_extra:s}.vcd"
        self.runSim(t * CLK_PERIOD, name=os.path.join(self.DEFAULT_LOG_DIR, vcd_name))

    @TestMatrix([8, 16, 32], [1, 2, 5], [False, True])
    def test_const_size_stream(self, dataWidth: int, frame_len: int, randomize: bool):
        T = HStruct(
            (HStream(HBits(8), frame_len=frame_len), "frame0"),
            (uint16_t, "footer"),
        )
        dut, fu = self.mySetUp(dataWidth, T, randomize, use_strb=True)
        dut.dataIn._ag.data.extend(
            fu.pack_frame(
                T.from_py({"frame0": [i + 1 for i in range(frame_len)],
                           "footer": 2}),
            )
        )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize)
        off, f = axi4s_receive_bytes(dut.dataOut.frame0)
        self.assertEqual(off, 0)
        self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])
        self.assertValSequenceEqual(dut.dataOut.footer._ag.data, [2])

    @TestMatrix([32], [0, 1, 2, 5], [(False, False),
                                     (False, True),
                                     (True, False)], [False, True], [False, True])
    def test_stream_and_footer(self, dataWidth: int, frame_len: int, prefix_suffix_as_padding: tuple[bool, bool],
                               randomize: bool, optional_start: bool):
        """
        :note: Footer separation is tested in Axi4S_footerSplitTC
            and this test only check that the Axi4S_frameParser can connect
            wires correctly
        """
        if not optional_start and frame_len == 0:
            # filtering tests which does not make sense from the test matrix
            return

        prefix_padding, suffix_padding = prefix_suffix_as_padding
        T = HStruct(
            (HStream(HBits(8), frame_len=(0, inf) if optional_start else (1, inf)), "frame0"),
            (uint16_t, "footer"),
        )
        fieldsToUse = set()
        if not prefix_padding:
            fieldsToUse.add("frame0")
        if not suffix_padding:
            fieldsToUse.add("footer")
        _T = HdlType_select(T, fieldsToUse)
        dut, fu = self.mySetUp(dataWidth, _T, randomize, use_strb=True)
        v = T.from_py({
            "frame0": [i + 1 for i in range(frame_len)],
            "footer": frame_len + 1
        })
        dut.dataIn._ag.data.extend(
            fu.pack_frame(v)
        )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize, name_extra=f"_startOpt{int(optional_start):d}")

        if not prefix_padding:
            off, f = axi4s_receive_bytes(dut.dataOut.frame0)
            self.assertEqual(off, 0)
            self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])

        if not suffix_padding:
            self.assertValSequenceEqual(dut.dataOut.footer._ag.data, [frame_len + 1])

    @TestMatrix([8], [0, 1, 2, 5], [(False, False),
                                    (False, True),
                                    (True, False)], [False, True], [False, True])
    def test_header_stream(self, dataWidth: int, frame_len: int, prefix_suffix_as_padding: tuple[bool, bool],
                               randomize: bool, optional_end: bool):
        """
        :note: Footer separation is tested in Axi4S_footerSplitTC
            and this test only check that the Axi4S_frameParser can connect
            wires correctly
        """
        if not optional_end and frame_len == 0:
            # filtering tests which does not make sense from the test matrix
            return

        prefix_padding, suffix_padding = prefix_suffix_as_padding
        T = HStruct(
            (uint8_t, "header"),
            (HStream(HBits(8), frame_len=(0, inf) if optional_end else (1, inf)), "frame0"),
        )
        fieldsToUse = set()
        if not prefix_padding:
            fieldsToUse.add("header")
        if not suffix_padding:
            fieldsToUse.add("frame0")
        _T = HdlType_select(T, fieldsToUse)
        dut, fu = self.mySetUp(dataWidth, _T, randomize, use_strb=True)
        v = T.from_py({
            "header": frame_len + 1,
            "frame0": [i + 1 for i in range(frame_len)],
        })
        dut.dataIn._ag.data.extend(
            fu.pack_frame(v)
        )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize, name_extra=f"_endOpt{int(optional_end):d}")

        if not prefix_padding:
            self.assertValSequenceEqual(dut.dataOut.header._ag.data, [frame_len + 1])

        if not suffix_padding:
            off, f = axi4s_receive_bytes(dut.dataOut.frame0)
            self.assertEqual(off, 0)
            self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_frameParserTC("test_pack_frame")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_frameParserTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
