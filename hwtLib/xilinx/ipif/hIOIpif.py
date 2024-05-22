from collections import deque
from enum import Enum

from hwt.constants import READ, WRITE, NOP
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.hdl.types.bits import HBits
from hwt.simulator.agentBase import SyncAgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.triggers import WaitCombStable, WaitCombRead, WaitWriteOnly
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask
from hwt.pyUtils.typingFuture import override


# https://www.xilinx.com/support/documentation/ip_documentation/axi_lite_ipif/v2_0/pg155-axi-lite-ipif.pdf
# https://www.xilinx.com/support/documentation/ip_documentation/axi_lite_ipif_ds765.pdf
class Ipif(HwIO):
    """
    IPIF - IP interface is interface which was often used
    in designs for Xilinx FPGAs around year 2012

    * shared address, validity signals, mask, write ack

    .. hwt-autodoc::
    """

    READ = 1
    WRITE = 0

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        # chip select
        self.bus2ip_cs = HwIOSignal()

        # A High level indicates the transfer request is a user IP read.
        # A Low level indicates the transfer request is a user IP write.
        self.bus2ip_rnw = HwIOSignal()

        # read /write addr
        self.bus2ip_addr = HwIOVectSignal(self.ADDR_WIDTH)

        self.bus2ip_data = HwIOVectSignal(self.DATA_WIDTH)
        # byte enable for bus2ip_data
        self.bus2ip_be = HwIOVectSignal(self.DATA_WIDTH // 8)

        self.ip2bus_data = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        # write ack
        self.ip2bus_wrack = HwIOSignal(masterDir=DIRECTION.IN)
        # read ack
        self.ip2bus_rdack = HwIOSignal(masterDir=DIRECTION.IN)
        self.ip2bus_error = HwIOSignal(masterDir=DIRECTION.IN)

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

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = IpifAgent(sim, self)


class IpifWithCE(Ipif):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        super(IpifWithCE, self).hwConfig()
        self.REG_COUNT = HwParam(1)

    @override
    def hwDeclr(self):
        super().hwDeclr()
        ce_t = HBits(self.REG_COUNT)
        # read chip enable bus
        self.bus2ip_rdce = HwIOSignal(dtype=ce_t)
        # Write chip enable bus
        self.bus2ip_wrce = HwIOSignal(dtype=ce_t)


class IpifAgentState(Enum):
    IDLE = 0
    READ = 1
    WRITE = 2


class IpifAgent(SyncAgentBase):
    """
    :ivar ~.requests: list of tuples (READ, address) or
        (WRITE, address, data, mask) used for driver
    :ivar ~.r_data: list of read data for driver
    :ivar ~.mem: if agent is in monitor mode (= is slave)
        all reads and writes are performed on mem object, index is word index
    :note: this behavior can be overridden by onRead/onWrite methods
    :ivar ~.actual: actual request which is performed (in driver mode)
    """

    def __init__(self, sim: HdlSimulator, hwIO, allowNoReset=True):
        super().__init__(sim, hwIO, allowNoReset=allowNoReset)

        # for driver only
        self.requests = deque()
        self.actual = NOP
        self.r_data = deque()

        # for monitor only
        self.READ_LATENCY = 0
        self.WRITE_LATENCY = 0
        self.mem = {}
        self._monitor_st = IpifAgentState.IDLE
        self._addr = self._rnw = self._be = self._wdata = None
        self._latencyCntr = 0

        self._word_bytes = hwIO.bus2ip_data._dtype.bit_length() // 8
        self.wmaskAll = mask(self._word_bytes)
        self._requireInit = True

    def onRead(self, addr):
        if addr % self._word_bytes != 0:
            raise NotImplementedError("Unaligned read")

        return self.mem[int(addr) // self._word_bytes]

    def onWrite(self, addr, val, byteen):
        if addr % self._word_bytes != 0:
            raise NotImplementedError("Unaligned write")

        if int(byteen) == self.wmaskAll:
            self.mem[addr//self._word_bytes] = val
        else:
            raise NotImplementedError("Masked write")

    def doReq(self, req):
        rw = req[0]
        addr = req[1]

        if rw == READ:
            rw = Ipif.READ
            wdata = None
            wmask = None
        elif rw == WRITE:
            wdata = req[2]
            rw = Ipif.WRITE
            wmask = req[3]
        else:
            raise ValueError(rw)

        hwIO = self.hwIO
        hwIO.bus2ip_cs.write(1)
        hwIO.bus2ip_rnw.write(rw)
        hwIO.bus2ip_addr.write(addr)
        hwIO.bus2ip_data.write(wdata)
        hwIO.bus2ip_be.write(wmask)

    @override
    def monitor(self):
        hwIO = self.hwIO

        yield WaitCombRead()
        en = self.notReset()
        yield WaitWriteOnly()
        if self._requireInit or not en:
            hwIO.ip2bus_rdack.write(0)
            hwIO.ip2bus_wrack.write(0)
            hwIO.ip2bus_error.write(None)
            self._requireInit = False
            if not en:
                return
        yield WaitCombRead()
        st = self._monitor_st
        if st == IpifAgentState.IDLE:
            yield WaitCombRead()
            cs = hwIO.bus2ip_cs.read()
            cs = int(cs)
            # [TODO] there can be multiple chips
            #        and we react on all chip selects
            if cs:
                # print("")
                # print(sim.now, "cs")
                self._rnw = bool(hwIO.bus2ip_rnw.read())
                self._addr = int(hwIO.bus2ip_addr.read())
                if self._rnw:
                    st = IpifAgentState.READ
                else:
                    self._be = int(hwIO.bus2ip_be.read())
                    self._wdata = hwIO.bus2ip_data.read()
                    st = IpifAgentState.WRITE
            else:
                yield WaitWriteOnly()
                # print("")
                # print(sim.now, "not cs")
                hwIO.ip2bus_rdack.write(0)
                hwIO.ip2bus_wrack.write(0)
                hwIO.ip2bus_error.write(None)
                hwIO.ip2bus_data.write(None)

            doStabilityCheck = False
        else:
            doStabilityCheck = True

        yield WaitWriteOnly()
        if st == IpifAgentState.READ:
            hwIO.ip2bus_wrack.write(0)
            if self._latencyCntr == self.READ_LATENCY:
                # print(sim.now, "read-done")
                self._latencyCntr = 0
                d = self.onRead(self._addr)
                hwIO.ip2bus_data.write(d)
                hwIO.ip2bus_rdack.write(1)
                hwIO.ip2bus_error.write(0)
                st = IpifAgentState.IDLE
            else:
                # print(sim.now, "read-wait")
                hwIO.ip2bus_data.write(None)
                self._latencyCntr += 1

        elif st == IpifAgentState.WRITE:
            hwIO.ip2bus_rdack.write(0)
            hwIO.ip2bus_data.write(None)
            if self._latencyCntr == self.WRITE_LATENCY:
                # print(sim.now, "write-done")
                self.onWrite(self._addr, self._wdata, self._be)
                hwIO.ip2bus_wrack.write(1)
                hwIO.ip2bus_error.write(0)
                self._latencyCntr = 0
                st = IpifAgentState.IDLE
            else:
                # print(sim.now, "write-wait")
                self._latencyCntr += 1

        if doStabilityCheck:
            sim = self.sim
            yield WaitCombStable()
            cs = bool(hwIO.bus2ip_cs.read())
            assert cs, (sim.now, "chip select signal has to be stable")
            rnw = bool(hwIO.bus2ip_rnw.read())
            assert rnw == self._rnw, (
                sim.now, "read not write signal has to be stable",
                rnw, self._rnw)
            addr = int(hwIO.bus2ip_addr.read())
            assert addr == self._addr, (
                sim.now, "address signal has to be stable",
                addr, self._addr)
            if st == IpifAgentState.WRITE:
                be = int(hwIO.bus2ip_be.read())
                assert be == self._be, (
                    sim.now, "byte enable signal has to be stable",
                    be, self._be)
                d = hwIO.bus2ip_data.read()
                assert (self._wdata.val == d.val
                        and self._wdata.vld_mask == d.vld_mask), (
                    sim.now, "ip2bus_data signal has to be stable",
                    be, self._be)

        self._monitor_st = st

    @override
    def driver(self):
        hwIO = self.hwIO
        actual = self.actual
        actual_next = actual
        if self._requireInit:
            yield WaitWriteOnly()
            hwIO.bus2ip_cs.write(0)
            self._requireInit = False

        yield WaitCombRead()
        # now we are after clk edge
        if actual is not NOP:
            if actual[0] is READ:
                yield WaitCombRead()
                rack = hwIO.ip2bus_rdack.read()
                rack = int(rack)
                if rack:
                    d = hwIO.ip2bus_data.read()
                    if self._debugOutput is not None:
                        name = self.hwIO._getFullName()
                        self._debugOutput.write(f"{name:s}, on {self.sim.now} read_data: {d.val:d}\n")
                    self.r_data.append(d)
                    actual_next = NOP
            else:
                # write in progress
                wack = int(hwIO.ip2bus_wrack.read())
                if wack:
                    if self._debugOutput is not None:
                        name = self.hwIO._getFullName()
                        self._debugOutput.write(f"{name:s}, on {self.sim.now} write_ack\n")
                    actual_next = NOP

        en = self.notReset()
        if en:
            if self.actual is NOP:
                if self.requests:
                    req = self.requests.popleft()
                    if req is not NOP:
                        yield WaitWriteOnly()
                        self.doReq(req)
                        self.actual = req
                        return
            else:
                self.actual = actual_next
                return

        yield WaitWriteOnly()
        hwIO.bus2ip_cs.write(0)
