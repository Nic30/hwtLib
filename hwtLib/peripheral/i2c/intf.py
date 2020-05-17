from hwt.interfaces.tristate import TristateClk, TristateSig
from hwt.simulator.agentBase import AgentWitReset
from hwt.synthesizer.interface import Interface
from ipCorePackager.intfIpMeta import IntfIpMeta
from pycocotb.agents.peripheral.i2c import I2cAgent
from pycocotb.hdlSimulator import HdlSimulator


class I2c(Interface):
    """
    I2C interface also known as IIC, TWI or Two Wire

    If interface is outside of chip it needs pull-up resistors
    """

    def _declr(self):
        self.scl = TristateClk()  # serial clk
        self.sda = TristateSig()  # serial data

    def _getIpCoreIntfClass(self):
        return IP_IIC

    def _initSimAgent(self, sim: HdlSimulator):
        scl = self.scl
        sda = self.sda
        rst = AgentWitReset._discoverReset(self, allowNoReset=True)
        self._ag = I2cAgent(
            sim, (scl, sda), rst)


class IP_IIC(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "iic"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {"scl": {"t": "SCL_T",
                            "i": "SCL_I",
                            "o": "SCL_O"},
                    "sda": {"t": "SDA_T",
                            "i": "SDA_I",
                            "o": "SDA_O"}
                    }
