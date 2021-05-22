#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import FifoWriter, FifoReader, VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class FifoCopy(Fifo):
    """
    :see: :class:`hwtLib.mem.fifo`

    Fifo with an extra signals to control replay of lastly stored data

    :ivar dataOut_copy_frame: The channel which drives when to capture start of the frame
        and when to start relaying previously stored frame from the marked start

    .. hwt-autodoc:: _example_FifoCopy
    """

    def _declr(self):
        assert int(self.DEPTH) > 0, \
            "Fifo is disabled in this case, do not use it entirely"
        assert int(self.DEPTH) > 1, \
            "Use register instead"

        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = FifoWriter()
            self.dataOut = FifoReader()._m()
        fc = self.dataOut_copy_frame = VldSynced()
        fc.DATA_WIDTH = 1

        self._declr_size_and_space()

        if self.EXPORT_SIZE or self.EXPORT_SPACE:
            raise NotImplementedError()

    def _impl(self):
        DEPTH = self.DEPTH

        index_t = Bits(log2ceil(DEPTH), signed=False)
        s = self._sig
        r = self._reg

        mem = self.mem = s("memory", Bits(self.DATA_WIDTH)[self.DEPTH + 1])
        # write pointer which is seen by reader
        wr_ptr = r("wr_ptr", index_t, 0)
        # read pointer which is used by reader and can be potentially
        # reseted to a rd_ptr value (copy command) or can update rd_ptr (non-copy command)
        rd_ptr_tmp = r("rd_ptr_tmp", index_t, 0)
        rd_ptr = r("rd_ptr", index_t, 0)
        MAX_DEPTH = DEPTH - 1
        assert MAX_DEPTH.bit_length() == index_t.bit_length(), (MAX_DEPTH, index_t)

        dout = self.dataOut
        din = self.dataIn

        fifo_write = s("fifo_write")
        fifo_read = s("fifo_read")
        frame_copy = self.dataOut_copy_frame

        # Update Tail pointer as needed
        If(fifo_read,
            If(frame_copy.vld & frame_copy.data,
                If(rd_ptr._eq(MAX_DEPTH),
                    rd_ptr_tmp(0)
                ).Else(
                    rd_ptr_tmp(rd_ptr + 1)
                )
            ).Elif(rd_ptr_tmp._eq(MAX_DEPTH),
                rd_ptr_tmp(0)
            ).Else(
                rd_ptr_tmp(rd_ptr_tmp + 1)
            ),
        )
        If(frame_copy.vld & ~frame_copy.data,
            # jump to next frame
            rd_ptr(rd_ptr_tmp)
            # If(rd_ptr_tmp._eq(MAX_DEPTH),
            #    rd_ptr(0)
            # ).Else(
            #    rd_ptr(rd_ptr_tmp + 1)
            # )
        )

        wr_ptr_next = self._sig("wr_ptr_next", index_t)
        If(wr_ptr._eq(MAX_DEPTH),
            wr_ptr_next(0)
        ).Else(
            wr_ptr_next(wr_ptr + 1)
        )
        # Increment Head pointer as needed
        If(fifo_write,
            wr_ptr(wr_ptr_next)
        )

        If(self.clk._onRisingEdge(),
            If(fifo_write,
                # Write Data to Memory
                mem[wr_ptr](din.data)
            )
        )

        fifo_read(dout.en & (
            (wr_ptr != rd_ptr_tmp) |
            (frame_copy.vld & frame_copy.data))
        )
        read_addr_tmp = rename_signal(self, (frame_copy.vld & frame_copy.data)._ternary(rd_ptr, rd_ptr_tmp), "read_addr_tmp")
        If(self.clk._onRisingEdge(),
            If(fifo_read,
                # Update data output
                dout.data(mem[read_addr_tmp])
            )
        )

        fifo_write(din.en & (wr_ptr_next != rd_ptr))

        # Update Empty and Full flags
        din.wait(wr_ptr_next._eq(rd_ptr))
        If(frame_copy.vld & frame_copy.data,
            dout.wait(0)
        ).Else(
            dout.wait((wr_ptr._eq(rd_ptr_tmp)))
        )


def _example_FifoCopy():
    u = FifoCopy()
    u.DATA_WIDTH = 8
    # u.EXPORT_SIZE = True
    # u.EXPORT_SPACE = True
    u.DEPTH = 16
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_FifoCopy()
    print(to_rtl_str(u))
