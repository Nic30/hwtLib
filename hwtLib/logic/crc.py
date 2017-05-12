from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.logic.crcPoly import CRC_5_USB
from hwt.interfaces.std import VldSynced, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwtLib.logic.crcUtils import parsePolyStr, buildCrcMatrix
from hwt.bitmask import selectBit
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.code import iterBits


# http://stackoverflow.com/questions/41734560/parallel-crc-32-calculation-ethernet-10ge-mac
class Crc(Unit):
    """
    Crc generator for any crc
    polynom can be string in usual format or integer f.e."x^3+x+1" or 0x1
    """
    def _config(self):
        self.DATA_WIDTH = Param(5)

        self.POLY = Param(CRC_5_USB)
        self.POLY_WIDTH = Param(5)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VldSynced()
            self.dataOut = VectSignal(self.POLY_WIDTH)

    def _impl(self):
        PW = evalParam(self.POLY_WIDTH).val
        DW = evalParam(self.DATA_WIDTH).val
        poly = evalParam(self.POLY).val
        if isinstance(poly, str):
            polyCoefs = parsePolyStr(poly, PW)
        elif isinstance(poly, int):
            polyCoefs = [selectBit(poly, i) for i in range(PW)]
        else:
            raise NotImplementedError()
        regXorMatrix, dataXorMatrix = buildCrcMatrix(polyCoefs, PW, DW)

        reg = self._reg("crcReg",
                        vecT(self.POLY_WIDTH),
                        0)

        dataXorMatrix = iter(dataXorMatrix)
        for regBit, regMask in zip(iterBits(reg.next),
                                   regXorMatrix):
            bit = None
            for m, b in zip(regMask, iterBits(reg)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b

            try:
                dataMask = next(dataXorMatrix)
            except StopIteration:
                dataMask = []

            for m, b in zip(dataMask, iterBits(self.dataIn.data)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b
            assert bit is not None
            regBit ** bit

        self.dataOut ** reg