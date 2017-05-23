from hwt.interfaces.agents.tristate import TristatePullUpAgent
from hwt.interfaces.tristate import TristateClk, TristateSig
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.simulator.agentBase import AgentBase
from hwt.synthesizer.interfaceLevel.interface import Interface


class I2c(Interface):
    def _declr(self):
        self.scl = TristateClk()  # serial clk
        self.sda = TristateSig()  # serial data

    def _getIpCoreIntfClass(self):
        return IP_IIC

    def _getSimAgent(self):
        return I2cAgent


class I2cAgent(AgentBase):
    START = "start"

    def __init__(self, intf):
        AgentBase.__init__(self, intf)
        self.bits = []
        self.listenForStart = True

    def startListener(self, sim):
        if self.listenForStart:
            self.bits.append(self.START)
            self.listenForStart = False

    def getMonitors(self):
        intf = self.intf
        self.sdaPullUp = TristatePullUpAgent(intf.sda)
        self.sclPullUp = TristatePullUpAgent(intf.scl,
                                             onRisingCallback=self.monitor,
                                             onFallingCallback=self.startListener)
        return (self.sdaPullUp.getMonitors() + 
                self.sclPullUp.getMonitors()
                )

    def monitor(self, sim):
        if sim.now > 0:
            v = sim.read(self.intf.sda.i)
            self.bits.append(v)


class IP_IIC(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "iic"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {'scl': {"t": "SCL_T",
                            "i": "SCL_I",
                            "o": "SCL_O"},
                    'sda': {"t": "SDA_T",
                            "i": "SDA_I",
                            "o": "SDA_O"}
                    }
