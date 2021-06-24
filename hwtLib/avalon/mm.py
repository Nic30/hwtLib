from collections import deque

from hwt.hdl.constants import DIRECTION, READ, WRITE, NOP, READ_WRITE
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.interfaces.std import VectSignal, Signal
from hwt.math import log2ceil
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator
from pyMathBitPrecise.bit_utils import mask


RESP_OKAY = 0b00
# RESP_RESERVED = 0b01
RESP_SLAVEERROR = 0b10
RESP_DECODEERROR = 0b11


class AvalonMM(Interface):
    """
    Avalon Memory Mapped interface

    :note: handshaked, shared address and response channel

    https://www.intel.com/content/dam/altera-www/global/en_US/pdfs/literature/manual/mnl_avalon_spec.pdf

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)
        self.MAX_BURST = Param(0)

    def _declr(self):
        # self.debugAccess = Signal()
        IN = DIRECTION.IN

        # read/write transaction start
        self.read = Signal()
        self.write = Signal()

        self.address = VectSignal(self.ADDR_WIDTH)
        # ready from slave to mark that the operation can not be started
        self.waitRequest = Signal(masterDir=IN)

        self.readData = VectSignal(self.DATA_WIDTH, masterDir=IN)
        self.readDataValid = Signal(masterDir=IN)  # read data valid

        self.byteEnable = VectSignal(self.DATA_WIDTH // 8)
        self.writeData = VectSignal(self.DATA_WIDTH)
        # self.lock = Signal()

        self.response = VectSignal(2, masterDir=IN)
        self.writeResponseValid = Signal(masterDir=IN)
        if self.MAX_BURST != 0:
            self.burstCount = VectSignal(log2ceil(self.MAX_BURST))
        # self.beginBurstTransfer = Signal()

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
        self._ag = AvalonMmAgent(sim, self)


class AvalonMmDataRAgent(VldSyncedAgent):
    """
    Simulation/verification agent for data part of AvalomMM interface

    * vld signal = readDataValid
    * data signal = (readData, response)
    """

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.readDataValid

    def get_valid(self):
        return self._vld.read()

    def set_valid(self, val):
        self._vld.write(val)

    def get_data(self):
        """extract data from interface"""
        intf = self.intf
        return (intf.readData.read(), intf.response.read())

    def set_data(self, data):
        """write data to interface"""
        intf = self.intf
        if data is None:
            intf.readData.write(None)
            intf.response.write(None)
        else:
            readData, response = data
            intf.readData.write(readData)
            intf.response.write(response)


class AvalonMmAddrAgent(HandshakedAgent):
    """
    data format is tuple (address, byteEnable, read/write, burstCount)

    * two valid signals "read", "write"
    * one ready_n signal "waitrequest")
    * on write set data and byteenamble as well
    """

    def __init__(self, sim: HdlSimulator, intf, allowNoReset=False):
        HandshakedAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self.BE_ALL = mask(intf.readData._dtype.bit_length() // 8)

    @classmethod
    def get_ready_signal(cls, intf):
        return intf.waitRequest

    def get_ready(self):
        rd = self._rd.read()
        rd.val = int(not rd.val)
        return rd

    def set_ready(self, val):
        self._rd.write(int(not val))

    @classmethod
    def get_valid_signal(cls, intf):
        return (intf.read, intf.write)

    def get_valid(self):
        r = self._vld[0].read()
        w = self._vld[1].read()

        r.val = r.val | w.val
        r.vld_mask = r.vld_mask & w.vld_mask

        return r

    def set_valid(self, val):
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
        self._vld[0].write(r)
        self._vld[1].write(w)

    def get_data(self):
        intf = self.intf
        address = intf.address.read()
        byteEnable = intf.byteEnable.read()
        read = intf.read.read()
        write = intf.write.read()
        wdata = intf.writeData.read()
        if intf.MAX_BURST != 0:
            burstCount = intf.burstCount.read()
        else:
            burstCount = 1

        if read.val:
            if write.val:
                rw = READ_WRITE
            else:
                rw = READ
                wdata = None
                byteEnable = None
        elif write.val:
            rw = WRITE
        else:
            raise AssertionError(
                "This funtion should not be called when data"
                "is not ready on interface")
        return (rw, address, burstCount, wdata, byteEnable)

    def set_data(self, data):
        intf = self.intf
        if data is None:
            intf.address.write(None)
            intf.byteEnable.write(None)
            if intf.MAX_BURST != 0:
                intf.burstCount.write(None)
            intf.writeData.write(None)
            intf.read.write(0)
            intf.write.write(0)

        else:
            rw, address, burstCount, d, be = data
            if rw is READ:
                rd, wr = 1, 0
                be = self.BE_ALL
            elif rw is WRITE:
                rd, wr = 0, 1
                intf.writeData.write(d)
            else:
                raise TypeError(f"rw is in invalid format {rw}")

            intf.address.write(address)
            intf.byteEnable.write(be)
            assert int(burstCount) >= 1, burstCount
            if intf.MAX_BURST:
                intf.burstCount.write(burstCount)
            intf.read.write(rd)
            intf.write.write(wr)


class AvalonMmWRespAgent(VldSyncedAgent):

    @classmethod
    def get_valid_signal(cls, intf):
        return intf.writeResponseValid

    def get_data(self):
        return self.intf.response.read()

    def set_data(self, data):
        self.intf.response.write(data)


class AvalonMmAgent(SyncAgentBase):
    """
    Simulation agent for AvalonMM bus interface

    :ivar ~.req: request data, items are tuples (READ/WRITE, address, burstCount, writeData, writeMask)
    :ivar ~.wResp: write response data
    :ivar ~.rData: data read from interface, items are typles (data, response)
    """

    def __init__(self, sim: HdlSimulator, intf, allowNoReset=False):
        SyncAgentBase.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self.addrAg = AvalonMmAddrAgent(sim, intf, allowNoReset=allowNoReset)
        self.rDataAg = AvalonMmDataRAgent(sim, intf, allowNoReset=allowNoReset)
        self.wRespAg = AvalonMmWRespAgent(sim, intf, allowNoReset=allowNoReset)

    def req_get(self):
        return self.addrAg.data

    def req_set(self, v):
        self.addrAg.data = v

    req = property(req_get, req_set)

    def wResp_get(self):
        return self.wRespAg.data

    def wResp_set(self, v):
        self.wRespAg = v

    wResp = property(wResp_get, wResp_set)

    def rData_get(self):
        return self.rDataAg.data

    def rData_set(self, v):
        self.rDataAg.data = v

    rData = property(rData_get, rData_set)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        return (self.rDataAg.getMonitors()
                +self.addrAg.getDrivers()
                +self.wRespAg.getMonitors())

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        return (self.rDataAg.getDrivers()
                +self.addrAg.getMonitors()
                +self.wRespAg.getDrivers())
