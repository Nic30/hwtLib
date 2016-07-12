from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.interfaces.amba import AxiStream_withUserAndStrb
from hdl_toolkit.interfaces.frameLink import FrameLink
from hdl_toolkit.synthetisator.shortcuts import toRtl

from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c, Concat
from hdl_toolkit.hdlObjects.typeShortcuts import hBit, vec
from hdl_toolkit.bitmask import Bitmask
from hdl_toolkit.synthetisator.rtlLevel.codeOp import Switch, If

from hwtLib.axi.axis_sof import AxiSsof 

def strbToRem(strbBits, remBits):
    for i in range(strbBits):
        strb = vec(Bitmask.mask(i + 1), strbBits)
        rem = vec(i, remBits)
        yield strb, rem

class AxiSToFrameLink(Unit):
    """
    Axi 4 stream to FrameLink 
    based on AXI4_STREAM_FRAMELINK from fpgalib
    """
    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.USER_WIDTH = Param(2)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.dataIn = AxiStream_withUserAndStrb()
            self.dataOut = FrameLink()
        
        self._shareAllParams()
        self.sofDetect = AxiSsof()
        
    def _impl(self):
        assert(evalParam(self.USER_WIDTH).val == 2)  # this is how is protocol specified
        In = self.dataIn
        Out = self.dataOut
        
        propagateClkRstn(self)
        sof = self.sofDetect.sof
        
        c(In.data, Out.data)
        c(~In.valid, Out.src_rdy_n)
        
        outRd = ~Out.dst_rdy_n
        self.sofDetect.listenOn(In, outRd)
        c(outRd, In.ready)
        
        c(~In.last, Out.eof_n)
        
        
        # AXI_USER(0) -> FL_SOP_N
        # Always set FL_SOP_N when FL_SOF_N - added for compatibility with xilinx 
        # axi components. Otherwise FL_SOP_N would never been set and FrameLink
        # protocol would be broken.
        sop = In.user[0]
        If(sof,
           c(hBit(0), Out.sop_n)
           ,
           c(~sop, Out.sop_n)
        )
        
        # AXI_USER(1) -> FL_EOP_N
        # Always set FL_EOP_N when FL_EOF_N - added for compatibility with xilinx 
        # axi components. Otherwise FL_EOP_N would never been set and FrameLink
        # protocol would be broken.
        eop = In.user[1]
        If(In.last,
           c(hBit(0), Out.eop_n)
           ,
           c(~eop, Out.eop_n)
        )

        remMap = []
        remBits = Out.rem._dtype.bit_length()
        strbBits = In.strb._dtype.bit_length()
        
        for strb, rem in strbToRem(strbBits, remBits):
            remMap.append((strb, c(rem, Out.rem)))
        
        end_of_part_or_transaction = In.last | eop
        
        
        If(end_of_part_or_transaction,
            Switch(In.strb,
                *remMap
            )
            ,
            c(vec(-1, remBits), Out.rem)
        )
        
        c(~sof, Out.sof_n)
        

class FrameLinkToAxiS(Unit):
    """
    Framelink to axi-stream
    """
    def _config(self):
        AxiSToFrameLink._config(self)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.dataIn = FrameLink()
            self.dataOut = AxiStream_withUserAndStrb()
        
        self._shareAllParams()
    
    def _impl(self):
        In = self.dataIn
        Out = self.dataOut
        
        sop = self._sig("sop")
        eop = self._sig("eop")
        
        
        c(In.data, Out.data)
        c(~In.src_rdy_n, Out.valid)
        c(~Out.ready, In.dst_rdy_n)
        
        c(~In.eof_n, Out.last)
        c(~In.eop_n, eop)
        c(~In.sop_n, sop)
        
        c(Concat(eop, sop), Out.user)

        strbMap = []
        remBits = In.rem._dtype.bit_length()
        strbBits = Out.strb._dtype.bit_length()
        for strb, rem in strbToRem(strbBits, remBits):
            strbMap.append((rem, c(strb, Out.strb)))
        Switch(In.rem,
                *strbMap
        )

if __name__ == "__main__":
    u = AxiSToFrameLink()
    
    print(toRtl(u))
