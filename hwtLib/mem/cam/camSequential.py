from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.interfaces.std import Ap_hs, Ap_vld

from hwtLib.mem.cam.interfaces import AddrDataHs
from hwtLib.mem.cam.camWrite import CamWrite
from hwtLib.mem.cam.camStorage import CamStorage

class CamSequential(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(36)
        self.ITEMS = Param(16)
        # Value of matching Sequencing Factor (SF).
        # Must be in range 0-6.
        # Duration of every match is 2^SF cycles.
        # Duration of every item write is 2^(6-SF) cycles.
        # One 7Series 6-LUT can store 2^SF elements (CAM cell height) of (6-SF) bits (CAM cell width).
        # SHORT: Higher SF means fewer FPGA resources but lower throughtput of matching.
        self.SEQUENCING_FACTOR = Param(0)
        
        
        # What to do when write and match are both requested in the same cycle?
        # true = write has higher priority
        # false = read has higher priority
        self.WRITE_BEFORE_MATCH = Param(False)
        
    def _declr(self):
        addClkRstn(self)
        self.match = Ap_hs()
        self.write = AddrDataHs()
        self.out = Ap_vld()
        
        self._mkIntfExtern()

        self.camWrite = CamWrite()
        self.camStorage = CamStorage()
        self.camMatch = CamMatch()
        
        self._shareAllParams()
    
    def _impl(self):
        propagateClkRstn(self)
        
