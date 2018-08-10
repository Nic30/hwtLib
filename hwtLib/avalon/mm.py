from hwt.code import log2ceil
from hwt.hdl.constants import DIRECTION, READ, WRITE
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.agents.rdSynced import RdSyncedAgent
from hwt.interfaces.std import VectSignal, Signal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param

RESP_OKAY = 0b00
RESP_LAVEERROR = 0b10
RESP_DECODEERROR = 0b11


class AvalonMM(Interface):
    """
    Avalon Memory Mapped interface

    (with wait signal)

    https://www.intel.com/content/dam/altera-www/global/en_US/pdfs/literature/manual/mnl_avalon_spec.pdf
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)
        self.MAX_BURST = Param(4)

    def _declr(self):
        # self.debugAccess = Signal()
        IN = DIRECTION.IN

        self.address = VectSignal(self.ADDR_WIDTH)
        self.byteEnable = VectSignal(self.DATA_WIDTH // 8)

        self.read = Signal()
        self.readData = VectSignal(self.DATA_WIDTH)
        self.readValid = Signal(masterDir=IN)  # read data valid
        self.response = VectSignal(2, masterDir=IN)

        self.write = Signal()
        self.writeData = VectSignal(self.DATA_WIDTH)
        # self.lock = Signal()
        self.waitRequest = Signal(masterDir=IN)
        # self.writeResponseValid = Signal(masterDir=IN)
        self.burstCount = VectSignal(log2ceil(self.MAX_BURST))
        # self.beginBurstTransfer = Signal()

    def _initSimAgent(self):
        self._ag = AvalonMMAgent(self)


class AvalonMMDataAgent(RdSyncedAgent):
    """
    Simulation/verification agent for data part of AvalomMM interface

    :note: it is 2x hadnshaked
       (vld0=read, rd0=~waitRequest),
       (vld1=write, rd0=~waitRequest)
    """

    def getRd(self, intf):
        return intf.readValid

    def doRead(self, s):
        """extract data from interface"""
        r = s.read
        intf = self.intf
        return (r(intf.readData), r(intf.response))

    def doWrite(self, s, data):
        """write data to interface"""
        w = s.write
        intf = self.intf
        if data is None:
            w(None, intf.readData)
            w(None, intf.response)
        else:
            readData, response = data
            w(readData, intf.readData)
            w(response, intf.response)


class AvalonAddrAgent(HandshakedAgent):
    """
    data format is tuple (address, byteEnable, read/write, burstCount)
    """

    def getRd(self):
        return self.intf.waitRequest

    def isRd(self, readFn):
        rd = readFn(self._rd)
        rd.val = not rd.val
        return rd

    def wrRd(self, wrFn, val):
        wrFn(int(not val), self._rd)

    def getVld(self):
        return (self.intf.read, self.intf.write)

    def isVld(self, readFn):
        r = readFn(self._vld[0])
        w = readFn(self._vld[1])

        r.val = r.val or w.val
        r.vldMask = r.vldMask and w.vldMask

        return r

    def wrVld(self, wrFn, val):
        """
        read/write which are there used as valid signal are written
        from doWrite funtion
        """

    def doRead(self, s):
        r = s.read

        intf = self.intf
        address = r(intf.address)
        byteEnable = r(intf.byteEnable)
        read = r(intf.read)
        write = r(intf.write)
        burstCount = r(intf.burstCount)

        if read.val:
            rw = READ
        elif write.val:
            rw = WRITE
        else:
            raise AssertionError("This funtion should not be called when data"
                                 "is not ready on interface")

        return (address, byteEnable, rw, burstCount)

    def doWrite(self, s, data):
        w = s.write
        intf = self.intf
        if data is None:
            w(None, intf.address)
            w(None, intf.byteEnable)
            w(0, intf.read)
            w(0, intf.write)
            w(None, intf.burstCount)

        else:
            address, byteEnable, rw, burstCount = data
            w(address, intf.address)
            w(byteEnable, intf.byteEnable)
            w(burstCount, intf.burstCount)
            if rw is READ:
                w(1, intf.read)
                w(0, intf.write)
            elif rw is WRITE:
                w(0, intf.read)
                w(1, intf.write)
            else:
                raise TypeError("rw is in invalid format %r" % (rw,))


class AvalonMMAgent(SyncAgentBase):

    def __init__(self, intf, allowNoReset=False):
        SyncAgentBase.__init__(self, intf, allowNoReset=allowNoReset)
        self.pendingRead = None
        self.pendingWrite = None

        self.dataAg = AvalonMMDataAgent(intf, allowNoReset=allowNoReset)
        self.addrAg = AvalonAddrAgent(intf, allowNoReset=allowNoReset)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return (self.dataAg.getDrivers()
                 +self.addrAg.getDrivers())

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return (self.dataAg.getMonitors()
                +self.addrAg.getMonitors())
