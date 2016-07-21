from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.std import Signal, VldSynced
from hdl_toolkit.interfaces.amba import AxiStream
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit, vec
from hdl_toolkit.synthetisator.codeOps import c, fitTo, If, Switch
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hdl_toolkit.bitmask import Bitmask
from hdl_toolkit.interfaces.utils import addClkRstn

class AxiSSampler(Unit):
    """    
        Samples values of a source into the output AXI-Stream
        interface. Samples are read from the sample interface.
        
        Sampling is done on request, ie. by asserting REQ.
        The value is sampled as soon as possible (may block
        if SAMPLE_VLD is low). The BUSY signal informs that
        the unit is blocking and waiting for SAMPLE_VLD high.
        
        The unit blocks (BUSY) also when the M_TREADY is low.
        In that case, the SAMPLE_DI value is saved internally.
        Ie. the sampled value always correlates as much as
        possible to the time when REQ has been asserted.
        
        @attention: last is always set
        @attention: strb is always -1
    """
    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.SAMPLE_WIDTH = Param(32)

    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            
            self.req = Signal()
            self.busy = Signal()
            self.done = Signal()
            
            self.out = AxiStream()
            self.out._replaceParam('DATA_WIDTH', self.DATA_WIDTH)
            
            self.sample = VldSynced()
            self.sample._replaceParam('DATA_WIDTH', self.SAMPLE_WIDTH)
        
    def _impl(self):
        assert(evalParam(self.DATA_WIDTH).val >= evalParam(self.SAMPLE_WIDTH).val) 
        
        stT = Enum("st_t", ["stIdle", "stBusy", "stBusyHold"])

        st = self._reg("st", stT, stT.stIdle)
        sample = self._reg('sample', vecT(self.SAMPLE_WIDTH))
        sample_ce = self._sig("sample_ce")
        
        # reg_samplep
        If(sample_ce,
           c(fitTo(self.sample.data, sample), sample)
        ).Else(
           c(sample, sample)
        )
        
        # shortcuts
        sampleIn = self.sample
        out = self.out
        req = self.req
        
        # fsm_next
        Switch(st)\
        .Case(stT.stIdle,
            If(req,
                If(sampleIn.vld._eq(hBit(0)),
                    c(stT.stBusy, st)
                ).Elif(out.ready,
                    c(stT.stBusyHold, st)
                ).Else(
                    c(st, st)
                )
            ).Else(
                c(st, st)
            )
        ).Case(stT.stBusy,
            If(sampleIn.vld,
                If(out.ready,
                    c(stT.stIdle)
                ).Else(
                    c(stT.stBusyHold)
                )
            ).Else(
               c(st, st)
            )
        ).Case(stT.stBusyHold,
            If(out.ready,
               c(stT.stIdle, st)
            ).Else(
               c(st, st)
            )
        )
        
        
        # fsm_output
        c((sampleIn.vld & ~out.ready) & ((st._eq(stT.stIdle) & req) | (st._eq(stT.stBusy))),
            sample_ce)
        
        If(st._eq(stT.stBusyHold),
           c(fitTo(sample, out.data), out.data)
        ).Else(
           c(fitTo(sampleIn.data, out.data), out.data)
        )
        c(st != stT.stIdle, self.busy)
        
        strbw = out.strb._dtype.bit_length()
        c(vec(Bitmask.mask(strbw), strbw), out.strb)
        c(hBit(1), out.last)
        Switch(st)\
        .Case(stT.stIdle,
            If(req & sampleIn.vld,
               c(hBit(1), out.valid)
            ).Else(
               c(hBit(0), out.valid)
            ),
            c(req & sampleIn.vld & out.ready, self.done)
        ).Case(stT.stBusy,
            c(sampleIn.vld, out.valid), 
            c(sampleIn.vld & out.ready, self.done)
        ).Case(stT.stBusyHold,
           c(hBit(1), out.valid), 
           c(out.ready, self.done) 
        )
if __name__ == "__main__":
    print(toRtl(AxiSSampler)) 
        
        
        
