from collections import deque

from hwt.constants import DIRECTION
from hwt.hdl.types.bits import HBits
from hwt.hwIO import HwIO
from hwt.hwIOs.hwIOTristate import HwIOTristateSig
from hwt.hwIOs.std import HwIOClk, HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.agentBase import SyncAgentBase
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.process_utils import OnRisingCallbackLoop, OnFallingCallbackLoop
from hwtSimApi.triggers import WaitCombRead, WaitWriteOnly, Timer
from pyMathBitPrecise.bit_utils import mask, get_bit


class SpiAgent(SyncAgentBase):
    """
    Simulation agent for SPI interface

    :ivar ~.txData: data to transceiver container
    :ivar ~.rxData: received data
    :ivar ~.chipSelects: values of chip select

    chipSelects, rxData and txData are lists of integers
    """
    BITS_IN_WORD = 8

    def __init__(self, sim: HdlSimulator, hwIO: "Spi", allowNoReset=False):
        AgentBase.__init__(self, sim, hwIO)

        self.txData = deque()
        self.rxData = deque()
        self.chipSelects = deque()

        self._txBitBuff = deque()
        self._rxBitBuff = deque()
        self.csMask = mask(hwIO.cs._dtype.bit_length())
        self.slaveEn = False

        # resolve clk and rstn
        self.clk = self.hwIO._getAssociatedClk()._sigInside
        self.rst, self.rstOffIn = self._discoverReset(hwIO, allowNoReset=allowNoReset)

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

    @override
    def setEnable(self, en):
        self._enabled = en
        self.monitorRx.setEnable(en)
        self.monitorTx.setEnable(en)
        self.driverRx.setEnable(en)
        self.driverTx.setEnable(en)

    def splitBits(self, v):
        return deque([get_bit(v, i)
                      for i in range(self.BITS_IN_WORD - 1, -1, -1)])

    def mergeBits(self, bits):
        t = HBits(self.BITS_IN_WORD, False)
        val = 0
        vld_mask = 0
        for v in bits:
            val <<= 1
            val |= v.val
            vld_mask <<= 1
            vld_mask |= v.vld_mask

        return t.getConstCls()(t, val, vld_mask)

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
            cs = self.hwIO.cs.read()
            cs = int(cs)
            if cs != self.csMask:  # if any slave is enabled
                if not self._rxBitBuff:
                    self.chipSelects.append(cs)
                self.readRxSig(self.hwIO.mosi)

    # def monitorTx_pre_set(self):
    #     yield WaitWriteOnly()
    #     self.writeTxSig(self.intf.miso)

    def monitorTx(self):
        yield WaitCombRead()
        if self.notReset():
            cs = self.hwIO.cs.read()
            cs = int(cs)
            if cs != self.csMask:
                yield Timer(1)
                yield WaitWriteOnly()
                self.writeTxSig(self.hwIO.miso)

    def driverRx(self):
        yield WaitCombRead()
        if self.notReset() and self.slaveEn:
            self.readRxSig(self.hwIO.miso)

    def driverTx(self):
        yield WaitCombRead()
        if self.notReset():
            if not self._txBitBuff:
                try:
                    cs = self.chipSelects.popleft()
                except IndexError:
                    self.slaveEn = False
                    yield WaitWriteOnly()
                    self.hwIO.cs.write(self.csMask)
                    return

                self.slaveEn = True
                yield WaitWriteOnly()
                self.hwIO.cs.write(cs)

            yield WaitWriteOnly()
            self.writeTxSig(self.hwIO.mosi)

    @override
    def getDrivers(self):
        yield self.driverRx()
        yield self.driverTx()

    @override
    def getMonitors(self):
        yield self.monitorRx()
        #  yield self.monitorTx_pre_set()
        yield self.monitorTx()


# http://www.corelis.com/education/SPI_Tutorial.htm
class Spi(HwIO):
    """
    Bare SPI interface (Serial peripheral interface)

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.SLAVE_CNT = HwParam(1)
        self.HAS_MISO = HwParam(True)
        self.HAS_MOSI = HwParam(True)
        self.FREQ = HwParam(HwIOClk.DEFAULT_FREQ)

    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self.clk.FREQ = self.FREQ

        assert self.HAS_MOSI or self.HAS_MISO
        if self.HAS_MOSI:
            self.mosi = HwIOSignal()  # master out slave in
        if self.HAS_MISO:
            self.miso = HwIOSignal(masterDir=DIRECTION.IN)  # master in slave out
        if self.SLAVE_CNT is not None:
            self.cs = HwIOVectSignal(self.SLAVE_CNT)  # chip select

        self._associatedClk = self.clk

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = SpiAgent(sim, self)


class SpiTristate(Spi):
    """
    SPI interface where mosi and miso signal are merged into one tri-state wire

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        Spi.hwConfig(self)
        self.DATA_WIDTH = HwParam(1)

    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        with self._hwParamsShared():
            self.io = HwIOTristateSig()  # mosi and miso in one wire
        self.cs = HwIOVectSignal(self.SLAVE_CNT)  # chip select

        self._associatedClk = self.clk


class QSPI(SpiTristate):
    """
    SPI interface with 4 tristate data wires

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        Spi.hwConfig(self)
        self.DATA_WIDTH = HwParam(4)
