from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream_withoutSTRB, packAxiSFrame, \
    unpackAxiSFrame
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t


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

    def _test_structManyInts_2x(self, dataWidth):
        structT = structManyInts
        u = self.mySetUp(dataWidth, structT)

        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, structT.fromPy(reference0)))
        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, structT.fromPy(reference1)))

        self.doSim(((8 * 64) / dataWidth) * 80 * Time.ns)

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


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameParserTC('test_structManyInts_51_2x'))
    suite.addTest(unittest.makeSuite(AxiS_frameParserTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
