#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwtLib.clocking.clkBuilder import ClkBuilder
from hwtLib.handshaked.hwIOBiDirectional import HwIORdVldSyncBiDirectionalData, \
    HwIORdVldSyncBiDirectionalDataAgent
from hwtLib.logic.binToOneHot import BinToOneHot
from hwtLib.peripheral.spi.intf import Spi
from hwtSimApi.hdlSimulator import HdlSimulator


class SpiCntrlDataAgent(HwIORdVldSyncBiDirectionalDataAgent):
    def get_data(self):
        """extract data from interface"""
        hwIO = self.hwIO

        return hwIO.slave.read(), hwIO.dout.read(), hwIO.last.read()

    def set_data(self, data):
        """write data to interface"""
        hwIO = self.hwIO
        if data is None:
            slave, d, last = None, None, None
        else:
            slave, d, last = data
        hwIO.slave.write(slave)
        hwIO.dout.write(d)
        hwIO.last.write(last)


class SpiCntrlData(HwIORdVldSyncBiDirectionalData):
    """
    HwIORdVldSyncBiDirectionalData interface with last and slave signal added.
    If last=1 slave will be deselected and initial slave select wait will be.
    Slave selects the slave where data should be read from and written to.

    .. hwt-autodoc::
    """

    def _declr(self):
        self.slave = HwIOVectSignal(1)
        HwIORdVldSyncBiDirectionalData._declr(self)
        self.last = HwIOSignal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = SpiCntrlDataAgent(sim, self)


class SpiMaster(HwModule):
    """
    Master for SPI interface

    :ivar ~.SPI_FREQ_PESCALER: frequency prescaler to get SPI clk from main clk (HwParam)
    :ivar ~.SS_WAIT_CLK_TICKS: number of SPI ticks to wait with SPI clk activation after slave select
    :ivar ~.HAS_TX: if set true write part will be instantiated
    :ivar ~.HAS_RX: if set true read part will be instantiated

    :attention: this implementation expects that slaves are reading data on rising edge of SPI clk
        and data from slaves are ready on risign edge as well
        and SPI clk is kept high in idle
        (most of them does but there are some exceptions)

    .. hwt-autodoc::
    """
    def _config(self):
        self.SPI_FREQ_PESCALER = HwParam(32)
        self.SS_WAIT_CLK_TICKS = HwParam(4)
        self.HAS_TX = HwParam(True)
        self.HAS_RX = HwParam(True)
        self.SPI_DATA_WIDTH = HwParam(1)
        Spi._config(self)

    def _declr(self):
        addClkRstn(self)

        self.spi = Spi()._m()
        assert self.HAS_RX or self.HAS_TX

        with self._hwParamsShared():
            self.DATA_WIDTH = int(self.SPI_DATA_WIDTH) * 8
            self.data = SpiCntrlData()
            self.data.DATA_WIDTH = self.DATA_WIDTH

        self.csDecoder = BinToOneHot()
        self.csDecoder.DATA_WIDTH = self.SLAVE_CNT

    def writePart(self, writeTick, isLastTick, data):
        txReg = self._reg("txReg", HBits(self.DATA_WIDTH))
        txInitialized = self._reg("txInitialized", def_val=0)
        If(writeTick,
            If(txInitialized,
                txReg(txReg << 1),
                If(isLastTick,
                   txInitialized(0),
                )
            ).Else(
               txInitialized(1),
               txReg(data)
            )
        ).Elif(isLastTick,
            txInitialized(0)
        )
        self.spi.mosi(txReg[self.DATA_WIDTH - 1])

    def readPart(self, readTick):
        rxReg = self._reg("rxReg", HBits(self.DATA_WIDTH))

        If(readTick,
           rxReg(Concat(rxReg[(self.DATA_WIDTH - 1):], self.spi.miso))
        )
        return rxReg

    def spiClkGen(self, requiresInitWait, en):
        """
        create clock generator for SPI
        writeTick is 1 on falling edge of spi clk
        readTick is 1 on rising edge of spi clk

        :return: tuple of tick signals (if data should be send, if data should be read)
        """
        builder = ClkBuilder(self, self.clk)
        timersRst = self._sig("timersRst")

        PESCALER = self.SPI_FREQ_PESCALER
        SPI_HALF_PERIOD = PESCALER // 2
        spiClkHalfTick, initWaitDone, endOfWord = builder.timers(
            [("spiClkHalfTick", SPI_HALF_PERIOD),
             ("initWait", SPI_HALF_PERIOD * self.SS_WAIT_CLK_TICKS * 2),
             ("endOfWord", SPI_HALF_PERIOD * 8 * 2)
            ],
            enableSig=en,
            rstSig=timersRst)

        timersRst(~en | (requiresInitWait & initWaitDone))

        clkIntern = self._reg("clkIntern", def_val=1)
        clkOut = self._reg("clkOut", def_val=1)
        If(spiClkHalfTick,
           clkIntern(~clkIntern)
        )

        If(~requiresInitWait & spiClkHalfTick,
           clkOut(~clkOut)
        )

        self.spi.clk(clkOut)  # clk idle value is high

        clkRisign, clkFalling = builder.edgeDetector(clkIntern.next,
                                                     rise=True,
                                                     fall=True,
                                                     initVal=1)

        rdEn = clkRisign & ~requiresInitWait
        wrEn = clkFalling & ~requiresInitWait

        return (wrEn, rdEn, initWaitDone, endOfWord)

    def _impl(self):
        d = self.data
        slaveSelectWaitRequired = self._reg("slaveSelectWaitRequired", def_val=1)
        endOfWordDelayed = self._reg("endOfWordDelayed", def_val=0)
        (writeTick, readTick,
         initWaitDone, endOfWord) = self.spiClkGen(
              slaveSelectWaitRequired,
              ~ endOfWordDelayed & self.data.vld)

        endOfWordDelayed(endOfWord)

        if self.HAS_RX:
            d.din(self.readPart(readTick))
        else:
            d.din(None)

        if self.HAS_TX:
            self.writePart(writeTick, endOfWordDelayed, d.dout)

        If(endOfWord,
           slaveSelectWaitRequired(d.last)
        ).Elif(initWaitDone,
           slaveSelectWaitRequired(0)
        )

        csD = self.csDecoder
        csD.din(d.slave)
        csD.en(d.vld)

        self.spi.cs(~csD.dout)
        d.rd(endOfWordDelayed)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = SpiMaster()
    print(to_rtl_str(m))
