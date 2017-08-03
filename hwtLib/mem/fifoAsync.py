#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Clk, Rst_n, FifoWriter, FifoReader
from hwtLib.logic.cntrGray import GrayCntr
from hwtLib.mem.fifo import Fifo
from hwt.serializer.mode import serializeParamsUniq


@serializeParamsUniq
class FifoAsync(Fifo):
    """
    Asynchronous fifo using BRAM memory based on:
    http://www.asic-world.com/examples/vhdl/asyn_fifo.html

    """

    def _declr(self):
        assert int(self.DEPTH) > 0,  "FifoAsync is disabled in this case, do not use it entirely"
        if int(self.EXPORT_SIZE) or int(self.EXPORT_SPACE):
            raise NotImplementedError()

        self.dataIn_clk = Clk() 
        self.dataOut_clk = Clk()
        self.rst_n = Rst_n()

        with self._paramsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn = FifoWriter()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut = FifoReader()

        self.pWr = GrayCntr()
        self.pRd = GrayCntr()
        self.addrW = log2ceil(self.DEPTH)

        for cntr in [self.pWr, self.pRd]:
            cntr.DATA_WIDTH.set(self.addrW)

    def _impl(self):
        memory_t = vecT(self.DATA_WIDTH)[self.DEPTH]
        memory = self._sig("memory", memory_t)
        full = self._sig("full")
        empty = self._sig("empty")
        status = self._sig("status")

        In = self.dataIn
        InClk = self.dataIn_clk._onRisingEdge()
        Out = self.dataOut
        OutClk = self.dataOut_clk._onRisingEdge()

        self.pWr.en ** (In.en & ~full)
        self.pWr.clk ** self.dataIn_clk
        self.pWr.rst_n ** self.rst_n
        pNextWordToWrite = self.pWr.dataOut

        self.pRd.en ** (Out.en & ~empty)
        self.pRd.clk ** self.dataOut_clk 
        self.pRd.rst_n ** self.rst_n
        pNextWordToRead = self.pRd.dataOut

        # data out logic
        If(OutClk,
            If(Out.en & ~empty,
               Out.data ** memory[pNextWordToRead] 
            )
        )

        # data in logic
        If(InClk,
            If(In.en & ~full,
               memory[pNextWordToWrite] ** In.data 
            )
        )

        equalAddresses = pNextWordToWrite._eq(pNextWordToRead)

        aw = self.addrW
        nw = pNextWordToWrite
        nr = pNextWordToRead
        setStatus = nw[aw - 2]._eq(nr[aw - 1]) & (nw[aw - 1] ^ nr[aw - 2])
        rstStatus = (nw[aw - 2] ^ nr[aw - 1]) & nw[aw - 1]._eq(nr[aw - 2])

        # status ltching
        If(rstStatus | self.rst_n._isOn(),
            status ** 0  # Going 'Empty'.
        ).Elif(setStatus,
            status ** 1  # Going 'Full'
        )

        # data in logic
        presetFull = status & equalAddresses

        # D Flip-Flop w/ Asynchronous Preset.
        If(presetFull,
            full ** 1
        ).Else(
            If(InClk,
               full ** 0 
            )
        )
        In.wait ** full 

        # data out logic
        presetEmpty = ~status & equalAddresses

        # D Flip-Flop w/ Asynchronous Preset.
        If(presetEmpty,
            empty ** 1
        ).Else(
            If(OutClk,
               empty ** 0 
            )
        )
        Out.wait ** empty

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = FifoAsync()
    u.DEPTH.set(4)
    print(toRtl(u))
