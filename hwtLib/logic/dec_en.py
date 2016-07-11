from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.std import s
from hdl_toolkit.interfaces.utils import log2ceil
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect

c = connect

class DecEn(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(32)
    
    def _declr(self):
        
        self.dIn= s(dtype=vecT(log2ceil(self.DATA_WIDTH)))
        self.en = s()
        self.dOut = s(dtype=vecT(self.DATA_WIDTH))
        self._mkIntfExtern()

    def _impl(self):
        en = self.en
        dIn = self.dIn
        
        
        WIDTH = self.DATA_WIDTH
        #empty_gen
        if evalParam(WIDTH).val == 1:
            c(en, self.dOut)
        else:
            # full_gen
            for i in range(evalParam(WIDTH).val):
                c(dIn._eq(i) & en, self.dOut[i])

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(DecEn))