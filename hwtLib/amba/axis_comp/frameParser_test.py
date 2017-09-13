from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream_withoutSTRB, packAxiSFrame, \
    unpackAxiSFrame
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
from hwtLib.amba.axis_comp.frameForge_test import unionOfStructs


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


class AxiS_frameParserTC(SimTestCase):
    def mySetUp(self, dataWidth, structTemplate):
        u = AxiS_frameParser(AxiStream_withoutSTRB, structTemplate)
        u.DATA_WIDTH.set(dataWidth)
        self.prepareUnit(u)

        return u

    def test_packAxiSFrame(self):
        t = structManyInts
        DW = 32
        d1 = t.fromPy(reference0)
        f = list(packAxiSFrame(DW, d1))
        d2 = unpackAxiSFrame(t, f, lambda x: x[0])

        for k in reference0.keys():
            self.assertEqual(getattr(d1, k), getattr(d2, k), k)

    def test_structManyInts_64_nop(self):
        DW = 64
        u = self.mySetUp(DW, structManyInts)

        self.doSim(300 * Time.ns)
        for intf in u.dataOut._interfaces:
            self.assertEmpty(intf._ag.data)

    def _test_structManyInts_2x(self, DW):
        t = structManyInts
        u = self.mySetUp(DW, t)

        u.dataIn._ag.data.extend(packAxiSFrame(DW, t.fromPy(reference0)))
        u.dataIn._ag.data.extend(packAxiSFrame(DW, t.fromPy(reference1)))

        self.doSim(((8 * 64) / DW) * 80 * Time.ns)

        for intf in u.dataOut._interfaces:
            n = intf._name
            d = [reference0[n], reference1[n]]
            self.assertValSequenceEqual(intf._ag.data, d, n)

    def test_structManyInts_64_2x(self):
        self._test_structManyInts_2x(64)

    def test_structManyInts_32_2x(self):
        self._test_structManyInts_2x(32)

    def test_structManyInts_51_2x(self):
        self._test_structManyInts_2x(51)

    def test_unionOfStructs_nop(self, DW=64):
        t = unionOfStructs
        u = self.mySetUp(DW, t)

        self.doSim(150 * Time.ns)
        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    def test_unionOfStructs_noSel(self, DW=32):
        t = unionOfStructs
        u = self.mySetUp(DW, t)

        for d in [reference_unionOfStructs0, reference_unionOfStructs2]:
            u.dataIn._ag.data.extend(packAxiSFrame(DW, t.fromPy(d)))

        self.doSim(150 * Time.ns)
        for i in [u.dataOut.frameA, u.dataOut.frameB]:
            for intf in i._interfaces:
                self.assertEmpty(intf._ag.data)

    def test_unionOfStructs(self, DW=32):
        t = unionOfStructs
        u = self.mySetUp(DW, t)

        for d in [reference_unionOfStructs0, reference_unionOfStructs2,
                  reference_unionOfStructs1, reference_unionOfStructs3]:
            u.dataIn._ag.data.extend(packAxiSFrame(DW, t.fromPy(d)))
        u.dataOut._select._ag.data.extend([0, 1, 0, 1])

        self.doSim(300 * Time.ns)
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


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameParserTC('test_unionOfStructs'))
    suite.addTest(unittest.makeSuite(AxiS_frameParserTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
