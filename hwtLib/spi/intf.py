from hwt.bitmask import selectBit, mask
from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import Clk, Signal, VectSignal, Rst_n
from hwt.interfaces.tristate import TristateSig
from hwt.simulator.agentBase import SyncAgentBase, AgentBase
from hwt.simulator.shortcuts import onRisingEdge, onFallingEdge
from hwt.simulator.types.simBits import simBitsT
from hwt.synthesizer.exceptions import IntfLvlConfErr
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from collections import deque


class SpiAgent(SyncAgentBase):
    """
    Simulation agent for SPI interface

    :ivar txData: data to transceive container
    :ivar rxData: received data
    :ivar chipSelects: values of chip select

    chipSelects, rxData and txData are lists of integers
    """
    BITS_IN_WORD = 8

    def __init__(self, intf, allowNoReset=False):
        AgentBase.__init__(self, intf)

        self.txData = deque()
        self.rxData = deque()
        self.chipSelects = deque()

        self._txBitBuff = deque()
        self._rxBitBuff = deque()
        self.csMask = mask(intf.cs._dtype.bit_length())
        self.slaveEn = False

        # resolve clk and rstn
        self.clk = self.intf._getAssociatedClk()._sigInside
        try:
            self.rst = self.intf._getAssociatedRst()
            self.rstOffIn = isinstance(self.rst, Rst_n)
            self.rst = self.rst._sigInside
        except IntfLvlConfErr as e:
            if allowNoReset:
                pass
            else:
                raise e

        # read on rising edge write on falling
        self.monitorRx = onRisingEdge(self.clk, self.monitorRx)
        self.monitorTx = onFallingEdge(self.clk, self.monitorTx)

        self.driverRx = onFallingEdge(self.clk, self.driverRx)
        self.driverTx = onRisingEdge(self.clk, self.driverTx)

    def splitBits(self, v):
        return deque([selectBit(v, i) for i in range(self.BITS_IN_WORD - 1, -1, -1)])

    def mergeBits(self, bits):
        t = simBitsT(self.BITS_IN_WORD, False)
        val = 0
        vldMask = 0
        time = -1
        for v in bits:
            val <<= 1
            val |= v.val
            vldMask <<= 1
            vldMask |= v.vldMask
            time = max(time, v.updateTime)

        return t.getValueCls()(val, t, vldMask, time)

    def readRxSig(self, sim, sig):
        d = sim.read(sig)
        bits = self._rxBitBuff
        bits.append(d)
        if len(bits) == self.BITS_IN_WORD:
            self.rxData.append(self.mergeBits(bits))
            self._rxBitBuff = []

    def writeTxSig(self, sim, sig):
        bits = self._txBitBuff
        if not bits:
            if not self.txData:
                return
            d = self.txData.popleft()
            bits = self._txBitBuff = self.splitBits(d)

        sim.write(bits.popleft(), sig)

    def monitorRx(self, s):
        yield s.updateComplete
        cs = s.read(self.intf.cs)
        if self.enable and self.notReset(s):
            assert cs._isFullVld()
            if cs.val != self.csMask:  # if any slave is enabled
                self.readRxSig(s, self.intf.mosi)
                if not self._rxBitBuff:
                    self.chipSelects.append(cs)

    def monitorTx(self, s):
        cs = s.read(self.intf.cs)
        if self.enable and self.notReset(s):
            assert cs._isFullVld()
            if cs.val != self.csMask:
                self.writeTxSig(s, self.intf.miso)

    def driverRx(self, s):
        yield s.updateComplete
        if self.enable and self.notReset(s) and self.slaveEn:
            self.readRxSig(s, self.intf.miso)

    def driverTx(self, s):
        if self.enable and self.notReset(s):
            if not self._txBitBuff:
                try:
                    cs = self.chipSelects.popleft()
                except IndexError:
                    self.slaveEn = False
                    s.write(self.csMask, self.intf.cs)
                    return

                self.slaveEn = True
                s.write(cs, self.intf.cs)

            self.writeTxSig(s, self.intf.mosi)

    def getDrivers(self):
        return [self.driverRx, self.driverTx]

    def getMonitors(self):
        return [self.monitorRx, self.monitorTx]


# http://www.corelis.com/education/SPI_Tutorial.htm
class Spi(Interface):
    """
    Bare SPI interface (Serial peripheral interface)
    """
    def _config(self):
        self.SLAVE_CNT = Param(1)

    def _declr(self):
        self.clk = Clk()
        self.mosi = Signal()  # master out slave in
        self.miso = Signal(masterDir=DIRECTION.IN)  # master in slave out
        self.cs = VectSignal(self.SLAVE_CNT)  # chip select

        self._associatedClk = self.clk

    def _getSimAgent(self):
        return SpiAgent


class SpiTristate(Spi):
    """
    SPI interface where mosi and miso signal are merged into one tristate wire
    """
    def _config(self):
        Spi._config(self)
        self.DATA_WIDTH = Param(1)

    def _declr(self):
        self.clk = Clk()
        with self._paramsShared():
            self.io = TristateSig()  # mosi and miso in one wire
        self.cs = VectSignal(self.SLAVE_CNT)  # chip select

        self._associatedClk = self.clk


class QSPI(SpiTristate):
    """
    SPI interface with 4 tristate data wires
    """
    def _config(self):
        Spi._config(self)
        self.DATA_WIDTH = Param(4)
