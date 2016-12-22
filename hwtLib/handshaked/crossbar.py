from hwt.hdlObjects.typeShortcuts import hInt
from hwt.interfaces.std import Handshaked
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.codeOps import And, connect, If


class HsCrossbar(Unit):
    """
    Universal crossbar (N:N) for handshaked interfaces
    """
    def __init__(self, intfCls, inputsCnt=1, outputsCnt=1, **kwargs):
        self._intfCls = intfCls
        self._inputsCnt = inputsCnt
        self._outputsCnt = outputsCnt
        super(HsCrossbar, self).__init__(**kwargs)
        
    def _config(self):
        assert(self._inputsCnt == 1 or self._outputsCnt == 1)
        self._intfCls._config(self)
        
    def _declr(self):
        intf = self._intfCls()
        intf._loadDeclarations()
        self._dataSignalNames = list(map(lambda i: i._name,
                                          where(intf._interfaces,
                                                lambda i: i is not intf.vld and i is not intf.rd)
                                          ))
        
        def applyCnt(cnt):
            if cnt == 1:
                return self._intfCls()
            else:
                return self._intfCls(multipliedBy=hInt(cnt))
        
        with self._paramsShared():
            self.input = applyCnt(self._inputsCnt)
            self.output = applyCnt(self._outputsCnt)
        
        
    def _impl(self):
        
        def connectDataSigs(a, b):
            assigs = []
            for dn in self._dataSignalNames:
                assigs.extend(getattr(b, dn) ** getattr(a, dn))
            return assigs
        
        if self._inputsCnt == 1 and  self._outputsCnt == 1:
            self.output ** self.input
        elif self._inputsCnt == 1:
            # 1:N
            # rd if all outputs are ready
            self.input.rd ** And(*map(lambda i: i.rd, self.output))
            
            for i in range(self._outputsCnt):
                # data signals are always connected
                o = self.output[i]
                connectDataSigs(self.input, o)
                
                # valid if everyone else is ready and input is valid
                everyOneElseRd = And(*map(lambda i: i.rd,
                                          where(self.output,
                                                 lambda i: i is not o)
                                           )
                                     )
                o.vld ** And(everyOneElseRd, self.input.vld)
            
            
        elif self._outputsCnt == 1:
            # N:1, higher no. higher priority
            def addInput(muxExprTop, inp):
                inputsWithHigherPriority = []
                for i in reversed(list(self.input)):
                    if i is inp:
                        break
                    inputsWithHigherPriority.append(i)
                    
                if inputsWithHigherPriority:
                    rd = ~And(*map(lambda x: x.vld,
                                        inputsWithHigherPriority 
                                        )
                                  ) & self.output.rd
                else:
                    rd = self.output.rd
                inp.rd ** rd 
                
                if muxExprTop is None:
                    return connectDataSigs(inp, self.output) + connect(inp.vld, self.output.vld)
                else:
                    return If(inp.vld,
                              connectDataSigs(inp, self.output),
                              self.output.vld ** inp.vld
                            ).Else(
                              muxExprTop
                            )
            muxExprTop = None
            for inp in self.input:
                muxExprTop = addInput(muxExprTop, inp)

        else:
            raise NotImplementedError()
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = HsCrossbar(Handshaked, inputsCnt=3)
    print(toRtl(u))
    
