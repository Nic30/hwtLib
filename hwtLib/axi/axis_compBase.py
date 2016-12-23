#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.interfaces.amba import AxiStream_withoutSTRB


class AxiSCompBase(HandshakedCompBase):
    def __init__(self, hsIntfCls):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(hsIntfCls, AxiStream_withoutSTRB)), hsIntfCls
        self.intfCls = hsIntfCls
        Unit.__init__(self)
        
    def getVld(self, intf):
        return intf.valid
    
    def getRd(self, intf):
        return intf.ready