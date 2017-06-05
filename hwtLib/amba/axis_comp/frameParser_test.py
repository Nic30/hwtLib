from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
from hwtLib.amba.axis import AxiStream_withoutSTRB
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.bits import Bits
from hwt.simulator.types.simBits import simBitsT
from hwt.bitmask import mask


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


def packFrame(dataWidth, structT, data):
    """
    Pack data into list of BitsVal of specified dataWidth

    :param dataWidth: width of word
    :param structT: HStruct type instance
    :param data: list of values for struct fields (with name specified) or dictionary {fieldName: value}

    :return: list of BitsVal which are representing values of words
    """
    typeOfWord = simBitsT(dataWidth, None)

    actualVal = 0
    actualVldMask = 0
    usedBits = 0

    i = 0
    for field in structT.fields:
        if field.name is None:
            value = None
        else:
            if isinstance(data, dict):
                value = data[field.name]
            else:
                value = data[i]
                i += 1

        t = field.dtype
        if isinstance(t, Bits):
            w = t.bit_length()
            while True:
                fieldEnd = usedBits + w
                if fieldEnd <= dataWidth:
                    # there is space in this word
                    if value is not None:
                        actualVal |= value << usedBits
                        actualVldMask |= mask(w) << usedBits
                    usedBits += w
                else:
                    # we can not fit this field into this word
                    space = dataWidth - usedBits
                    if value is not None:
                        m = mask(space)
                        actualVal |= (value & m) << usedBits
                        actualVldMask |= m << usedBits
                        value >>= space
                    w -= space

                if fieldEnd >= dataWidth:
                    yield typeOfWord.getValueCls()(actualVal, typeOfWord, actualVldMask, -1)
                    actualVal = 0
                    actualVldMask = 0
                    if fieldEnd < dataWidth:
                        usedBits += w
                    else:
                        usedBits = 0

                if fieldEnd <= dataWidth:
                    break

        else:
            raise NotImplementedError()

    if usedBits:
        yield typeOfWord.getValueCls()(actualVal, typeOfWord, actualVldMask, -1)


def packAxiSFrame(dataWidth, structT, data, withStrb=False):
    if withStrb:
        raise NotImplementedError()
    words = list(packFrame(dataWidth, structT, data))
    end = len(words) - 1
    for i, d in enumerate(words):
        last = int(i == end)
        yield (d, last)


class AxiS_frameParserTC(SimTestCase):
    def mySetUp(self, dataWidth, structTemplate):
        u = AxiS_frameParser(AxiStream_withoutSTRB, structTemplate)
        u.DATA_WIDTH.set(dataWidth)
        self.prepareUnit(u)

        return u

    def test_structManyInts_64_nop(self):
        DW = 64
        u = self.mySetUp(DW, structManyInts)

        self.doSim(300 * Time.ns)
        for intf in u.dataOut._interfaces:
            self.assertEmpty(intf._ag.data)

    def _test_structManyInts_2x(self, dataWidth):
        structT = structManyInts
        u = self.mySetUp(dataWidth, structT)

        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, structT, reference0))
        u.dataIn._ag.data.extend(packAxiSFrame(dataWidth, structT, reference1))

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
    # suite.addTest(AxiS_measuringFifoTC('test_withPause'))
    suite.addTest(unittest.makeSuite(AxiS_frameParserTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
