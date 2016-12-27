from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.interfaces.utils import addClkRstn
from hwt.interfaces.std import Signal, VldSynced
from hwt.interfaces.differential import DifferentialSig
from hwt.code import Concat

FS_IDLE = 0b000
K1 = 0b001
J1 = 0b010
K2 = 0b011
J2 = 0b100
K3 = 0b101
J3 = 0b110
K4 = 0b111

class UsbPhy_1_1_rx(Unit):
    def _declr(self):
        addClkRstn(self)
        self.fs_ce = Signal()
        self.rxd = Signal()
        self.rx = DifferentialSig()
        
        self.dataIn = VldSynced()
        self.rxActive = Signal()
        self.rxError = Signal()
        self.rxEn = Signal()
        
        self.lineState = Signal()
    def _impl(self):
        s, r = self._sig, self._reg
        
        fs_ce = s("fs_ce_intern") 
        rx_active = s("rx_active_intern")
        rx_valid = s("rx_valid_intern")
        sync_err = r("sync_err", defVal=False)
        sync_err_d = s("sync_err_d")
        bit_stuff_err = s("bit_stuff_err")
        byte_err = s("byte_err")
        hold_reg= s("hold_reg")
        rxdn_s1 = s("rxdn_s1")
        rxdp_s1 = s("rxdp_s1")
        rx_en = r("rx_en_intern")
        
        #  Misc Logic 
        self.fs_ce_o ** fs_ce
        self.rxActive ** rx_active
        self.rx_valid ** rx_valid
        self.rxError ** (sync_err | bit_stuff_err | byte_err)
        self.dataIn.data ** hold_reg
        self.lineState ** Concat(rxdn_s1, rxdp_s1)
        
        rx_en ** self.rxEn
        sync_err ** (~rx_active & sync_err_d)

        # Synchronize Inputs                                                                 --

        # First synchronize to the local system clock to
        # avoid metastability outside the sync block (*_s0).
        # Then make sure we see the signal for at least two
        # clock cycles stable to avoid glitches and noise
        
        
        