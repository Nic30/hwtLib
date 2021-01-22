#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, List

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import FifoWriter, FifoReader, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit


# https://eewiki.net/pages/viewpage.action?pageId=20939499
@serializeParamsUniq
class Fifo(Unit):
    """
    Generic FIFO usually mapped to BRAM.

    :ivar ~.EXPORT_SIZE: parameter, if true "size" signal will be exported
    :ivar ~.size: optional signal with count of items stored in this fifo
    :ivar ~.EXPORT_SPACE: parameter, if true "space" signal is exported
    :ivar ~.space: optional signal with count of items which can be added to this fifo

    .. hwt-autodoc:: _example_Fifo
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DEPTH = Param(0)
        self.EXPORT_SIZE = Param(False)
        self.EXPORT_SPACE = Param(False)

    def _declr_size_and_space(self):
        if self.EXPORT_SIZE:
            self.size = VectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()
        if self.EXPORT_SPACE:
            self.space = VectSignal(log2ceil(self.DEPTH + 1), signed=False)._m()

    def _declr(self):
        assert self.DEPTH > 0,\
            "Fifo is disabled in this case, do not use it entirely"

        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = FifoWriter()
            self.dataOut = FifoReader()._m()
        self._declr_size_and_space()

    def fifo_pointers(self, DEPTH: int,
                      write_en_wait: Tuple[RtlSignal, RtlSignal],
                      read_en_wait_list: List[Tuple[RtlSignal, RtlSignal]])\
                      -> List[Tuple[RtlSignal, RtlSignal]]:
        """
        Create fifo writer and reader pointers and enable/wait logic
        This functions supports multiple reader pointers

        :attention: writer pointer next logic check only last reader pointer
        :return: list, tule(en, ptr) for writer and each reader
        """
        index_t = Bits(log2ceil(DEPTH), signed=False)
        # assert isPow2(DEPTH), DEPTH
        MAX_DEPTH = DEPTH - 1
        s = self._sig
        r = self._reg
        fifo_write = s("fifo_write")
        write_ptr = _write_ptr = r("write_ptr", index_t, 0)
        ack_ptr_list = [(fifo_write, write_ptr), ]
        # update writer (head) pointer as needed
        If(fifo_write,
            If(write_ptr._eq(MAX_DEPTH),
                write_ptr(0)
            ).Else(
                write_ptr(write_ptr + 1)
            )
        )

        write_en, _ = write_en_wait
        # instantiate all read pointers
        for i, (read_en, read_wait) in enumerate(read_en_wait_list):
            read_ptr = r(f"read_ptr{i:d}", index_t, 0)
            fifo_read = s(f"fifo_read{i:d}")
            ack_ptr_list.append((fifo_read, read_ptr))
            # update reader (tail) pointer as needed
            If(fifo_read,
                If(read_ptr._eq(MAX_DEPTH),
                    read_ptr(0)
                ).Else(
                    read_ptr(read_ptr + 1)
                )
            )

            looped = r(f"looped{i:d}", def_val=False)
            # looped logic
            If(write_en & write_ptr._eq(MAX_DEPTH),
                looped(True)
            ).Elif(read_en & read_ptr._eq(MAX_DEPTH),
                looped(False)
            )

            # Update Empty and Full flags
            read_wait(write_ptr._eq(read_ptr) & ~looped)
            fifo_read(read_en & (looped | (write_ptr != read_ptr)))
            # previous reader is next port writer (producer) as it next reader can continue only if previous reader did consume the item
            write_en, _ = read_en, read_wait
            write_ptr = read_ptr

        write_en, write_wait = write_en_wait
        write_ptr = _write_ptr
        # Update Empty and Full flags
        write_wait(write_ptr._eq(read_ptr) & looped)
        fifo_write(write_en & (~looped | (write_ptr != read_ptr)))

        return ack_ptr_list

    def _impl(self):
        DEPTH = self.DEPTH

        dout = self.dataOut
        din = self.dataIn

        s = self._sig
        r = self._reg
        ((fifo_write, wr_ptr), (fifo_read, rd_ptr), ) = self.fifo_pointers(
            DEPTH, (din.en, din.wait), [(dout.en, dout.wait), ])

        if self.DATA_WIDTH:
            mem = self.mem = s("memory", Bits(self.DATA_WIDTH)[DEPTH])
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
            space = r("space_reg", self.space._dtype, DEPTH)
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


def _example_Fifo():
    u = Fifo()
    u.DATA_WIDTH = 8
    # u.EXPORT_SIZE = True
    u.DEPTH = 16
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_Fifo()
    print(to_rtl_str(u))
