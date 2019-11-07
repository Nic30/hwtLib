from collections import deque

from hwt.hdl.constants import DIRECTION
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Clk, Signal, VectSignal
from hwt.interfaces.tristate import TristateSig
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from pyMathBitPrecise.bit_utils import mask, selectBit
from pycocotb.agents.base import AgentBase
from pycocotb.hdlSimulator import HdlSimulator
from pycocotb.process_utils import OnRisingCallbackLoop, OnFallingCallbackLoop
from pycocotb.triggers import WaitCombRead, WaitWriteOnly, Timer
from pycocotb.constants import Time


class SpiAgent(SyncAgentBase):
    """
    Simulation agent for SPI interface

    :ivar txData: data to transceiver container
    :ivar rxData: received data
    :ivar chipSelects: values of chip select

    chipSelects, rxData and txData are lists of integers
    """
    BITS_IN_WORD = 8

    def __init__(self, sim: HdlSimulator, intf: "Spi", allowNoReset=False):
        AgentBase.__init__(self, sim, intf)

        self.txData = deque()
        self.rxData = deque()
        self.chipSelects = deque()

        self._txBitBuff = deque()
        self._rxBitBuff = deque()
        self.csMask = mask(intf.cs._dtype.bit_length())
        self.slaveEn = False

        # resolve clk and rstn
        self.clk = self.intf._getAssociatedClk()._sigInside
        self.rst, self.rstOffIn = self._discoverReset(intf, allowNoReset=allowNoReset)

        # read on rising edge write on falling
        self.monitorRx = OnRisingCallbackLoop(self.sim, self.clk,
                                              self.monitorRx,
                                              self.getEnable)
        self.monitorTx = OnFallingCallbackLoop(self.sim, self.clk,
                                               self.monitorTx,
                                               self.getEnable)

        self.driverRx = OnFallingCallbackLoop(self.sim, self.clk,
                                              self.driverRx,
                                              self.getEnable)
        self.driverTx = OnRisingCallbackLoop(self.sim, self.clk,
                                             self.driverTx,
                                             self.getEnable)

    def setEnable(self, en):
        self._enabled = en
        self.monitorRx.setEnable(en)
        self.monitorTx.setEnable(en)
        self.driverRx.setEnable(en)
        self.driverTx.setEnable(en)

    def splitBits(self, v):
        return deque([selectBit(v, i)
                      for i in range(self.BITS_IN_WORD - 1, -1, -1)])

    def mergeBits(self, bits):
        t = Bits(self.BITS_IN_WORD, False)
        val = 0
        vld_mask = 0
        for v in bits:
            val <<= 1
            val |= v.val
            vld_mask <<= 1
            vld_mask |= v.vld_mask

        return t.getValueCls()(t, val, vld_mask)

    def readRxSig(self, sig):
        d = sig.read()
        bits = self._rxBitBuff
        bits.append(d)
        if len(bits) == self.BITS_IN_WORD:
            self.rxData.append(self.mergeBits(bits))
            self._rxBitBuff = []

    def writeTxSig(self, sig):
        bits = self._txBitBuff
        if not bits:
            if not self.txData:
                return
            d = self.txData.popleft()
            bits = self._txBitBuff = self.splitBits(d)

        sig.write(bits.popleft())

    def monitorRx(self):
        yield WaitCombRead()
        if self.notReset():
            cs = self.intf.cs.read()
            cs = int(cs)
            if cs != self.csMask:  # if any slave is enabled
                if not self._rxBitBuff:
                    self.chipSelects.append(cs)
                self.readRxSig(self.intf.mosi)

    # def monitorTx_pre_set(self):
    #     yield WaitWriteOnly()
    #     self.writeTxSig(self.intf.miso)

    def monitorTx(self):
        yield WaitCombRead()
        if self.notReset():
            cs = self.intf.cs.read()
            cs = int(cs)
            if cs != self.csMask:
                yield Timer(1)
                yield WaitWriteOnly()
                self.writeTxSig(self.intf.miso)

    def driverRx(self):
        yield WaitCombRead()
        if self.notReset() and self.slaveEn:
            self.readRxSig(self.intf.miso)

    def driverTx(self):
        yield WaitCombRead()
        if self.notReset():
            if not self._txBitBuff:
                try:
                    cs = self.chipSelects.popleft()
                except IndexError:
                    self.slaveEn = False
                    yield WaitWriteOnly()
                    self.intf.cs.write(self.csMask)
                    return

                self.slaveEn = True
                yield WaitWriteOnly()
                self.intf.cs.write(cs)

            yield WaitWriteOnly()
            self.writeTxSig(self.intf.mosi)

    def getDrivers(self):
        return [self.driverRx(), self.driverTx()]

    def getMonitors(self):
        return [self.monitorRx(),
                #self.monitorTx_pre_set(),
                self.monitorTx()]


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

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = SpiAgent(sim, self)


class SpiTristate(Spi):
    """
    SPI interface where mosi and miso signal are merged into one tri-state wire
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
