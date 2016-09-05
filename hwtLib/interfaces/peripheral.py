from cli_toolkit.ip_packager.interfaces.intfConfig import IntfConfig 
from hdl_toolkit.interfaces.std import Clk, s, D, Signal
from hdl_toolkit.interfaces.tristate import TristateClk, TristateSig
from hdl_toolkit.synthesizer.interfaceLevel.interface import Interface


class Spi(Interface):
    def _declr(self):
        self.clk = Clk()
        self.mosi = s()  # master out slave in
        self.miso = s(masterDir=D.IN)  # master in slave out
        self.cs = s()  # chip select

class I2c(Interface):
    def _declr(self):
        self.slc = TristateClk()  # clk
        self.sda = TristateSig()  # data
    
    def _getIpCoreIntfClass(self):
        return IP_IIC


class Uart(Interface):
    def _declr(self):
        self.rx = Signal(masterDir=D.IN)
        self.tx = Signal()
    
    def _getIpCoreIntfClass(self):
        return IP_Uart        
        


class IP_IIC(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "iic"
        self.version = "1.0"
        self.vendor = "xilinx.com" 
        self.library = "interface"
        self.map = {'slc':{"t":"SLC_T",
                           "i": "SLC_I",
                           "o": "SLC_O"},
                    'sda':{"t": "SDA_T",
                           "i": "SDA_I",
                           "o": "SDA_O"}
                     }

class IP_Uart(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "iic"
        self.version = "1.0"
        self.vendor = "xilinx.com" 
        self.library = "interface"
        self.map = {'rx':"RxD",
                    'tx':"TxD"}
