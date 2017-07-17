from collections import deque

from hwt.bitmask import mask
from hwt.hdlObjects.constants import READ, WRITE, NOP
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import s, D, VectSignal
from hwt.simulator.agentBase import SyncAgentBase
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param


class Ipif(Interface):
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
        :return: how many bits is one unit of address (f.e. 8 bits for  char * pointer,
             36 for 36 bit bram)
        """
        return 8

    def _getSimAgent(self):
        return IpifAgent


class IpifWithCE(Ipif):
    def _config(self):
        super(IpifWithCE, self)._config()
        self.REG_COUNT = Param(1)

    def _declr(self):
        super()._declr()
        ce_t = vecT(self.REG_COUNT)
        # read chip enable bus
        self.bus2ip_rdce = s(dtype=ce_t)
        # Write chip enable bus
        self.bus2ip_wrce = s(dtype=ce_t)


class IpifAgent(SyncAgentBase):
    """
    :ivar requests: list of tuples (request type, address, [write data], [write mask]) - used for driver
    :ivar data: list of data in memory, used for monitor
    :ivar mem: if agent is in monitor mode (= is slave) all reads and writes are performed on
        mem object
    :ivar actual: actual request which is performed
    """
    def __init__(self, intf, allowNoReset=True):
        super().__init__(intf, allowNoReset=allowNoReset)

        self.requests = deque()
        self.actual = NOP
        self.readed = deque()

        self.wmaskAll = mask(intf.bus2ip_data._dtype.bit_length()//8)

        self.mem = {}
        self.requireInit = True

    def doReq(self, s, req):
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
            raise NotImplementedError(rw)

        intf = self.intf
        w = s.write
        w(1, intf.bus2ip_cs)
        w(rw, intf.bus2ip_rnw)
        w(addr, intf.bus2ip_addr)
        w(wdata, intf.bus2ip_data)
        w(wmask, intf.bus2ip_be)

    def monitor(self, s):
        raise NotImplementedError()

    def driver(self, s):
        intf = self.intf
        actual = self.actual
        actual_next = actual
        w = s.write
        r = s.read

        if self.requireInit:
            w(0, intf.bus2ip_cs)
            self.requireInit = False

        yield s.updateComplete
        # now we are after clk edge
        if actual is not NOP:
            yield s.updateComplete
            if actual[0] is READ:
                rack = r(intf.ip2bus_rdack)
                assert rack.vldMask == 1
                if rack.val:
                    d = r(intf.ip2bus_data)
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r read_data: %d\n" % (
                                                self.intf._getFullName(), s.now, d.val))
                    self.readed.append(d)
                    actual_next = NOP
            else:
                # write in progress
                wack = r(intf.ip2bus_wrack)
                assert wack.vldMask == 1
                if wack.val:
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r write_ack\n" % (
                                                self.intf._getFullName(), s.now))
                    actual_next = NOP

        en = self.notReset(s) and self.enable
        if en:
            if self.actual is NOP:
                if self.requests:
                    req = self.requests.popleft()
                    if req is not NOP:
                        self.doReq(s, req)
                        self.actual = req
                        return
            else:
                self.actual = actual_next
                return
        w(0, intf.bus2ip_cs)
