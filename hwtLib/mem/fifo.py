#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, log2ceil
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import FifoWriter, FifoReader, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


# https://eewiki.net/pages/viewpage.action?pageId=20939499
@serializeParamsUniq
class Fifo(Unit):
    """
    Generic FIFO usually mapped to BRAM.

    :ivar EXPORT_SIZE: parameter, if true "size" signal will be exported
    :ivar size: optional signal with count of items stored in this fifo
    :ivar EXPORT_SPACE: parameter, if true "space" signal is exported
    :ivar space: optional signal with count of items which can be added to this fifo
    
    .. hwt-schematic:: _example_Fifo
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DEPTH = Param(0)
        self.EXPORT_SIZE = Param(False)
        self.EXPORT_SPACE = Param(False)

    def _declr(self):
        assert int(
            self.DEPTH) > 0, "Fifo is disabled in this case, do not use it entirely"
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = FifoWriter()
            self.dataOut = FifoReader()._m()

        if self.EXPORT_SIZE:
            self.size = VectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()
        if self.EXPORT_SPACE:
            self.space = VectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()

    def _impl(self):
        DEPTH = self.DEPTH

        index_t = Bits(log2ceil(DEPTH), signed=False)
        s = self._sig
        r = self._reg

        mem = self.mem = s("memory", Bits(self.DATA_WIDTH)[self.DEPTH])
        wr_ptr = r("wr_ptr", index_t, 0)
        rd_ptr = r("rd_ptr", index_t, 0)
        MAX_DEPTH = DEPTH - 1

        dout = self.dataOut
        din = self.dataIn

        # we are storing signals to properties because someone else may use
        # them
        self.__fifo_write = fifo_write = s("fifo_write")
        self.__fifo_read = fifo_read = s("fifo_read")

        # Update Tail pointer as needed
        If(fifo_read,
            If(rd_ptr._eq(MAX_DEPTH),
               rd_ptr(0)
            ).Else(
                rd_ptr(rd_ptr + 1)
            )
        )

        # Increment Head pointer as needed
        If(fifo_write,
            If(wr_ptr._eq(MAX_DEPTH),
                wr_ptr(0)
               ).Else(
                wr_ptr(wr_ptr + 1)
            )
           )

        If(self.clk._onRisingEdge(),
            If(fifo_write,
                # Write Data to Memory
                mem[wr_ptr](din.data)
            )
        )

        # assert isPow2(int(DEPTH)), DEPTH

        looped = r("looped", def_val=False)

        fifo_read(dout.en & (looped | (wr_ptr != rd_ptr)))
        If(self.clk._onRisingEdge(),
            If(fifo_read,
                # Update data output
                dout.data(mem[rd_ptr])
            )
        )

        fifo_write(din.en & (~looped | (wr_ptr != rd_ptr)))

        # looped logic
        If(din.en & wr_ptr._eq(MAX_DEPTH),
            looped(True)
        ).Elif(dout.en & rd_ptr._eq(MAX_DEPTH),
            looped(False)
        )

        # Update Empty and Full flags
        If(wr_ptr._eq(rd_ptr),
            If(looped,
                din.wait(1),
                dout.wait(0)
            ).Else(
                dout.wait(1),
                din.wait(0)
            )
        ).Else(
            din.wait(0),
            dout.wait(0)
        )
        if self.EXPORT_SIZE:
            size = r("size_reg", self.size._dtype, 0)
            If(fifo_read,
                If(~fifo_write,
                   size(size - 1)
                )
            ).Else(
                If(fifo_write,
                   size(size + 1)
                )
            )
            self.size(size)
        if self.EXPORT_SPACE:
            space = r("space_reg", self.size._dtype, DEPTH)
            If(fifo_read,
                If(~fifo_write,
                   size(space + 1)
                )
            ).Else(
                If(fifo_write,
                   size(space - 1)
                )
            )
            self.space(space)


def _example_Fifo():
    u = Fifo()
    u.DATA_WIDTH = 8
    # u.EXPORT_SIZE = True
    u.DEPTH = 16
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_Fifo()
    print(toRtl(u))
