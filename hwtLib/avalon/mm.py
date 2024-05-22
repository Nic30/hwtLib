from collections import deque

from hwt.constants import DIRECTION, READ, WRITE, NOP, READ_WRITE
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.agents.vldSync import HwIODataVldAgent
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.math import log2ceil
from hwt.simulator.agentBase import SyncAgentBase
from hwt.hwIO import HwIO
from hwt.hwParam import HwParam
from hwtSimApi.hdlSimulator import HdlSimulator
from pyMathBitPrecise.bit_utils import mask

RESP_OKAY = 0b00
# RESP_RESERVED = 0b01
RESP_SLAVEERROR = 0b10
RESP_DECODEERROR = 0b11


class AvalonMM(HwIO):
    """
    Avalon Memory Mapped interface

    :note: handshaked, shared address and response channel

    https://www.intel.com/content/dam/altera-www/global/en_US/pdfs/literature/manual/mnl_avalon_spec.pdf

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)
        self.MAX_BURST = HwParam(0)

    def _declr(self):
        # self.debugAccess = HwIOSignal()
        IN = DIRECTION.IN

        # read/write transaction start
        self.read = HwIOSignal()
        self.write = HwIOSignal()

        self.address = HwIOVectSignal(self.ADDR_WIDTH)
        # ready from slave to mark that next request can not be accepted
        self.waitRequest = HwIOSignal(masterDir=IN)

        self.readData = HwIOVectSignal(self.DATA_WIDTH, masterDir=IN)
        self.readDataValid = HwIOSignal(masterDir=IN)  # read data valid

        self.byteEnable = HwIOVectSignal(self.DATA_WIDTH // 8)
        self.writeData = HwIOVectSignal(self.DATA_WIDTH)
        # self.lock = HwIOSignal()

        self.response = HwIOVectSignal(2, masterDir=IN)
        self.writeResponseValid = HwIOSignal(masterDir=IN)
        if self.MAX_BURST != 0:
            self.burstCount = HwIOVectSignal(log2ceil(self.MAX_BURST))
        # self.beginBurstTransfer = HwIOSignal()

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


class AvalonMmDataRAgent(HwIODataVldAgent):
    """
    Simulation/verification agent for data part of AvalomMM interface

    * vld signal = readDataValid
    * data signal = (readData, response)
    """

    @classmethod
    def get_valid_signal(cls, hwIO):
        return hwIO.readDataValid

    def get_valid(self):
        return self._vld.read()

    def set_valid(self, val):
        self._vld.write(val)

    def get_data(self):
        """extract data from interface"""
        hwIO = self.hwIO
        return (hwIO.readData.read(), hwIO.response.read())

    def set_data(self, data):
        """write data to interface"""
        hwIO = self.hwIO
        if data is None:
            hwIO.readData.write(None)
            hwIO.response.write(None)
        else:
            readData, response = data
            hwIO.readData.write(readData)
            hwIO.response.write(response)


class AvalonMmAddrAgent(HwIODataRdVldAgent):
    """
    data format is tuple (address, byteEnable, READ/WRITE, burstCount)

    * two valid signals "read", "write"
    * one ready_n signal "waitrequest")
    * on write set data and byteenamble as well
    """

    def __init__(self, sim: HdlSimulator, hwIO, allowNoReset=False):
        HwIODataRdVldAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        self.BE_ALL = mask(hwIO.readData._dtype.bit_length() // 8)

    @classmethod
    def get_ready_signal(cls, hwIO: AvalonMM):
        return hwIO.waitRequest

    def get_ready(self):
        rd = self._rd.read()
        rd.val = int(not rd.val)
        return rd

    def set_ready(self, val: int):
        self._rd.write(int(not val))

    @classmethod
    def get_valid_signal(cls, hwIO: AvalonMM):
        return (hwIO.read, hwIO.write)

    def get_valid(self):
        r = self._vld[0].read()
        w = self._vld[1].read()

        r.val = r.val | w.val
        r.vld_mask = r.vld_mask & w.vld_mask

        return r

    def set_valid(self, val: int):
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
        hwIO = self.hwIO
        address = hwIO.address.read()
        byteEnable = hwIO.byteEnable.read()
        read = hwIO.read.read()
        write = hwIO.write.read()
        wdata = hwIO.writeData.read()
        if hwIO.MAX_BURST != 0:
            burstCount = hwIO.burstCount.read()
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
                "This function should not be called when data"
                "is not ready on interface")
        return (rw, address, burstCount, wdata, byteEnable)

    def set_data(self, data):
        hwIO = self.hwIO
        if data is None:
            hwIO.address.write(None)
            hwIO.byteEnable.write(None)
            if hwIO.MAX_BURST != 0:
                hwIO.burstCount.write(None)
            hwIO.writeData.write(None)
            hwIO.read.write(0)
            hwIO.write.write(0)

        else:
            rw, address, burstCount, d, be = data
            if rw is READ:
                rd, wr = 1, 0
                be = self.BE_ALL
            elif rw is WRITE:
                rd, wr = 0, 1
                hwIO.writeData.write(d)
            else:
                raise TypeError(f"rw is in invalid format {rw}")

            hwIO.address.write(address)
            hwIO.byteEnable.write(be)
            assert int(burstCount) >= 1, burstCount
            if hwIO.MAX_BURST:
                hwIO.burstCount.write(burstCount)
            hwIO.read.write(rd)
            hwIO.write.write(wr)


class AvalonMmWRespAgent(HwIODataVldAgent):

    @classmethod
    def get_valid_signal(cls, hwIO):
        return hwIO.writeResponseValid

    def get_data(self):
        return self.hwIO.response.read()

    def set_data(self, data):
        self.hwIO.response.write(data)


class AvalonMmAgent(SyncAgentBase):
    """
    Simulation agent for AvalonMM bus interface

    :ivar ~.req: request data, items are tuples (READ/WRITE, address, burstCount, writeData, writeMask)
    :ivar ~.wResp: write response data
    :ivar ~.rData: data read from interface, items are typles (data, response)
    """

    def __init__(self, sim: HdlSimulator, hwIO, allowNoReset=False):
        SyncAgentBase.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        self.addrAg = AvalonMmAddrAgent(sim, hwIO, allowNoReset=allowNoReset)
        self.rDataAg = AvalonMmDataRAgent(sim, hwIO, allowNoReset=allowNoReset)
        self.wRespAg = AvalonMmWRespAgent(sim, hwIO, allowNoReset=allowNoReset)

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

    def setEnable_asDriver(self, en: bool):
        self._enabled = en
        self.addrAg.setEnable(en)
        # self.wRespAg.setEnable(en)

    def setEnable_asMonitor(self, en: bool):
        self._enabled = en
        self.addrAg.setEnable(en)
        self.wRespAg.setEnable(en)
        self.rData.setEnable(en)

    def getDrivers(self):
        self.setEnable = self.setEnable_asDriver
        yield from self.rDataAg.getMonitors()
        yield from self.addrAg.getDrivers()
        yield from self.wRespAg.getMonitors()

    def getMonitors(self):
        self.setEnable = self.setEnable_asMonitor
        yield from self.rDataAg.getDrivers()
        yield from self.addrAg.getMonitors()
        yield from self.wRespAg.getDrivers()
