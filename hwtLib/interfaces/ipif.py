from hwt.hdlObjects.typeShortcuts import vecT
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param, evalParam
from hwt.interfaces.std import s, D


class IPIF(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        # read /write addr
        self.bus2ip_addr = s(dtype=vecT(self.ADDR_WIDTH))
        self.bus2ip_data = s(dtype=vecT(self.DATA_WIDTH))
        # byte enable for bus2ip_data
        self.bus2ip_be = s(dtype=vecT(4))

        # A High level indicates the transfer request is a user IP read.
        # A Low level indicates the transfer request is a user IP write.
        self.bus2ip_rnw = s()

        # chip select
        self.bus2ip_cs = s()

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
