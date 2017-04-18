from hwt.bitmask import mask
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import If, connect, Concat, Switch, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync, streamAck
from hwtLib.amba.axis import AxiStream
from hwtLib.mem.fifo import Fifo


def strbToRem(strbBits):
    """
    :return: tuples (mask, numberofBits)
    """
    for rem in range(strbBits):
        if (rem == 0):
            strb = mask(strbBits)
        else:
            strb = mask(rem)
        yield strb, rem


class AxiS_measuringFifo(Unit):
    """
    Fifo which are counting sizes of frames and sends it over
    dedicated handshaked interface
    """
    def _config(self):
        Fifo._config(self)
        self.SIZES_BUFF_DEPTH = Param(16)
        self.MAX_LEN = Param((2048 // 8) - 1)

    def getAlignBitsCnt(self):
        return log2ceil(self.DATA_WIDTH // 8).val

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.dataOut = AxiStream()

        self.sizes = Handshaked()
        self.sizes.DATA_WIDTH.set(log2ceil(self.MAX_LEN) + 1 + self.getAlignBitsCnt())

        db = self.dataBuff = AxiSFifo(AxiStream)
        # to place fifo in bram
        db.DATA_WIDTH.set(self.DATA_WIDTH)
        db.DEPTH.set((self.MAX_LEN + 1) * 2)

        sb = self.sizesBuff = HandshakedFifo(Handshaked)
        sb.DEPTH.set(self.SIZES_BUFF_DEPTH)
        sb.DATA_WIDTH.set(self.sizes.DATA_WIDTH.get())
        self.errorAlignment = Signal()

    def _impl(self):
        propagateClkRstn(self)
        dIn = AxiSBuilder(self, self.dataIn).reg().end
        STRB_BITS = dIn.strb._dtype.bit_length()

        sb = self.sizesBuff
        db = self.dataBuff

        wordCntr = self._reg("wordCntr",
                             vecT(log2ceil(self.MAX_LEN) + 1),
                             defVal=0)
        errorAlignment = self._reg("errorAlignment_reg", defVal=0)
        self.errorAlignment ** errorAlignment

        overflow = wordCntr._eq(self.MAX_LEN)
        last = dIn.last | overflow
        If(streamAck(masters=[dIn], slaves=[sb.dataIn, db.dataIn]),
            If(last,
                wordCntr ** 0
            ).Else(
                wordCntr ** (wordCntr + 1)
            )
        )
        rem = self._sig("rem", vecT(log2ceil(STRB_BITS)))
        Switch(dIn.strb).addCases(
           [(strb, rem ** r)
            for strb, r in strbToRem(STRB_BITS)]
        ).Default(
            rem ** 0,
            If(dIn.valid,
               errorAlignment ** 1
            )
        )

        length = self._sig("length", wordCntr._dtype)
        If(dIn.strb != mask(STRB_BITS),
            length ** wordCntr
        ).Else(
            length ** (wordCntr + 1)
        )

        sb.dataIn.data ** Concat(length, rem)

        connect(dIn, db.dataIn, exclude=[dIn.valid, dIn.ready])

        streamSync(masters=[dIn],
                   slaves=[sb.dataIn, db.dataIn],
                   extraConds={
                               sb.dataIn: last
                              })

        self.sizes ** sb.dataOut
        connect(db.dataOut, self.dataOut, exclude=[db.dataOut.last])
        self.dataOut.last ** db.dataOut.last


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiS_measuringFifo()
    print(toRtl(u))
