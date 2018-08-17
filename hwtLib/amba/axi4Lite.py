from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwtLib.amba.axi3Lite import IP_Axi3Lite, Axi3Lite, Axi3Lite_r,\
    Axi3Lite_b, Axi3Lite_w, Axi3Lite_addr, Axi3Lite_addrAgent
from hwtLib.amba.axi_intf_common import AxiMap


class Axi4Lite_addr(Axi3Lite_addr):
    def _declr(self):
        super(Axi4Lite_addr, self)._declr()
        self.prot = VectSignal(3)

    def _initSimAgent(self):
        self._ag = Axi4Lite_addrAgent(self)


class Axi4Lite_addrAgent(Axi3Lite_addrAgent):
    """
    :ivar data: iterable of addr
    """

    def doRead(self, s):
        return s.read(self.intf.addr), s.read(self.intf.prot)

    def doWrite(self, s, data):
        if data is None:
            addr, prot = None, None
        else:
            addr, prot = data

        s.write(addr, self.intf.addr)
        s.write(prot, self.intf.prot)


class Axi4Lite_w(Axi3Lite_w):
    pass


class Axi4Lite_b(Axi3Lite_b):
    pass


class Axi4Lite_r(Axi3Lite_r):
    pass


class Axi4Lite(Axi3Lite):
    """
    Axi4-lite bus interface
    """

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi4Lite_addr()
            self.ar = Axi4Lite_addr()
            self.w = Axi4Lite_w()
            self.r = Axi4Lite_r(masterDir=DIRECTION.IN)
            self.b = Axi4Lite_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi4Lite


class IP_Axi4Lite(IP_Axi3Lite):
    """
    IP core meta description for Axi4-lite interface
    """

    def __init__(self):
        super().__init__()
        self.quartus_name = "axi4lite"
        a_sigs = ['addr', 'prot', 'valid', 'ready']
        self.map = {'aw': AxiMap('aw', a_sigs),
                    'w': AxiMap('w', ['data', 'strb', 'valid', 'ready']),
                    'ar': AxiMap('ar', a_sigs),
                    'r': AxiMap('r', ['data', 'resp', 'valid', 'ready']),
                    'b': AxiMap('b', ['valid', 'ready', 'resp'])
                    }
