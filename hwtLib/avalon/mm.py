from hwt.code import log2ceil
from hwt.hdl.constants import DIRECTION, READ, WRITE, NOP
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, Signal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.bitmask import mask

RESP_OKAY = 0b00
# RESP_RESERVED = 0b01 
RESP_SLAVEERROR = 0b10
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
        self.readData = VectSignal(self.DATA_WIDTH, masterDir=IN)
        self.readDataValid = Signal(masterDir=IN)  # read data valid
        self.response = VectSignal(2, masterDir=IN)

        self.write = Signal()
        self.writeData = VectSignal(self.DATA_WIDTH)
        # self.lock = Signal()
        self.waitRequest = Signal(masterDir=IN)
        self.writeResponseValid = Signal(masterDir=IN)
        # self.burstCount = VectSignal(log2ceil(self.MAX_BURST))
        # self.beginBurstTransfer = Signal()

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        return int(self.DATA_WIDTH) // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address (f.e. 8 bits for  char * pointer,
             36 for 36 bit bram)
        """
        return 8

    def _initSimAgent(self):
        self._ag = AvalonMMAgent(self)


class AvalonMmDataRAgent(VldSyncedAgent):
    """
    Simulation/verification agent for data part of AvalomMM interface
    
    * vld signal = readDataValid
    * data signal = (readData, response)
    """

    def doReadVld(self, readFn):
        return readFn(self.intf.readDataValid)

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


class AvalonMmAddrAgent(HandshakedAgent):
    """
    data format is tuple (address, byteEnable, read/write, burstCount)

    * two valid signals "read", "write"
    * one ready_n signal "waitrequest")
    * on write set data and byteenamble as well
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
        if self.actualData is None or self.actualData is NOP:
            r = 0
            w = 0
        else:
            mode = self.actualData[0]
            
            if mode is READ:
                r = val
                w = 0
            elif mode is WRITE:
                r = 0
                w = val
            else:
                raise ValueError("Unknown mode", mode)
        wrFn(r, self._vld[0])
        wrFn(w, self._vld[1])

    def doRead(self, s):
        r = s.read

        intf = self.intf
        address = r(intf.address)
        byteEnable = r(intf.byteEnable)
        read = r(intf.read)
        write = r(intf.write)
        burstCount = 1  # r(intf.burstCount)

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
            # w(None, intf.burstCount)
            w(0, intf.read)
            w(0, intf.write)

        else:
            rw, address, burstCount = data
            if rw is READ:
                rd, wr = 1, 0
                be = mask(intf.readData._dtype.bit_length() // 8)
            elif rw is WRITE:
                rd, wr = 1, 0
                rw, address, burstCount = data
                d, be = self.wData.popleft()
                w(d, intf.writeData)
            else:
                raise TypeError("rw is in invalid format %r" % (rw,))

            w(address, intf.address)
            w(be, intf.byteEnable)
            assert int(burstCount) >= 1, burstCount
            # w(burstCount, intf.burstCount)
            w(rd, intf.read)
            w(wr, intf.write)


class AvalonMMAgent(SyncAgentBase):

    def __init__(self, intf, allowNoReset=False):
        SyncAgentBase.__init__(self, intf, allowNoReset=allowNoReset)
        # self.pendingRead = None
        # self.pendingWrite = None

        self.rDataAg = AvalonMmDataRAgent(intf, allowNoReset=allowNoReset)
        self.addrAg = AvalonMmAddrAgent(intf, allowNoReset=allowNoReset)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return (self.rDataAg.getMonitors()
                 +self.addrAg.getDrivers())

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return (self.rDataAg.getDrivers()
                +self.addrAg.getMonitors())
