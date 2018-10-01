from collections import deque

from hwt.interfaces.agents.tristate import TristateAgent, \
    TristateClkAgent, toGenerator
from hwt.interfaces.tristate import TristateClk, TristateSig
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.simulator.agentBase import AgentWitReset
from hwt.synthesizer.interface import Interface


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

    def _initSimAgent(self):
        self._ag = I2cAgent(self)


class I2cAgent(AgentWitReset):
    START = "start"

    def __init__(self, intf, allowNoReset=True):
        AgentWitReset.__init__(self, intf, allowNoReset=allowNoReset)
        self.bits = deque()
        self.start = True
        self.sda = TristateAgent(intf.sda)
        self.sda.collectData = False
        self.sda.selfSynchronization = False

    def startListener(self, sim):
        if self.start:
            self.bits.append(self.START)
            self.start = False

        return
        yield

    def startSender(self, sim):
        if self.start:
            self.sda._write(0, sim)
            self.start = False
        return
        yield
    
    def getMonitors(self):
        self.scl = TristateClkAgent(self.intf.scl,
                                    onRisingCallback=self.monitor,
                                    onFallingCallback=self.startListener)
        return (self.sda.getMonitors() + 
                self.scl.getMonitors()
                )

    def getDrivers(self):
        self.scl = TristateClkAgent(self.intf.scl,
                                    onRisingCallback=self.driver,
                                    onFallingCallback=self.startSender)
        return ([toGenerator(self.driver)] +  # initial initialization
                self.sda.getDrivers() + 
                self.scl.getDrivers()
                )

    def monitor(self, sim):
        # now intf.sdc is rising
        yield sim.waitOnCombUpdate()
        # wait on all agents to update values and on 
        # simulator to appply them
        if sim.now > 0 and self.notReset(sim):
            v = sim.read(self.intf.sda.i)
            self.bits.append(v)

    def driver(self, sim):
        # now intf.sdc is rising
        # yield sim.wait(1)
        # yield sim.waitOnCombUpdate()
        yield from self.sda.driver(sim)
        # now we are after clk
        # prepare data for next clk
        if self.bits:
            b = self.bits.popleft()
            if b == self.START:
                return
            self.sda._write(b, sim)


class IP_IIC(IntfConfig):

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
