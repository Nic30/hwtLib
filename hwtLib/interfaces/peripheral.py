from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig 
from hwt.interfaces.std import Clk, s, D, Signal
from hwt.interfaces.tristate import TristateClk, TristateSig
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.simulator.agentBase import AgentBase
from hwt.interfaces.agents.tristate import TristatePullUpAgent


class Spi(Interface):
    def _declr(self):
        self.clk = Clk()
        self.mosi = s()  # master out slave in
        self.miso = s(masterDir=D.IN)  # master in slave out
        self.cs = s()  # chip select


class Uart(Interface):
    def _declr(self):
        self.rx = Signal(masterDir=D.IN)
        self.tx = Signal()
    
    def _getIpCoreIntfClass(self):
        return IP_Uart        
        



class IP_Uart(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "iic"
        self.version = "1.0"
        self.vendor = "xilinx.com" 
        self.library = "interface"
        self.map = {'rx':"RxD",
                    'tx':"TxD"}


