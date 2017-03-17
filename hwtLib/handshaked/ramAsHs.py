from hwt.code import If
from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import Handshaked, BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class RamHsR(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.addr = Handshaked()
        self.addr._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        with self._paramsShared():
            self.data = Handshaked(masterDir=DIRECTION.IN)


class RamHsW(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.addr = Handshaked()
        self.addr._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        with self._paramsShared():
            self.data = Handshaked()


class RamAsHs(Unit):
    """
    Converter from ram port to handshaked interfaces
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.r = RamHsR()
            self.w = RamHsW()
            self.ram = BramPort_withoutClk()

    def _impl(self):
        r = self.r
        w = self.w
        ram = self.ram

        readRegEmpty = self._reg("readRegEmpty", defVal=0)
        readDataPending = self._reg("readDataPending", defVal=0)
        readData = self._reg("readData", r.data.data._dtype)

        rEn = readRegEmpty | r.data.rd
        readDataPending ** (r.addr.vld & rEn)
        If(readDataPending,
           readData ** ram.dout
        )
        If(readDataPending & ~r.data.rd,
           readRegEmpty ** 1
        ).Elif(~readDataPending & r.data.rd,
           readRegEmpty ** 0
        )
        r.addr.rd ** rEn

        If(rEn & r.addr.vld,
           ram.we ** 0,
           ram.addr ** r.addr.data 
        ).Else(
           ram.we ** 1,
           ram.addr ** w.addr.data
        )
        wEn = ~rEn | ~r.addr.vld
        w.addr.rd ** wEn
        w.data.rd ** wEn

        ram.din ** w.data.data
        ram.en ** ((rEn & r.addr.vld) | (w.addr.vld & w.data.vld))
        r.data.data ** readData
        r.data.vld ** ~readRegEmpty


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = RamAsHs()
    print(toRtl(u))         
            
