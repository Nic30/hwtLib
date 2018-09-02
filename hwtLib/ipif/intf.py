from collections import deque
from enum import Enum

from hwt.bitmask import mask
from hwt.hdl.constants import READ, WRITE, NOP
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import s, D, VectSignal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param


# https://www.xilinx.com/support/documentation/ip_documentation/axi_lite_ipif/v2_0/pg155-axi-lite-ipif.pdf
# https://www.xilinx.com/support/documentation/ip_documentation/axi_lite_ipif_ds765.pdf
class Ipif(Interface):
    """
    IPIF - IP interface is interface which was often used
    in designs for Xilinx FPGAs around year 2012

    * shared address, validity signals, mask, write ack
    """
    READ = 1
    WRITE = 0

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        # chip select
        self.bus2ip_cs = s()

        # A High level indicates the transfer request is a user IP read.
        # A Low level indicates the transfer request is a user IP write.
        self.bus2ip_rnw = s()

        # read /write addr
        self.bus2ip_addr = VectSignal(self.ADDR_WIDTH)

        self.bus2ip_data = VectSignal(self.DATA_WIDTH)
        # byte enable for bus2ip_data
        self.bus2ip_be = VectSignal(self.DATA_WIDTH // 8)

        self.ip2bus_data = VectSignal(self.DATA_WIDTH, masterDir=D.IN)
        # write ack
        self.ip2bus_wrack = s(masterDir=D.IN)
        # read ack
        self.ip2bus_rdack = s(masterDir=D.IN)
        self.ip2bus_error = s(masterDir=D.IN)

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

    def _initSimAgent(self):
        self._ag = IpifAgent(self)


class IpifWithCE(Ipif):

    def _config(self):
        super(IpifWithCE, self)._config()
        self.REG_COUNT = Param(1)

    def _declr(self):
        super()._declr()
        ce_t = Bits(self.REG_COUNT)
        # read chip enable bus
        self.bus2ip_rdce = s(dtype=ce_t)
        # Write chip enable bus
        self.bus2ip_wrce = s(dtype=ce_t)


class IpifAgentState(Enum):
    IDLE = 0
    READ = 1
    WRITE = 2


class IpifAgent(SyncAgentBase):
    """
    :ivar requests: list of tuples (READ, address) or 
        (WRITE, address, data, mask) used for driver
    :ivar readed: list of readed data for driver
    :ivar mem: if agent is in monitor mode (= is slave)
        all reads and writes are performed on mem object, index is word index
    :note: this behavior can be overriden by onRead/onWrite methods
    :ivar actual: actual request which is performed (in driver mode)
    """

    def __init__(self, intf, allowNoReset=True):
        super().__init__(intf, allowNoReset=allowNoReset)
        
        # for driver only
        self.requests = deque()
        self.actual = NOP
        self.readed = deque()

        # for monitor only
        self.READ_LATENCY = 0
        self.WRITE_LATENCY = 0
        self.mem = {}
        self._monitor_st = IpifAgentState.IDLE
        self._addr = self._rnw = self._be = self._wdata = None
        self._latencyCntr = 0
    
        self._word_bytest = intf.bus2ip_data._dtype.bit_length() // 8
        self.wmaskAll = mask(self._word_bytest)
        self._requireInit = True

    def onRead(self, sim, addr):
        if addr % self._word_bytest != 0:
            raise NotImplementedError("Unaligned read")

        return self.mem[int(addr) // self._word_bytest]

    def onWrite(self, sim, addr, val, byteen):
        if addr % self._word_bytest != 0:
            raise NotImplementedError("Unaligned write")
        
        if int(byteen) == self.wmaskAll:
            self.mem[addr//self._word_bytest] = val
        else:
            raise NotImplementedError("Masked write")
    
    def doReq(self, sim, req):
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

        intf = self.intf
        w = sim.write
        w(1, intf.bus2ip_cs)
        w(rw, intf.bus2ip_rnw)
        w(addr, intf.bus2ip_addr)
        w(wdata, intf.bus2ip_data)
        w(wmask, intf.bus2ip_be)

    def monitor(self, sim):
        intf = self.intf
        w = sim.write
        r = sim.read
        
        en = self.notReset(sim)
        if self._requireInit or not en:
            w(0, intf.ip2bus_rdack)
            w(0, intf.ip2bus_wrack)
            w(None, intf.ip2bus_error)
            self._requireInit = False
            if not en:
                return
        
        #yield sim.waitOnCombUpdate()
        st = self._monitor_st
        if st == IpifAgentState.IDLE:
            cs = r(intf.bus2ip_cs)
            cs = int(cs)
            # [TODO] there can be multiple chips and we react on all chip selects
            if cs:
                # print("")
                # print(sim.now, "cs")
                self._rnw = bool(r(intf.bus2ip_rnw))
                self._addr = int(r(intf.bus2ip_addr))
                if self._rnw:
                    st = IpifAgentState.READ
                else:
                    self._be = int(r(intf.bus2ip_be))
                    self._wdata = r(intf.bus2ip_data)
                    st = IpifAgentState.WRITE
            else:
                # print("")
                # print(sim.now, "not cs")
                w(0, intf.ip2bus_rdack)
                w(0, intf.ip2bus_wrack)
                w(None, intf.ip2bus_error)
                w(None, intf.ip2bus_data)
                    
            doStabilityCheck = False 
        else:
            doStabilityCheck = True
            
        if st == IpifAgentState.READ:
            w(0, intf.ip2bus_wrack)
            if self._latencyCntr == self.READ_LATENCY:
                # print(sim.now, "read-done")
                self._latencyCntr = 0
                d = self.onRead(sim, self._addr)
                w(d, intf.ip2bus_data)
                w(1, intf.ip2bus_rdack)
                w(0, intf.ip2bus_error)
                st = IpifAgentState.IDLE
            else:
                # print(sim.now, "read-wait")
                w(None, intf.ip2bus_data)
                self._latencyCntr += 1

        elif st == IpifAgentState.WRITE:
            w(0, intf.ip2bus_rdack)
            w(None, intf.ip2bus_data)
            if self._latencyCntr == self.WRITE_LATENCY:
                # print(sim.now, "write-done")
                self.onWrite(sim, self._addr, self._wdata, self._be)
                w(1, intf.ip2bus_wrack)
                w(0, intf.ip2bus_error)
                self._latencyCntr = 0
                st = IpifAgentState.IDLE
            else:
                # print(sim.now, "write-wait")
                self._latencyCntr += 1 
        
        if doStabilityCheck:
            yield sim.waitOnCombUpdate()
            cs = bool(r(intf.bus2ip_cs))
            assert cs, (sim.now, "chip select signal has to be stable")
            rnw = bool(r(intf.bus2ip_rnw))
            assert rnw == self._rnw, (sim.now, "read not write signal has to be stable", rnw, self._rnw)
            addr = int(r(intf.bus2ip_addr))
            assert addr == self._addr, (sim.now, "address signal has to be stable", addr, self._addr)
            if st == IpifAgentState.WRITE:
                be = int(r(intf.bus2ip_be))
                assert be == self._be, (sim.now, "byte enable signal has to be stable", be, self._be)
                d = r(intf.bus2ip_data)
                assert self._wdata.val == d.val and self._wdata.vldMask == d.vldMask, (
                    sim.now, "ip2bus_data signal has to be stable", be, self._be)
        
        self._monitor_st = st

    def driver(self, sim):
        intf = self.intf
        actual = self.actual
        actual_next = actual
        w = sim.write
        r = sim.read

        if self._requireInit:
            w(0, intf.bus2ip_cs)
            self._requireInit = False

        yield sim.waitOnCombUpdate()
        yield sim.waitOnCombUpdate()
        # now we are after clk edge
        if actual is not NOP:
            if actual[0] is READ:
                rack = r(intf.ip2bus_rdack)
                assert rack.vldMask == 1
                if rack.val:
                    d = r(intf.ip2bus_data)
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r read_data: %d\n" % (
                                                self.intf._getFullName(),
                                                sim.now, d.val))
                    self.readed.append(d)
                    actual_next = NOP
            else:
                # write in progress
                wack = r(intf.ip2bus_wrack)
                assert wack.vldMask == 1
                if wack.val:
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r write_ack\n" % (
                                                self.intf._getFullName(),
                                                sim.now))
                    actual_next = NOP

        en = self.notReset(sim)
        if en:
            if self.actual is NOP:
                if self.requests:
                    req = self.requests.popleft()
                    if req is not NOP:
                        self.doReq(sim, req)
                        self.actual = req
                        return
            else:
                self.actual = actual_next
                return
        w(0, intf.bus2ip_cs)
