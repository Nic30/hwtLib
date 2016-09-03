from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import s
from hdl_toolkit.interfaces.utils import log2ceil
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam


class BinToOneHot(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(32)
    
    def _declr(self):
        with self._asExtern():
            self.din = s(dtype=vecT(log2ceil(self.DATA_WIDTH)))
            self.en = s()
            self.dout = s(dtype=vecT(self.DATA_WIDTH))

    def _impl(self):
        en = self.en
        dIn = self.din
        
        WIDTH = self.DATA_WIDTH
        # empty_gen
        if evalParam(WIDTH).val == 1:
            self.dout[0] ** en
        else:
            # full_gen
            for i in range(evalParam(WIDTH).val):
                self.dout[i] ** (dIn._eq(i) & en)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(BinToOneHot))
