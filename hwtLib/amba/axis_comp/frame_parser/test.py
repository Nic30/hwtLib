#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf
import os

from hwt.hdl.constants import Time
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structUtils import HdlType_select
from hwt.interfaces.structIntf import StructIntf
from hwt.pyUtils.testUtils import TestMatrix
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import packAxiSFrame, \
    unpackAxiSFrame, axis_recieve_bytes
from hwtLib.amba.axis_comp.frame_deparser.test_types import unionOfStructs, unionSimple
from hwtLib.amba.axis_comp.frame_parser import AxiS_frameParser
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


class AxiS_frameParserTC(SimTestCase):

    def setDown(self):
        self.rtl_simulator_cls = None
        super(AxiS_frameParserTC, self).setDown()

    def randomizeIntf(self, intf):
        if isinstance(intf, StructIntf):
            for _intf in intf._interfaces:
                self.randomizeIntf(_intf)
        else:
            self.randomize(intf)

    def mySetUp(self, dataWidth, structTemplate, randomize=False,
                use_strb=False, use_keep=False):
        u = AxiS_frameParser(structTemplate)
        u.USE_STRB = use_strb
        u.USE_KEEP = use_keep
        u.DATA_WIDTH = dataWidth
        if self.DEFAULT_BUILD_DIR is not None:
            # because otherwise files gets mixed in parralel test execution
            test_name = self.getTestName()
            u_name = u._getDefaultName()
            unique_name = f"{test_name:s}_{u_name:s}_dw{dataWidth:d}_r{randomize:d}"
            build_dir = os.path.join(self.DEFAULT_BUILD_DIR,
                                     self.getTestName() + unique_name)
        else:
            unique_name = None
            build_dir = None
        self.compileSimAndStart(u, unique_name=unique_name,
                                build_dir=build_dir)
        # because we want to prevent resuing of this class in TestCase.setUp()
        self.__class__.rtl_simulator_cls = None
        if randomize:
            self.randomizeIntf(u.dataIn)
            self.randomizeIntf(u.dataOut)
        return u

    def test_packAxiSFrame(self):
        t = structManyInts
        for DW in TEST_DW:
            d1 = t.from_py(ref0_structManyInts)
            f = list(packAxiSFrame(DW, d1))
            d2 = unpackAxiSFrame(t, f, lambda x: x[0])

            for k in ref0_structManyInts.keys():
                self.assertEqual(getattr(d1, k), getattr(d2, k), (DW, k))

    def runMatrixSim(self, time, dataWidth, randomize):
        test_name = self.getTestName()
        vcd_name = f"{test_name:s}_dw{dataWidth:d}_r{randomize:d}.vcd"
        self.runSim(time, name=os.path.join(self.DEFAULT_LOG_DIR, vcd_name))

    @testMatrix
    def test_structManyInts_nop(self, dataWidth, randomize):
        u = self.mySetUp(dataWidth, structManyInts, randomize)

        self.runMatrixSim(30 * CLK_PERIOD, dataWidth, randomize)
        for intf in u.dataOut._interfaces:
            self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_structManyInts_2x(self, dataWidth, randomize):
        t = structManyInts
        u = self.mySetUp(dataWidth, t, randomize)

        u.dataIn._ag.data.extend(packAxiSFrame(
            dataWidth, t.from_py(ref0_structManyInts)))
        u.dataIn._ag.data.extend(packAxiSFrame(
            dataWidth, t.from_py(ref1_structManyInts)))

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

        for intf in u.dataOut._interfaces:
            n = intf._name
            d = [ref0_structManyInts[n], ref1_structManyInts[n]]
            self.assertValSequenceEqual(intf._ag.data, d, n)

    @testMatrix
    def test_unionOfStructs_nop(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)
        t = 15 * CLK_PERIOD

        self.runMatrixSim(t, dataWidth, randomize)
        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_unionOfStructs_noSel(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionOfStructs0, ref_unionOfStructs2]:
            u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(d)))

        t = 15 * CLK_PERIOD
        self.runMatrixSim(t, dataWidth, randomize)

        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_unionOfStructs(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionOfStructs0, ref_unionOfStructs2,
                  ref_unionOfStructs1, ref_unionOfStructs3]:
            u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(d)))
        u.dataOut._select._ag.data.extend([0, 1, 0, 1])

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

        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            if i._name == "frameA":
                v0 = ref_unionOfStructs0[1]
                v1 = ref_unionOfStructs1[1]
            else:
                v0 = ref_unionOfStructs2[1]
                v1 = ref_unionOfStructs3[1]

            for intf in i._interfaces:
                n = intf._name
                vals = v0[n], v1[n]
                self.assertValSequenceEqual(intf._ag.data, vals, (i._name, n))

    @testMatrix
    def test_simpleUnion(self, dataWidth, randomize):
        t = unionSimple
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [ref_unionSimple0, ref_unionSimple2,
                  ref_unionSimple1, ref_unionSimple3]:
            u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(d)))
        u.dataOut._select._ag.data.extend([0, 1, 0, 1])

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

        for i in [u.dataOut.a, u.dataOut.b]:
            if i._name == "a":
                v0 = ref_unionSimple0[1]
                v1 = ref_unionSimple1[1]
            else:
                v0 = ref_unionSimple2[1]
                v1 = ref_unionSimple3[1]

            self.assertValSequenceEqual(i._ag.data, [v0, v1], i._name)

    def runMatrixSim2(self, t, dataWidth, frame_len, randomize, name_extra=""):
        test_name = self.getTestName()
        vcd_name = f"{test_name:s}_dw{dataWidth:d}_len{frame_len:d}_r{randomize:d}{name_extra:s}.vcd"
        self.runSim(t * CLK_PERIOD, name=os.path.join(self.DEFAULT_LOG_DIR, vcd_name))

    @TestMatrix([8, 16, 32], [1, 2, 5], [False, True])
    def test_const_size_stream(self, dataWidth, frame_len, randomize):
        T = HStruct(
            (HStream(Bits(8), frame_len=frame_len), "frame0"),
            (uint16_t, "footer"),
        )
        u = self.mySetUp(dataWidth, T, randomize, use_strb=True)
        u.dataIn._ag.data.extend(
            packAxiSFrame(dataWidth,
                          T.from_py({"frame0": [i + 1 for i in range(frame_len)],
                                     "footer": 2}),
                          withStrb=True,
                          )
            )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize)
        off, f = axis_recieve_bytes(u.dataOut.frame0)
        self.assertEqual(off, 0)
        self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])
        self.assertValSequenceEqual(u.dataOut.footer._ag.data, [2])

    @TestMatrix([32], [0, 1, 2, 5], [(False, False),
                                     (False, True),
                                     (True, False)], [False, True], [False, True])
    def test_stream_and_footer(self, dataWidth, frame_len, prefix_suffix_as_padding, randomize, optional_start):
        """
        :note: Footer separation is tested in AxiS_footerSplitTC
            and this test only check that the AxiS_frameParser can connect
            wires correctly
        """
        if not optional_start and frame_len == 0:
            # filtering tests which does not make sence from the test matrix
            return

        prefix_padding, suffix_padding = prefix_suffix_as_padding
        T = HStruct(
            (HStream(Bits(8), frame_len=(0, inf) if optional_start else (1, inf)), "frame0"),
            (uint16_t, "footer"),
        )
        fieldsToUse = set()
        if not prefix_padding:
            fieldsToUse.add("frame0")
        if not suffix_padding:
            fieldsToUse.add("footer")
        _T = HdlType_select(T, fieldsToUse)
        u = self.mySetUp(dataWidth, _T, randomize, use_strb=True)
        v = T.from_py({
            "frame0": [i + 1 for i in range(frame_len)],
            "footer": frame_len + 1
        })
        u.dataIn._ag.data.extend(
            packAxiSFrame(dataWidth, v, withStrb=True)
        )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize, name_extra=f"_startOpt{int(optional_start):d}")

        if not prefix_padding:
            off, f = axis_recieve_bytes(u.dataOut.frame0)
            self.assertEqual(off, 0)
            self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])

        if not suffix_padding:
            self.assertValSequenceEqual(u.dataOut.footer._ag.data, [frame_len + 1])

    @TestMatrix([8], [0, 1, 2, 5], [(False, False),
                                    (False, True),
                                    (True, False)], [False, True], [False, True])
    def test_header_stream(self, dataWidth, frame_len, prefix_suffix_as_padding, randomize, optional_end):
        """
        :note: Footer separation is tested in AxiS_footerSplitTC
            and this test only check that the AxiS_frameParser can connect
            wires correctly
        """
        if not optional_end and frame_len == 0:
            # filtering tests which does not make sence from the test matrix
            return
        prefix_padding, suffix_padding = prefix_suffix_as_padding
        T = HStruct(
            (uint8_t, "header"),
            (HStream(Bits(8), frame_len=(0, inf) if optional_end else (1, inf)), "frame0"),
        )
        fieldsToUse = set()
        if not prefix_padding:
            fieldsToUse.add("header")
        if not suffix_padding:
            fieldsToUse.add("frame0")
        _T = HdlType_select(T, fieldsToUse)
        u = self.mySetUp(dataWidth, _T, randomize, use_strb=True)
        v = T.from_py({
            "header": frame_len + 1,
            "frame0": [i + 1 for i in range(frame_len)],
        })
        u.dataIn._ag.data.extend(
            packAxiSFrame(dataWidth, v, withStrb=True)
        )
        t = 20
        if randomize:
            t *= 3

        self.runMatrixSim2(t, dataWidth, frame_len, randomize, name_extra=f"_endOpt{int(optional_end):d}")

        if not prefix_padding:
            self.assertValSequenceEqual(u.dataOut.header._ag.data, [frame_len + 1])

        if not suffix_padding:
            off, f = axis_recieve_bytes(u.dataOut.frame0)
            self.assertEqual(off, 0)
            self.assertValSequenceEqual(f, [i + 1 for i in range(frame_len)])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameParserTC('test_header_stream'))
    suite.addTest(unittest.makeSuite(AxiS_frameParserTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
