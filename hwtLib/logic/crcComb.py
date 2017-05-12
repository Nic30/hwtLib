from hwt.bitmask import selectBit
from hwt.code import iterBits
from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.logic.crcPoly import CRC_5_USB
from hwtLib.logic.crcUtils import parsePolyStr, buildCrcMatrix_dataMatrix


# http://www.sunshine2k.de/coding/javascript/crc/crc_js.html
class CrcComb(Unit):
    """
    CRC generator
    polynomial can be string in usual format or integer (f.e."x^3+x+1" or 0b1011)

    @attention: Input not reflected, Result not reflected, Initial Value: 0x0, Final Xor Value: 0x0
    """
    def _config(self):
        self.DATA_WIDTH = Param(5)

        self.POLY = Param(CRC_5_USB)
        self.POLY_WIDTH = Param(5)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VectSignal(self.DATA_WIDTH)
            self.dataOut = VectSignal(self.POLY_WIDTH)

    def _impl(self):
        PW = evalParam(self.POLY_WIDTH).val
        DW = evalParam(self.DATA_WIDTH).val
        # assert PW == DW
        poly = evalParam(self.POLY).val
        if isinstance(poly, str):
            polyCoefs = parsePolyStr(poly, PW)
        elif isinstance(poly, int):
            polyCoefs = [selectBit(poly, i) for i in range(PW)]
        else:
            raise NotImplementedError()
        xorMatrix = buildCrcMatrix_dataMatrix(polyCoefs, PW, DW)

        for outBit, inMask in zip(iterBits(self.dataOut),
                                  xorMatrix):
            bit = None
            for m, b in zip(inMask, iterBits(self.dataIn)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b
            assert bit is not None

            outBit ** bit


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = CrcComb()
    print(toRtl(u))
