from hwt.hdl.constants import READ, WRITE, READ_WRITE
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.interfaces.std import VectSignal, Signal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.avalon.mm import AvalonMmAddrAgent
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask
from pycocotb.hdlSimulator import HdlSimulator


class Mi32(Interface):
    """
    Simple memory interface similar to AvalonMM

    :ivar addr: r/w address
    :ivar rd: read enable
    :ivar wr: write enable
    :ivar ardy: slave address channel ready
    :ivar be: data byte mask for write
    :ivar dwr: write data
    :ivar drd: readed data
    :ivar drdy: read data valid
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.rd = Signal()
        self.wr = Signal()
        self.ardy = Signal(masterDir=DIRECTION.IN)
        self.be = VectSignal(self.DATA_WIDTH // 8)
        self.dwr = VectSignal(self.DATA_WIDTH)
        self.drd = VectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        self.drdy = Signal(masterDir=DIRECTION.IN)

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        return int(self.DATA_WIDTH) // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address
                 (f.e. 8 bits for  char * pointer, 36 for 36 bit bram)
        """
        return 8

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Mi32Agent(sim, self)


class Mi32Agent(SyncAgentBase):
    """
    Simulation agent for Mi32 bus interface

    :ivar req: request data, items are tuples (READ, address)
               or (WRITE, address, data, be_mask)
    :ivar rData: data read from interface
    """

    def __init__(self, sim: HdlSimulator, intf: Mi32, allowNoReset=False):
        SyncAgentBase.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self.addrAg = Mi32AddrAgent(sim, intf, allowNoReset=allowNoReset)
        self.dataAg = Mi32DataAgent(sim, intf, allowNoReset=allowNoReset)

    def req_get(self):
        return self.addrAg.data

    def req_set(self, v):
        self.addrAg.data = v

    req = property(req_get, req_set)

    def rData_get(self):
        return self.dataAg.data

    def rData_set(self, v):
        self.dataAg.data = v

    rData = property(rData_get, rData_set)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return (self.dataAg.getMonitors()
                +self.addrAg.getDrivers())

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return (self.dataAg.getDrivers()
                +self.addrAg.getMonitors())


class Mi32AddrAgent(HandshakedAgent):
    """
    :ivar req: request data, items are tuples (READ, address)
               or (WRITE, address, data, be_mask)
    * two valid signals "read", "write"
    * one ready_n signal "waitrequest")
    * on write set data and byteenamble as well
    """

    @classmethod
    def get_ready_signal(cls, intf):
        return intf.ardy

    @classmethod
    def get_valid_signal(cls, intf):
        return (intf.rd, intf.wr)

    def get_valid(self):
        r = self._vld[0].read()
        w = self._vld[1].read()

        r.val = r.val | w.val
        r.vld_mask = r.vld_mask & w.vld_mask

        return r

    def set_valid(self, val):
        AvalonMmAddrAgent.set_valid(self, val)

    def get_data(self):
        intf = self.intf
        address = intf.addr.read()
        byteEnable = intf.be.read()
        read = bool(intf.rd.read())
        write = bool(intf.wr.read())
        wdata = intf.dwr.read()

        if read and write:
            rw = READ_WRITE
        elif read:
            rw = READ
        elif write:
            rw = WRITE
        else:
            raise AssertionError("This funtion should not be called when data"
                                 "is not ready on interface")

        return (rw, address, wdata, byteEnable)

    def set_data(self, data):
        intf = self.intf
        if data is None:
            intf.addr.write(None)
            intf.be.write(None)
            intf.rd.write(0)
            intf.wr.write(0)
        else:
            rw = data[0]
            if rw is READ:
                _, address = data
                rd, wr = 1, 0
                be = mask(intf.DATA_WIDTH // 8)
                wdata = None
            elif rw is WRITE:
                rd, wr = 0, 1
                _, address, wdata, be = data
            elif wr is READ_WRITE:
                rd, wr = 1, 1
                _, address, wdata, be = data
            else:
                raise TypeError("rw is in invalid format %r" % (rw,))

            intf.addr.write(address)
            intf.rd.write(rd)
            intf.wr.write(wr)
            intf.be.write(be)
            intf.dwr.write(wdata)


class Mi32DataAgent(VldSyncedAgent):

    @classmethod
    def get_valid_signal(cls, intf: Mi32):
        return intf.drdy

    def get_data(self):
        return self.intf.drd.read()

    def set_data(self, data):
        self.intf.drd.write(data)
