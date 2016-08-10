from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.ipif import IPIFWithCE


class IpifConv(Unit):
    def _config(self):
        self.IN_SUFFIX = "_in"
        self.OUT_SUFFIX = "_out"
        
        
    def _declr(self):
        with self._paramsShared(), self._asExtern():
            addClkRstn(self)
            self.cntrl = IPIFWithCE()
    
    def _declr(self):
        Unit._declr(self)