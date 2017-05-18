from hwt.hdlObjects.typeShortcuts import vecT
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param, evalParam
from hwt.interfaces.std import s, D
from hwt.simulator.agentBase import SyncAgentBase
from hwt.hdlObjects.constants import READ, WRITE, NOP
from hwt.bitmask import mask


class IPIF(Interface):
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
        self.bus2ip_addr = s(dtype=vecT(self.ADDR_WIDTH))
        
        self.bus2ip_data = s(dtype=vecT(self.DATA_WIDTH))
        # byte enable for bus2ip_data
        self.bus2ip_be = s(dtype=vecT(evalParam(self.DATA_WIDTH) // 8))
        
        self.ip2bus_data = s(dtype=vecT(self.DATA_WIDTH), masterDir=D.IN)
        # write ack
        self.ip2bus_wrack = s(masterDir=D.IN)
        # read ack
        self.ip2bus_rdack = s(masterDir=D.IN)
        self.ip2bus_error = s(masterDir=D.IN)

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        DW = evalParam(self.DATA_WIDTH).val
        return DW // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address (f.e. 8 bits for  char * pointer,
             36 for 36 bit bram)
        """
        return 8
    
    def _getSimAgent(self):
        return IPIFAgent


class IPIFWithCE(IPIF):
    def _config(self):
        super(IPIFWithCE, self)._config()
        self.REG_COUNT = Param(1)

    def _declr(self):
        super()._declr()
        ce_t = vecT(self.REG_COUNT)
        # read chip enable bus
        self.bus2ip_rdce = s(dtype=ce_t)
        # Write chip enable bus
        self.bus2ip_wrce = s(dtype=ce_t)


class IPIFAgent(SyncAgentBase):
    """
    :ivar requests: list of tuples (request type, address, [write data]) - used for driver
    :ivar data: list of data in memory, used for monitor
    :ivar mem: if agent is in monitor mode (= is slave) all reads and writes are performed on
        mem object
    :ivar actual: actual request which is performed
    """
    def __init__(self, intf, clk=None, rstn=None, allowNoReset=True):
        super().__init__(intf, clk=clk, rstn=rstn, allowNoReset=allowNoReset)

        self.requests = []
        self.actual = NOP
        self.readed = []
        
        self.wmaskAll = mask(intf.bus2ip_data._dtype.bit_length())

        self.mem = {}
        self.requireInit = True

    def doReq(self, s, req):
        rw = req[0]
        addr = req[1]
        
        if rw == READ:
            rw = IPIF.READ
            wdata = None
            wmask = None
        elif rw == WRITE:
            wdata = req[2]
            rw = IPIF.WRITE
            wmask = self.wmaskAll
        else:
            raise NotImplementedError(rw)

        intf = self.intf
        
        s.w(1, intf.bus2ip_cs)
        s.w(rw, intf.bus2ip_rnw)
        s.w(addr, intf.bus2ip_addr)
        s.w(wdata, intf.bus2ip_data)
        s.w(wmask, intf.bus2ip_be)

    def monitor(self, s):
        raise NotImplementedError()

    def driver(self, s):
        intf = self.intf
        actual = self.actual
      
        if self.requireInit:
            s.w(0, intf.bus2ip_cs)
            self.requireInit = False

        yield s.updateComplete         
        # now we are after clk edge

        en = s.r(self.rst_n).val and self.enable
        if en and self.requests and self.actual is NOP:
            req = self.requests.pop(0)
            if req is NOP:
                s.w(0, intf.bus2ip_cs)
            else:
                self.doReq(s, req)
                self.actual = req  
        else:
            s.w(0, intf.bus2ip_cs)

        if actual is not NOP:
            yield s.updateComplete
            if actual[0] is READ:
                rack = s.r(intf.ip2bus_rdack)
                assert rack.vldMask == 1
                if rack.val:
                    d = s.r(intf.ip2bus_data)
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r read_data: %d\n" % (
                                                self.intf._getFullName(), s.now, d.val))
                    self.readed.append(d)
                    self.actual = NOP
            else:
                # write in progress
                wack = s.r(intf.ip2bus_wrack)
                assert wack.vldMask == 1
                if wack.val:
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, on %r write_ack\n" % (
                                                self.intf._getFullName(), s.now))
                    self.actual = NOP