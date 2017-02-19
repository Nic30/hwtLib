#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.bitmask import mask
from hwt.code import Concat, Switch, If
from hwt.hdlObjects.typeShortcuts import vec
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axis import AxiStream_withUserAndStrb
from hwtLib.amba.axis_comp.sof import AxiSsof
from hwtLib.interfaces.frameLink import FrameLink


def strbToRem(strbBits, remBits):
    for i in range(strbBits):
        strb = vec(mask(i + 1), strbBits)
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
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = AxiStream_withUserAndStrb()
            self.dataOut = FrameLink()
        
        self.sofDetect = AxiSsof()
        
    def _impl(self):
        assert(evalParam(self.USER_WIDTH).val == 2)  # this is how is protocol specified
        In = self.dataIn
        Out = self.dataOut
        
        propagateClkRstn(self)
        sof = self.sofDetect.sof
        
        Out.data ** In.data
        Out.src_rdy_n ** ~In.valid
        
        outRd = ~Out.dst_rdy_n
        self.sofDetect.listenOn(In, outRd)
        In.ready ** outRd
        
        Out.eof_n ** ~In.last
        
        
        # AXI_USER(0) -> FL_SOP_N
        # Always set FL_SOP_N when FL_SOF_N - added for compatibility with xilinx 
        # axi components. Otherwise FL_SOP_N would never been set and FrameLink
        # protocol would be broken.
        sop = In.user[0]
        If(sof,
           Out.sop_n ** 0
        ).Else(
           Out.sop_n ** ~sop
        )
        
        # AXI_USER(1) -> FL_EOP_N
        # Always set FL_EOP_N when FL_EOF_N - added for compatibility with xilinx 
        # axi components. Otherwise FL_EOP_N would never been set and FrameLink
        # protocol would be broken.
        eop = In.user[1]
        If(In.last,
           Out.eop_n ** 0
        ).Else(
           Out.eop_n ** ~eop
        )

        remMap = []
        remBits = Out.rem._dtype.bit_length()
        strbBits = In.strb._dtype.bit_length()
        
        for strb, rem in strbToRem(strbBits, remBits):
            remMap.append((strb, Out.rem ** rem))
        
        end_of_part_or_transaction = In.last | eop
        
        
        If(end_of_part_or_transaction,
            Switch(In.strb)\
            .addCases(remMap)
        ).Else(
            Out.rem ** vec(-1, remBits)
        )
        
        Out.sof_n ** ~sof
        

class FrameLinkToAxiS(Unit):
    """
    Framelink to axi-stream
    """
    def _config(self):
        AxiSToFrameLink._config(self)
    
    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = FrameLink()
            self.dataOut = AxiStream_withUserAndStrb()
    
    def _impl(self):
        In = self.dataIn
        Out = self.dataOut
        
        sop = self._sig("sop")
        eop = self._sig("eop")
        
        
        Out.data ** In.data 
        Out.valid ** ~In.src_rdy_n
        In.dst_rdy_n ** ~Out.ready 
        
        Out.last ** ~In.eof_n
        eop ** ~In.eop_n 
        sop ** ~In.sop_n
        
        Out.user ** Concat(eop, sop)

        strbMap = []
        remBits = In.rem._dtype.bit_length()
        strbBits = Out.strb._dtype.bit_length()
        for strb, rem in strbToRem(strbBits, remBits):
            strbMap.append((rem, Out.strb ** strb))
        Switch(In.rem).addCases(strbMap)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = FrameLinkToAxiS()
    print(toRtl(u))
