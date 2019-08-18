from collections import deque

from hwt.bitmask import selectBit, mask
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import Clk, Signal, VectSignal
from hwt.interfaces.tristate import TristateSig
from hwt.simulator.agentBase import SyncAgentBase, AgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from pycocotb.process_utils import OnRisingCallbackLoop, OnFallingCallbackLoop
from hwt.hdl.types.bits import Bits


class SpiAgent(SyncAgentBase):
    """
    Simulation agent for SPI interface

    :ivar txData: data to transceiver container
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
        self._discoverReset(allowNoReset=allowNoReset)

        # read on rising edge write on falling
        self.monitorRx = OnRisingCallbackLoop(self.clk,
                                              self.monitorRx,
                                              self.getEnable)
        self.monitorTx = OnFallingCallbackLoop(self.clk,
                                               self.monitorTx,
                                               self.getEnable)

        self.driverRx = OnFallingCallbackLoop(self.clk,
                                              self.driverRx,
                                              self.getEnable)
        self.driverTx = OnRisingCallbackLoop(self.clk,
                                             self.driverTx,
                                             self.getEnable)

    def setEnable(self, en):
        self._enabled = en
        self.monitorRx.setEnable(en)
        self.monitorTx.setEnable(en)
        self.driverRx.setEnable(en)
        self.driverTx.setEnable(en)

    def splitBits(self, v):
        return deque([selectBit(v, i) for i in range(self.BITS_IN_WORD - 1, -1, -1)])

    def mergeBits(self, bits):
        t = Bits(self.BITS_IN_WORD, False)
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
        d = sig.read()
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

        sig.write(bits.popleft())

    def monitorRx(self, sim):
        yield sim.waitReadOnly()
        cs = sim.read(self.intf.cs)
        cs = int(cs)
        if self.notReset(sim):
            if cs != self.csMask:  # if any slave is enabled
                self.readRxSig(sim, self.intf.mosi)
                if not self._rxBitBuff:
                    self.chipSelects.append(cs)

    def monitorTx(self, sim):
        yield sim.waitReadOnly()
        cs = self.intf.cs.read()
        cs = int(cs)
        if self.notReset(sim):
            if cs != self.csMask:
                yield sim.waitWriteOnly()
                self.writeTxSig(sim, self.intf.miso)

    def driverRx(self, sim):
        yield sim.waitReadOnly()
        if self.notReset(sim) and self.slaveEn:
            self.readRxSig(sim, self.intf.miso)

    def driverTx(self, sim):
        yield sim.waitReadOnly()
        if self.notReset(sim):
            if not self._txBitBuff:
                try:
                    cs = self.chipSelects.popleft()
                except IndexError:
                    self.slaveEn = False
                    yield sim.waitWriteOnly()
                    self.intf.cs.write(self.csMask)
                    return

                self.slaveEn = True
                yield sim.waitWriteOnly()
                self.intf.cs.write(cs)

            yield sim.waitWriteOnly()
            self.writeTxSig(sim, self.intf.mosi)

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

    def _initSimAgent(self):
        self._ag = SpiAgent(self)


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
