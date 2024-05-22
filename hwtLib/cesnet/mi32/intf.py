from hwt.constants import READ, WRITE, READ_WRITE
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.agents.vldSync import HwIODataVldAgent
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.hwIO import HwIO
from hwt.hwParam import HwParam
from hwtLib.avalon.mm import AvalonMmAddrAgent
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.hdlSimulator import HdlSimulator


class Mi32(HwIO):
    """
    Simple memory interface similar to AvalonMM

    :ivar ~.addr: r/w address
    :ivar ~.rd: read enable
    :ivar ~.wr: write enable
    :ivar ~.ardy: slave address channel ready
    :ivar ~.be: data byte mask for write
    :ivar ~.dwr: write data
    :ivar ~.drd: read data
    :ivar ~.drdy: read data valid

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(32)
        self.ADDR_WIDTH = HwParam(32)

    def _declr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.rd = HwIOSignal()
        self.wr = HwIOSignal()
        self.ardy = HwIOSignal(masterDir=DIRECTION.IN)
        self.be = HwIOVectSignal(self.DATA_WIDTH // 8)
        self.dwr = HwIOVectSignal(self.DATA_WIDTH)
        self.drd = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        self.drdy = HwIOSignal(masterDir=DIRECTION.IN)

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        return int(self.DATA_WIDTH) // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address
                 (e.g. 8 bits for  char * pointer, 36 for 36 bit bram)
        """
        return 8

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Mi32Agent(sim, self)


class Mi32Agent(SyncAgentBase):
    """
    Simulation agent for Mi32 bus interface

    :ivar ~.requests: request data, items are tuples (READ, address)
        or (WRITE, address, data, be_mask)
    :ivar ~.rData: data read from interface
    """

    def __init__(self, sim: HdlSimulator, hwIO: Mi32, allowNoReset=False):
        SyncAgentBase.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        self.addrAg = Mi32AddrAgent(sim, hwIO, allowNoReset=allowNoReset)
        self.dataAg = Mi32DataAgent(sim, hwIO, allowNoReset=allowNoReset)

    def requests_get(self):
        return self.addrAg.data

    def requests_set(self, v):
        self.addrAg.data = v

    requests = property(requests_get, requests_set)

    def r_data_get(self):
        return self.dataAg.data

    def r_data_set(self, v):
        self.dataAg.data = v

    r_data = property(r_data_get, r_data_set)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        yield from self.dataAg.getMonitors()
        yield from self.addrAg.getDrivers()

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        yield from self.dataAg.getDrivers()
        yield from self.addrAg.getMonitors()


class Mi32AddrAgent(HwIODataRdVldAgent):
    """
    :ivar ~.requests: request data, items are tuples (READ, address)
        or (WRITE, address, data, be_mask)

    :note: two valid signals "read", "write"
    :note: one ready_n signal "waitrequest"
    :note: on write set data and byteenamble as well
    """

    @classmethod
    def get_ready_signal(cls, hwIO):
        return hwIO.ardy

    @classmethod
    def get_valid_signal(cls, hwIO):
        return (hwIO.rd, hwIO.wr)

    def get_valid(self):
        r = self._vld[0].read()
        w = self._vld[1].read()

        r.val = r.val | w.val
        r.vld_mask = r.vld_mask & w.vld_mask

        return r

    def set_valid(self, val):
        AvalonMmAddrAgent.set_valid(self, val)

    def get_data(self):
        hwIO = self.hwIO
        address = hwIO.addr.read()
        byteEnable = hwIO.be.read()
        read = bool(hwIO.rd.read())
        write = bool(hwIO.wr.read())
        wdata = hwIO.dwr.read()

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
        hwIO = self.hwIO
        if data is None:
            hwIO.addr.write(None)
            hwIO.be.write(None)
            hwIO.rd.write(0)
            hwIO.wr.write(0)
        else:
            rw = data[0]
            if rw is READ:
                _, address = data
                rd, wr = 1, 0
                be = mask(hwIO.DATA_WIDTH // 8)
                wdata = None
            elif rw is WRITE:
                rd, wr = 0, 1
                _, address, wdata, be = data
            elif rw is READ_WRITE:
                rd, wr = 1, 1
                _, address, wdata, be = data
            else:
                raise TypeError(f"rw is in invalid format {rw}")

            hwIO.addr.write(address)
            hwIO.rd.write(rd)
            hwIO.wr.write(wr)
            hwIO.be.write(be)
            hwIO.dwr.write(wdata)


class Mi32DataAgent(HwIODataVldAgent):

    @classmethod
    def get_valid_signal(cls, hwIO: Mi32):
        return hwIO.drdy

    def get_data(self):
        return self.hwIO.drd.read()

    def set_data(self, data):
        self.hwIO.drd.write(data)
