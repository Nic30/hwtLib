from hdl_toolkit.interfaces.std import BramPort_withoutClk
from hdl_toolkit.synthesizer.codeOps import c
from hwtLib.handshaked.bramReader import HsBramPortReader


class HsFlipRamReader(HsBramPortReader):
    """
    Same as HsBramPortReader but has one BRAM port more.
    Every data which is readed, is  overwritten with 0.
    """
    def _declr(self):
        super()._declr()
        with self._asExtern(), self._paramsShared():
            self.dataWriteBack = BramPort_withoutClk()
                
    
    def cleanAfterRead(self):
        st = self.st
        st_t = st._dtype
        wb = self.dataWriteBack
        c((self.data_flag & st._eq(st_t.sendingData)) , wb.we)
        c(0, wb.din)
        c(1, wb.en)
        c(self.addr, wb.addr) 
                
    def _impl(self):
        HsBramPortReader._impl(self)
        self.cleanAfterRead()
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = HsFlipRamReader()
    print(toRtl(u))        
