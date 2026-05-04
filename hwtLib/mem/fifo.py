#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.constants import NOT_SPECIFIED
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsRtlSignal import HBitsRtlSignal
from hwt.hwIOs.std import HwIOFifoWriter, HwIOFifoReader, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.mem.fifoPtrLogic import FifoPtrLogic


@serializeParamsUniq
class Fifo(HwModule):
    """
    Generic FIFO usually mapped to BRAM.
    :note: 1clk to write, 1clk to read 

    :ivar ~.EXPORT_SIZE: parameter, if true "size" signal will be exported
    :ivar ~.size: optional signal with count of items stored in this fifo
    :ivar ~.EXPORT_SPACE: parameter, if true "space" signal is exported
    :ivar ~.space: optional signal with count of items which can be added to this fifo

    .. hwt-autodoc:: _example_Fifo
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.DEPTH = HwParam(0)
        self.EXPORT_SIZE = HwParam(False)
        self.EXPORT_SPACE = HwParam(False)
        self.INIT_DATA: tuple = HwParam(())
        self.INIT_DATA_FIRST_WORD = HwParam(NOT_SPECIFIED)

    def _declr_size_and_space(self):
        if self.EXPORT_SIZE:
            self.size = HwIOVectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()
        if self.EXPORT_SPACE:
            self.space = HwIOVectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()

    @override
    def hwDeclr(self):
        assert self.DEPTH > 0, \
            "Fifo is disabled in this case, do not use it entirely"
        assert self.DEPTH > 1, \
            "Fifo DEPTH must be >1 in order to fifo pointers to work correctly"

        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = HwIOFifoWriter()
            self.dataOut = HwIOFifoReader()._m()
        self._declr_size_and_space()

    def constructFifoSizeLogic(self, fifo_read: HBitsRtlSignal, fifo_write: HBitsRtlSignal):
        size = self._reg("size_reg", self.size._dtype, len(self.INIT_DATA))
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

    def constructFifoSpaceLogic(self, fifo_read: HBitsRtlSignal, fifo_write: HBitsRtlSignal):
        space = self._reg("space_reg", self.space._dtype, self.DEPTH - len(self.INIT_DATA))
        If(fifo_read,
            If(~fifo_write,
               space(space + 1)
            )
        ).Else(
            If(fifo_write,
               space(space - 1)
            )
        )
        self.space(space)

    @override
    def hwImpl(self):
        DEPTH = self.DEPTH

        dout = self.dataOut
        din = self.dataIn

        s = self._sig
        fifoPtrs = FifoPtrLogic(self, DEPTH, INIT_SIZE=len(self.INIT_DATA))
        ((fifo_write, wr_ptr), (fifo_read, rd_ptr),) = fifoPtrs.fifo_pointers(
            (din.en, din.wait), [(dout.en, dout.wait), ])

        init_data = self.INIT_DATA
        if not init_data:
            init_data_expanded = None
        else:
            init_data_expanded = list(init_data) + [None for _ in range(self.DEPTH - len(init_data))]

        if self.DATA_WIDTH:
            mem = self.mem = s("memory", HBits(self.DATA_WIDTH)[DEPTH], def_val=init_data_expanded)
            If(self.clk._onRisingEdge(),
                If(fifo_write,
                    # Write Data to Memory
                    mem[wr_ptr](din.data)
                )
            )

            If(self.clk._onRisingEdge(),
                If(fifo_read,
                    # Update data output
                    dout.data(mem[rd_ptr])
                )

                if self.INIT_DATA_FIRST_WORD == NOT_SPECIFIED else

                If(self.rst_n._isOn(),
                   dout.data(self.INIT_DATA_FIRST_WORD),
                ).Elif(fifo_read,
                    # Update data output
                    dout.data(mem[rd_ptr])
                )
            )

        if self.EXPORT_SIZE:
            self.constructFifoSizeLogic(fifo_read, fifo_write)

        if self.EXPORT_SPACE:
            self.constructFifoSpaceLogic(fifo_read, fifo_write)


def _example_Fifo():
    m = Fifo()
    m.DATA_WIDTH = 8
    m.EXPORT_SIZE = True
    m.EXPORT_SPACE = True
    m.INIT_DATA = (1, 2, 3)
    m.INIT_DATA_FIRST_WORD = 0
    m.DEPTH = 16

    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_Fifo()
    print(to_rtl_str(m))
