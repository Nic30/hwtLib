from typing import Optional
from hwtLib.logic.crcPoly import CRC_POLY
from pyMathBitPrecise.bit_utils import reverse_bits, mask, \
    bit_list_reversed_endianity, bit_list_reversed_bits_in_bytes, \
    bit_list_to_int
from hwtLib.logic.crcComb import CrcComb


class NaiveCrcAccumulator:
    """
    Holds the intermediate state of the CRC algorithm.

    Based on http://www.nightmare.com/~ryb/
    """

    def __init__(self, params: CRC_POLY, value: Optional[int]=None):
        """
        :param value:

          The initial register value to use.  The result previous of a
          previous CRC calculation, can be used here to continue
          calculation with more data.  If this parameter is ``None``
          or not given, the register will be initialized with
          algorithm's default seed value.
        """

        self.params = params
        self.bitMask = mask(params.WIDTH)
        self.polyMask = params.POLY & self.bitMask
        self.inBitMask = 1
        self.outBitMask = 1 << (params.WIDTH - 1)

        if params.REFIN:
            self.polyMask = reverse_bits(self.polyMask, params.WIDTH)
            # (swap)
            self.inBitMask = self.outBitMask
            self.outBitMask = 1

        # print("%x" % self.polyMask, self.inBitMask, self.outBitMask)
        self.REFOUT = params.REFOUT

        self.reset()

        if value is not None:
            self.value = value ^ params.XOROUT

    def reset(self):
        """
        Reset the state of the register with the default seed value.
        """
        self.value = self.params.INIT

    def takeBit(self, bit: int):
        """
        Process a single input bit.
        """
        assert bit in (0, 1, True, False), bit
        outBit = int((self.value & self.outBitMask) != 0)
        if self.params.REFIN:
            self.value >>= 1
        else:
            self.value <<= 1
            self.value &= self.bitMask

        # print("o, i", outBit, bit)
        if outBit ^ bit:
            self.value ^= self.polyMask
            # print("{0:05b}".format(self.value))

    def takeWord(self, word: int, width: int):
        """
        Process a binary input word.

        :param word:

          The input word.  Since this can be a Python ``long``, there
          is no coded limit to the number of bits the word can
          represent.
        """
        assert (word >> width) == 0, (word, width)
        if self.REFOUT:
            bitI = range(0, width)
        else:
            bitI = range(width - 1, -1, -1)

        # sprint(self.value)
        for i in bitI:
            self.takeBit((word >> i) & 1)

    def getValue(self):
        """
        Return the current value of the register as an integer.
        """
        return self.value

    def getFinalValue(self):
        """
        Return the current value of the register as an integer with
        *xorMask* applied.  This can be used after all input data is
        processed to obtain the final result.
        """
        v = self.value ^ self.params.XOROUT

        if self.REFOUT:
            v = reverse_bits(v, self.params.WIDTH)

        return v


def naive_crc(dataBits, crcBits, polyBits,
              refin=False, refout=False):
    crc_mask = CrcComb.buildCrcXorMatrix(len(dataBits), polyBits)

    dataBits = bit_list_reversed_endianity(dataBits)
    if refin:
        # reflect bytes in input data signal
        # whole signal should not be reflected if DW > PW
        # polyBits = list(reversed(polyBits))
        dataBits = bit_list_reversed_bits_in_bytes(dataBits)
        # crcBits = reversedBitsInBytes(crcBits)

    res = []
    for stateMask, dataMask in crc_mask:
        # if refin:
        #    stateMask = reversed(stateMask)
        #    dataMask = reversed(dataMask)

        v = 0
        for useBit, b in zip(stateMask, crcBits):
            if useBit:
                v ^= b

        for useBit, b in zip(dataMask, dataBits):
            if useBit:
                v ^= b

        res.append(v)

    assert len(res) == len(polyBits)
    if refout:
        res = reversed(res)
    return bit_list_to_int(res)


if __name__ == "__main__":
    from hwtLib.logic.crcPoly import CRC_5_USB

    def assert_eq(r, v):
        if r.getFinalValue() == v:
            print("OK: {0:05b}".format(v))
            return
        else:
            print(r)
            print("Error: {0:05b} != {1:05b}".format(
                r.getFinalValue(), v))

    # from https://www.usb.org/sites/default/files/crcdes.pdf
    r = NaiveCrcAccumulator(CRC_5_USB)
    r.takeWord(0x0710, 11)
    assert_eq(r, 0b10100)

    r = NaiveCrcAccumulator(CRC_5_USB)
    r.takeWord(0x15, 7)
    r.takeWord(0xE, 4)
    assert_eq(r, 0b10111)

