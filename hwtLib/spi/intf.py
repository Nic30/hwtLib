from hwt.bitmask import selectBit
from hwt.hdlObjects.constants import DIRECTION
from hwt.hdlObjects.operatorDefs import onFallingEdge
from hwt.interfaces.std import Clk, Signal, VectSignal
from hwt.interfaces.tristate import TristateSig
from hwt.simulator.agentBase import SyncAgentBase, AgentBase
from hwt.simulator.shortcuts import onRisingEdge
from hwt.simulator.types.simBits import simBitsT
from hwt.synthesizer.exceptions import IntfLvlConfErr
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param


class SpiAgent(SyncAgentBase):
    """
    Simulation agent for SPI interface
    :attention: enable is not implemented
    """
    BITS_IN_BYTE = 8
    
    def __init__(self, intf, allowNoReset=False):
        AgentBase.__init__(self, intf)
        self.txData = []
        self.rxData = []

        self._txBitBuff = []
        self._rxBitBuff = []
        # resolve clk and rstn
        self.clk = self.intf._getAssociatedClk()
        try:
            self.rst_n = self.getRst_n(allowNoReset=allowNoReset)
        except IntfLvlConfErr as e:
            if allowNoReset:
                pass
            else:
                raise e
            
        # run monitor, driver only on rising edge of clk
        self.monitorRx = onRisingEdge(self.clk, self.monitorRx)
        self.monitorTx = onFallingEdge(self.clk, self.monitorTx)
        
        self.driverRx = onRisingEdge(self.clk, self.driverRx)
        self.driverTx = onFallingEdge(self.clk, self.driverTx)
    
    def splitBits(self, v):
        return [selectBit(v, i) for i in range(self.BITS_IN_BYTE - 1, -1, -1)]

    def mergeBits(self, bits):
        t = simBitsT(self.BITS_IN_BYTE, False)
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
        if len(bits) == self.BITS_IN_BYTE: 
            self.rxData.append(self.mergeBits(bits))
            self._rxBitBuff = []
    
    def writeTxSig(self, sim, sig):
        bits = self._txBitBuff
        if not bits:
            if not self.txData:
                return
            d = self.txData.pop(0)
            bits = self._txBitBuff = self.splitOnBits(d)
            
        sim.write(bits.pop(0), sig)
        
    
    def monitorRx(self, s):
        self.readRxSig(s, self.intf.mosi)

    def monitorTx(self, s):
        self.writeTxSig(s, self.intf.miso)
 
    def driverRx(self, s):
        self.readRxSig(s, self.intf.miso)

    def driverTx(self, s):
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
