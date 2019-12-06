from itertools import product

from hwt.hdl.constants import Time
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.structIntf import StructIntf
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import packAxiSFrame, \
    unpackAxiSFrame
from hwtLib.amba.axis_comp.frameForge_test import unionOfStructs, unionSimple
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
import os


structManyInts = HStruct(
                    (uint64_t, "i0"),
                    (uint64_t, None),  # dummy word
                    (uint64_t, "i1"),
                    (uint64_t, None),
                    (uint16_t, "i2"),
                    (uint16_t, "i3"),
                    (uint32_t, "i4"),  # 3 items in one word

                    (uint32_t, None),
                    (uint64_t, "i5"),  # this word is split on two bus words
                    (uint32_t, None),

                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, None),
                    (uint64_t, "i6"),
                    (uint64_t, "i7"),
                    )
MAGIC = 14
reference0 = {
    "i0": MAGIC + 1,
    "i1": MAGIC + 2,
    "i2": MAGIC + 3,
    "i3": MAGIC + 4,
    "i4": MAGIC + 5,
    "i5": MAGIC + 6,
    "i6": MAGIC + 7,
    "i7": MAGIC + 8,
}
reference1 = {
    "i0": MAGIC + 10,
    "i1": MAGIC + 20,
    "i2": MAGIC + 30,
    "i3": MAGIC + 40,
    "i4": MAGIC + 50,
    "i5": MAGIC + 60,
    "i6": MAGIC + 70,
    "i7": MAGIC + 80,
}


reference_unionOfStructs0 = (
    "frameA", {
        "itemA0": MAGIC + 1,
        "itemA1": MAGIC + 2,
        },
    )

reference_unionOfStructs1 = (
    "frameA", {
        "itemA0": MAGIC + 10,
        "itemA1": MAGIC + 20,
        },
    )

reference_unionOfStructs2 = (
    "frameB", {
        "itemB0": MAGIC + 3,
        "itemB1": MAGIC + 4,
        "itemB2": MAGIC + 5,
        "itemB3": MAGIC + 6,
        }
    )

reference_unionOfStructs3 = (
    "frameB", {
        "itemB0": MAGIC + 30,
        "itemB1": MAGIC + 40,
        "itemB2": MAGIC + 50,
        "itemB3": MAGIC + 60,
        }
    )


reference_unionSimple0 = ("a", MAGIC + 1)
reference_unionSimple1 = ("a", MAGIC + 10)
reference_unionSimple2 = ("b", MAGIC + 2)
reference_unionSimple3 = ("b", MAGIC + 20)


TEST_DW = [
    15, 16, 32, 51, 64, 
    128, 512
]
RAND_FLAGS = [
    False,
    True
]


def testMatrix(fn):
    def test_wrap(self):
        for dw, randomized in product(TEST_DW, RAND_FLAGS):
            try:
                fn(self, dw, randomized)
            except Exception as e:
                m = "DW:%d, Randomized:%r \n" % (dw, randomized)
                if isinstance(e.args[0], str):
                    e.args = (m + e.args[0], *e.args[1:])
                else:
                    e.args = (*e.args, m)
                raise
    return test_wrap


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

    def mySetUp(self, dataWidth, structTemplate, randomize=False):
        u = AxiS_frameParser(structTemplate)
        u.DATA_WIDTH = dataWidth
        if self.DEFAULT_BUILD_DIR is not None:
            # because otherwise files gets mixed in parralel test execution
            unique_name = "%s_%s_dw%d_r%d" % (self.getTestName(),
                                              u._getDefaultName(),
                                              dataWidth,
                                              randomize)
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
            d1 = t.from_py(reference0)
            f = list(packAxiSFrame(DW, d1))
            d2 = unpackAxiSFrame(t, f, lambda x: x[0])

            for k in reference0.keys():
                self.assertEqual(getattr(d1, k), getattr(d2, k), (DW, k))

    def runMatrixSim(self, time, dataWidth, randomize):
        unique_name = self.getTestName() + ("_dw%d_r%d" % (dataWidth, randomize))
        self.runSim(time, name="tmp/" + unique_name + ".vcd")

    @testMatrix
    def test_structManyInts_nop(self, dataWidth, randomize):
        u = self.mySetUp(dataWidth, structManyInts, randomize)

        self.runMatrixSim(300 * Time.ns, dataWidth, randomize)
        for intf in u.dataOut._interfaces:
            self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_structManyInts_2x(self, dataWidth, randomize):
        t = structManyInts
        u = self.mySetUp(dataWidth, t, randomize)

        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(reference0)))
        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(reference1)))

        t = ((8 * 64) / dataWidth) * 80 * Time.ns
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
            t = ts[dataWidth] * 10 * Time.ns
        self.runMatrixSim(t, dataWidth, randomize)

        for intf in u.dataOut._interfaces:
            n = intf._name
            d = [reference0[n], reference1[n]]
            self.assertValSequenceEqual(intf._ag.data, d, n)

    @testMatrix
    def test_unionOfStructs_nop(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)
        t = 150 * Time.ns

        self.runMatrixSim(t, dataWidth, randomize)
        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_unionOfStructs_noSel(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [reference_unionOfStructs0, reference_unionOfStructs2]:
            u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(d)))

        t = 150 * Time.ns
        self.runMatrixSim(t, dataWidth, randomize)

        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    @testMatrix
    def test_unionOfStructs(self, dataWidth, randomize):
        t = unionOfStructs
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [reference_unionOfStructs0, reference_unionOfStructs2,
                  reference_unionOfStructs1, reference_unionOfStructs3]:
            u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, t.from_py(d)))
        u.dataOut._select._ag.data.extend([0, 1, 0, 1])

        t = 500 * Time.ns
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
            t = ts[dataWidth] * 10 * Time.ns
        self.runMatrixSim(t, dataWidth, randomize)

        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            if i._name == "frameA":
                v0 = reference_unionOfStructs0[1]
                v1 = reference_unionOfStructs1[1]
            else:
                v0 = reference_unionOfStructs2[1]
                v1 = reference_unionOfStructs3[1]

            for intf in i._interfaces:
                n = intf._name
                vals = v0[n], v1[n]
                self.assertValSequenceEqual(intf._ag.data, vals, (i._name, n))

    @testMatrix
    def test_simpleUnion(self, dataWidth, randomize):
        t = unionSimple
        u = self.mySetUp(dataWidth, t, randomize)

        for d in [reference_unionSimple0, reference_unionSimple2,
                  reference_unionSimple1, reference_unionSimple3]:
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
            t = ts[dataWidth] * 20 * Time.ns
        self.runMatrixSim(t, dataWidth, randomize)

        for i in [u.dataOut.a, u.dataOut.b]:
            if i._name == "a":
                v0 = reference_unionSimple0[1]
                v1 = reference_unionSimple1[1]
            else:
                v0 = reference_unionSimple2[1]
                v1 = reference_unionSimple3[1]

            self.assertValSequenceEqual(i._ag.data, [v0, v1], i._name)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameParserTC('test_simpleUnion'))
    # suite.addTest(AxiS_frameParserTC('test_structManyInts_2x'))
    suite.addTest(unittest.makeSuite(AxiS_frameParserTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
