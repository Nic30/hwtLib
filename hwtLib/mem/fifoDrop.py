#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.agents.fifo import HwIOFifoWriterAgent
from hwt.hwIOs.std import HwIOFifoWriter, HwIOFifoReader, HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.mem.fifo import Fifo
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.intfIpMeta import IntfIpMetaNotSpecifiedError


class FifoWriterDropable(HwIOFifoWriter):
    """
    FIFO write port interface witch commit and discard signal
    used to drop data chunks already written in FIFO

    :note: commit and discard behaves as another data signal
        it is valid if en=1
    :note: only one from "commit", "discard" can be 1 at the same time
    :ivar ~.commit: if 1 all the written data are made available to reader,
        including current data word
    :ivar ~.discard: if 1 all written data which were not commited are discarded
        including current data word

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        super(FifoWriterDropable, self).hwDeclr()
        self.commit = HwIOSignal()
        self.discard = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = FifoWriterDropableAgent(sim, self)

    @override
    def _getIpCoreIntfClass(self):
        raise IntfIpMetaNotSpecifiedError()


class FifoWriterDropableAgent(HwIOFifoWriterAgent):

    @override
    def set_data(self, d):
        i = self.hwIO
        if d is None:
            commit, discard = (None, None)
        else:
            d, commit, discard = d
        i.commit.write(commit)
        i.discard.write(discard)
        i.data.write(d)

    @override
    def get_data(self):
        i = self.hwIO
        return (
            i.commit.read(),
            i.discard.read(),
            i.data.read(),
        )


@serializeParamsUniq
class FifoDrop(Fifo):
    """
    :see: :class:`hwtLib.mem.fifo`

    Fifo with an extra signals for writter which allows to commit
    or discard data chung writen in to fifo.

    :attention: the commit/drop logic is executed on write
        but also during dataIn.wait=1 this allows for droping
        if FIFO is full of uncommited data

    .. hwt-autodoc:: _example_FifoDrop
    """

    @override
    def hwDeclr(self):
        assert int(self.DEPTH) > 0,\
            "Fifo is disabled in this case, do not use it entirely"
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = FifoWriterDropable()
            self.dataOut = HwIOFifoReader()._m()

        self._declr_size_and_space()

    @override
    def hwImpl(self):
        DEPTH = self.DEPTH

        index_t = HBits(log2ceil(DEPTH), signed=False)
        s = self._sig
        r = self._reg

        mem = self.mem = s("memory", HBits(self.DATA_WIDTH)[self.DEPTH])
        # write pointer which is seen by reader
        wr_ptr = r("wr_ptr", index_t, 0)
        # write pointer which is used by writer and can be potentially
        # reseted to a wr_ptr value or can update wr_ptr
        wr_ptr_tmp = r("wr_ptr_tmp", index_t, 0)
        rd_ptr = r("rd_ptr", index_t, 0)
        MAX_DEPTH = DEPTH - 1

        dout = self.dataOut
        din = self.dataIn

        fifo_write = s("fifo_write")
        fifo_read = s("fifo_read")

        # Update Tail pointer as needed
        If(fifo_read,
            If(rd_ptr._eq(MAX_DEPTH),
               rd_ptr(0)
            ).Else(
                rd_ptr(rd_ptr + 1)
            )
        )

        # Increment Head pointer as needed
        If(din.discard,
            wr_ptr_tmp(wr_ptr),
        ).Elif(fifo_write,
            If(wr_ptr_tmp._eq(MAX_DEPTH),
                wr_ptr_tmp(0)
            ).Else(
                wr_ptr_tmp(wr_ptr_tmp + 1)
            ),
            If(din.commit,
               wr_ptr(wr_ptr_tmp._rtlNextSig)
            )
        )

        If(self.clk._onRisingEdge(),
            If(fifo_write,
                # Write Data to Memory
                mem[wr_ptr_tmp](din.data)
            )
        )

        # assert isPow2(int(DEPTH)), DEPTH

        looped = r("looped", def_val=False)
        # same thing for looped as wr_ptr_tmp for wr_ptr
        looped_tmp = r("looped_tmp", def_val=False)

        fifo_read(dout.en & (looped | (wr_ptr != rd_ptr)))
        If(self.clk._onRisingEdge(),
            If(fifo_read,
                # Update data output
                dout.data(mem[rd_ptr])
            )
        )

        fifo_write(din.en & (~looped_tmp | (wr_ptr_tmp != rd_ptr)))

        # looped logic
        If(din.en & din.commit,
            looped(looped_tmp._rtlNextSig)
        ).Elif(dout.en & rd_ptr._eq(MAX_DEPTH),
            looped(False)
        )
        If(din.discard,
            looped_tmp(looped)
        ).Elif(din.en & wr_ptr_tmp._eq(MAX_DEPTH),
            looped_tmp(True)
        ).Elif(dout.en & rd_ptr._eq(MAX_DEPTH),
            looped_tmp(False)
        )

        # Update Empty and Full flags
        If(wr_ptr_tmp._eq(rd_ptr),
            If(looped_tmp,
                din.wait(1),
            ).Else(
                din.wait(0)
            )
        ).Else(
            din.wait(0),
        )
        If(wr_ptr._eq(rd_ptr),
            If(looped,
                dout.wait(0)
            ).Else(
                dout.wait(1),
            )
        ).Else(
            dout.wait(0)
        )
        if self.EXPORT_SIZE or self.EXPORT_SPACE:
            stash_size = r("stash_size_reg", self.size._dtype, 0)
            If(din.discard,
                stash_size(0)
            ).Elif(fifo_write,
                If(din.commit,
                   stash_size(0)
                ).Else(
                   stash_size(stash_size + 1)
                )
            )

        if self.EXPORT_SIZE:
            size = r("size_reg", self.size._dtype, 0)
            If(fifo_read,
                If(fifo_write & din.commit,
                   size(size + stash_size)
                ).Else(
                   size(size - 1)
                )
            ).Else(
                If(fifo_write & din.commit,
                   size(size + stash_size + 1)
                )
            )
            self.size(size + stash_size)

        if self.EXPORT_SPACE:
            space = r("space_reg", self.space._dtype, DEPTH)
            If(fifo_read,
                If(din.discard,
                   space(space - stash_size)
                ).Elif(fifo_write,
                   space(space - 1)
                ).Else(
                   space(space + 1)
                )
            ).Else(
                If(din.discard,
                   space(space - stash_size)
                )
            )
            self.space(space)


def _example_FifoDrop():
    m = FifoDrop()
    m.DATA_WIDTH = 8
    m.EXPORT_SIZE = True
    m.EXPORT_SPACE = True
    m.DEPTH = 16
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_FifoDrop()
    print(to_rtl_str(m))
