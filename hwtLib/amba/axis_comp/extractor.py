#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint

from hwt.code import If, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import VldSynced, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.amba.axis import AxiStream_withoutSTRB


def unpackDataPositions(record, wordWidth):
    if len(record) == 4:
        return record
    
    elif len(record) == 2:
        wordIndex, name = record
        offset = 0
        bitSize = wordWidth
        
        return wordIndex, name, offset, bitSize
    else:
        raise TypeError("Wrong format of data map %s" % (str(record)))
        
        

class AxiSExtractor(Unit):
    """
    This unit extracts fields from stream
    
    actual configuration is:
    (wordindex, name, bitoffset, size)"""
    def __init__(self, data_map):
        """
        @param data_map: array of tupes (wordIndex, name) or (wordIndex, name, offset, bitSize) 
        """
        self.DATA_MAP = data_map 
        super().__init__()
        
    def decorateWithExtractedInterfaces(self):
        assert len(self.DATA_MAP) > 0
 
        self._dataMapped = []
        for am in sorted(self.DATA_MAP, key=lambda x: x[0]):
            wordIndex, name, offset, bitSize = unpackDataPositions(am, self.DATA_WIDTH)
            p = VldSynced()
            p.DATA_WIDTH.set(bitSize)
            self._dataMapped.append(((wordIndex, name, offset, bitSize), p))
            setattr(self, name, p)
    
    def _config(self):
        AxiStream_withoutSTRB._config(self)
            
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream_withoutSTRB()
        self.dataOutRd = Signal()
        self.decorateWithExtractedInterfaces()
        
        self.__doc__ = self.__doc__ + '\n' + str(pprint.pformat(self.DATA_MAP))
            
    def _impl(self):
        cntrMax = self._dataMapped[-1][0][0]
        In = self.dataIn
        cntr = self._reg("word_cntr", vecT(log2ceil(cntrMax) + 1), defVal=0)
        allExtracted = cntr._eq(cntrMax + 1)
        
        If(In.valid & self.dataOutRd,
            If(In.last,
               cntr ** 0
            ).Elif(~allExtracted,
                cntr ** (cntr + 1)
            )
        )
        In.ready ** self.dataOutRd 
        
        for (wordIndex, _, offset, bitSize), intf in self._dataMapped:
            intf.vld ** (In.valid & cntr._eq(wordIndex) & self.dataOutRd)
            intf.data ** In.data[(bitSize + offset):offset]

      
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSExtractor([(i, "data%d" % i) for i in range(2)] + 
                      [(2, "data3a", 0, 16), (2, "data3b", 16, 16),
                       (2, "data3c", 32, 16), (2, "data3d", 48, 16)])
    
    print(toRtl(u))
      
