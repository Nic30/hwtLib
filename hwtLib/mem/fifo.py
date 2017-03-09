#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.std import FifoWriter, FifoReader, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.code import If, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


# https://eewiki.net/pages/viewpage.action?pageId=20939499
class Fifo(Unit):
    _serializerMode = SERI_MODE.PARAMS_UNIQ

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DEPTH = Param(200)
        self.EXPORT_SIZE = Param(False)
        self.EXPORT_SPACE = Param(False)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = FifoWriter()
            self.dataOut = FifoReader()

        if evalParam(self.EXPORT_SIZE).val:
            self.size = VectSignal(log2ceil(self.DEPTH + 1), signed=False)
        if evalParam(self.EXPORT_SPACE).val:
            self.space = VectSignal(log2ceil(self.DEPTH + 1), signed=False)

    def _impl(self):
        DEPTH = self.DEPTH
        assert evalParam(DEPTH).val > 0

        index_t = vecT(log2ceil(DEPTH), False)
        s = self._sig
        r = self._reg

        mem = self.mem = s("memory", Array(vecT(self.DATA_WIDTH), self.DEPTH))
        wr_ptr = r("wr_ptr", index_t, 0)
        rd_ptr = r("rd_ptr", index_t, 0)
        MAX_DEPTH = DEPTH - 1

        dout = self.dataOut
        din = self.dataIn

        # we are storing signals to properties because someone else may use them
        self.__fifo_write = fifo_write = s("fifo_write")
        self.__fifo_read = fifo_read = s("fifo_read")

        # Update Tail pointer as needed
        If(fifo_read,
            If(rd_ptr._eq(MAX_DEPTH),
               rd_ptr ** 0
            ).Else(
               rd_ptr ** (rd_ptr + 1)
            )
        )

        # Increment Head pointer as needed
        If(fifo_write,
            If(wr_ptr._eq(MAX_DEPTH),
                wr_ptr ** 0
            ).Else(
                wr_ptr ** (wr_ptr + 1) 
            )
        )

        If(self.clk._onRisingEdge(),
            If(fifo_write,
                # Write Data to Memory
                mem[wr_ptr] ** din.data
            )
        )

        # assert isPow2(evalParam(DEPTH).val), DEPTH

        looped = r("looped", defVal=False)

        fifo_read ** (dout.en & (looped | (wr_ptr != rd_ptr)))
        If(self.clk._onRisingEdge(),
            If(fifo_read,
                # Update data output
                dout.data ** mem[rd_ptr]
            )
        )

        fifo_write ** (din.en & (~looped | (wr_ptr != rd_ptr)))

        # looped logic
        If(din.en & wr_ptr._eq(MAX_DEPTH),
            looped ** True
        ).Elif(dout.en & rd_ptr._eq(MAX_DEPTH),
            looped ** False
        )

        # Update Empty and Full flags
        If(wr_ptr._eq(rd_ptr),
            If(looped,
                din.wait ** 1,
                dout.wait ** 0 
            ).Else(
                dout.wait ** 1,
                din.wait ** 0
            )
        ).Else(
            din.wait ** 0,
            dout.wait ** 0 
        )
        if evalParam(self.EXPORT_SIZE).val:
            size = r("size_reg", self.size._dtype, 0)
            If(fifo_read,
                If(~fifo_write,
                   size ** (size - 1)
                )
            ).Else(
                If(fifo_write,
                   size ** (size + 1)
                )
            )
            self.size ** size
        if evalParam(self.EXPORT_SPACE).val:
            space = r("space_reg", self.size._dtype, self.DEPTH)
            If(fifo_read,
                If(~fifo_write,
                   size ** (space + 1)
                )
            ).Else(
                If(fifo_write,
                   size ** (space - 1)
                )
            )
            self.space ** space

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Fifo()
    u.DATA_WIDTH.set(8)
    # u.EXPORT_SIZE.set(True)
    u.DEPTH.set(16)
    print(toRtl(u))

